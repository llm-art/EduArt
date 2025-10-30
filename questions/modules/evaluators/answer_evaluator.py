"""Answer evaluator for comparing LLM responses with correct answers."""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from difflib import SequenceMatcher
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
        """
        Parse LLM response based on question type.
        
        Args:
            question_type: Type of question
            response: Raw LLM response
            
        Returns:
            List of parsed response elements
        """
        response = response.strip()
        
        if question_type in ['multiple_choice_radio', 'multiple_choice']:
            # Extract single letter
            match = re.search(r'\b([A-E])\b', response)
            return [match.group(1)] if match else [response]
        
        elif question_type == 'multiple_choice_check':
            # Extract multiple letters
            letters = re.findall(r'\b([A-F])\b', response)
            return letters if letters else [response]
        
        elif question_type == 'select_errors':
            # Split by commas and clean
            errors = [item.strip() for item in response.split(',')]
            return [error for error in errors if error]
        
        elif question_type == 'completion_closed':
            # Extract BLANK_X: answer pairs
            matches = re.findall(r'BLANK_\d+:\s*([^,\n]+)', response)
            return [match.strip() for match in matches] if matches else [response]
        
        elif question_type == 'positioning':
            # For positioning questions, preserve the full response to parse BLANK_X format
            return [response]
        
        elif question_type == 'completion_open':
            # Split by commas
            terms = [item.strip() for item in response.split(',')]
            return [term for term in terms if term]
        
        elif question_type == 'true_false':
            # Extract A: True/False pairs
            matches = re.findall(r'([A-F]):\s*(Vero|Falso|True|False)', response, re.IGNORECASE)
            return [f"{letter}:{value}" for letter, value in matches] if matches else [response]
        
        return [response]
    
    def calculate_comprehensive_metrics(self, user_answers: set, correct_answers: set) -> Dict[str, float]:
        """
        Calculate comprehensive metrics for multi-answer questions.
        
        Args:
            user_answers: Set of user-provided answers
            correct_answers: Set of correct answers
            
        Returns:
            Dictionary with all calculated metrics
        """
        # Handle empty sets
        if not correct_answers:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'jaccard': 0.0,
                'accuracy': 0.0,
                'exact_match': False
            }
        
        if not user_answers:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'jaccard': 0.0,
                'accuracy': 0.0,
                'exact_match': False
            }
        
        # Calculate basic sets
        intersection = user_answers & correct_answers
        union = user_answers | correct_answers
        
        # Precision: correct selections / total selections
        precision = len(intersection) / len(user_answers) if user_answers else 0.0
        
        # Recall: correct selections / total correct answers
        recall = len(intersection) / len(correct_answers) if correct_answers else 0.0
        
        # F1-Score: harmonic mean of precision and recall
        f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Jaccard: intersection / union
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # Accuracy: for multi-label, this is the intersection over union (same as Jaccard)
        accuracy = jaccard
        
        # Exact match: perfect match
        exact_match = user_answers == correct_answers
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'jaccard': jaccard,
            'accuracy': accuracy,
            'exact_match': exact_match
        }
    
    def determine_confidence_level(self, metrics: Dict[str, float], question_type: str) -> str:
        """
        Determine confidence level based on metrics and question type.
        
        Args:
            metrics: Dictionary of calculated metrics
            question_type: Type of question
            
        Returns:
            Confidence level string
        """
        config = self.QUESTION_TYPE_THRESHOLDS.get(question_type, {'primary_metric': 'f1_score', 'threshold': 0.7})
        primary_metric = config['primary_metric']
        
        if primary_metric == 'manual':
            return 'manual_review'
        
        primary_score = metrics.get(primary_metric, 0.0)
        
        if primary_score >= 0.8:
            return 'high'
        elif primary_score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def analyze_errors(self, user_answers: set, correct_answers: set) -> Dict[str, List[str]]:
        """
        Analyze different types of errors in the response.
        
        Args:
            user_answers: Set of user-provided answers
            correct_answers: Set of correct answers
            
        Returns:
            Dictionary with error analysis
        """
        missing_answers = list(correct_answers - user_answers)
        incorrect_answers = list(user_answers - correct_answers)
        correct_answers_list = list(user_answers & correct_answers)
        
        return {
            'missing_answers': sorted(missing_answers),
            'incorrect_answers': sorted(incorrect_answers),
            'correct_answers': sorted(correct_answers_list)
        }
    
    def evaluate_response(self, question_type: str, llm_response: str,
                         correct_answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate LLM response against correct answers.
        
        Args:
            question_type: Type of question
            llm_response: LLM response text
            correct_answers: Dictionary with correct answer information
            
        Returns:
            Evaluation result dictionary
        """
        parsed_response = self.parse_llm_response(question_type, llm_response)
        answers = correct_answers.get('answers', [])
        
        if not answers:
            return {
                'is_correct': None,
                'score': None,
                'details': 'No ground truth available',
                'parsed_response': parsed_response
            }
        
        if question_type in ['multiple_choice_radio', 'multiple_choice']:
            return self._evaluate_single_choice(parsed_response, answers, question_type)
        
        elif question_type == 'multiple_choice_check':
            return self._evaluate_multiple_choice(parsed_response, answers, question_type)
        
        elif question_type == 'select_errors':
            return self._evaluate_select_errors(parsed_response, answers, question_type)
        
        elif question_type == 'completion_closed':
            return self._evaluate_completion_closed(parsed_response, answers, question_type)
        
        elif question_type == 'positioning':
            return self._evaluate_positioning(parsed_response, answers, question_type)
        
        elif question_type == 'completion_open':
            return {
                'is_correct': None,
                'score': None,
                'details': 'Manual evaluation required',
                'parsed_response': parsed_response,
                'metrics': {},
                'confidence_level': 'manual_review',
                'error_analysis': {}
            }
        
        elif question_type == 'true_false':
            return self._evaluate_true_false(parsed_response, answers, question_type)
        
        return {
            'is_correct': False,
            'score': 0.0,
            'details': 'Unknown question type',
            'parsed_response': parsed_response,
            'metrics': {},
            'confidence_level': 'low',
            'error_analysis': {}
        }
    
    def _evaluate_single_choice(self, parsed_response: List[str], answers: List[Dict], question_type: str) -> Dict[str, Any]:
        """Evaluate single choice questions with enhanced metrics."""
        if not parsed_response:
            return {
                'is_correct': False,
                'score': 0.0,
                'details': 'No response',
                'parsed_response': parsed_response,
                'metrics': {'exact_match': False, 'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0, 'jaccard': 0.0},
                'confidence_level': 'low',
                'error_analysis': {'missing_answers': [], 'incorrect_answers': [], 'correct_answers': []}
            }
        
        user_answer = parsed_response[0].upper()
        correct_answer = answers[0].get('id', '').upper() if answers else ''
        
        is_correct = user_answer == correct_answer
        metrics = {
            'exact_match': is_correct,
            'accuracy': 1.0 if is_correct else 0.0,
            'precision': 1.0 if is_correct else 0.0,
            'recall': 1.0 if is_correct else 0.0,
            'f1_score': 1.0 if is_correct else 0.0,
            'jaccard': 1.0 if is_correct else 0.0
        }
        
        confidence_level = self.determine_confidence_level(metrics, question_type)
        
        error_analysis = {
            'missing_answers': [] if is_correct else [correct_answer],
            'incorrect_answers': [] if is_correct else [user_answer],
            'correct_answers': [correct_answer] if is_correct else []
        }
        
        return {
            'is_correct': is_correct,
            'score': 1.0 if is_correct else 0.0,
            'details': f'User: {user_answer}, Correct: {correct_answer}',
            'parsed_response': parsed_response,
            'metrics': metrics,
            'confidence_level': confidence_level,
            'error_analysis': error_analysis
        }
    
    def _evaluate_multiple_choice(self, parsed_response: List[str], answers: List[Dict], question_type: str) -> Dict[str, Any]:
        """Evaluate multiple choice questions with comprehensive metrics."""
        user_answers = set(ans.upper() for ans in parsed_response)
        correct_answers = set(ans.get('id', '').upper() for ans in answers)
        
        # Calculate comprehensive metrics
        metrics = self.calculate_comprehensive_metrics(user_answers, correct_answers)
        
        # Determine confidence level
        confidence_level = self.determine_confidence_level(metrics, question_type)
        
        # Analyze errors
        error_analysis = self.analyze_errors(user_answers, correct_answers)
        
        # Determine correctness based on question-type specific threshold
        config = self.QUESTION_TYPE_THRESHOLDS.get(question_type, {'primary_metric': 'f1_score', 'threshold': 0.7})
        primary_metric = config['primary_metric']
        threshold = config['threshold']
        
        if primary_metric == 'exact_match':
            is_correct = metrics['exact_match']
            primary_score = 1.0 if metrics['exact_match'] else 0.0
        else:
            primary_score = metrics.get(primary_metric, 0.0)
            is_correct = primary_score >= threshold
        
        return {
            'is_correct': is_correct,
            'score': primary_score,
            'details': f'User: {sorted(user_answers)}, Correct: {sorted(correct_answers)}',
            'parsed_response': parsed_response,
            'metrics': metrics,
            'confidence_level': confidence_level,
            'error_analysis': error_analysis
        }
    
    def _evaluate_text_list(self, parsed_response: List[str], answers: List[str]) -> Dict[str, Any]:
        """Evaluate text-based list answers with fuzzy matching."""
        if not parsed_response or not answers:
            return {'is_correct': False, 'score': 0.0, 'details': 'Empty response or answers', 'parsed_response': parsed_response}
        
        # Fuzzy matching for each answer
        matched = 0
        total_correct = len(answers)
        
        for correct_answer in answers:
            best_match = 0.0
            for user_answer in parsed_response:
                similarity = SequenceMatcher(None, user_answer.lower(), correct_answer.lower()).ratio()
                best_match = max(best_match, similarity)
            
            if best_match > 0.8:  # 80% similarity threshold
                matched += 1
        
        score = matched / total_correct if total_correct > 0 else 0.0
        is_correct = score >= 0.8
        
        return {
            'is_correct': is_correct,
            'score': score,
            'details': f'Matched {matched}/{total_correct} answers',
            'parsed_response': parsed_response
        }
    
    def _evaluate_completion_closed(self, parsed_response: List[str], answers: List[Dict], question_type: str) -> Dict[str, Any]:
        """Evaluate completion closed questions with enhanced metrics."""
        if not parsed_response or not answers:
            return {
                'is_correct': False,
                'score': 0.0,
                'details': 'Empty response or answers',
                'parsed_response': parsed_response,
                'metrics': {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0, 'jaccard': 0.0, 'exact_match': False},
                'confidence_level': 'low',
                'error_analysis': {'missing_answers': [], 'incorrect_answers': [], 'correct_answers': []}
            }
        
        correct_answers = [ans.get('description', '').lower() for ans in answers]
        user_answers = [ans.lower() for ans in parsed_response]
        
        matched = 0
        correct_list = []
        incorrect_list = []
        missing_list = []
        
        for i, correct in enumerate(correct_answers):
            if i < len(user_answers):
                similarity = SequenceMatcher(None, user_answers[i], correct).ratio()
                if similarity > 0.8:
                    matched += 1
                    correct_list.append(f"BLANK_{i+1}:{user_answers[i]}")
                else:
                    incorrect_list.append(f"BLANK_{i+1}:{user_answers[i]}")
            else:
                missing_list.append(f"BLANK_{i+1}:{correct}")
        
        score = matched / len(correct_answers) if correct_answers else 0.0
        
        # Calculate enhanced metrics
        metrics = {
            'accuracy': score,
            'precision': score,
            'recall': score,
            'f1_score': score,
            'jaccard': score,
            'exact_match': score == 1.0
        }
        
        # Determine correctness based on threshold
        config = self.QUESTION_TYPE_THRESHOLDS.get(question_type, {'primary_metric': 'accuracy', 'threshold': 0.8})
        threshold = config['threshold']
        is_correct = score >= threshold
        
        confidence_level = self.determine_confidence_level(metrics, question_type)
        
        error_analysis = {
            'missing_answers': missing_list,
            'incorrect_answers': incorrect_list,
            'correct_answers': correct_list
        }
        
        return {
            'is_correct': is_correct,
            'score': score,
            'details': f'Matched {matched}/{len(correct_answers)} blanks',
            'parsed_response': parsed_response,
            'metrics': metrics,
            'confidence_level': confidence_level,
            'error_analysis': error_analysis
        }
    
    def _evaluate_true_false(self, parsed_response: List[str], answers: List[Dict], question_type: str) -> Dict[str, Any]:
        """Evaluate true/false questions with enhanced metrics."""
        if not parsed_response or not answers:
            return {
                'is_correct': False,
                'score': 0.0,
                'details': 'Empty response or answers',
                'parsed_response': parsed_response,
                'metrics': {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0, 'jaccard': 0.0, 'exact_match': False},
                'confidence_level': 'low',
                'error_analysis': {'missing_answers': [], 'incorrect_answers': [], 'correct_answers': []}
            }
        
        # Create mapping of correct answers
        correct_map = {}
        for ans in answers:
            if ans.get('note') == 'Risposta esatta.':
                correct_map[ans.get('id', '')] = ans.get('text', '').lower()
        
        matched = 0
        total = len(correct_map)
        user_responses = {}
        
        for response in parsed_response:
            if ':' in response:
                letter, value = response.split(':', 1)
                letter = letter.strip().upper()
                value = value.strip().lower()
                user_responses[letter] = value
                
                if letter in correct_map:
                    correct_value = correct_map[letter]
                    if (value in ['vero', 'true'] and correct_value in ['true', 'vero']) or \
                       (value in ['falso', 'false'] and correct_value in ['false', 'falso']):
                        matched += 1
        
        score = matched / total if total > 0 else 0.0
        
        # Calculate enhanced metrics
        metrics = {
            'accuracy': score,
            'precision': score,  # For true/false, precision equals accuracy
            'recall': score,     # For true/false, recall equals accuracy
            'f1_score': score,   # For true/false, F1 equals accuracy
            'jaccard': score,    # For true/false, Jaccard equals accuracy
            'exact_match': score == 1.0
        }
        
        # Determine correctness based on threshold
        config = self.QUESTION_TYPE_THRESHOLDS.get(question_type, {'primary_metric': 'accuracy', 'threshold': 0.8})
        threshold = config['threshold']
        is_correct = score >= threshold
        
        confidence_level = self.determine_confidence_level(metrics, question_type)
        
        # Error analysis
        correct_answers = []
        incorrect_answers = []
        missing_answers = []
        
        for letter, correct_value in correct_map.items():
            user_value = user_responses.get(letter, '')
            if user_value:
                if (user_value in ['vero', 'true'] and correct_value in ['true', 'vero']) or \
                   (user_value in ['falso', 'false'] and correct_value in ['false', 'falso']):
                    correct_answers.append(f"{letter}:{user_value}")
                else:
                    incorrect_answers.append(f"{letter}:{user_value}")
            else:
                missing_answers.append(f"{letter}:{correct_value}")
        
        error_analysis = {
            'missing_answers': missing_answers,
            'incorrect_answers': incorrect_answers,
            'correct_answers': correct_answers
        }
        
        return {
            'is_correct': is_correct,
            'score': score,
            'details': f'Matched {matched}/{total} statements',
            'parsed_response': parsed_response,
            'metrics': metrics,
            'confidence_level': confidence_level,
            'error_analysis': error_analysis
        }
    
    def _evaluate_positioning(self, parsed_response: List[str], answers: List[Dict], question_type: str) -> Dict[str, Any]:
        """Evaluate positioning questions by comparing BLANK_X answers with correct terms."""
        if not parsed_response or not answers:
            return {
                'is_correct': False,
                'score': 0.0,
                'details': 'Empty response or answers',
                'parsed_response': parsed_response,
                'metrics': {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0, 'jaccard': 0.0, 'exact_match': False},
                'confidence_level': 'low',
                'error_analysis': {'missing_answers': [], 'incorrect_answers': [], 'correct_answers': []}
            }
        
        # Parse the LLM response to extract BLANK_X: answer pairs
        blank_answers = {}
        response_text = ' '.join(parsed_response)
        
        # Extract BLANK_X: answer pairs from the response
        matches = re.findall(r'BLANK_(\d+):\s*([^,\n]+)', response_text)
        for blank_num, answer in matches:
            blank_answers[int(blank_num)] = answer.strip()
        
        # If no BLANK_X format found, try to parse as comma-separated list
        if not blank_answers and len(parsed_response) > 0:
            # Assume the response is a comma-separated list in order
            terms = [term.strip() for term in parsed_response[0].split(',')]
            for i, term in enumerate(terms, 1):
                blank_answers[i] = term
        
        # Create mapping of correct answers by blank position
        correct_answers = {}
        for answer in answers:
            if isinstance(answer, dict):
                blank_pos = answer.get('blank_position')
                correct_term = answer.get('correct_term', '')
                if blank_pos:
                    correct_answers[blank_pos] = correct_term.strip()
        
        if not correct_answers:
            return {'is_correct': False, 'score': 0.0, 'details': 'No correct answers found', 'parsed_response': parsed_response}
        
        # Compare answers
        matched = 0
        total = len(correct_answers)
        details = []
        
        for blank_pos, correct_term in correct_answers.items():
            user_answer = blank_answers.get(blank_pos, '').strip()
            
            # Use fuzzy matching for comparison
            similarity = SequenceMatcher(None, user_answer.lower(), correct_term.lower()).ratio()
            
            if similarity > 0.8:  # 80% similarity threshold
                matched += 1
                details.append(f"BLANK_{blank_pos}: '{user_answer}' ≈ '{correct_term}' ✓")
            else:
                details.append(f"BLANK_{blank_pos}: '{user_answer}' ≠ '{correct_term}' ✗")
        
        score = matched / total if total > 0 else 0.0
        
        # Calculate enhanced metrics
        metrics = {
            'accuracy': score,
            'precision': score,
            'recall': score,
            'f1_score': score,
            'jaccard': score,
            'exact_match': score == 1.0
        }
        
        # Determine correctness based on threshold
        config = self.QUESTION_TYPE_THRESHOLDS.get(question_type, {'primary_metric': 'accuracy', 'threshold': 0.8})
        threshold = config['threshold']
        is_correct = score >= threshold
        
        confidence_level = self.determine_confidence_level(metrics, question_type)
        
        # Error analysis
        correct_list = []
        incorrect_list = []
        missing_list = []
        
        for blank_pos, correct_term in correct_answers.items():
            user_answer = blank_answers.get(blank_pos, '').strip()
            if user_answer:
                similarity = SequenceMatcher(None, user_answer.lower(), correct_term.lower()).ratio()
                if similarity > 0.8:
                    correct_list.append(f"BLANK_{blank_pos}:{user_answer}")
                else:
                    incorrect_list.append(f"BLANK_{blank_pos}:{user_answer}")
            else:
                missing_list.append(f"BLANK_{blank_pos}:{correct_term}")
        
        error_analysis = {
            'missing_answers': missing_list,
            'incorrect_answers': incorrect_list,
            'correct_answers': correct_list
        }
        
        return {
            'is_correct': is_correct,
            'score': score,
            'details': f'Matched {matched}/{total} blanks. ' + '; '.join(details),
            'parsed_response': parsed_response,
            'metrics': metrics,
            'confidence_level': confidence_level,
            'error_analysis': error_analysis
        }
    
    def _evaluate_select_errors(self, parsed_response: List[str], answers: List[Dict], question_type: str) -> Dict[str, Any]:
        """Evaluate select_errors questions by comparing identified errors with correct error terms."""
        if not parsed_response or not answers:
            return {
                'is_correct': False,
                'score': 0.0,
                'details': 'Empty response or answers',
                'parsed_response': parsed_response,
                'metrics': {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1_score': 0.0, 'jaccard': 0.0, 'exact_match': False},
                'confidence_level': 'low',
                'error_analysis': {'missing_answers': [], 'incorrect_answers': [], 'correct_answers': []}
            }
        
        # Extract error terms from the response
        user_errors = []
        for response in parsed_response:
            # Split by semicolon or comma and clean
            errors = re.split(r'[;,]', response)
            user_errors.extend([error.strip() for error in errors if error.strip()])
        
        # Remove duplicates while preserving order
        seen = set()
        user_errors = [x for x in user_errors if not (x in seen or seen.add(x))]
        
        # Extract correct error terms from answers
        correct_errors = []
        for answer in answers:
            if isinstance(answer, dict):
                error_term = answer.get('error', '')
                if error_term:
                    correct_errors.append(error_term.strip())
        
        if not correct_errors:
            return {'is_correct': False, 'score': 0.0, 'details': 'No correct errors found', 'parsed_response': parsed_response}
        
        # Compare errors using fuzzy matching
        matched = 0
        total = len(correct_errors)
        details = []
        
        for correct_error in correct_errors:
            best_match = 0.0
            best_user_error = ''
            
            for user_error in user_errors:
                similarity = SequenceMatcher(None, user_error.lower(), correct_error.lower()).ratio()
                if similarity > best_match:
                    best_match = similarity
                    best_user_error = user_error
            
            if best_match > 0.8:  # 80% similarity threshold
                matched += 1
                details.append(f"'{best_user_error}' ≈ '{correct_error}' ✓")
            else:
                details.append(f"'{correct_error}' not found ✗")
        
        # Check for extra errors (false positives)
        extra_errors = []
        for user_error in user_errors:
            found = False
            for correct_error in correct_errors:
                similarity = SequenceMatcher(None, user_error.lower(), correct_error.lower()).ratio()
                if similarity > 0.8:
                    found = True
                    break
            if not found:
                extra_errors.append(user_error)
        
        score = matched / total if total > 0 else 0.0
        
        # Calculate enhanced metrics using set-based approach
        user_errors_set = set(user_errors)
        correct_errors_set = set(correct_errors)
        metrics = self.calculate_comprehensive_metrics(user_errors_set, correct_errors_set)
        
        # Determine correctness based on threshold and no extra errors
        config = self.QUESTION_TYPE_THRESHOLDS.get(question_type, {'primary_metric': 'f1_score', 'threshold': 0.8})
        primary_metric = config['primary_metric']
        threshold = config['threshold']
        
        primary_score = metrics.get(primary_metric, 0.0)
        is_correct = primary_score >= threshold and len(extra_errors) == 0
        
        confidence_level = self.determine_confidence_level(metrics, question_type)
        
        # Error analysis
        matched_errors = []
        missing_errors = []
        for correct_error in correct_errors:
            found = False
            for user_error in user_errors:
                similarity = SequenceMatcher(None, user_error.lower(), correct_error.lower()).ratio()
                if similarity > 0.8:
                    matched_errors.append(user_error)
                    found = True
                    break
            if not found:
                missing_errors.append(correct_error)
        
        error_analysis = {
            'missing_answers': missing_errors,
            'incorrect_answers': extra_errors,
            'correct_answers': matched_errors
        }
        
        extra_details = f" Extra errors: {extra_errors}" if extra_errors else ""
        
        return {
            'is_correct': is_correct,
            'score': primary_score,
            'details': f'Matched {matched}/{total} errors. ' + '; '.join(details) + extra_details,
            'parsed_response': parsed_response,
            'metrics': metrics,
            'confidence_level': confidence_level,
            'error_analysis': error_analysis
        }