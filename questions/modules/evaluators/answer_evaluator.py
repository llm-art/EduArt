"""Answer evaluator for comparing LLM responses with correct answers."""

import json
import re
from typing import Dict, List, Any, Optional
from ..core.exceptions import ProcessingError


class AnswerEvaluator:
    """Evaluator for comparing LLM responses with correct answers."""
    
    # Question-type specific thresholds for determining correctness
    QUESTION_TYPE_THRESHOLDS = {
        'multiple_choice_radio': {'primary_metric': 'exact_match', 'threshold': 1.0},
        'multiple_choice': {'primary_metric': 'exact_match', 'threshold': 1.0},
        'multiple_choice_check': {'primary_metric': 'f1_score', 'threshold': 0.7},
        'true_false': {'primary_metric': 'accuracy', 'threshold': 0.8},
        'positioning': {'primary_metric': 'accuracy', 'threshold': 0.8},
        'select_errors': {'primary_metric': 'f1_score', 'threshold': 0.8},
        'completion_closed': {'primary_metric': 'accuracy', 'threshold': 0.8},
        'completion_open': {'primary_metric': 'manual', 'threshold': None}
    }
    
    def extract_correct_answers(self, json_filepath: str) -> Dict[str, Any]:
        """
        Extract correct answers from JSON file.
        
        Args:
            json_filepath: Path to the JSON file containing correct answers
            
        Returns:
            Dictionary with answer information
            
        Raises:
            ProcessingError: If file cannot be read or parsed
        """
        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            question_type = data.get('type', '')
            answers = data.get('answers', [])
            
            return {
                'type': question_type,
                'answers': answers,
                'raw_data': data
            }
        except Exception as e:
            raise ProcessingError(f"Error reading {json_filepath}: {e}")
    
    def parse_llm_response(self, question_type: str, response: str) -> List[str]:
        """Parse LLM response based on question type."""
        pass
    
    def calculate_metrics(self, true_positives: int, false_positives: int,
                         false_negatives: int, true_negatives: int = 0) -> Dict[str, Any]:
        """
        Calculate comprehensive evaluation metrics.
        
        Args:
            true_positives: Correctly identified positive cases
            false_positives: Incorrectly identified as positive
            false_negatives: Incorrectly identified as negative
            true_negatives: Correctly identified negative cases (optional)
            
        Returns:
            Dictionary with precision, recall, f1, exact_match, and ratio
        """
        total = true_positives + false_negatives
        
        # Precision: TP / (TP + FP)
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        
        # Recall: TP / (TP + FN)
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        
        # F1 Score: 2 * (precision * recall) / (precision + recall)
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Exact Match: 1.0 if all correct, 0.0 otherwise
        exact_match = 1.0 if (false_positives == 0 and false_negatives == 0 and true_positives > 0) else 0.0
        
        # Ratio (for backward compatibility)
        ratio = true_positives / total if total > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'exact_match': exact_match,
            'ratio': ratio,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'total': total
        }
    
    def evaluate_response(self, question_type: str, llm_response: str,
                         correct_answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate LLM response against correct answers.
        
        Args:
            question_type: Type of question being evaluated
            llm_response: JSON string response from LLM
            correct_answers: Dictionary or list of correct answers
            
        Returns:
            Dictionary with evaluation results compatible with process_questions
        """
        try:
            # Clean and extract JSON from response
            original_response = llm_response
            llm_response = llm_response.replace("```json","").replace("```", "").strip()
            
            # Fix common JSON formatting issues from LLMs
            # Remove double braces that some LLMs add
            llm_response = re.sub(r'^\{\{', '{', llm_response)
            llm_response = re.sub(r'\}\}$', '}', llm_response)
            
            # Attempt to fix incomplete JSON responses
            # Count opening and closing braces and brackets
            open_braces = llm_response.count('{')
            close_braces = llm_response.count('}')
            open_brackets = llm_response.count('[')
            close_brackets = llm_response.count(']')
            
            # Add missing closing brackets/braces
            if close_brackets < open_brackets:
                llm_response += ']' * (open_brackets - close_brackets)
            if close_braces < open_braces:
                llm_response += '}' * (open_braces - close_braces)
            
            # Try to parse the JSON
            response_data = json.loads(llm_response)
            parsed_response = response_data.get('Answers', [])
            
            # Route to appropriate evaluation function based on question type
            # ID-only evaluation (text is ignored)
            if question_type in ['multiple_choice_radio', 'multiple_choice_check']:
                evaluation = self._evaluate_by_id(parsed_response, correct_answers, question_type)
            
            # ID+Text evaluation (both must match)
            elif question_type in ['completion_closed', 'positioning', 'true_false', 'select_errors', 'completion_open']:
                evaluation = self._evaluate_by_id_text(parsed_response, correct_answers, question_type)
            
            else:
                # Unknown question type
                evaluation = {
                    'is_correct': False,
                    'score': 0.0,
                    'details': f'Unknown question type: {question_type}',
                    'parsed_response': parsed_response,
                    'metrics': {},
                    'error_analysis': {}
                }
            
            # Remove explanation and motivation fields from answers
            cleaned_response = []
            for answer in parsed_response:
                if isinstance(answer, dict):
                    # Create a copy of the answer dict and remove unwanted fields
                    cleaned_answer = answer.copy()
                    cleaned_answer.pop('explanation', None)
                    cleaned_answer.pop('motivation', None)
                    cleaned_response.append(cleaned_answer)
                else:
                    cleaned_response.append(answer)
            
            evaluation["llm_answer"] = {"Answers": cleaned_response}
            
            return evaluation
            
        except json.JSONDecodeError as e:
            # Failed to parse JSON response
            return {
                'is_correct': False,
                'score': 0.0,
                'details': f'JSON parsing error: {str(e)}',
                'parsed_response': [],
                'metrics': {},
                'error_analysis': {'parse_error': str(e)},
                'llm_answer': llm_response  # Include raw response for debugging
            }
        except Exception as e:
            # Other errors
            return {
                'is_correct': False,
                'score': 0.0,
                'details': f'Evaluation error: {str(e)}',
                'parsed_response': [],
                'metrics': {},
                'error_analysis': {'evaluation_error': str(e)},
                'llm_answer': llm_response if 'llm_response' in locals() else ''  # Include raw response if available
            }
    
    def _evaluate_by_id(self, parsed_response: List, answers: List[Dict], question_type: str) -> Dict[str, Any]:
        """
        Unified evaluation for ID-only comparison (multiple choice questions).
        Text content is ignored - only ID matching matters.
        
        Args:
            parsed_response: List of answer IDs from LLM (can be string or dict)
            answers: List of correct answer dictionaries with 'id' field
            question_type: Type of question
            
        Returns:
            Evaluation result dictionary
        """
        # Extract user IDs (normalize to uppercase)
        user_ids = set()
        for item in parsed_response:
            if isinstance(item, dict):
                user_id = item.get('id', '').strip().upper()
                if user_id:
                    user_ids.add(user_id)
            elif isinstance(item, str):
                user_id = item.strip().upper()
                if user_id:
                    user_ids.add(user_id)
        
        # Extract correct IDs (already normalized to uppercase by bundler)
        correct_ids = set()
        for ans in answers:
            if isinstance(ans, dict):
                ans_id = ans.get('id', '').strip().upper()
                if ans_id:
                    correct_ids.add(ans_id)
        
        if not correct_ids:
            return {
                'is_correct': False,
                'score': 0.0,
                'details': 'No correct answers found in metadata',
                'parsed_response': parsed_response,
                'metrics': {},
                'error_analysis': {'error': 'Missing correct answers in metadata'}
            }
        
        # For single choice (radio), expect exactly one answer
        if question_type == 'multiple_choice_radio':
            if len(user_ids) != 1:
                metrics = self.calculate_metrics(0, len(user_ids), 1)
                return {
                    'is_correct': False,
                    'score': 0.0,
                    'details': f'Expected 1 answer, got {len(user_ids)}',
                    'parsed_response': parsed_response,
                    'metrics': metrics,
                    'error_analysis': {'error': 'Wrong number of answers'}
                }
            
            # Check if the single answer is correct
            is_correct = user_ids == correct_ids
            true_positives = 1 if is_correct else 0
            false_positives = 0 if is_correct else 1
            false_negatives = 0 if is_correct else 1
        else:
            # Multiple choice (checkbox) - calculate overlap
            true_positives = len(user_ids & correct_ids)
            false_positives = len(user_ids - correct_ids)
            false_negatives = len(correct_ids - user_ids)
        
        metrics = self.calculate_metrics(true_positives, false_positives, false_negatives)
        threshold = self.QUESTION_TYPE_THRESHOLDS[question_type]['threshold']
        is_correct = metrics['f1'] >= threshold if question_type == 'multiple_choice_check' else metrics['exact_match'] == 1.0
        
        return {
            'is_correct': is_correct,
            'score': metrics['f1'],
            'details': f"F1: {metrics['f1']:.2f}, Precision: {metrics['precision']:.2f}, Recall: {metrics['recall']:.2f}, Exact Match: {metrics['exact_match']:.2f}",
            'parsed_response': parsed_response,
            'metrics': metrics,
            'error_analysis': {
                'correct_answers': list(user_ids & correct_ids),
                'incorrect_answers': list((user_ids - correct_ids) | (correct_ids - user_ids))
            }
        }
    
    def _evaluate_by_id_text(self, parsed_response: List, answers: List[Dict], question_type: str) -> Dict[str, Any]:
        """
        Unified evaluation for ID+Text comparison.
        Both ID (position) and text (content) must match.
        
        Used for: completion_closed, positioning, true_false, select_errors, completion_open
        
        Args:
            parsed_response: List of dicts with 'id' and 'description'/'text' from LLM
            answers: List of correct answer dicts with 'id' and 'text' (normalized by bundler)
            question_type: Type of question
            
        Returns:
            Evaluation result dictionary
        """
        # Helper function to clean text by removing numeric prefixes
        def clean_text(text: str) -> str:
            """Remove numeric prefix pattern like '1. ' or '2. ' from text and normalize."""
            cleaned = re.sub(r'^\d+\.\s*', '', text.strip())

            return cleaned.lower()
        
        # Build lookup dictionary from user response: {id: text}
        response_dict = {}
        for item in parsed_response:
            if isinstance(item, dict):
                item_id = item.get('id', '').strip().upper()
                # Try multiple field names for text content
                text = item.get('text', item.get('description', item.get('error', ''))).strip()
                if item_id and text:
                    response_dict[item_id] = clean_text(text)
        
        # Build lookup dictionary from correct answers: {id: text}
        # Text is already normalized to lowercase by bundler
        answer_dict = {}
        for item in answers:
            if isinstance(item, dict):
                item_id = item.get('id', '').strip().upper()
                text = item.get('text', '').strip().lower()
                if item_id and text:
                    answer_dict[item_id] = text
        
        if not answer_dict:
            return {
                'is_correct': False,
                'score': 0.0,
                'details': 'No correct answers found in metadata',
                'parsed_response': parsed_response,
                'metrics': {},
                'error_analysis': {'error': 'Missing correct answers in metadata'}
            }
        
        # Compare each answer by ID and text
        true_positives = 0
        false_negatives = 0
        total = len(answer_dict)
        
        correct_items = []
        incorrect_items = []
        
        for answer_id, correct_text in answer_dict.items():
            user_text = response_dict.get(answer_id, '').strip().lower()
            
            if user_text == correct_text:
                true_positives += 1
                correct_items.append(f"{answer_id}: {correct_text}")
            else:
                false_negatives += 1
                incorrect_items.append(f"{answer_id} (got: '{user_text}', expected: '{correct_text}')")
        
        # For ID+Text evaluation, false positives are 0 since we only check expected IDs
        false_positives = 0
        metrics = self.calculate_metrics(true_positives, false_positives, false_negatives)
        threshold = self.QUESTION_TYPE_THRESHOLDS[question_type].get('threshold')
        
        # Handle manual evaluation for completion_open
        if threshold is None:
            return {
                'is_correct': None,
                'score': metrics['recall'],
                'details': f"Manual evaluation required. Recall: {metrics['recall']:.2f}, Precision: {metrics['precision']:.2f}, F1: {metrics['f1']:.2f}, Exact Match: {metrics['exact_match']:.2f}",
                'parsed_response': parsed_response,
                'metrics': metrics,
                'error_analysis': {
                    'correct_answers': correct_items,
                    'incorrect_answers': incorrect_items
                }
            }
        
        is_correct = metrics['recall'] >= threshold
        
        return {
            'is_correct': is_correct,
            'score': metrics['recall'],
            'details': f"Recall: {metrics['recall']:.2f}, Precision: {metrics['precision']:.2f}, F1: {metrics['f1']:.2f}, Exact Match: {metrics['exact_match']:.2f}",
            'parsed_response': parsed_response,
            'metrics': metrics,
            'error_analysis': {
                'correct_answers': correct_items,
                'incorrect_answers': incorrect_items
            }
        }
    