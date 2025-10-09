#!/usr/bin/env python3
"""
Browser automation for submitting answers to Zanichelli and capturing results.
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from .automator import ZanichelliExerciseAutomator


class ZanichelliAnswerSubmitter:
    def __init__(self, config_path: str = "config.json"):
        self.automator = ZanichelliExerciseAutomator(config_path)
        self.is_initialized = False
    
    async def initialize(self, headless: bool = True):
        """Initialize the browser automation."""
        print(f"Initializing Zanichelli submitter (headless: {headless})...")
        success = await self.automator.initialize(headless=headless)
        self.is_initialized = success
        if success:
            print("✅ Zanichelli submitter initialized successfully")
        else:
            print("❌ Failed to initialize Zanichelli submitter")
        return success
    
    async def submit_answer(
        self, 
        exercise_url: str,
        exercise_index: int,
        question_number: int,
        answer: str,
        question_type: str
    ) -> Dict[str, Any]:
        """
        Submit an answer to Zanichelli and capture the result.
        
        Args:
            exercise_url: URL of the exercise
            exercise_index: Index of the exercise (0-based)
            question_number: Question number (1-based)
            answer: The answer to submit
            question_type: Type of question
            
        Returns:
            Dictionary with submission results
        """
        if not self.is_initialized:
            raise RuntimeError("Submitter not initialized")
        
        result = {
            'success': False,
            'submitted_answer': answer,
            'correct_answer': None,
            'is_correct': None,
            'error': None
        }
        
        try:
            print(f"Submitting answer '{answer}' for question {question_number}...")
            
            # Navigate to exercise and start it
            print("Navigating to exercise...")
            await self.automator.navigate_to_exercise_list(exercise_url)
            
            print("Performing login...")
            await self.automator.perform_login()
            
            print(f"Starting exercise {exercise_index + 1}...")
            await self.automator.start_exercise(exercise_index)
            
            # Navigate to specific question if needed
            if question_number > 1:
                await self._navigate_to_question(question_number)
            
            # Submit the answer based on question type
            await self._submit_answer_by_type(answer, question_type)
            
            # Capture the result (correct/incorrect feedback)
            correct_answer, is_correct = await self._capture_result()
            
            result.update({
                'success': True,
                'correct_answer': correct_answer,
                'is_correct': is_correct
            })
            
            print(f"✅ Answer submitted successfully")
            print(f"   Submitted: {answer}")
            print(f"   Correct: {correct_answer}")
            print(f"   Result: {'✓' if is_correct else '✗' if is_correct is False else '?'}")
            
        except Exception as e:
            error_msg = f"Error submitting answer: {e}"
            print(f"❌ {error_msg}")
            result['error'] = error_msg
        
        return result
    
    async def _navigate_to_question(self, question_number: int):
        """Navigate to a specific question number."""
        print(f"Navigating to question {question_number}...")
        
        # This is a simplified approach - you may need to adjust based on Zanichelli's UI
        page = self.automator.browser_manager.page
        
        # Try to find and click "next" buttons to reach the desired question
        current_question = 1
        while current_question < question_number:
            try:
                # Look for next button (adjust selector based on actual UI)
                next_selectors = [
                    'button:has-text("AVANTI")',
                    'button:has-text("NEXT")',
                    'button:has-text(">")',
                    '.next-button',
                    '[data-action="next"]'
                ]
                
                clicked = False
                for selector in next_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        clicked = True
                        break
                    except:
                        continue
                
                if not clicked:
                    print(f"⚠️ Could not find next button at question {current_question}")
                    break
                
                await page.wait_for_timeout(1000)  # Wait for navigation
                current_question += 1
                
            except Exception as e:
                print(f"⚠️ Error navigating to question {question_number}: {e}")
                break
    
    async def _submit_answer_by_type(self, answer: str, question_type: str):
        """Submit answer based on question type."""
        page = self.automator.browser_manager.page
        
        print(f"Submitting {question_type} answer: {answer}")
        
        try:
            if question_type in ['multiple_choice', 'true_false']:
                # Try different selectors for multiple choice options
                selectors_to_try = [
                    f'input[value="{answer}"]',
                    f'label:has-text("{answer}")',
                    f'[data-option="{answer}"]',
                    f'.option-{answer.lower()}',
                    f'input[id*="{answer}"]'
                ]
                
                clicked = False
                for selector in selectors_to_try:
                    try:
                        await page.click(selector, timeout=2000)
                        clicked = True
                        print(f"✅ Clicked option {answer} using selector: {selector}")
                        break
                    except:
                        continue
                
                if not clicked:
                    print(f"⚠️ Could not find option {answer}, trying to click by text...")
                    # Fallback: try to find any element containing the answer
                    await page.click(f'text="{answer}"', timeout=2000)
            
            elif question_type in ['completion_open', 'completion_closed']:
                # Fill in text input
                input_selectors = [
                    'input[type="text"]',
                    'textarea',
                    '.text-input',
                    '[data-input="answer"]'
                ]
                
                filled = False
                for selector in input_selectors:
                    try:
                        await page.fill(selector, answer, timeout=2000)
                        filled = True
                        print(f"✅ Filled text input with: {answer}")
                        break
                    except:
                        continue
                
                if not filled:
                    print(f"⚠️ Could not find text input field")
            
            # Wait a moment before submitting
            await page.wait_for_timeout(1000)
            
            # Try to submit the answer
            submit_selectors = [
                'button:has-text("CORREGGI")',
                'button:has-text("AVANTI")',
                'button:has-text("SUBMIT")',
                '.submit-button',
                '[data-action="submit"]'
            ]
            
            submitted = False
            for selector in submit_selectors:
                try:
                    await page.click(selector, timeout=2000)
                    submitted = True
                    print(f"✅ Clicked submit button")
                    break
                except:
                    continue
            
            if not submitted:
                print(f"⚠️ Could not find submit button")
            
            # Wait for response
            await page.wait_for_timeout(2000)
            
        except Exception as e:
            print(f"❌ Error submitting answer: {e}")
            raise
    
    async def _capture_result(self) -> tuple[Optional[str], Optional[bool]]:
        """Capture the correct answer and whether our answer was correct."""
        page = self.automator.browser_manager.page
        
        print("Capturing result...")
        
        # Wait for feedback to appear
        await page.wait_for_timeout(3000)
        
        correct_answer = None
        is_correct = None
        
        try:
            # Look for correct answer indicators (adjust selectors based on actual UI)
            correct_selectors = [
                '.correct-answer',
                '.solution',
                '[data-correct-answer]',
                '.answer-feedback .correct'
            ]
            
            for selector in correct_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        correct_answer = await element.text_content()
                        correct_answer = correct_answer.strip()
                        print(f"Found correct answer: {correct_answer}")
                        break
                except:
                    continue
            
            # Check if our answer was correct
            success_selectors = [
                '.correct',
                '.success',
                '.right',
                '[data-result="correct"]',
                '.feedback.positive'
            ]
            
            error_selectors = [
                '.incorrect',
                '.error',
                '.wrong',
                '[data-result="incorrect"]',
                '.feedback.negative'
            ]
            
            for selector in success_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        is_correct = True
                        print("✅ Answer was correct!")
                        break
                except:
                    continue
            
            if is_correct is None:
                for selector in error_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            is_correct = False
                            print("❌ Answer was incorrect")
                            break
                    except:
                        continue
                        
        except Exception as e:
            print(f"⚠️ Error capturing result: {e}")
        
        return correct_answer, is_correct
    
    async def cleanup(self):
        """Clean up resources."""
        print("Cleaning up Zanichelli submitter...")
        if self.automator:
            await self.automator.cleanup()
        print("✅ Cleanup completed")


if __name__ == "__main__":
    # Simple test
    async def test_submitter():
        submitter = ZanichelliAnswerSubmitter()
        await submitter.initialize(headless=False)
        
        # This would need a real URL and exercise setup
        # result = await submitter.submit_answer(
        #     exercise_url="https://example.com",
        #     exercise_index=0,
        #     question_number=1,
        #     answer="A",
        #     question_type="multiple_choice"
        # )
        # print(f"Test result: {result}")
        
        await submitter.cleanup()
    
    # asyncio.run(test_submitter())
    print("Zanichelli submitter module loaded successfully")