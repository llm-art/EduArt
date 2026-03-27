#!/usr/bin/env python3
"""
LLM Questioner Script - Modular Version

Queries multiple LLMs with Italian art history questions from the dataset.

Features:
- Dual prompt conditions: answer-with-motivation (primary) and answer-only (baseline)
- Per-provider temperature/seed settings for reproducibility
- Parallel workers for faster processing
- k-run reproducibility checks on a stratified subsample
- Results stored in answers/{prompt_condition}/{model_name}/

Usage:
    python llm_questioner.py --models google/gemini-2.5-flash-lite
    python llm_questioner.py --models model1 --models model2 --workers 4
    python llm_questioner.py --prompt-condition answer-only --start 1 --end 10
    python llm_questioner.py --k-runs 3 --models google/gemini-2.5-flash
"""

import click
import os
from pathlib import Path
import sys

# Add questions directory to path for shared modules
sys.path.insert(0, str(Path(__file__).parent / "questions"))

from modules.questioner import LLMQuestioner
from modules.core.exceptions import ConfigurationError, ProcessingError


@click.command()
@click.option('--start', type=int, help='Start question number')
@click.option('--end', type=int, help='End question number')
@click.option('--types', help='Comma-separated list of question types to test')
@click.option('--models', multiple=True, help='Model to test (can be specified multiple times)')
@click.option('--output', default='llm_evaluation_results.csv', help='Output CSV file')
@click.option('--api-version', default='v2', help='Harvard Bedrock API version (v1 or v2)')
@click.option('--force', is_flag=True, default=False, help='Force reprocessing of existing results')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--prompt-condition',
              type=click.Choice(['default', 'motivation', 'both']),
              default='both',
              help='Prompt condition to run (default: both)')
@click.option('--workers', type=int, default=1,
              help='Number of parallel workers (default: 1)')
@click.option('--k-runs', type=int, default=1,
              help='Number of independent runs for reproducibility subsample (default: 1)')
@click.option('--temperature', type=float, default=None,
              help='Override temperature for all providers (e.g., 0.0)')
def main(start, end, types, models, output, api_version, force, verbose,
         prompt_condition, workers, k_runs, temperature):
    """LLM Questioner for Italian Art History."""

    # Set Harvard API version
    os.environ['HARVARD_API_VERSION'] = api_version

    # Parse question types filter
    question_types = None
    if types:
        question_types = [t.strip() for t in types.split(',')]

    # Parse models
    models_to_test = list(models) if models else None

    # Resolve prompt conditions
    if prompt_condition == 'both':
        conditions = ['default', 'motivation']
    else:
        conditions = [prompt_condition]

    try:
        base_dir = Path(__file__).parent
        prompts_dir = base_dir / "prompts"

        # Override temperature for all providers if specified
        if temperature is not None:
            os.environ['TEMPERATURE_OVERRIDE'] = str(temperature)
        elif 'TEMPERATURE_OVERRIDE' in os.environ:
            del os.environ['TEMPERATURE_OVERRIDE']

        questioner = LLMQuestioner(
            models_to_test=models_to_test,
            base_dir=base_dir,
            prompts_dir=prompts_dir,
        )

        provider_info = questioner.get_provider_info()
        print(f"Initialized {len(provider_info)} LLM providers")
        for info in provider_info:
            print(f"  - {info['model_name']} (temp={info.get('temperature', '?')})")
        print(f"Prompt conditions: {conditions}")
        if workers > 1:
            print(f"Workers: {workers}")
        if k_runs > 1:
            print(f"Reproducibility k-runs: {k_runs}")

        results = questioner.process_questions(
            start=start,
            end=end,
            question_types=question_types,
            output_file=output,
            force=force,
            prompt_conditions=conditions,
            workers=workers,
            k_runs=k_runs,
        )

        # Print final summary
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total operations: {results['total_operations']}")
        print(f"Successful: {results['successful_operations']}")
        print(f"Failed: {results['failed_operations']}")
        print(f"Skipped: {results.get('skipped_operations', 0)}")
        print(f"Success rate: {results['success_rate']:.1f}%")
        print(f"Questions: {results['questions_processed']}")
        print(f"Models: {results['models_tested']}")
        for cond, folder in results.get('answers_folders', {}).items():
            print(f"  {cond}: {folder}")

    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1

    except ProcessingError as e:
        print(f"Processing error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1

    except Exception as e:
        print(f"Unexpected error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
