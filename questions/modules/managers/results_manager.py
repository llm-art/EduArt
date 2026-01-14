"""Results manager for storing and exporting evaluation results."""

import os
import csv
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from ..core.exceptions import ProcessingError


# Cost lookup table for different models (cost per million tokens)
MODEL_COSTS = {
    'google/gemini-2.5-flash-lite': {
        'input_cost_per_million_tokens': 0.1,
        'output_cost_per_million_tokens': 0.4
    },
    'google/gemini-2.5-flash': {
        'input_cost_per_million_tokens': 0.3,
        'output_cost_per_million_tokens': 2.5
    },
    'google/gemini-2.5-flash-preview-09-2025': {
        'input_cost_per_million_tokens': 0.3,
        'output_cost_per_million_tokens': 2.5
    },
    'google/gemini-2.5-pro': {
        'input_cost_per_million_tokens': 1.25,
        'output_cost_per_million_tokens': 10
    },
    'openai/gpt-4o': {
        'input_cost_per_million_tokens': 2.50,
        'output_cost_per_million_tokens': 10.00
    },
    'openai/gpt-4o-mini': {
        'input_cost_per_million_tokens': 0.15,
        'output_cost_per_million_tokens': 0.60
    },
    'openai/gpt-3.5-turbo': {
        'input_cost_per_million_tokens': 0.50,
        'output_cost_per_million_tokens': 1.50
    },
    'openai/gpt-4.1-2025-04-14': {
        'input_cost_per_million_tokens': 2.00,
        'output_cost_per_million_tokens': 8.00
    },
    'openai/gpt-5-2025-08-07': {
        'input_cost_per_million_tokens': 1.25,
        'output_cost_per_million_tokens': 10.00
    },
    'openai/gpt-5.2-2025-12-11': {
        'input_cost_per_million_tokens': 1.75,
        'output_cost_per_million_tokens': 14.00
    },
    'openai/gpt-5.2-pro-2025-12-11': {
        'input_cost_per_million_tokens': 21.00,
        'output_cost_per_million_tokens': 168.00
    },
    'openai/gpt-5-mini-2025-08-07': {
        'input_cost_per_million_tokens': 0.25,
        'output_cost_per_million_tokens': 2.00
    },
    'openai/gpt-5-nano-2025-08-07': {
        'input_cost_per_million_tokens': 0.05,
        'output_cost_per_million_tokens': 0.40
    },
    'anthropic/claude-3-5-sonnet-20241022': {
        'input_cost_per_million_tokens': 3.00,
        'output_cost_per_million_tokens': 15.00
    },
    'anthropic/claude-3-haiku-20240307': {
        'input_cost_per_million_tokens': 0.25,
        'output_cost_per_million_tokens': 1.25
    },
    # Harvard Bedrock - Anthropic Claude models
    'harvard/us.anthropic.claude-opus-4-5-20251101-v1:0': {
        'input_cost_per_million_tokens': 15.00,
        'output_cost_per_million_tokens': 75.00
    },
    'harvard/us.anthropic.claude-sonnet-4-5-20250929-v1:0': {
        'input_cost_per_million_tokens': 3.00,
        'output_cost_per_million_tokens': 15.00
    },
    'harvard/us.anthropic.claude-3-5-sonnet-20241022-v2:0': {
        'input_cost_per_million_tokens': 3.00,
        'output_cost_per_million_tokens': 15.00
    },
    'harvard/us.anthropic.claude-3-5-haiku-20241022-v1:0': {
        'input_cost_per_million_tokens': 1.00,
        'output_cost_per_million_tokens': 5.00
    },
    # Harvard Bedrock - Mistral models
    'harvard/mistral.pixtral-large-2411-v1:0': {
        'input_cost_per_million_tokens': 2.00,
        'output_cost_per_million_tokens': 6.00
    },
    'harvard/us.mistral.pixtral-large-2502-v1:0': {
        'input_cost_per_million_tokens': 2.00,
        'output_cost_per_million_tokens': 6.00
    },
    'harvard/mistral.mistral-large-2407-v1:0': {
        'input_cost_per_million_tokens': 3.00,
        'output_cost_per_million_tokens': 9.00
    }
}


