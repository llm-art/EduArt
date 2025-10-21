"""Answer evaluator for comparing LLM responses with correct answers."""

import json
import re
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher
from ..core.exceptions import ProcessingError


class AnswerEvaluator:
    """Evaluator for comparing LLM responses with correct answers."""
    
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
            return self._evaluate_single_choice(parsed_response, answers)
        
        elif question_type == 'multiple_choice_check':
            return self._evaluate_multiple_choice(parsed_response, answers)
        
        elif question_type == 'select_errors':
            return self._evaluate_select_errors(parsed_response, answers)
        
        elif question_type == 'completion_closed':
            return self._evaluate_completion_closed(parsed_response, answers)
        
        elif question_type == 'positioning':
            return self._evaluate_positioning(parsed_response, answers)
        
        elif question_type == 'completion_open':
            return {
                'is_correct': None,
                'score': None,
                'details': 'Manual evaluation required',
                'parsed_response': parsed_response
            }
        
        elif question_type == 'true_false':
            return self._evaluate_true_false(parsed_response, answers)
        
        return {
            'is_correct': False,
            'score': 0.0,
            'details': 'Unknown question type',
            'parsed_response': parsed_response
        }
    
    def _evaluate_single_choice(self, parsed_response: List[str], answers: List[Dict]) -> Dict[str, Any]:
        """Evaluate single choice questions."""
        if not parsed_response:
            return {'is_correct': False, 'score': 0.0, 'details': 'No response', 'parsed_response': parsed_response}
        
        user_answer = parsed_response[0].upper()
        correct_answer = answers[0].get('id', '').upper() if answers else ''
        
        is_correct = user_answer == correct_answer
        return {
            'is_correct': is_correct,
            'score': 1.0 if is_correct else 0.0,
            'details': f'User: {user_answer}, Correct: {correct_answer}',
            'parsed_response': parsed_response
        }
    
    def _evaluate_multiple_choice(self, parsed_response: List[str], answers: List[Dict]) -> Dict[str, Any]:
        """Evaluate multiple choice questions."""
        user_answers = set(ans.upper() for ans in parsed_response)
        correct_answers = set(ans.get('id', '').upper() for ans in answers)
        
        if user_answers == correct_answers:
            return {
                'is_correct': True,
                'score': 1.0,
                'details': f'Perfect match: {sorted(correct_answers)}',
                'parsed_response': parsed_response
            }
        
        # Partial credit
        intersection = user_answers & correct_answers
        union = user_answers | correct_answers
        score = len(intersection) / len(union) if union else 0.0
        
        return {
            'is_correct': False,
            'score': score,
            'details': f'User: {sorted(user_answers)}, Correct: {sorted(correct_answers)}',
            'parsed_response': parsed_response
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
    
    def _evaluate_completion_closed(self, parsed_response: List[str], answers: List[Dict]) -> Dict[str, Any]:
        """Evaluate completion closed questions."""
        if not parsed_response or not answers:
            return {'is_correct': False, 'score': 0.0, 'details': 'Empty response or answers', 'parsed_response': parsed_response}
        
        correct_answers = [ans.get('description', '').lower() for ans in answers]
        user_answers = [ans.lower() for ans in parsed_response]
        
        matched = 0
        for i, correct in enumerate(correct_answers):
            if i < len(user_answers):
                similarity = SequenceMatcher(None, user_answers[i], correct).ratio()
                if similarity > 0.8:
                    matched += 1
        
        score = matched / len(correct_answers) if correct_answers else 0.0
        is_correct = score >= 0.8
        
        return {
            'is_correct': is_correct,
            'score': score,
            'details': f'Matched {matched}/{len(correct_answers)} blanks',
            'parsed_response': parsed_response
        }
    
    def _evaluate_true_false(self, parsed_response: List[str], answers: List[Dict]) -> Dict[str, Any]:
        """Evaluate true/false questions."""
        if not parsed_response or not answers:
            return {'is_correct': False, 'score': 0.0, 'details': 'Empty response or answers', 'parsed_response': parsed_response}
        
        # Create mapping of correct answers
        correct_map = {}
        for ans in answers:
            if ans.get('note') == 'Risposta esatta.':
                correct_map[ans.get('id', '')] = ans.get('text', '').lower()
        
        matched = 0
        total = len(correct_map)
        
        for response in parsed_response:
            if ':' in response:
                letter, value = response.split(':', 1)
                letter = letter.strip().upper()
                value = value.strip().lower()
                
                if letter in correct_map:
                    correct_value = correct_map[letter]
                    if (value in ['vero', 'true'] and correct_value in ['true', 'vero']) or \
                       (value in ['falso', 'false'] and correct_value in ['false', 'falso']):
                        matched += 1
        
        score = matched / total if total > 0 else 0.0
        is_correct = score >= 0.8
        
        return {
            'is_correct': is_correct,
            'score': score,
            'details': f'Matched {matched}/{total} statements',
            'parsed_response': parsed_response
        }
    
    def _evaluate_positioning(self, parsed_response: List[str], answers: List[Dict]) -> Dict[str, Any]:
        """Evaluate positioning questions by comparing BLANK_X answers with correct terms."""
        if not parsed_response or not answers:
            return {'is_correct': False, 'score': 0.0, 'details': 'Empty response or answers', 'parsed_response': parsed_response}
        
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
        is_correct = score >= 0.8  # Consider correct if 80% or more blanks are correct
        
        return {
            'is_correct': is_correct,
            'score': score,
            'details': f'Matched {matched}/{total} blanks. ' + '; '.join(details),
            'parsed_response': parsed_response
        }
    
    def _evaluate_select_errors(self, parsed_response: List[str], answers: List[Dict]) -> Dict[str, Any]:
        """Evaluate select_errors questions by comparing identified errors with correct error terms."""
        if not parsed_response or not answers:
            return {'is_correct': False, 'score': 0.0, 'details': 'Empty response or answers', 'parsed_response': parsed_response}
        
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
        is_correct = score >= 0.8 and len(extra_errors) == 0  # Perfect match required
        
        extra_details = f" Extra errors: {extra_errors}" if extra_errors else ""
        
        return {
            'is_correct': is_correct,
            'score': score,
            'details': f'Matched {matched}/{total} errors. ' + '; '.join(details) + extra_details,
            'parsed_response': parsed_response
        }