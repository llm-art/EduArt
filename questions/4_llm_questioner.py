#!/usr/bin/env python3
"""
LLM Questioner Script - Modular Version

This script uses the modular architecture to query multiple LLMs with Italian art history questions
from the dataset and evaluates their responses against ground truth answers.

Features:
- Modular architecture with reusable components
- Support for OpenAI, Google Gemini, and Anthropic Claude models
- Two question modes: text (default) and screenshot
- Comprehensive evaluation metrics including precision, recall, and F1 score
- Configurable question filtering by range and type
- Detailed results export and analysis
- Retry logic with exponential backoff for API calls

Question Modes:
- TEXT MODE (default): Uses structured TXT files from dataset/data/ with metadata evaluation
- SCREENSHOT MODE: Uses PNG images from dataset/raw/ with metadata evaluation
  Note: Screenshot images may contain different questions than the metadata, affecting accuracy

Usage:
    python 4_llm_questioner.py --start 1 --end 10 --models google-gemini-2.5-flash-lite
    python 4_llm_questioner.py --models model1 --models model2 --models model3
    python 4_llm_questioner.py --types multiple_choice,true_false
    python 4_llm_questioner.py --output my_results.csv
    python 4_llm_questioner.py --question-mode screenshot --models google-gemini-2.5-flash
    python 4_llm_questioner.py --question-mode text --start 1 --end 5
"""

import click
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from questions directory
questions_dir = Path(__file__).parent
env_path = questions_dir / '.env'
load_dotenv(env_path)

# Import modular components
from modules.questioner import LLMQuestioner
from modules.core.exceptions import ConfigurationError, ProcessingError


@click.command()
@click.option('--start', type=int, help='Start question number')
@click.option('--end', type=int, help='End question number')
@click.option('--types', help='Comma-separated list of question types to test')
@click.option('--models', multiple=True, help='Model to test (can be specified multiple times)')
@click.option('--output', default='llm_evaluation_results.csv', help='Output CSV file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--question-mode', type=click.Choice(['text', 'screenshot']), default='text',
              help='Question mode: "text" uses TXT files (default), "screenshot" uses PNG images from dataset/raw')
def main(start, end, types, models, output, verbose, question_mode):
    """LLM Questioner for Italian Art History - Modular Version."""
    
    if verbose:
        print("LLM Questioner for Italian Art History - Modular Version")
        print("=" * 60)
        print(f"Question mode: {question_mode}")
    
    # Parse question types filter
    question_types = None
    if types:
        question_types = [t.strip() for t in types.split(',')]
        if verbose:
            print(f"Question types filter: {question_types}")
    
    # Parse models filter
    models_to_test = None
    if models:
        models_to_test = list(models)  # models is now a tuple from multiple=True
        if verbose:
            print(f"Models to test: {models_to_test}")
    
    try:
        # Initialize questioner
        if verbose:
            print("\nInitializing LLM Questioner...")
        
        questioner = LLMQuestioner(models_to_test=models_to_test, question_mode=question_mode)
        
        if verbose:
            questioner.print_status()
        else:
            provider_info = questioner.get_provider_info()
            print(f"Initialized {len(provider_info)} LLM providers")
            for info in provider_info:
                print(f"  - {info['model_name']}")
        
        # Process questions
        if verbose:
            print(f"\nProcessing questions...")
            if start is not None or end is not None:
                print(f"Question range: {start or 'start'} to {end or 'end'}")
        
        results = questioner.process_questions(
            start=start,
            end=end,
            question_types=question_types,
            output_file=output
        )
        
        # Print final summary
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total operations: {results['total_operations']}")
        print(f"Successful operations: {results['successful_operations']}")
        print(f"Failed operations: {results['failed_operations']}")
        print(f"Success rate: {results['success_rate']:.1f}%")
        print(f"Questions processed: {results['questions_processed']}")
        print(f"Models tested: {results['models_tested']}")
        print(f"Results saved to: {results['answers_folder']}")
        
        if verbose:
            print(f"\nDetailed results summary:")
            summary = questioner.get_results_summary()
            if summary:
                overall = summary.get('overall_metrics', {})
                print(f"  Overall accuracy: {overall.get('accuracy', 0):.3f}")
                print(f"  Overall F1 score: {overall.get('f1', 0):.3f}")
                print(f"  Average processing time: {summary.get('average_processing_time', 0):.2f}s")
        
        print(f"\nEvaluation complete!")
        
    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        if verbose:
            print("\nTroubleshooting tips:")
            print("- Check that API keys are set in the .env file")
            print("- Verify that the dataset directory exists and contains question files")
            print("- Ensure required dependencies are installed")
        return 1
    
    except ProcessingError as e:
        print(f"Processing error: {e}")
        if verbose:
            print("\nThis may be due to:")
            print("- Network connectivity issues")
            print("- API rate limiting")
            print("- Invalid question file formats")
        return 1
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        if verbose:
            import traceback
            print("\nFull traceback:")
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())