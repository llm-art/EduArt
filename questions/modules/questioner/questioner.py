"""Main LLM questioner orchestrator class."""

import json
import os
import random
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from tqdm import tqdm

from ..llm.factory import create_providers_from_config
from ..processors.question_parser import QuestionParser
from ..managers.results_manager import ResultsManager
from ..core.exceptions import ProcessingError, ConfigurationError
from .config import QuestionerConfig


# Experiment configuration table
EXPERIMENT_CONFIG = {
    'openai':             {'temperature': 1, 'seed': 42, 'max_tokens': 1024},
    'google':             {'temperature': 1, 'seed': 42, 'max_tokens': 1024},
    'anthropic':          {'temperature': 0, 'seed': None, 'max_tokens': 1024},
    'harvard_anthropic':  {'temperature': 0, 'seed': None, 'max_tokens': 1024},
    'harvard_openweight': {'temperature': 0, 'seed': None, 'max_tokens': 1024},
}

# Prompt condition -> prompt filename mapping
PROMPT_FILES = {
    'motivation': 'answer_question_motivation.txt',
    'default': 'answer_question.txt',
}


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry function with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt)
            time.sleep(delay)


class LLMQuestioner:
    """Main orchestrator for LLM question evaluation."""

    def __init__(self, models_to_test: Optional[List[str]] = None, question_mode: str = 'text',
                 base_dir: Optional[Path] = None, prompts_dir: Optional[Path] = None):
        """
        Initialize LLM questioner.

        Args:
            models_to_test: List of model specifications to test
            question_mode: Question mode - 'text' or 'screenshot'
            base_dir: Base directory for dataset operations
            prompts_dir: Directory containing prompt templates
        """
        self.config = QuestionerConfig(base_dir=base_dir)
        self.question_mode = question_mode
        self.prompts_dir = Path(prompts_dir) if prompts_dir else None
        self.base_dir = base_dir

        errors = self.config.validate_configuration()
        if errors:
            raise ConfigurationError(f"Configuration errors: {'; '.join(errors)}")

        try:
            self.providers = create_providers_from_config(models_to_test)
            self.question_parser = QuestionParser(question_mode=question_mode, prompts_dir=prompts_dir)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize components: {e}")

        self._log_lock = threading.Lock()

    def _load_system_prompt(self, condition: str) -> Optional[str]:
        """Load system prompt for a given prompt condition."""
        filename = PROMPT_FILES.get(condition)
        if not filename:
            return None
        if self.prompts_dir:
            path = self.prompts_dir / filename
        else:
            path = Path(__file__).parent.parent.parent.parent / 'prompts' / filename
        try:
            return path.read_text(encoding='utf-8').strip()
        except Exception as e:
            print(f"Warning: Could not load prompt for '{condition}' from {path}: {e}")
            return None

    def _write_log_entry(self, model_name: str, entry: Dict[str, Any],
                         prompt_condition: Optional[str] = None):
        """Write a per-question log file to answers/{model}/{condition}/{qid}.log."""
        safe_model_name = model_name.replace('/', '_').replace('\\', '_')
        qid = entry.get('question_id', 'unknown')
        if prompt_condition:
            log_dir = self.config.base_dir / 'answers' / safe_model_name / prompt_condition
        else:
            log_dir = self.config.base_dir / 'answers' / safe_model_name
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f'{qid}.log'
        try:
            log_path.write_text(
                json.dumps(entry, indent=2, ensure_ascii=False),
                encoding='utf-8',
            )
        except Exception:
            pass

    def _parse_question(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse a question file and return all data needed for querying."""
        txt_file = file_path
        question_id = self.question_parser.get_question_id_from_path(txt_file)
        json_file = self.config.get_question_metadata_path(txt_file)

        if not os.path.exists(json_file):
            return None

        question_data = self.question_parser.parse_json_file(json_file)
        if not self.question_parser.validate_question_data(question_data):
            return None

        with open(txt_file) as f:
            prompt = f.read()

        has_image = question_data.get('has_image', False)
        image_path = None
        if has_image:
            image_ref = question_data.get('image')
            if image_ref:
                img = self.config.base_dir / 'dataset' / image_ref
                if img.exists():
                    image_path = str(img)
                else:
                    has_image = False

        return {
            'question_id': question_id,
            'question_data': question_data,
            'question_type': question_data['type'],
            'prompt': prompt,
            'correct_answers': question_data['answers'],
            'has_image': has_image,
            'image_path': image_path,
        }

    def _process_single_task(
        self,
        parsed: Dict[str, Any],
        provider,
        system_prompt: Optional[str],
        prompt_condition: str,
        results_manager: ResultsManager,
        force: bool,
        run_index: Optional[int] = None,
    ) -> str:
        """
        Process a single (question, provider, condition, run) task.
        Stores only the raw LLM response — no evaluation.
        Returns 'success', 'skipped', or 'failed'.
        """
        question_id = parsed['question_id']
        question_type = parsed['question_type']
        model_name = provider.get_model_name()
        prompt = parsed['prompt']
        image_path = parsed['image_path']
        has_image = parsed['has_image']

        # For k-runs, store in {model}/reproducibility/run{k}/{qid}.json
        is_krun = run_index is not None

        if is_krun:
            safe_model = model_name.replace('/', '_').replace('\\', '_')
            krun_dir = self.config.base_dir / 'answers' / safe_model / 'reproducibility' / f'run{run_index}'
            krun_dir.mkdir(parents=True, exist_ok=True)
            result_path = krun_dir / f"{question_id}.json"
            if not force and result_path.exists():
                return 'skipped'
        else:
            if not force and results_manager.result_exists(question_id, model_name):
                return 'skipped'

        start_time = time.time()

        try:
            def query_llm():
                result = provider.query(prompt, system_prompt=system_prompt, image_path=image_path)
                if isinstance(result, tuple) and len(result) == 2:
                    return result
                return result, {'input_tokens': 0, 'output_tokens': 0}

            response_data = retry_with_backoff(query_llm)

            if isinstance(response_data, tuple):
                llm_response, token_metadata = response_data
                input_tokens = token_metadata.get('input_tokens', 0)
                output_tokens = token_metadata.get('output_tokens', 0)
            else:
                llm_response = response_data
                input_tokens, output_tokens = 0, 0

            # Parse answer and motivation from response
            llm_answer = llm_response
            motivation = ""
            try:
                import re as _re
                raw = llm_response.replace("```json", "").replace("```", "").strip()
                raw = _re.sub(r'^\{\{', '{', raw)
                raw = _re.sub(r'\}\}$', '}', raw)
                response_json = json.loads(raw)
                llm_answer = response_json.get('Answers', llm_response)
                motivation = response_json.get('motivation', '')
            except (json.JSONDecodeError, Exception):
                pass

            processing_time = time.time() - start_time

            # Save minimal result
            result = {
                'question_id': question_id,
                'question_type': question_type,
                'model_name': model_name,
                'prompt_condition': prompt_condition,
                'llm_answer': llm_answer,
                'raw_response': llm_response,
                'input_tokens': int(input_tokens),
                'output_tokens': int(output_tokens),
                'processing_time': round(processing_time, 3),
                'timestamp': datetime.now().isoformat(),
            }
            if motivation:
                result['motivation'] = motivation
            if is_krun:
                result['run_index'] = run_index

            # Write result JSON
            if not is_krun:
                model_dir = results_manager._prepare_model_folder(model_name, force=False)
                result_path = model_dir / f"{question_id}.json"
            # else: result_path already set above for k-runs
            result_path.write_text(
                json.dumps(result, indent=2, ensure_ascii=False),
                encoding='utf-8',
            )

            # Write log
            self._write_log_entry(model_name, {
                'timestamp': result['timestamp'],
                'question_id': question_id,
                'prompt_condition': prompt_condition,
                'question_type': question_type,
                'input_tokens': int(input_tokens),
                'output_tokens': int(output_tokens),
                'processing_time': result['processing_time'],
                'error': None,
            }, prompt_condition=prompt_condition)

            return 'success'

        except Exception as e:
            processing_time = time.time() - start_time
            error_str = f"{e.__class__.__name__}: {e}"

            self._write_log_entry(model_name, {
                'timestamp': datetime.now().isoformat(),
                'question_id': question_id,
                'prompt_condition': prompt_condition,
                'question_type': question_type,
                'input_tokens': 0,
                'output_tokens': 0,
                'processing_time': round(processing_time, 3),
                'error': error_str,
            }, prompt_condition=prompt_condition)

            return 'failed'

    def _select_reproducibility_subsample(
        self, question_files: List[Path], n: int = 100, seed: int = 42
    ) -> set:
        """
        Select a stratified random subsample for reproducibility testing.
        Stratified by (question_type, epistemic_level, has_image, language).
        Persists selection to answers/reproducibility_subsample.json.
        """
        subsample_path = self.config.base_dir / 'answers' / 'reproducibility_subsample.json'
        if subsample_path.exists():
            data = json.loads(subsample_path.read_text(encoding='utf-8'))
            return set(data['question_ids'])

        # Parse all questions to get stratification keys
        items = []
        for fp in question_files:
            parsed = self._parse_question(fp)
            if parsed:
                qd = parsed['question_data']
                items.append({
                    'question_id': parsed['question_id'],
                    'stratum': (
                        qd.get('type', ''),
                        qd.get('epistemic_level', ''),
                        str(qd.get('has_image', False)),
                        qd.get('language', ''),
                    ),
                })

        # Group by stratum
        strata = defaultdict(list)
        for item in items:
            strata[item['stratum']].append(item['question_id'])

        # Proportional sampling
        rng = random.Random(seed)
        total = len(items)
        selected = []
        for stratum_key, members in strata.items():
            k = max(1, round(len(members) / total * n))
            k = min(k, len(members))
            selected.extend(rng.sample(members, k))

        # Trim or pad to target size
        if len(selected) > n:
            selected = rng.sample(selected, n)

        # Save
        subsample_path.parent.mkdir(parents=True, exist_ok=True)
        subsample_path.write_text(json.dumps({
            'n': len(selected),
            'seed': seed,
            'question_ids': sorted(selected),
        }, indent=2, ensure_ascii=False), encoding='utf-8')

        return set(selected)

    def process_questions(
        self,
        start: Optional[int] = None,
        end: Optional[int] = None,
        question_types: Optional[List[str]] = None,
        output_file: str = 'llm_evaluation_results.csv',
        force: bool = False,
        prompt_conditions: Optional[List[str]] = None,
        workers: int = 1,
        k_runs: int = 1,
    ) -> Dict[str, Any]:
        """
        Process questions and query LLM responses.

        Args:
            start: Start question number
            end: End question number
            question_types: List of question types to filter by
            output_file: Output CSV filename (not used)
            force: Force reprocessing of existing results
            prompt_conditions: List of prompt conditions to run
            workers: Number of parallel workers
            k_runs: Number of independent runs for reproducibility subsample
        """
        if prompt_conditions is None:
            prompt_conditions = ['default', 'motivation']

        # Load system prompts for each condition
        system_prompts = {}
        for cond in prompt_conditions:
            sp = self._load_system_prompt(cond)
            if sp is None:
                raise ConfigurationError(f"Could not load system prompt for condition '{cond}'")
            system_prompts[cond] = sp

        # Create a ResultsManager per condition
        results_managers = {}
        for cond in prompt_conditions:
            results_managers[cond] = ResultsManager(
                str(self.config.results_dir),
                question_mode=self.question_mode,
                answers_base_dir=self.base_dir,
                prompt_condition=cond,
            )

        # Find and parse question files
        question_files = self.config.find_question_files(start, end, question_types)
        if not question_files:
            raise ProcessingError("No question files found matching the criteria")

        # Parse all questions upfront
        parsed_questions = {}
        for fp in question_files:
            parsed = self._parse_question(fp)
            if parsed:
                parsed_questions[parsed['question_id']] = parsed

        print(f"Found {len(parsed_questions)} questions to process")
        print(f"Providers: {len(self.providers)}")
        print(f"Prompt conditions: {prompt_conditions}")
        print(f"Workers: {workers}")

        # Select reproducibility subsample if k_runs > 1
        subsample_ids = set()
        if k_runs > 1:
            subsample_ids = self._select_reproducibility_subsample(question_files)
            print(f"Reproducibility subsample: {len(subsample_ids)} questions, k={k_runs}")

        # Build work list: (parsed, provider, condition, run_index)
        # When k_runs > 1, ONLY process the subsample (reproducibility-only mode)
        work_items = []
        for qid, parsed in sorted(parsed_questions.items()):
            if k_runs > 1 and qid not in subsample_ids:
                continue  # skip non-subsample questions in reproducibility mode
            for cond in prompt_conditions:
                for provider in self.providers:
                    if k_runs > 1:
                        for k in range(k_runs):
                            work_items.append((parsed, provider, cond, k))
                    else:
                        work_items.append((parsed, provider, cond, None))

        total = len(work_items)
        print(f"Total operations: {total}\n")

        counts = {'success': 0, 'failed': 0, 'skipped': 0}
        count_lock = threading.Lock()

        pbar = tqdm(total=total, unit="op", desc="Processing")

        def run_task(item):
            parsed, provider, cond, run_idx = item
            rm = results_managers[cond]
            sp = system_prompts[cond]
            status = self._process_single_task(
                parsed, provider, sp, cond, rm, force, run_idx
            )
            with count_lock:
                counts[status] += 1
                pbar.set_postfix(ok=counts['success'], skip=counts['skipped'], fail=counts['failed'])
                pbar.update(1)
            return status

        # Execute
        if workers <= 1:
            for item in work_items:
                run_task(item)
        else:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(run_task, item): item for item in work_items}
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        with count_lock:
                            counts['failed'] += 1
                            pbar.update(1)

        pbar.close()

        # Print summary
        print(f"\nDone: ok={counts['success']}, skip={counts['skipped']}, fail={counts['failed']}")

        # Compute reproducibility metrics if k_runs > 1
        if k_runs > 1:
            self._compute_reproducibility_metrics(
                subsample_ids, k_runs, prompt_conditions, workers,
            )

        return {
            'total_operations': total,
            'successful_operations': counts['success'],
            'failed_operations': counts['failed'],
            'skipped_operations': counts['skipped'],
            'success_rate': (counts['success'] / total * 100) if total > 0 else 0,
            'questions_processed': len(parsed_questions),
            'models_tested': len(self.providers),
            'prompt_conditions': prompt_conditions,
            'answers_folders': {c: str(rm.answers_dir) for c, rm in results_managers.items()},
        }

    def _compute_reproducibility_metrics(
        self, subsample_ids: set, k: int,
        prompt_conditions: List[str], workers: int,
    ):
        """
        Compute reproducibility metrics from k-run results.
        Reads from answers/{model}/reproducibility/run{i}/{qid}.json
        Writes report to answers/{model}/reproducibility/report.json
        """
        print(f"\nReproducibility analysis (k={k}):")

        for provider in self.providers:
            model_name = provider.get_model_name()
            safe_model = model_name.replace('/', '_').replace('\\', '_')
            repro_dir = self.config.base_dir / 'answers' / safe_model / 'reproducibility'

            # Load all runs
            by_question = defaultdict(list)  # qid -> [run0_answer, run1_answer, ...]
            for run_idx in range(k):
                run_dir = repro_dir / f'run{run_idx}'
                if not run_dir.exists():
                    continue
                for qid in sorted(subsample_ids):
                    result_path = run_dir / f'{qid}.json'
                    if result_path.exists():
                        data = json.loads(result_path.read_text(encoding='utf-8'))
                        by_question[qid].append({
                            'run': run_idx,
                            'llm_answer': data.get('llm_answer'),
                            'raw_response': data.get('raw_response', ''),
                        })

            # Compute metrics
            consistent = 0
            total_q = 0
            per_question = {}

            for qid in sorted(subsample_ids):
                runs = by_question.get(qid, [])
                if len(runs) != k:
                    continue
                total_q += 1
                answers_str = [json.dumps(r['llm_answer'], sort_keys=True, ensure_ascii=False) for r in runs]
                is_consistent = len(set(answers_str)) == 1
                if is_consistent:
                    consistent += 1
                per_question[qid] = {
                    'consistent': is_consistent,
                    'distinct_answers': len(set(answers_str)),
                    'answers': [r['llm_answer'] for r in runs],
                }

            consistency_rate = round(consistent / total_q, 4) if total_q > 0 else 0

            # Build command string
            model_specs = [p.get_model_name() for p in self.providers]
            cmd_parts = ['python llm_questioner.py']
            for ms in model_specs:
                cmd_parts.append(f'--models {ms}')
            cmd_parts.append(f'--k-runs {k}')
            if prompt_conditions != ['default', 'motivation']:
                cmd_parts.append(f'--prompt-condition {prompt_conditions[0]}')
            if workers > 1:
                cmd_parts.append(f'--workers {workers}')
            command = ' '.join(cmd_parts)

            report = {
                'model': model_name,
                'k_runs': k,
                'n_subsample': len(subsample_ids),
                'n_complete': total_q,
                'consistency_rate': f"{consistency_rate * 100:.1f}%",
                'n_consistent': consistent,
                'n_inconsistent': total_q - consistent,
                'command': command,
                'per_question': per_question,
            }

            report_path = repro_dir / 'report.json'
            report_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False),
                encoding='utf-8',
            )

            print(f"  {model_name}: consistency={consistency_rate:.1%} "
                  f"({consistent}/{total_q})")
            print(f"  Report: {report_path}")

    def get_provider_info(self) -> List[Dict[str, Any]]:
        """Get information about initialized providers."""
        return [provider.get_provider_info() for provider in self.providers]

    def print_status(self):
        """Print current questioner status."""
        print("=== LLM Questioner Status ===")
        self.config.print_configuration_status()
        print(f"\nInitialized Providers ({len(self.providers)}):")
        for provider in self.providers:
            info = provider.get_provider_info()
            print(f"  - {info['model_name']} ({info['provider_type']})")
        print("=" * 30)
