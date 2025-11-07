"""Main LLM questioner orchestrator class."""

import os
import time
from typing import List, Optional, Dict, Any
from pathlib import Path

from ..llm.factory import create_providers_from_config
from ..processors.question_parser import QuestionParser
from ..managers.results_manager import ResultsManager
from ..core.exceptions import ProcessingError, ConfigurationError
from ..evaluators import AnswerEvaluator
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
            self.results_manager = ResultsManager(str(self.config.results_dir), question_mode=question_mode)
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize components: {e}")
    
    def process_questions(self, start: Optional[int] = None, end: Optional[int] = None,
                          question_types: Optional[List[str]] = None,
                          output_file: str = 'llm_evaluation_results.csv') -> Dict[str, Any]:
        """
        Process questions and query LLM responses.
        
        Args:
            start: Start question number
            end: End question number
            question_types: List of question types to filter by
            output_file: Output CSV filename (not used)
            
        Returns:
            Processing results summary
            
        Raises:
            ProcessingError: If processing fails
        """
        # Load system prompt
        system_prompt_path = Path(__file__).parent.parent.parent.parent / 'prompts' / 'answer_question.txt'
        try:
            with open(system_prompt_path, 'r') as f:
                system_prompt = f.read().strip()
        except Exception as e:
            print(f"Warning: Could not load system prompt from {system_prompt_path}: {e}")
            system_prompt = None
        
        # Find question files
        question_files = self.config.find_question_files(start, end, question_types)
        evaluator = AnswerEvaluator()
        
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
                # Handle text mode
                txt_file = file_path
                question_id = self.question_parser.get_question_id_from_path(txt_file)
                json_file = self.config.get_question_metadata_path(txt_file)

                evaluator
                
                if not os.path.exists(json_file):
                    print(f"Warning: JSON file not found for {question_id}")
                    continue

                # Parse question
                question_data = self.question_parser.parse_json_file(json_file)
                question_type = question_data['type']
                
                if not self.question_parser.validate_question_data(question_data):
                    print(f"Warning: Invalid question data for {question_id}")
                    continue


                with open(txt_file) as f:
                  prompt = f.read()
                
                # Stub values for compatibility
                correct_answers = question_data['answers']
                
                # Check if question has an image (from question data)
                has_image = question_data.get('has_image', False)
                image_path = question_data.get('image') if has_image else None
                
                print(f"\nProcessing Question {question_id} ({question_type})")
                
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
                            return provider.query(prompt, system_prompt=system_prompt, image_path=image_path)
                        
                        llm_response = retry_with_backoff(query_llm)
                        print(f"    Response received: {len(llm_response)} characters")
                        
                        # Evaluate the response
                        evaluation = evaluator.evaluate_response(question_type, llm_response, correct_answers)
                        
                        successful_operations += 1
                    
                    except Exception as e:
                        error_msg = str(e)
                        print(f"ERROR: {error_msg}")
                        failed_operations += 1
                    
                    processing_time = time.time() - start_time
                    
                    # Simple token estimation
                    input_tokens = len(prompt.split())
                    output_tokens = len(llm_response.split())
                    
                    # Format correct answers as string for display
                    correct_answer_str = str(correct_answers)
                    
                    # Store result
                    self.results_manager.add_result(
                        question_id=question_id,
                        model_name=model_name,
                        question_type=question_type,
                        llm_answer=str(evaluation["llm_answer"]),
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