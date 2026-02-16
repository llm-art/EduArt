"""
Level 1 Evaluation Metrics for Non-Multiple-Choice Question Types

This module implements Level 1 (basic) evaluation metrics for:
- true_false: True/False questions
- completion_closed: Fill-in-the-blank with binary choices
- completion_open: Free-text fill-in-the-blank
- positioning: Select terms from pool to fill blanks
- select_errors: Identify and correct errors in text

Level 1 Metrics (Easy to implement):
- Exact Match Accuracy: Percentage of items correctly answered
- Perfect Question Score: Binary - 1 if all correct, 0 otherwise
- Partial Credit Score: Percentage of correct items
"""

import re
from typing import Dict, List, Any, Tuple


class Level1Evaluator:
    """Level 1 evaluation metrics for non-multiple-choice questions."""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison: lowercase, strip whitespace, remove numeric prefixes."""
        cleaned = re.sub(r'^\d+\.\s*', '', text.strip())
        return cleaned.lower()
    
    @staticmethod
    def normalize_boolean(text: str) -> str:
        """Normalize boolean values to 'true' or 'false'."""
        text_lower = text.strip().lower()
        if text_lower in ['true', 't', 'vero', 'v', '1', 'yes', 'si', 'sì']:
            return 'true'
        elif text_lower in ['false', 'f', 'falso', '0', 'no']:
            return 'false'
        return text_lower
    
    @staticmethod
    def calculate_level1_metrics(correct_count: int, total_count: int) -> Dict[str, float]:
        """
        Calculate Level 1 metrics.
        
        Args:
            correct_count: Number of correct items
            total_count: Total number of items
            
        Returns:
            Dictionary with Level 1 metrics
        """
        exact_match_accuracy = correct_count / total_count if total_count > 0 else 0.0
        perfect_question_score = 1.0 if correct_count == total_count else 0.0
        partial_credit_score = exact_match_accuracy
        
        return {
            'exact_match_accuracy': exact_match_accuracy,
            'perfect_question_score': perfect_question_score,
            'partial_credit_score': partial_credit_score,
            'correct_count': correct_count,
            'total_count': total_count
        }
    
    def evaluate_true_false(self, parsed_response: List, answers: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate true/false questions with Level 1 metrics.
        
        Level 1 Metrics:
        - Exact Match Accuracy: Percentage of statements correctly classified
        - Per-Statement Accuracy: Individual accuracy for each statement
        - Perfect Question Score: Binary - 1 if all correct, 0 otherwise
        
        Args:
            parsed_response: List of dicts with 'id' and 'text' (True/False)
            answers: List of correct answer dicts with 'id' and 'text' (True/False)
            
        Returns:
            Evaluation result dictionary with Level 1 metrics
        """
        # Build response dictionary: {id: normalized_value}
        response_dict = {}
        for item in parsed_response:
            if isinstance(item, dict):
                item_id = item.get('id', '').strip().upper()
                text = item.get('text', '').strip()
                if item_id:
                    response_dict[item_id] = self.normalize_boolean(text)
        
        # Build answer dictionary: {id: normalized_value}
        answer_dict = {}
        for item in answers:
            if isinstance(item, dict):
                item_id = item.get('id', '').strip().upper()
                text = item.get('text', '').strip()
                if item_id:
                    answer_dict[item_id] = self.normalize_boolean(text)
        
        if not answer_dict:
            return self._error_result('No correct answers found')
        
        # Calculate per-statement accuracy
        correct_count = 0
        total_count = len(answer_dict)
        per_statement_results = {}
        correct_items = []
        incorrect_items = []
        
        for answer_id, correct_value in answer_dict.items():
            user_value = response_dict.get(answer_id, '')
            is_match = (user_value == correct_value)
            
            per_statement_results[answer_id] = {
                'correct': is_match,
                'expected': correct_value,
                'got': user_value
            }
            
            if is_match:
                correct_count += 1
                correct_items.append(f"{answer_id}: {correct_value}")
            else:
                incorrect_items.append(f"{answer_id} (got: '{user_value}', expected: '{correct_value}')")
        
        # Calculate Level 1 Metrics
        level1_metrics = self.calculate_level1_metrics(correct_count, total_count)
        
        # Build comprehensive metrics
        metrics = {
            **level1_metrics,
            'per_statement_accuracy': per_statement_results,
            # Standard metrics for compatibility
            'precision': 1.0 if correct_count == total_count else (correct_count / total_count if total_count > 0 else 0.0),
            'recall': level1_metrics['exact_match_accuracy'],
            'f1': level1_metrics['exact_match_accuracy'],
            'exact_match': level1_metrics['perfect_question_score'],
            'ratio': level1_metrics['exact_match_accuracy'],
            'true_positives': correct_count,
            'false_positives': 0,
            'false_negatives': total_count - correct_count,
            'total': total_count
        }
        
        return {
            'is_correct': level1_metrics['perfect_question_score'] == 1.0,
            'score': level1_metrics['exact_match_accuracy'],
            'details': f"Accuracy: {level1_metrics['exact_match_accuracy']:.2%} ({correct_count}/{total_count}), Perfect Score: {level1_metrics['perfect_question_score']:.0f}",
            'parsed_response': parsed_response,
            'metrics': metrics,
            'error_analysis': {
                'correct_answers': correct_items,
                'incorrect_answers': incorrect_items,
                'per_statement': per_statement_results
            }
        }
    
    def evaluate_completion_closed(self, parsed_response: List, answers: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate completion_closed questions (multiple blanks with binary choices).
        
        Level 1 Metrics:
        - Exact Match Accuracy: Percentage of blanks filled correctly
        - Per-Blank Accuracy: Individual accuracy for each blank
        - Perfect Question Score: Binary - 1 if all correct, 0 otherwise
        - Partial Credit Score: Percentage of correct blanks
        
        Args:
            parsed_response: List of dicts with 'id' and 'description'
            answers: List of correct answer dicts with 'id' and 'description'
            
        Returns:
            Evaluation result dictionary with Level 1 metrics
        """
        # Build response dictionary: {id: normalized_text}
        response_dict = {}
        for item in parsed_response:
            if isinstance(item, dict):
                item_id = item.get('id', '').strip().upper()
                text = item.get('description', item.get('text', '')).strip()
                if item_id and text:
                    response_dict[item_id] = self.normalize_text(text)
        
        # Build answer dictionary: {id: normalized_text}
        answer_dict = {}
        for item in answers:
            if isinstance(item, dict):
                item_id = item.get('id', '').strip().upper()
                text = item.get('description', item.get('text', '')).strip()
                if item_id and text:
                    answer_dict[item_id] = self.normalize_text(text)
        
        if not answer_dict:
            return self._error_result('No correct answers found')
        
        # Calculate per-blank accuracy
        correct_count = 0
        total_count = len(answer_dict)
        per_blank_results = {}
        correct_items = []
        incorrect_items = []
        
        for answer_id, correct_text in answer_dict.items():
            user_text = response_dict.get(answer_id, '')
            is_match = (user_text == correct_text)
            
            per_blank_results[answer_id] = {
                'correct': is_match,
                'expected': correct_text,
                'got': user_text
            }
            
            if is_match:
                correct_count += 1
                correct_items.append(f"{answer_id}: {correct_text}")
            else:
                incorrect_items.append(f"{answer_id} (got: '{user_text}', expected: '{correct_text}')")
        
        # Calculate Level 1 Metrics
        level1_metrics = self.calculate_level1_metrics(correct_count, total_count)
        
        # Build comprehensive metrics
        metrics = {
            **level1_metrics,
            'per_blank_accuracy': per_blank_results,
            # Standard metrics for compatibility
            'precision': 1.0 if correct_count == total_count else (correct_count / total_count if total_count > 0 else 0.0),
            'recall': level1_metrics['exact_match_accuracy'],
            'f1': level1_metrics['exact_match_accuracy'],
            'exact_match': level1_metrics['perfect_question_score'],
            'ratio': level1_metrics['exact_match_accuracy'],
            'true_positives': correct_count,
            'false_positives': 0,
            'false_negatives': total_count - correct_count,
            'total': total_count
        }
        
        return {
            'is_correct': level1_metrics['perfect_question_score'] == 1.0,
            'score': level1_metrics['exact_match_accuracy'],
            'details': f"Accuracy: {level1_metrics['exact_match_accuracy']:.2%} ({correct_count}/{total_count}), Perfect Score: {level1_metrics['perfect_question_score']:.0f}",
            'parsed_response': parsed_response,
            'metrics': metrics,
            'error_analysis': {
                'correct_answers': correct_items,
                'incorrect_answers': incorrect_items,
                'per_blank': per_blank_results
            }
        }
    
    def evaluate_completion_open(self, parsed_response: List, answers: List) -> Dict[str, Any]:
        """
        Evaluate completion_open questions (free-text answers).
        
        Level 1 Metrics:
        - Exact Match Accuracy: Percentage of blanks with exact string match
        - Perfect Question Score: Binary - 1 if all exact matches, 0 otherwise
        - Partial Credit Score: Percentage of correct blanks
        
        Note: For completion_open, answers can be a simple list of strings (no IDs).
        
        Args:
            parsed_response: List of strings or dicts with answers
            answers: List of correct answer strings
            
        Returns:
            Evaluation result dictionary with Level 1 metrics
        """
        # Extract user responses - handle both list of strings and list of dicts
        user_answers = []
        if isinstance(parsed_response, list):
            for item in parsed_response:
                if isinstance(item, dict):
                    # Try to extract text from dict
                    text = item.get('text', item.get('description', item.get('answer', ''))).strip()
                    if text:
                        user_answers.append(self.normalize_text(text))
                elif isinstance(item, str):
                    user_answers.append(self.normalize_text(item))
        
        # Normalize correct answers
        correct_answers = []
        if isinstance(answers, list):
            for item in answers:
                if isinstance(item, str):
                    correct_answers.append(self.normalize_text(item))
                elif isinstance(item, dict):
                    text = item.get('text', item.get('description', '')).strip()
                    if text:
                        correct_answers.append(self.normalize_text(text))
        
        if not correct_answers:
            return self._error_result('No correct answers found')
        
        # Match answers by position
        total_count = len(correct_answers)
        correct_count = 0
        per_position_results = {}
        correct_items = []
        incorrect_items = []
        
        for i, correct_text in enumerate(correct_answers):
            user_text = user_answers[i] if i < len(user_answers) else ''
            is_match = (user_text == correct_text)
            
            position_label = chr(65 + i)  # A, B, C, etc.
            per_position_results[position_label] = {
                'correct': is_match,
                'expected': correct_text,
                'got': user_text
            }
            
            if is_match:
                correct_count += 1
                correct_items.append(f"{position_label}: {correct_text}")
            else:
                incorrect_items.append(f"{position_label} (got: '{user_text}', expected: '{correct_text}')")
        
        # Calculate Level 1 Metrics
        level1_metrics = self.calculate_level1_metrics(correct_count, total_count)
        
        # Build comprehensive metrics
        metrics = {
            **level1_metrics,
            'per_position_accuracy': per_position_results,
            # Standard metrics for compatibility
            'precision': 1.0 if correct_count == total_count else (correct_count / total_count if total_count > 0 else 0.0),
            'recall': level1_metrics['exact_match_accuracy'],
            'f1': level1_metrics['exact_match_accuracy'],
            'exact_match': level1_metrics['perfect_question_score'],
            'ratio': level1_metrics['exact_match_accuracy'],
            'true_positives': correct_count,
            'false_positives': 0,
            'false_negatives': total_count - correct_count,
            'total': total_count
        }
        
        # For open completion, we mark as requiring manual review if not perfect
        is_correct = None if level1_metrics['perfect_question_score'] < 1.0 else True
        
        return {
            'is_correct': is_correct,
            'score': level1_metrics['exact_match_accuracy'],
            'details': f"Exact Match Accuracy: {level1_metrics['exact_match_accuracy']:.2%} ({correct_count}/{total_count}), Manual review recommended for non-exact matches",
            'parsed_response': parsed_response,
            'metrics': metrics,
            'error_analysis': {
                'correct_answers': correct_items,
                'incorrect_answers': incorrect_items,
                'per_position': per_position_results,
                'note': 'Open completion may have acceptable alternatives not captured by exact match'
            }
        }
    
    def evaluate_positioning(self, parsed_response: List, answers: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate positioning questions (select terms from pool to fill blanks).
        
        Level 1 Metrics:
        - Exact Match Accuracy: Percentage of positions correctly filled
        - Perfect Question Score: Binary - 1 if all correct, 0 otherwise
        - Partial Credit Score: Percentage of correct positions
        
        Args:
            parsed_response: List of dicts with 'id' and 'description'
            answers: List of correct answer dicts with 'id' and 'description'
            
        Returns:
            Evaluation result dictionary with Level 1 metrics
        """
        # Build response dictionary: {id: normalized_text}
        response_dict = {}
        for item in parsed_response:
            if isinstance(item, dict):
                item_id = item.get('id', '').strip().upper()
                text = item.get('description', item.get('text', '')).strip()
                if item_id and text:
                    response_dict[item_id] = self.normalize_text(text)
        
        # Build answer dictionary: {id: normalized_text}
        answer_dict = {}
        for item in answers:
            if isinstance(item, dict):
                item_id = item.get('id', '').strip().upper()
                text = item.get('description', item.get('text', '')).strip()
                if item_id and text:
                    answer_dict[item_id] = self.normalize_text(text)
        
        if not answer_dict:
            return self._error_result('No correct answers found')
        
        # Calculate per-position accuracy
        correct_count = 0
        total_count = len(answer_dict)
        per_position_results = {}
        correct_items = []
        incorrect_items = []
        
        for answer_id, correct_text in answer_dict.items():
            user_text = response_dict.get(answer_id, '')
            is_match = (user_text == correct_text)
            
            per_position_results[answer_id] = {
                'correct': is_match,
                'expected': correct_text,
                'got': user_text
            }
            
            if is_match:
                correct_count += 1
                correct_items.append(f"{answer_id}: {correct_text}")
            else:
                incorrect_items.append(f"{answer_id} (got: '{user_text}', expected: '{correct_text}')")
        
        # Calculate Level 1 Metrics
        level1_metrics = self.calculate_level1_metrics(correct_count, total_count)
        
        # Build comprehensive metrics
        metrics = {
            **level1_metrics,
            'per_position_accuracy': per_position_results,
            # Standard metrics for compatibility
            'precision': 1.0 if correct_count == total_count else (correct_count / total_count if total_count > 0 else 0.0),
            'recall': level1_metrics['exact_match_accuracy'],
            'f1': level1_metrics['exact_match_accuracy'],
            'exact_match': level1_metrics['perfect_question_score'],
            'ratio': level1_metrics['exact_match_accuracy'],
            'true_positives': correct_count,
            'false_positives': 0,
            'false_negatives': total_count - correct_count,
            'total': total_count
        }
        
        return {
            'is_correct': level1_metrics['perfect_question_score'] == 1.0,
            'score': level1_metrics['exact_match_accuracy'],
            'details': f"Accuracy: {level1_metrics['exact_match_accuracy']:.2%} ({correct_count}/{total_count}), Perfect Score: {level1_metrics['perfect_question_score']:.0f}",
            'parsed_response': parsed_response,
            'metrics': metrics,
            'error_analysis': {
                'correct_answers': correct_items,
                'incorrect_answers': incorrect_items,
                'per_position': per_position_results
            }
        }
    
    def evaluate_select_errors(self, parsed_response: List, answers: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate select_errors questions (identify and correct errors in text).
        
        Level 1 Metrics:
        - Exact Match Accuracy: Percentage of error-correction pairs correctly identified
        - Perfect Question Score: Binary - 1 if all pairs correct, 0 otherwise
        - Partial Credit Score: Percentage of correct pairs
        
        Note: For select_errors, answers have 'error' and 'correct' fields.
        
        Args:
            parsed_response: List of dicts with error-correction pairs
            answers: List of correct answer dicts with 'error' and 'correct' fields
            
        Returns:
            Evaluation result dictionary with Level 1 metrics
        """
        # Build response dictionary: {normalized_error: normalized_correction}
        response_dict = {}
        for item in parsed_response:
            if isinstance(item, dict):
                error_text = item.get('error', item.get('incorrect', '')).strip()
                correct_text = item.get('correct', item.get('correction', '')).strip()
                if error_text and correct_text:
                    response_dict[self.normalize_text(error_text)] = self.normalize_text(correct_text)
        
        # Build answer dictionary: {normalized_error: normalized_correction}
        answer_dict = {}
        for item in answers:
            if isinstance(item, dict):
                error_text = item.get('error', '').strip()
                correct_text = item.get('correct', '').strip()
                if error_text and correct_text:
                    answer_dict[self.normalize_text(error_text)] = self.normalize_text(correct_text)
        
        if not answer_dict:
            return self._error_result('No correct answers found')
        
        # Calculate per-pair accuracy
        correct_count = 0
        total_count = len(answer_dict)
        per_pair_results = {}
        correct_items = []
        incorrect_items = []
        
        pair_index = 0
        for error_text, correct_text in answer_dict.items():
            user_correction = response_dict.get(error_text, '')
            is_match = (user_correction == correct_text)
            
            pair_label = chr(65 + pair_index)  # A, B, C, etc.
            per_pair_results[pair_label] = {
                'correct': is_match,
                'error': error_text,
                'expected_correction': correct_text,
                'got_correction': user_correction
            }
            
            if is_match:
                correct_count += 1
                correct_items.append(f"{pair_label}: '{error_text}' → '{correct_text}'")
            else:
                incorrect_items.append(f"{pair_label}: '{error_text}' (got: '{user_correction}', expected: '{correct_text}')")
            
            pair_index += 1
        
        # Calculate Level 1 Metrics
        level1_metrics = self.calculate_level1_metrics(correct_count, total_count)
        
        # Build comprehensive metrics
        metrics = {
            **level1_metrics,
            'per_pair_accuracy': per_pair_results,
            # Standard metrics for compatibility
            'precision': 1.0 if correct_count == total_count else (correct_count / total_count if total_count > 0 else 0.0),
            'recall': level1_metrics['exact_match_accuracy'],
            'f1': level1_metrics['exact_match_accuracy'],
            'exact_match': level1_metrics['perfect_question_score'],
            'ratio': level1_metrics['exact_match_accuracy'],
            'true_positives': correct_count,
            'false_positives': 0,
            'false_negatives': total_count - correct_count,
            'total': total_count
        }
        
        return {
            'is_correct': level1_metrics['perfect_question_score'] == 1.0,
            'score': level1_metrics['exact_match_accuracy'],
            'details': f"Accuracy: {level1_metrics['exact_match_accuracy']:.2%} ({correct_count}/{total_count}), Perfect Score: {level1_metrics['perfect_question_score']:.0f}",
            'parsed_response': parsed_response,
            'metrics': metrics,
            'error_analysis': {
                'correct_answers': correct_items,
                'incorrect_answers': incorrect_items,
                'per_pair': per_pair_results
            }
        }
    
    def _error_result(self, error_message: str) -> Dict[str, Any]:
        """Return a standard error result."""
        return {
            'is_correct': False,
            'score': 0.0,
            'details': error_message,
            'parsed_response': [],
            'metrics': {},
            'error_analysis': {'error': error_message}
        }
