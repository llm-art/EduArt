#!/usr/bin/env python3
"""
Enhanced question preprocessor using the new modular architecture.

This refactored version uses the new service-oriented architecture with:
- Configuration classes for better parameter management
- Service layer for OCR and vision model operations
- Proper error handling and logging
- Structured data types

USAGE:
    python 2_question_preprocessor_refactored.py -e 1 --min-question 1 --max-question 10

REQUIREMENTS:
    - paddleocr: Italian OCR text extraction
    - transformers: Qwen2-VL-Instruct local model (optional)
    - langchain-google-genai: Gemini 2.5 Pro API integration (optional)
    - langchain-core: Pipeline orchestration
    - pillow: Image handling
    - python-dotenv: Environment configuration
"""

import click
from pathlib import Path

from modules.core.config import ProcessorConfig
from modules.core.exceptions import ProcessingError, ConfigurationError
from modules.processors.question_processor import QuestionProcessor
from modules.config import Config


def count_png_files_in_raw(exercise: int) -> int:
    """Count the number of PNG files in the raw folder for the given exercise."""
    base_path = Path(__file__).parent / "data"
    raw_path = base_path / f"{exercise}/raw/"
    
    if not raw_path.exists():
        print(f"Warning: Raw folder does not exist: {raw_path}")
        return 0
    
    png_files = list(raw_path.glob("*.png"))
    png_count = len(png_files)
    
    print(f"Found {png_count} PNG files in {raw_path}")
    return png_count


@click.command()
@click.option('--force-ocr', is_flag=True, help='Force OCR processing even if OCR JSON files already exist')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose/debug output')
@click.option('--exercise', '-e', default=1, help='Exercise number to process', show_default=True)
@click.option('--min-question', default=1, help='Minimum question number to process', show_default=True)
@click.option('--max-question', default=20, help='Maximum question number to process', show_default=True)
@click.option('--use-langchain', is_flag=True, help='Use LangChain pipeline (for backward compatibility)')
@click.option('--metadata-ai/--no-metadata-ai', default=True, help='Track AI call metadata including token usage', show_default=True)
def main(force_ocr, verbose, exercise, min_question, max_question, use_langchain, metadata_ai):
    """Process multiple questions using the new modular architecture."""
    
    try:
        # Count actual PNG files in the raw folder
        actual_png_count = count_png_files_in_raw(exercise)
        
        # Use the minimum between max_question and actual PNG count
        effective_max_question = min(max_question, actual_png_count)
        
        print("=== Enhanced Multi-Model Exam Question Processor (Refactored) ===")
        print(f"Configuration: {Config.get_model_info()}")
        print(f"Force OCR: {force_ocr}")
        print(f"Verbose: {verbose}")
        print(f"Exercise: {exercise}")
        print(f"Requested questions: {min_question}-{max_question}")
        print(f"Available PNG files: {actual_png_count}")
        print(f"Effective questions: {min_question}-{effective_max_question}")
        print(f"Using LangChain pipeline: {use_langchain}")
        print(f"AI metadata tracking: {metadata_ai}")
        
        # Check if we have any questions to process
        if effective_max_question < min_question:
            print(f"Error: No questions to process. Available PNG files ({actual_png_count}) is less than min_question ({min_question})")
            return
        
        # Create configuration
        config = ProcessorConfig(
            exercise=exercise,
            min_question=min_question,
            max_question=effective_max_question,
            force_ocr=force_ocr,
            verbose=verbose,
            metadata_ai=metadata_ai
        )
        
        # Set global verbose flag for models
        Config.VERBOSE = verbose
        
        # Create processor
        processor = QuestionProcessor(config)
        
        # Create question range
        question_range = range(min_question, effective_max_question + 1)
        
        print(f"\nStarting processing of exercise {exercise}, questions {min_question}-{effective_max_question}...")
        print(f"Using {Config.MODEL_TYPE.upper()} model")

        # Use new batch processing
        print("Using new batch processing...")
        batch_result = processor.process_questions_batch(exercise, question_range)
        
        # Print detailed summary (already printed by processor)
        if batch_result.success_rate < 100:
            print(f"\nFailed questions:")
            for result in batch_result.results:
                if not result.success:
                    print(f"  Question {result.question}: {'; '.join(result.errors)}")
        
        print(f"\nResults saved to: questions/output/{exercise}/json/")
        
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        return 1
    except ProcessingError as e:
        print(f"❌ Processing error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())