class ResultsManager:
    """Manager for storing and exporting evaluation results."""
    
    def __init__(self, results_dir: Optional[str] = None, question_mode: str = 'text', answers_base_dir: Optional[Path] = None):
        """
        Initialize results manager.
        
        Args:
            results_dir: Directory to store results (not used, kept for compatibility)
            question_mode: Question mode - 'text' or 'screenshot' (kept for compatibility, but no longer creates subdirectories)
            answers_base_dir: Base directory for answers folder. Should be passed from calling script.
                            Defaults to None for backward compatibility (uses project root).
        """
        # Don't create results directory - we only use answers directory
        self.results: List[Dict[str, Any]] = []
        self.question_mode = question_mode
        
        # Determine answers directory location
        if answers_base_dir is None:
            # Backward compatibility: default to project root
            questions_dir = Path(__file__).parent.parent.parent
            project_root = questions_dir.parent  # Go up one level from questions/ to project root
            answers_base = project_root / 'answers'
        else:
            answers_base = Path(answers_base_dir) / 'answers'
        
        # Create answers directory directly without mode-specific or data subdirectories
        self.answers_dir = answers_base
        self.answers_dir.mkdir(parents=True, exist_ok=True)
        self.answers_data_dir = self.answers_dir  # Model folders go directly in answers/
        
        # Track AI calls for metadata and processed models
        self.ai_calls: List[Dict[str, Any]] = []
        self.processed_models: set = set()
        
        # Track existing results loaded from previous runs
        self.existing_results: List[Dict[str, Any]] = []
    
    def _prepare_model_folder(self, model_name: str, force: bool = False):
        """
        Prepare model-specific folder. Only removes if force=True.
        
        Args:
            model_name: Name of the model
            force: If True, remove existing folder and recreate
        """
        # Create safe folder name from model name
        safe_model_name = model_name.replace('/', '_').replace('\\', '_')
        model_dir = self.answers_data_dir / safe_model_name
        
        # Only remove and recreate folder once per session if force is True
        if model_name not in self.processed_models:
            if force and model_dir.exists():
                # Remove existing model folder if force is enabled
                shutil.rmtree(model_dir)
                print(f"Removed existing results for model: {model_name}")
            
            # Create model folder (will not fail if already exists)
            model_dir.mkdir(parents=True, exist_ok=True)
            self.processed_models.add(model_name)
            
            if not force and model_dir.exists():
                print(f"Using existing folder for model: {model_name}")
            else:
                print(f"Created fresh folder for model: {model_name}")
        
        return model_dir
    
    def result_exists(self, question_id: str, model_name: str) -> bool:
        """
        Check if a result already exists for a question/model combination.
        
        Args:
            question_id: Question identifier
            model_name: Name of the model
            
        Returns:
            True if result exists, False otherwise
        """
        safe_model_name = model_name.replace('/', '_').replace('\\', '_')
        model_dir = self.answers_data_dir / safe_model_name
        json_filepath = model_dir / f"{question_id}.json"
        return json_filepath.exists()
    
    def load_existing_result(self, question_id: str, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Load an existing result from disk.
        
        Args:
            question_id: Question identifier
            model_name: Name of the model
            
        Returns:
            Result dictionary or None if not found
        """
        safe_model_name = model_name.replace('/', '_').replace('\\', '_')
        model_dir = self.answers_data_dir / safe_model_name
        json_filepath = model_dir / f"{question_id}.json"
        
        if not json_filepath.exists():
            return None
        
        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract result data from the JSON structure
            if 'evaluation' in data:
                eval_data = data['evaluation']
                result = {
                    'question_id': data.get('question_id', question_id),
                    'model_name': eval_data.get('model_name', model_name),
                    'question_type': eval_data.get('question_type', ''),
                    'llm_answer': eval_data.get('llm_answer', ''),
                    'correct_answer': eval_data.get('correct_answer', ''),
                    'is_correct': eval_data.get('is_correct'),
                    'score': eval_data.get('score'),
                    'details': eval_data.get('details', ''),
                    'processing_time': eval_data.get('processing_time', 0),
                    'error': eval_data.get('error', ''),
                    'error_type': eval_data.get('error_type', ''),
                    'timestamp': eval_data.get('timestamp', ''),
                    'input_tokens': 0,
                    'output_tokens': 0,
                    'metrics': eval_data.get('metrics', {}),
                    'error_analysis': eval_data.get('error_analysis', {}),
                    'motivation': eval_data.get('motivation', '')
                }
                
                # Try to get token info from ai_calls if available
                if 'ai_calls' in data and data['ai_calls']:
                    latest_call = data['ai_calls'][-1]
                    result['input_tokens'] = latest_call.get('input_tokens', 0)
                    result['output_tokens'] = latest_call.get('output_tokens', 0)
                
                return result
        except Exception as e:
            print(f"Warning: Failed to load existing result for {question_id}/{model_name}: {e}")
            return None
    
    def add_existing_result(self, result: Dict[str, Any]):
        """
        Add an existing result to the results list for summary generation.
        
        Args:
            result: Result dictionary
        """
        self.existing_results.append(result)
    
    def add_result(self, question_id: str, model_name: str, question_type: str,
                   llm_answer: str, correct_answer: str, evaluation: Dict[str, Any],
                   processing_time: float, error: str = "", error_type: str = "",
                   question_data: Optional[Dict[str, Any]] = None,
                   input_tokens: int = 0, output_tokens: int = 0, force: bool = False):
        """
        Add evaluation result with enhanced metrics.
        
        Args:
            question_id: Question identifier
            model_name: Name of the LLM model
            question_type: Type of question
            llm_answer: LLM response
            correct_answer: Correct answer
            evaluation: Evaluation results (now includes metrics, confidence_level, error_analysis, motivation)
            processing_time: Time taken to process
            error: Error message if any
            question_data: Additional question data for individual JSON files
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens generated
            force: If True, clear old ai_calls when saving (used with --force flag)
        """
        result = {
            'question_id': question_id,
            'model_name': model_name,
            'question_type': question_type,
            'llm_answer': llm_answer,
            'correct_answer': correct_answer,
            'is_correct': evaluation.get('is_correct'),
            'score': evaluation.get('score'),
            'details': evaluation.get('details', ''),
            'processing_time': processing_time,
            'error': error,
            'error_type': error_type,
            'timestamp': datetime.now().isoformat(),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            # Enhanced metrics
            'metrics': evaluation.get('metrics', {}),
            'error_analysis': evaluation.get('error_analysis', {}),
            'motivation': evaluation.get('motivation', '')
        }
        
        self.results.append(result)
        
        # Prepare model-specific folder (don't force remove)
        model_dir = self._prepare_model_folder(model_name, force=False)
        
        # Track AI call for metadata
        ai_call = {
            'description': 'question answering',
            'model_name': model_name,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        }
        self.ai_calls.append(ai_call)
        
        # Save individual question result as JSON in model-specific folder
        self._save_individual_result(question_id, result, question_data, model_dir, force=force)
    
    def _save_individual_result(self, question_id: str, result: Dict[str, Any], question_data: Optional[Dict[str, Any]] = None, model_dir: Optional[Path] = None, force: bool = False):
        """
        Save individual question result as JSON file in model-specific folder.
        
        Args:
            question_id: Question identifier
            result: Result data
            question_data: Additional question data
            model_dir: Model-specific directory path
            force: If True, clear old ai_calls and start fresh
        """
        try:
            # Use model-specific directory
            if model_dir is None:
                safe_model_name = result['model_name'].replace('/', '_').replace('\\', '_')
                model_dir = self.answers_data_dir / safe_model_name
            
            json_filepath = model_dir / f"{question_id}.json"
            
            # Load existing file if it exists to preserve previous AI calls
            existing_data = {}
            if json_filepath.exists() and not force:
                with open(json_filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # Create comprehensive result data
            # If force=True, start fresh without old ai_calls; otherwise preserve them
            individual_result = existing_data.copy() if (existing_data and not force) else {
                'question_id': question_id,
                'ai_calls': []
            }
            
            # Add question data if provided and not already present
            if question_data and 'question_data' not in individual_result:
                individual_result['question_data'] = question_data
            
            # Add current AI call to the ai_calls array
            ai_call = {
                'description': 'question answering',
                'model_name': result['model_name'],
                'input_tokens': result.get('input_tokens', 0),
                'output_tokens': result.get('output_tokens', 0),
                'total_tokens': result.get('input_tokens', 0) + result.get('output_tokens', 0),
                'processing_time': result['processing_time'],
                'timestamp': result['timestamp']
            }
            individual_result['ai_calls'].append(ai_call)
            
            # Add evaluation results with enhanced metrics
            evaluation_data = {
                'model_name': result['model_name'],
                'question_type': result['question_type'],
                'llm_answer': result['llm_answer'],  # Keep as dict/object, not string
                'correct_answer': result['correct_answer'],
                'is_correct': result['is_correct'],
                'score': result['score'],
                'details': result['details'],
                'processing_time': result['processing_time'],
                'error': result['error'],
                'error_type': result.get('error_type', ''),
                'timestamp': result['timestamp']
            }
            
            # Add enhanced metrics if available
            if 'metrics' in result and result['metrics']:
                evaluation_data['metrics'] = result['metrics']
            
            # Add error analysis if available
            if 'error_analysis' in result and result['error_analysis']:
                evaluation_data['error_analysis'] = result['error_analysis']
            
            # Add motivation if available
            if 'motivation' in result and result['motivation']:
                evaluation_data['motivation'] = result['motivation']
            
            individual_result['evaluation'] = evaluation_data
            
            # Save to individual JSON file in model-specific folder
            with open(json_filepath, 'w', encoding='utf-8') as f:
                json.dump(individual_result, f, indent=2, ensure_ascii=False)
            
            print(f"Individual result saved to {json_filepath} for question {question_id}")
            
        except Exception as e:
            print(f"Warning: Failed to save individual result for question {question_id}: {e}")
            import traceback
            traceback.print_exc()
    
    def export_to_csv(self, filepath: str):
        """
        Export results to CSV.
        
        Args:
            filepath: Path to CSV file
            
        Raises:
            ProcessingError: If export fails
        """
        if not self.results:
            print("No results to export")
            return
        
        try:
            fieldnames = ['question_id', 'model_name', 'question_type', 'llm_answer',
                         'correct_answer', 'is_correct', 'score', 'details',
                         'processing_time', 'error', 'timestamp', 'input_tokens', 'output_tokens']
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)
            
            print(f"Results exported to {filepath}")
        except Exception as e:
            raise ProcessingError(f"Failed to export results to CSV: {e}")
    
    def calculate_precision_recall_f1(self, results_subset: List[Dict]) -> Dict[str, float]:
        """
        Calculate comprehensive metrics for a subset of results using enhanced evaluation data.
        
        Args:
            results_subset: Subset of results to analyze
            
        Returns:
            Dictionary with aggregated metrics
        """
        if not results_subset:
            return {
                'precision': 0.0, 'recall': 0.0, 'f1': 0.0,
                'exact_match_rate': 0.0, 'total_samples': 0
            }
        
        # Filter out results without ground truth (None values)
        valid_results = [r for r in results_subset if r['is_correct'] is not None]
        
        if not valid_results:
            return {
                'precision': 0.0, 'recall': 0.0, 'f1': 0.0,
                'exact_match_rate': 0.0, 'total_samples': 0
            }
        
        # Aggregate metrics from individual results
        total_precision = 0.0
        total_recall = 0.0
        total_f1 = 0.0
        exact_matches = 0
        
        for result in valid_results:
            # Use enhanced metrics if available, otherwise fall back to legacy calculation
            if 'metrics' in result and result['metrics']:
                metrics = result['metrics']
                total_precision += metrics.get('precision', 0.0)
                total_recall += metrics.get('recall', 0.0)
                total_f1 += metrics.get('f1', 0.0)
                if metrics.get('exact_match', 0.0) == 1.0:
                    exact_matches += 1
            else:
                # Legacy fallback: use is_correct for all metrics
                score = 1.0 if result['is_correct'] else 0.0
                total_precision += score
                total_recall += score
                total_f1 += score
                if result['is_correct']:
                    exact_matches += 1
        
        total_samples = len(valid_results)
        
        return {
            'precision': total_precision / total_samples,
            'recall': total_recall / total_samples,
            'f1': total_f1 / total_samples,
            'exact_match_rate': exact_matches / total_samples,
            'total_samples': total_samples
        }
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary statistics.
        
        Returns:
            Summary statistics dictionary
        """
        if not self.results:
            return {}
        
        total_questions = len(set(r['question_id'] for r in self.results))
        total_evaluations = len(self.results)
        
        # Overall metrics
        overall_metrics = self.calculate_precision_recall_f1(self.results)
        
        # Accuracy by model (legacy metric)
        accuracy_by_model = {}
        metrics_by_model = {}
        for model in set(r['model_name'] for r in self.results):
            model_results = [r for r in self.results if r['model_name'] == model]
            model_results_valid = [r for r in model_results if r['is_correct'] is not None]
            
            if model_results_valid:
                correct = sum(1 for r in model_results_valid if r['is_correct'])
                accuracy_by_model[model] = correct / len(model_results_valid)
                metrics_by_model[model] = self.calculate_precision_recall_f1(model_results)
        
        # Accuracy by type (legacy metric)
        accuracy_by_type = {}
        metrics_by_type = {}
        for qtype in set(r['question_type'] for r in self.results):
            type_results = [r for r in self.results if r['question_type'] == qtype]
            type_results_valid = [r for r in type_results if r['is_correct'] is not None]
            
            if type_results_valid:
                correct = sum(1 for r in type_results_valid if r['is_correct'])
                accuracy_by_type[qtype] = correct / len(type_results_valid)
                metrics_by_type[qtype] = self.calculate_precision_recall_f1(type_results)
        
        # Average processing time
        processing_times = [r['processing_time'] for r in self.results if r['processing_time'] > 0]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Score distribution
        scores = [r['score'] for r in self.results if r['score'] is not None]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        return {
            'total_questions': total_questions,
            'total_evaluations': total_evaluations,
            'overall_metrics': overall_metrics,
            'accuracy_by_model': accuracy_by_model,  # Legacy
            'accuracy_by_type': accuracy_by_type,    # Legacy
            'metrics_by_model': metrics_by_model,
            'metrics_by_type': metrics_by_type,
            'average_processing_time': avg_processing_time,
            'average_score': avg_score,
            'errors': len([r for r in self.results if r['error']])
        }
    
    def print_summary(self):
        """Print comprehensive summary statistics."""
        summary = self.generate_summary()
        
        print("\n" + "="*70)
        print("EVALUATION SUMMARY")
        print("="*70)
        print(f"Total Questions: {summary.get('total_questions', 0)}")
        print(f"Total Evaluations: {summary.get('total_evaluations', 0)}")
        print(f"Errors: {summary.get('errors', 0)}")
        print(f"Average Processing Time: {summary.get('average_processing_time', 0):.2f}s")
        print(f"Average Score: {summary.get('average_score', 0):.3f}")
        
        # Overall metrics
        overall = summary.get('overall_metrics', {})
        print(f"\nOVERALL PERFORMANCE:")
        print(f"  Precision:      {overall.get('precision', 0):.3f}")
        print(f"  Recall:         {overall.get('recall', 0):.3f}")
        print(f"  F1 Score:       {overall.get('f1', 0):.3f}")
        print(f"  Exact Match:    {overall.get('exact_match_rate', 0):.3f}")
        print(f"  Samples:        {overall.get('total_samples', 0)}")
        
        # Metrics by model
        print(f"\nPERFORMANCE BY MODEL:")
        print(f"{'Model':<35} {'Prec':<6} {'Rec':<6} {'F1':<6} {'ExM':<6} {'Samples':<8}")
        print("-" * 80)
        for model, metrics in summary.get('metrics_by_model', {}).items():
            print(f"{model:<35} {metrics.get('precision', 0):.3f}  {metrics.get('recall', 0):.3f}  "
                  f"{metrics.get('f1', 0):.3f}  {metrics.get('exact_match_rate', 0):.3f}  {metrics.get('total_samples', 0):<8}")
        
        # Metrics by question type
        print(f"\nPERFORMANCE BY QUESTION TYPE:")
        print(f"{'Question Type':<25} {'Prec':<6} {'Rec':<6} {'F1':<6} {'ExM':<6} {'Samples':<8}")
        print("-" * 70)
        for qtype, metrics in summary.get('metrics_by_type', {}).items():
            print(f"{qtype:<25} {metrics.get('precision', 0):.3f}  {metrics.get('recall', 0):.3f}  "
                  f"{metrics.get('f1', 0):.3f}  {metrics.get('exact_match_rate', 0):.3f}  {metrics.get('total_samples', 0):<8}")
    
    def save_summary_json(self, filepath: Optional[str] = None):
        """
        Save summary as JSON file - DISABLED (no results folder created).
        """
        pass
    
    def save_summary_txt(self, filepath: Optional[str] = None):
        """
        Save summary as TXT file - DISABLED (no results folder created).
        """
        pass
    
    def save_summary_md(self, filepath: Optional[str] = None):
        """
        Save summary as Markdown file - DISABLED (no results folder created).
        """
        pass
    
    def clear_results(self):
        """Clear all stored results."""
        self.results.clear()
    
    def get_results_count(self) -> int:
        """Get the number of stored results."""
        return len(self.results)
    
    def get_results_by_model(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Get results for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of results for the model
        """
        return [r for r in self.results if r['model_name'] == model_name]
    
    def get_results_by_question_type(self, question_type: str) -> List[Dict[str, Any]]:
        """
        Get results for a specific question type.
        
        Args:
            question_type: Type of question
            
        Returns:
            List of results for the question type
        """
        return [r for r in self.results if r['question_type'] == question_type]
    
    def _load_existing_metadata(self) -> Dict[str, Any]:
        """Load existing metadata.json if it exists."""
        metadata_path = self.answers_dir / 'metadata.json'
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load existing metadata: {e}")
        return {}
    
    def _load_all_model_results(self) -> List[Dict[str, Any]]:
        """Load all results from all model folders."""
        all_results = []
        
        # Load from current session results (new results)
        all_results.extend(self.results)
        
        # Load from existing results (loaded but not reprocessed)
        all_results.extend(self.existing_results)
        
        # Load from existing model folders (models not in current session at all)
        for model_dir in self.answers_data_dir.iterdir():
            if model_dir.is_dir():
                model_name = model_dir.name.replace('_', '/')  # Convert back from safe name
                
                # Skip if this model was processed in current session
                if model_name in self.processed_models:
                    continue
                
                # Load all JSON files from this model folder
                for json_file in model_dir.glob('*.json'):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            
                        # Extract result data from the JSON structure
                        if 'evaluation' in data:
                            eval_data = data['evaluation']
                            result = {
                                'question_id': data.get('question_id', json_file.stem),
                                'model_name': eval_data.get('model_name', model_name),
                                'question_type': eval_data.get('question_type', ''),
                                'llm_answer': eval_data.get('llm_answer', ''),
                                'correct_answer': eval_data.get('correct_answer', ''),
                                'is_correct': eval_data.get('is_correct'),
                                'score': eval_data.get('score'),
                                'details': eval_data.get('details', ''),
                                'processing_time': eval_data.get('processing_time', 0),
                                'error': eval_data.get('error', ''),
                                'error_type': eval_data.get('error_type', ''),
                                'timestamp': eval_data.get('timestamp', ''),
                                'input_tokens': 0,  # Default for existing data
                                'output_tokens': 0,  # Default for existing data
                                'metrics': eval_data.get('metrics', {}),
                                'error_analysis': eval_data.get('error_analysis', {}),
                                'motivation': eval_data.get('motivation', '')
                            }
                            
                            # Try to get token info from ai_calls if available
                            if 'ai_calls' in data and data['ai_calls']:
                                latest_call = data['ai_calls'][-1]
                                result['input_tokens'] = latest_call.get('input_tokens', 0)
                                result['output_tokens'] = latest_call.get('output_tokens', 0)
                            
                            all_results.append(result)
                    except Exception as e:
                        print(f"Warning: Failed to load {json_file}: {e}")
        
        return all_results
    
    def generate_answers_metadata(self) -> Dict[str, Any]:
        """
        Generate metadata for the answers folder, including existing data.
        
        Returns:
            Metadata dictionary
        """
        # Load all results (current + existing)
        all_results = self._load_all_model_results()
        
        if not all_results:
            return {}
        
        # Count questions and exercises
        question_ids = set(r['question_id'] for r in all_results)
        exercise_ids = set(q.split('_')[0] for q in question_ids)
        
        # Count questions with images - need to check the stored question data properly
        questions_with_images = 0
        processed_questions = set()
        
        # Check from current results
        for result in self.results:
            question_id = result['question_id']
            if question_id not in processed_questions:
                # Try to load the individual JSON file to get question data
                safe_model_name = result['model_name'].replace('/', '_').replace('\\', '_')
                model_dir = self.answers_data_dir / safe_model_name
                json_filepath = model_dir / f"{question_id}.json"
                
                if json_filepath.exists():
                    try:
                        with open(json_filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if data.get('question_data', {}).get('has_image', False):
                            questions_with_images += 1
                        processed_questions.add(question_id)
                    except Exception:
                        pass
        
        # Check from existing model folders for questions not in current session
        for model_dir in self.answers_data_dir.iterdir():
            if model_dir.is_dir():
                for json_file in model_dir.glob('*.json'):
                    question_id = json_file.stem
                    if question_id not in processed_questions:
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            if data.get('question_data', {}).get('has_image', False):
                                questions_with_images += 1
                            processed_questions.add(question_id)
                        except Exception:
                            pass
        
        # Count questions by type (count each question only once, not per model)
        questions_by_type = {}
        processed_question_types = set()
        
        for result in all_results:
            question_id = result['question_id']
            qtype = result['question_type']
            question_key = f"{question_id}_{qtype}"
            
            # Only count each question once, regardless of how many models processed it
            if question_key not in processed_question_types:
                questions_by_type[qtype] = questions_by_type.get(qtype, 0) + 1
                processed_question_types.add(question_key)
        
        # Generate model statistics
        models = []
        for model_name in set(r['model_name'] for r in all_results):
            model_results = [r for r in all_results if r['model_name'] == model_name]
            model_metrics = self.calculate_precision_recall_f1(model_results)
            
            # Calculate token usage and costs
            total_input_tokens = sum(r.get('input_tokens', 0) for r in model_results)
            total_output_tokens = sum(r.get('output_tokens', 0) for r in model_results)
            total_processing_time = sum(r.get('processing_time', 0) for r in model_results)
            
            # Get cost information
            cost_info = MODEL_COSTS.get(model_name, {})
            input_cost_per_million = cost_info.get('input_cost_per_million_tokens', 0)
            output_cost_per_million = cost_info.get('output_cost_per_million_tokens', 0)
            
            # Calculate question type breakdown for this model
            question_types = []
            for qtype in set(r['question_type'] for r in model_results):
                type_results = [r for r in model_results if r['question_type'] == qtype]
                type_metrics = self.calculate_precision_recall_f1(type_results)
                
                # Count questions with images for this type - check individual JSON files
                type_questions_with_images = 0
                type_processed_questions = set()
                
                for r in type_results:
                    question_id = r['question_id']
                    if question_id not in type_processed_questions:
                        safe_model_name = model_name.replace('/', '_').replace('\\', '_')
                        model_dir = self.answers_data_dir / safe_model_name
                        json_filepath = model_dir / f"{question_id}.json"
                        
                        if json_filepath.exists():
                            try:
                                with open(json_filepath, 'r', encoding='utf-8') as f:
                                    data = json.load(f)
                                if data.get('question_data', {}).get('has_image', False):
                                    type_questions_with_images += 1
                                type_processed_questions.add(question_id)
                            except Exception:
                                pass
                
                correctly_answered = sum(1 for r in type_results if r.get('is_correct', False))
                
                question_types.append({
                    'type': qtype,
                    'number_of_questions': len(type_results),
                    'questions_with_images': type_questions_with_images,
                    'correctly_answered_questions': correctly_answered,
                    'precision': type_metrics.get('precision', 0),
                    'recall': type_metrics.get('recall', 0),
                    'f1': type_metrics.get('f1', 0),
                    'exact_match_rate': type_metrics.get('exact_match_rate', 0)
                })
            
            models.append({
                'model_name': model_name,
                'precision': model_metrics.get('precision', 0),
                'recall': model_metrics.get('recall', 0),
                'f1': model_metrics.get('f1', 0),
                'exact_match_rate': model_metrics.get('exact_match_rate', 0),
                'input_cost_per_million_tokens': input_cost_per_million,
                'output_cost_per_million_tokens': output_cost_per_million,
                'ai_calls': [{
                    'description': 'question_answer',
                    'input_tokens': total_input_tokens,
                    'output_tokens': total_output_tokens,
                    'total_tokens': total_input_tokens + total_output_tokens,
                    'processing_time': total_processing_time
                }],
                'question_type': question_types
            })
        
        metadata = {
            'creation_datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'version': 0.3,
            'exercise_count': len(exercise_ids),
            'question_count': len(question_ids),
            'questions_with_images': questions_with_images,
            'questions_by_type': questions_by_type,
            'models': models
        }
        
        return metadata
    
    def save_answers_metadata(self):
        """Save metadata.json in the answers folder."""
        try:
            metadata = self.generate_answers_metadata()
            metadata_path = self.answers_dir / 'metadata.json'
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"Metadata saved to {metadata_path}")
        except Exception as e:
            print(f"Warning: Failed to save metadata: {e}")
    
    def generate_answers_readme(self) -> str:
        """
        Generate README.md content for the answers folder.
        
        Returns:
            README content as string
        """
        if not self.results:
            return "# Evaluation Results\n\nNo results available."
        
        metadata = self.generate_answers_metadata()
        
        readme_content = f"""# LLM Evaluation Results

## Overview

This directory contains the results of evaluating Large Language Models (LLMs) on Italian art history questions.

- **Creation Date**: {metadata.get('creation_datetime', 'N/A')}
- **Version**: {metadata.get('version', 'N/A')}
- **Total Exercises**: {metadata.get('exercise_count', 0)}
- **Total Questions**: {metadata.get('question_count', 0)}
- **Questions with Images**: {metadata.get('questions_with_images', 0)}

## Available Models

| Model Name | Version | Input Cost ($/1M) | Output Cost ($/1M) | Reasoning |
|------------|---------|-------------------|--------------------|-----------|
"""
        
        # Add model information table
        # Define reasoning models (o1, o3 series)
        reasoning_models = ['o1', 'o3']
        
        # Get all unique models from MODEL_COSTS
        all_model_names = set()
        for model in metadata.get('models', []):
            all_model_names.add(model.get('model_name', ''))
        
        # Sort models by provider and name
        sorted_model_list = sorted(all_model_names)
        
        for model_name in sorted_model_list:
            cost_info = MODEL_COSTS.get(model_name, {})
            input_cost = cost_info.get('input_cost_per_million_tokens', 0)
            output_cost = cost_info.get('output_cost_per_million_tokens', 0)
            
            # Extract version from model name (e.g., "2025-04-14" from "gpt-4.1-2025-04-14")
            version = "N/A"
            if '/' in model_name:
                model_short = model_name.split('/')[-1]
                # Try to extract date pattern YYYY-MM-DD
                import re
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', model_short)
                if date_match:
                    version = date_match.group(1)
                else:
                    # For models like "gemini-2.5-flash", extract version number
                    version_match = re.search(r'(\d+\.\d+)', model_short)
                    if version_match:
                        version = version_match.group(1)
            
            # Check if it's a reasoning model
            is_reasoning = any(reasoning_model in model_name.lower() for reasoning_model in reasoning_models)
            reasoning_str = "✓" if is_reasoning else "✗"
            
            readme_content += f"| {model_name} | {version} | ${input_cost:.2f} | ${output_cost:.2f} | {reasoning_str} |\n"
        
        readme_content += f"""
## Directory Structure

```
answers/
├── metadata.json          # Comprehensive evaluation metadata
├── README.md             # This file
├── google_gemini-2.5-flash-lite/
│   ├── 0001.json         # Results for question 0001
│   ├── 0002.json         # Results for question 0002
│   └── ...               # More question results
├── openai_gpt-4o/
│   ├── 0001.json         # Results for question 0001
│   └── ...               # More question results
└── ...                   # More model folders
```

## Question Types Distribution

"""
        
        questions_by_type = metadata.get('questions_by_type', {})
        for qtype, count in questions_by_type.items():
            readme_content += f"- **{qtype}**: {count} questions\n"
        
        readme_content += "\n## Model Performance Summary\n\n"
        
        # Simplified performance table for multiple choice questions
        readme_content += "| Model | Accuracy | Correct/Total | Input Tokens | Output Tokens | Actual Cost |\n"
        readme_content += "|-------|----------|---------------|--------------|---------------|-------------|\n"
        
        # Sort models with Gemini models in specific order
        models = metadata.get('models', [])
        def sort_models(model):
            model_name = model.get('model_name', '')
            if 'gemini-2.5-flash-lite' in model_name:
                return (0, model_name)
            elif 'gemini-2.5-flash' in model_name and 'lite' not in model_name:
                return (1, model_name)
            elif 'gemini-2.5-pro' in model_name:
                return (2, model_name)
            else:
                return (999, model_name)  # Other models come after Gemini models
        
        sorted_models = sorted(models, key=sort_models)
        
        for model in sorted_models:
            model_name = model.get('model_name', 'Unknown')
            exact_match = model.get('exact_match_rate', 0)
            
            # Calculate correct/total from question types
            total_questions = 0
            correct_questions = 0
            for qtype_data in model.get('question_type', []):
                total_questions += qtype_data.get('number_of_questions', 0)
                correct_questions += qtype_data.get('correctly_answered_questions', 0)
            
            # Get token usage and calculate actual cost
            ai_calls = model.get('ai_calls', [])
            if ai_calls:
                input_tokens = ai_calls[0].get('input_tokens', 0)
                output_tokens = ai_calls[0].get('output_tokens', 0)
                
                # Calculate actual cost
                input_cost_per_million = model.get('input_cost_per_million_tokens', 0)
                output_cost_per_million = model.get('output_cost_per_million_tokens', 0)
                
                actual_cost = (input_tokens * input_cost_per_million / 1_000_000) + (output_tokens * output_cost_per_million / 1_000_000)
                
                readme_content += f"| {model_name} | {exact_match:.1%} | {correct_questions}/{total_questions} | {input_tokens:,} | {output_tokens:,} | ${actual_cost:.4f} |\n"
            else:
                readme_content += f"| {model_name} | {exact_match:.1%} | {correct_questions}/{total_questions} | 0 | 0 | $0.0000 |\n"
        
        readme_content += "\n## Performance by Model and Question Type\n\n"
        
        # Create one table per model
        for model in sorted_models:
            model_name = model.get('model_name', 'Unknown')
            readme_content += f"### {model_name}\n\n"
            readme_content += "| Question Type | Questions | With Images | Correct | Accuracy |\n"
            readme_content += "|---------------|-----------|-------------|---------|----------|\n"
            
            # Sort question types alphabetically
            question_types = sorted(model.get('question_type', []), key=lambda x: x.get('type', ''))
            
            for type_data in question_types:
                qtype = type_data.get('type', 'Unknown')
                questions = type_data.get('number_of_questions', 0)
                with_images = type_data.get('questions_with_images', 0)
                correct = type_data.get('correctly_answered_questions', 0)
                accuracy = (correct / questions * 100) if questions > 0 else 0
                
                readme_content += f"| {qtype} | {questions} | {with_images} | {correct} | {accuracy:.1f}% |\n"
            
            readme_content += "\n"
        
        readme_content += "\n"
        
        return readme_content
    
    def save_answers_readme(self):
        """Save README.md in the answers folder."""
        try:
            readme_content = self.generate_answers_readme()
            readme_path = self.answers_dir / 'README.md'
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            
            print(f"README saved to {readme_path}")
        except Exception as e:
            print(f"Warning: Failed to save README: {e}")
    
    def finalize_answers_output(self):
        """Generate and save all answers folder outputs."""
        self.save_answers_metadata()
        self.save_answers_readme()
        
        # Count files in all model folders
        total_files = 0
        model_folders = []
        for model_dir in self.answers_data_dir.iterdir():
            if model_dir.is_dir():
                file_count = len(list(model_dir.glob('*.json')))
                total_files += file_count
                model_folders.append(f"  - {model_dir.name}/: {file_count} files")
        
        print(f"\nAnswers folder structure created at: {self.answers_dir}")
        print(f"- metadata.json: Comprehensive evaluation metadata")
        print(f"- README.md: Human-readable summary and analysis")
        print(f"- Model folders: Individual question results organized by model ({total_files} total files)")
        for folder_info in model_folders:
            print(folder_info)