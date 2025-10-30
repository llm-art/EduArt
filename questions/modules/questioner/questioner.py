"""Main LLM questioner orchestrator class."""

import os
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..llm.factory import create_providers_from_config
from ..processors.question_parser import QuestionParser
from ..evaluators.answer_evaluator import AnswerEvaluator
from ..managers.results_manager import ResultsManager
from ..core.exceptions import ProcessingError, ConfigurationError
from .config import QuestionerConfig


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    Retry function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        
    Returns:
        Function result
        
    Raises:
        Exception: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            delay = base_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)


class LLMQuestioner:
    """Main orchestrator for LLM question evaluation."""
    
    def __init__(self, models_to_test: Optional[List[str]] = None, question_mode: str = 'text'):
        """
        Initialize LLM questioner.
        
        Args:
            models_to_test: List of model specifications to test
            question_mode: Question mode - 'text' or 'screenshot'
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = QuestionerConfig()
        self.question_mode = question_mode
        
        # Validate configuration
        errors = self.config.validate_configuration()
        if errors:
            raise ConfigurationError(f"Configuration errors: {'; '.join(errors)}")
        
        # Initialize components
        try:
            self.providers = create_providers_from_config(models_to_test)
            self.question_parser = QuestionParser(question_mode=question_mode)
            self.answer_evaluator = AnswerEvaluator()
            self.results_manager = ResultsManager(str(self.config.results_dir), question_mode=question_mode)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize components: {e}")
    
    def process_questions(self, start: Optional[int] = None, end: Optional[int] = None,
                         question_types: Optional[List[str]] = None, 
                         output_file: str = 'llm_evaluation_results.csv') -> Dict[str, Any]:
        """
        Process questions and evaluate LLM responses.
        
        Args:
            start: Start question number
            end: End question number
            question_types: List of question types to filter by
            output_file: Output CSV filename
            
        Returns:
            Processing results summary
            
        Raises:
            ProcessingError: If processing fails
        """
        if self.question_mode == 'screenshot':
            # Find screenshot files instead of text files
            screenshot_files = self.question_parser.find_screenshot_files()
            if not screenshot_files:
                raise ProcessingError("No screenshot files found in dataset/raw")
            
            # Filter by range if specified
            if start is not None or end is not None:
                filtered_files = []
                for file_path in screenshot_files:
                    filename = Path(file_path).stem
                    try:
                        file_num = int(filename)
                        if (start is None or file_num >= start) and (end is None or file_num <= end):
                            filtered_files.append(file_path)
                    except ValueError:
                        continue
                screenshot_files = filtered_files
            
            question_files = screenshot_files
            print(f"Found {len(question_files)} screenshot files to process")
        else:
            # Find question files
            question_files = self.config.find_question_files(start, end, question_types)
            
            if not question_files:
                raise ProcessingError("No question files found matching the criteria")
            
            print(f"Found {len(question_files)} question files to process")
        
        print(f"Testing with {len(self.providers)} LLM providers")
        
        # Process each question with each model
        total_operations = len(question_files) * len(self.providers)
        current_operation = 0
        successful_operations = 0
        failed_operations = 0
        
        for file_path in question_files:
            try:
                all_images = []  # Initialize for all modes
                
                if self.question_mode == 'screenshot':
                    # Handle screenshot mode
                    filename = Path(file_path).stem
                    question_id = filename.zfill(4)  # Pad with zeros to match format
                    
                    # Find corresponding metadata file
                    current_dir = Path(__file__).parent.parent.parent.parent
                    json_file = current_dir / 'dataset' / 'metadata' / f'{question_id}.json'
                    
                    if not os.path.exists(json_file):
                        print(f"Warning: Metadata file not found for {question_id}")
                        continue
                    
                    # Parse screenshot file (minimal data)
                    question_data = self.question_parser.parse_screenshot_file(file_path)
                    prompt = self.question_parser.create_prompt(question_data)
                    
                    # Extract correct answers from metadata
                    correct_answers = self.answer_evaluator.extract_correct_answers(str(json_file))
                    correct_answer_str = str(correct_answers.get('answers', []))
                    
                    # For screenshot mode, collect all images
                    has_image = True
                    image_path = file_path  # Primary screenshot
                    additional_images = question_data.get('additional_images', [])
                    
                    # Create list of all images (screenshot first, then additional)
                    all_images = [file_path] + additional_images
                    
                    # Get question type from metadata
                    try:
                        import json
                        with open(json_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        question_type = metadata.get('type', 'unknown')
                    except Exception:
                        question_type = 'unknown'
                    
                else:
                    # Handle text mode (original logic)
                    txt_file = file_path
                    question_id = self.question_parser.get_question_id_from_path(txt_file)
                    json_file = self.config.get_question_metadata_path(txt_file)
                    
                    if not os.path.exists(json_file):
                        print(f"Warning: JSON file not found for {question_id}")
                        continue
                    
                    # Parse question
                    question_data = self.question_parser.parse_txt_file(txt_file)
                    
                    if not self.question_parser.validate_question_data(question_data):
                        print(f"Warning: Invalid question data for {question_id}")
                        continue
                    
                    question_type = self.question_parser.refine_question_type(question_data)
                    prompt = self.question_parser.create_prompt(question_data)
                    
                    # Extract correct answers
                    correct_answers = self.answer_evaluator.extract_correct_answers(json_file)
                    correct_answer_str = str(correct_answers.get('answers', []))
                    
                    # Check if question has an image
                    has_image = correct_answers.get('raw_data', {}).get('has_image', False)
                    image_path = correct_answers.get('raw_data', {}).get('image') if has_image else None
                
                print(f"\nProcessing Question {question_id} ({question_type})")
                if has_image:
                    if self.question_mode == 'screenshot' and all_images:
                        print(f"Images required: {len(all_images)} total")
                        for i, img in enumerate(all_images):
                            print(f"  Image {i+1}: {img}")
                    elif image_path:
                        print(f"Image required: {image_path}")
                print(f"Prompt being sent:\n{prompt}\n")
                
                for provider in self.providers:
                    current_operation += 1
                    model_name = provider.get_model_name()
                    
                    print(f"  [{current_operation}/{total_operations}] Testing {model_name}...", end=' ')
                    
                    start_time = time.time()
                    error_msg = ""
                    llm_response = ""
                    evaluation = {'is_correct': False, 'score': 0.0, 'details': 'Error occurred'}
                    
                    try:
                        # Query LLM with retry logic
                        def query_llm():
                            if self.question_mode == 'screenshot' and all_images:
                                return provider.query(prompt, image_paths=all_images)
                            else:
                                return provider.query(prompt, image_path)
                        
                        llm_response = retry_with_backoff(query_llm)
                        
                        # Log the raw response for debugging
                        print(f"\n    Raw LLM Response: '{llm_response}'")
                        
                        # Evaluate response
                        evaluation = self.answer_evaluator.evaluate_response(
                            question_type,
                            llm_response,
                            correct_answers
                        )
                        
                        # Log evaluation details for debugging
                        print(f"    Parsed Response: {evaluation.get('parsed_response', [])}")
                        print(f"    Expected Answer: {correct_answers.get('answers', [])}")
                        print(f"    Evaluation Details: {evaluation.get('details', '')}")
                        
                        # Print result
                        if evaluation['is_correct'] is None:
                            print("    Result: MANUAL_REVIEW")
                        elif evaluation['is_correct']:
                            print(f"    Result: CORRECT (score: {evaluation['score']:.2f})")
                        else:
                            print(f"    Result: INCORRECT (score: {evaluation['score']:.2f})")
                        
                        successful_operations += 1
                    
                    except Exception as e:
                        error_msg = str(e)
                        print(f"ERROR: {error_msg}")
                        failed_operations += 1
                    
                    processing_time = time.time() - start_time
                    
                    # Estimate token usage (rough approximation)
                    # For more accurate tracking, this should be implemented in each provider
                    input_tokens = len(prompt.split()) * 1.3  # Rough approximation for text
                    
                    # Add significant tokens for image if present
                    if has_image and image_path:
                        # Images typically use 85-170 tokens per image depending on size and detail
                        # Using a conservative estimate of 1000 tokens for vision models
                        input_tokens += 1000
                    
                    output_tokens = len(llm_response.split()) * 1.3  # Rough approximation
                    
                    # Store result
                    self.results_manager.add_result(
                        question_id=question_id,
                        model_name=model_name,
                        question_type=question_type,
                        llm_answer=llm_response,
                        correct_answer=correct_answer_str,
                        evaluation=evaluation,
                        processing_time=processing_time,
                        error=error_msg,
                        question_data={
                            'question_text': question_data.get('question_text', ''),
                            'question_type': question_type,
                            'has_image': has_image,
                            'image_path': image_path,
                            'correct_answers': correct_answers,
                            'prompt': prompt
                        },
                        input_tokens=int(input_tokens),
                        output_tokens=int(output_tokens)
                    )
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
            
            except Exception as e:
                print(f"Error processing question {question_id}: {e}")
                failed_operations += len(self.providers)
                continue
        
        # Only generate answers folder structure (no results/ folder files)
        self.results_manager.print_summary()
        self.results_manager.finalize_answers_output()
        
        return {
            'total_operations': total_operations,
            'successful_operations': successful_operations,
            'failed_operations': failed_operations,
            'success_rate': (successful_operations / total_operations * 100) if total_operations > 0 else 0,
            'questions_processed': len(question_files),
            'models_tested': len(self.providers),
            'answers_folder': str(self.results_manager.answers_dir)
        }
    
    def get_provider_info(self) -> List[Dict[str, Any]]:
        """
        Get information about initialized providers.
        
        Returns:
            List of provider information dictionaries
        """
        return [provider.get_provider_info() for provider in self.providers]
    
    def print_status(self):
        """Print current questioner status."""
        print("=== LLM Questioner Status ===")
        self.config.print_configuration_status()
        
        print(f"\nInitialized Providers ({len(self.providers)}):")
        for provider in self.providers:
            info = provider.get_provider_info()
            print(f"  - {info['model_name']} ({info['provider_type']})")
        
        print(f"\nResults stored: {self.results_manager.get_results_count()}")
        print("=" * 30)
    
    def clear_results(self):
        """Clear all stored results."""
        self.results_manager.clear_results()
    
    def get_results_summary(self) -> Dict[str, Any]:
        """
        Get current results summary.
        
        Returns:
            Results summary dictionary
        """
        return self.results_manager.generate_summary()