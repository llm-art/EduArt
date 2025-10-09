#!/usr/bin/env python3
"""
Zanichelli Question Answerer - Simple Multiple Choice Testing

This script systematically tests multiple choice questions by clicking the first option
and scraping the correct answers from the feedback interface. It reuses the complete
infrastructure from 1_question_downloader.py for maximum reliability.

Strategy:
1. Navigate to exercises using existing browser automation
2. Check question type from preprocessed JSON files  
3. Click first option (A) for multiple choice questions
4. Submit answer using "CORREGGI ESERCIZIO" button
5. Scrape correct answer from feedback interface
6. Store results in JSON files

Usage: python 3_question_answerer.py -e 1 -e 2 --min-question 1 --max-question 10

Requirements:
- playwright
- click
- All dependencies from 1_question_downloader.py
"""

import asyncio
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import click

# Import the existing automator infrastructure
from modules import ZanichelliExerciseAutomator


class QuestionAnswererSimple:
    """
    Simple question answerer that reuses ZanichelliExerciseAutomator infrastructure.
    
    Focuses on multiple choice questions only, using a systematic approach:
    - Click first option (A) for each question
    - Scrape correct answer from feedback
    - Store results for analysis
    """
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize with existing automator infrastructure."""
        # Reuse existing automator completely - same as 1_question_downloader.py
        self.automator = ZanichelliExerciseAutomator(config_path)
        self.is_initialized = False
        
        # Statistics tracking
        self.stats = {
            'questions_processed': 0,
            'questions_successful': 0,
            'questions_failed': 0,
            'questions_skipped': 0,
            'correct_answers': 0,
            'incorrect_answers': 0
        }
    
    async def initialize(self, headless: bool = False) -> bool:
        """Initialize exactly like 1_question_downloader.py"""
        
        print("Initializing browser and components...")
        if not await self.automator.initialize(headless=headless):
            print("❌ Failed to initialize automator")
            return False
        
        print("✅ Initialization successful")
        self.is_initialized = True
        return True
    
    async def process_exercise_answers(
        self,
        url: str,
        exercise_index: int,
        question_range: range
    ) -> Dict[str, Any]:
        """Process exercise answers using same flow as question downloader."""
        
        if not self.is_initialized:
            raise RuntimeError("Answerer not initialized. Call initialize() first.")
        
        print(f"\n📚 Starting Exercise {exercise_index + 1}")
        print(f"Questions to process: {min(question_range)}-{max(question_range)}")
        
        results = {
            'success': False,
            'exercise': exercise_index + 1,
            'results': [],
            'stats': {},
            'errors': []
        }
        
        try:
            # Exact same navigation as 1_question_downloader.py
            print("🌐 Navigating to exercise list...")
            await self.automator.navigate_to_exercise_list(url)
            
            print("🔐 Performing login...")
            await self.automator.perform_login()
            
            print(f"🚀 Starting exercise {exercise_index + 1}...")
            await self.automator.start_exercise(exercise_index)
            
            print("✅ Exercise started successfully")
            
            # Process each question
            question_results = []
            for question_num in question_range:
                print(f"\n❓ Processing Question {exercise_index + 1}/{question_num}")
                
                result = await self._process_single_question_answer(
                    exercise_index + 1, 
                    question_num
                )
                
                question_results.append(result)
                self._update_stats(result)
                
                # Navigate to next question if not the last one
                if question_num < max(question_range):
                    await self._navigate_to_next_question()
            
            results.update({
                'success': True,
                'results': question_results,
                'stats': self.stats.copy()
            })
            
            # Print exercise summary
            self._print_exercise_summary(exercise_index + 1)
            
        except Exception as e:
            error_msg = f"Error processing exercise {exercise_index + 1}: {e}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    async def _process_single_question_answer(
        self, 
        exercise: int, 
        question: int
    ) -> Dict[str, Any]:
        """Process a single question by clicking first option and scraping result."""
        
        result = {
            'exercise': exercise,
            'question': question,
            'success': False,
            'question_type': None,
            'submitted_answer': None,
            'correct_answer': None,
            'all_correct_answers': [],
            'is_correct': None,
            'feedback_text': None,
            'error': None,
            'processing_time': 0
        }
        
        start_time = time.time()
        
        try:
            # 1. Load question data from JSON to check type
            question_data = await self._load_question_json(exercise, question)
            question_type = question_data.get('type', 'unknown')
            
            result['question_type'] = question_type
            
            # 2. Only process multiple_choice questions
            if not question_type.startswith('multiple_choice'):
                result['error'] = f'Skipping non-multiple-choice question type: {question_type}'
                print(f"⏭️  Skipping {question_type} question")
                return result
            
            print(f"🎯 Processing {question_type} question")
            
            # 3. Click first option (A) - type-specific strategy
            submitted_answer = await self._click_first_option_by_type(question_data)
            result['submitted_answer'] = submitted_answer
            
            # 4. Click CORREGGI ESERCIZIO button
            if not await self._click_correggi_button():
                result['error'] = 'Failed to click CORREGGI button'
                return result
            
            # 5. Scrape the result based on question type
            feedback = await self._scrape_feedback_by_type(question_type)
            result.update(feedback)
            
            # 6. Update JSON file with results
            await self._update_question_json(exercise, question, result)
            
            result['success'] = True
            result['processing_time'] = time.time() - start_time
            
            # Format output
            output = self._format_result_output(result)
            print(f"   {output}")
            
        except Exception as e:
            result['error'] = str(e)
            result['processing_time'] = time.time() - start_time
            print(f"   ❌ Failed: {e}")
        
        return result
    
    async def _load_question_json(self, exercise: int, question: int) -> Dict[str, Any]:
        """Load question data from existing JSON file."""
        json_path = Path(f"questions/output/{exercise}/json/{question}.json")
        
        if not json_path.exists():
            raise FileNotFoundError(f"Question JSON not found: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def _click_first_option_by_type(self, question_data: Dict[str, Any]) -> str:
        """Click first option based on question type with correct selectors."""
        
        question_type = question_data.get('type')
        choices = question_data.get('choices', [])
        
        if not choices:
            raise ValueError("No choices found in question data")
        
        first_choice = choices[0]
        choice_id = first_choice.get('id', 'A')
        choice_text = first_choice.get('text', '')
        
        page = self.automator.browser_manager.page
        
        if question_type == 'multiple_choice_radio':
            # Radio button selectors (circular buttons, single selection)
            selectors = [f'input[type="radio"]']
            
        elif question_type == 'multiple_choice_check':
            # Checkbox selectors (square boxes, multiple selection)
            selectors = [
                f'input[type="checkbox"][value="{choice_id}"]',   # Direct checkbox input
                f'input[type="checkbox"]:first-of-type',          # First checkbox
                f'label:has-text("{choice_text}") input[type="checkbox"]',  # Checkbox in label
                f'[data-choice="{choice_id}"] input[type="checkbox"]',      # Checkbox with data attr
                f'.option-{choice_id.lower()} input[type="checkbox"]',      # Checkbox with class
                f'#{choice_id}_checkbox',                         # ID-based selector
                f'[id*="{choice_id}"] input[type="checkbox"]'     # Partial ID match
            ]
            
        else:
            raise ValueError(f"Unsupported question type: {question_type}")
        
        # Try each selector
        for i, selector in enumerate(selectors, 1):
            try:
                await page.click(selector, timeout=3000)
                print(f"   ✅ Clicked {question_type} option {choice_id} (strategy {i})")
                return f"{choice_id}: {choice_text}"
            except Exception as e:
                if i < len(selectors):
                    continue
                else:
                    # Last attempt failed
                    print(f"   ⚠️ All selectors failed for {choice_id}")
        
        raise Exception(f"Could not click first option {choice_id} for {question_type}")
    
    async def _click_correggi_button(self) -> bool:
        """Click CORREGGI ESERCIZIO button."""
        
        page = self.automator.browser_manager.page
        selectors = [
            'button:has-text("CORREGGI ESERCIZIO")',
            'button:has-text("CORREGGI")',
            '.submit-button',
            '.check-button',
            '[data-action="submit"]',
            '[data-action="check"]',
            'button[type="submit"]',
            '.btn-submit'
        ]
        
        for i, selector in enumerate(selectors, 1):
            try:
                await page.click(selector, timeout=3000)
                await page.wait_for_timeout(2000)  # Wait for feedback to load
                print(f"   ✅ Clicked CORREGGI button (strategy {i})")
                return True
            except Exception as e:
                if i < len(selectors):
                    continue
                else:
                    print(f"   ❌ Could not click CORREGGI button: {e}")
        
        return False
    
    async def _scrape_feedback_by_type(self, question_type: str) -> Dict[str, Any]:
        """Scrape feedback based on question type and interface structure."""
        
        page = self.automator.browser_manager.page
        feedback = {
            'correct_answer': None,
            'is_correct': None,
            'feedback_text': None,
            'all_correct_answers': []  # For multiple_choice_check
        }
        
        try:
            # Wait for feedback to appear
            await page.wait_for_timeout(3000)
            
            if question_type == 'multiple_choice_radio':
                # Single correct answer (from Image 2)
                await self._scrape_radio_feedback(feedback)
                
            elif question_type == 'multiple_choice_check':
                # Multiple correct answers (from Image 1)
                await self._scrape_checkbox_feedback(feedback)
            
            print(f"   📊 Result: {feedback['feedback_text'] or 'Unknown'}")
            
        except Exception as e:
            print(f"   ⚠️ Error scraping {question_type} feedback: {e}")
        
        return feedback
    
    async def _scrape_radio_feedback(self, feedback: Dict) -> None:
        """Scrape feedback for radio button questions (single answer)."""
        
        page = self.automator.browser_manager.page
        
        # Check for success/error indicators first
        try:
            if await page.query_selector('text="Risposta esatta"'):
                feedback['is_correct'] = True
                feedback['feedback_text'] = "Risposta esatta"
            elif await page.query_selector('text="Risposta sbagliata"'):
                feedback['is_correct'] = False
                feedback['feedback_text'] = "Risposta sbagliata"
            elif await page.query_selector('text="Risposta corretta"'):
                feedback['is_correct'] = True
                feedback['feedback_text'] = "Risposta corretta"
            elif await page.query_selector('text="Risposta errata"'):
                feedback['is_correct'] = False
                feedback['feedback_text'] = "Risposta errata"
        except:
            pass
        
        # Look for the correct answer (green highlighted or marked)
        correct_selectors = [
            '.choiceChip',                    
        ]
        
        # Extract the correct answer text
        for selector in correct_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    if text and text.strip():
                        feedback['correct_answer'] = text.strip()
                        break
            except:
                continue
    
    async def _scrape_checkbox_feedback(self, feedback: Dict) -> None:
        """Scrape feedback for checkbox questions (multiple answers)."""
        
        page = self.automator.browser_manager.page
        
        # Check for success/error indicators
        try:
            if await page.query_selector('text="Risposta sbagliata"'):
                feedback['is_correct'] = False
                feedback['feedback_text'] = "Risposta sbagliata"
            elif await page.query_selector('text="Risposta corretta"'):
                feedback['is_correct'] = True
                feedback['feedback_text'] = "Risposta corretta"
            elif await page.query_selector('text="Risposta esatta"'):
                feedback['is_correct'] = True
                feedback['feedback_text'] = "Risposta esatta"
            elif await page.query_selector('text="Risposta non data"'):
                feedback['is_correct'] = False
                feedback['feedback_text'] = "Risposta non data"
        except:
            pass
        
        # Extract all correct answers (those that should have been selected)
        correct_indicators = [
            '.correct-option',
            '[data-correct="true"]',
            '.should-be-selected',
            '.answer-key',
            '.correct-choice',
            '[style*="color: green"]'
        ]
        
        all_correct = []
        for selector in correct_indicators:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.text_content()
                    if text and text.strip():
                        all_correct.append(text.strip())
            except:
                continue
        
        feedback['all_correct_answers'] = all_correct
        if all_correct:
            feedback['correct_answer'] = '; '.join(all_correct)
    
    async def _navigate_to_next_question(self) -> bool:
        """Navigate to next question using existing navigation patterns."""
        
        page = self.automator.browser_manager.page
        next_selectors = [
            'button:has-text("AVANTI")',
            'button:has-text("NEXT")',
            '.next-question',
            '[data-action="next"]',
            'button[aria-label*="next"]',
            '.btn-next',
            '.question-nav-next'
        ]
        
        for selector in next_selectors:
            try:
                await page.click(selector, timeout=3000)
                await page.wait_for_timeout(2000)  # Wait for navigation
                return True
            except:
                continue
        
        print("   ⚠️ Could not find next question button")
        return False
    
    async def _update_question_json(
        self, 
        exercise: int, 
        question: int, 
        result: Dict[str, Any]
    ) -> bool:
        """Update JSON with type-specific results."""
        
        json_path = Path(f"questions/output/{exercise}/json/{question}.json")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'test_results' not in data:
                data['test_results'] = []
            
            # Create result record based on question type
            test_record = {
                'timestamp': datetime.now().isoformat(),
                'question_type': result['question_type'],
                'submitted_answer': result['submitted_answer'],
                'is_correct': result['is_correct'],
                'test_method': 'systematic_first_option',
                'feedback_text': result.get('feedback_text'),
                'processing_time': result.get('processing_time', 0)
            }
            
            # Add type-specific data
            if result['question_type'] == 'multiple_choice_radio':
                test_record['correct_answer'] = result.get('correct_answer')
                
            elif result['question_type'] == 'multiple_choice_check':
                test_record['correct_answer'] = result.get('correct_answer')
                test_record['all_correct_answers'] = result.get('all_correct_answers', [])
            
            data['test_results'].append(test_record)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"   ⚠️ Error updating JSON: {e}")
            return False
    
    def _format_result_output(self, result: Dict[str, Any]) -> str:
        """Format result output based on question type."""
        
        question_type = result.get('question_type', 'unknown')
        submitted = result.get('submitted_answer', 'N/A')
        correct = result.get('correct_answer', 'N/A')
        is_correct = result.get('is_correct')
        
        status = '✓' if is_correct else '✗' if is_correct is False else '?'
        
        if question_type == 'multiple_choice_radio':
            return f"{status} Radio: {submitted} → Correct: {correct}"
        elif question_type == 'multiple_choice_check':
            all_correct = result.get('all_correct_answers', [])
            if all_correct:
                return f"{status} Check: {submitted} → All correct: {', '.join(all_correct)}"
            else:
                return f"{status} Check: {submitted} → Correct: {correct}"
        else:
            return f"{status} {question_type}: {submitted} → {correct}"
    
    def _update_stats(self, result: Dict[str, Any]) -> None:
        """Update processing statistics."""
        
        self.stats['questions_processed'] += 1
        
        if result['success']:
            self.stats['questions_successful'] += 1
            
            if result['is_correct'] is True:
                self.stats['correct_answers'] += 1
            elif result['is_correct'] is False:
                self.stats['incorrect_answers'] += 1
        else:
            if result.get('error', '').startswith('Skipping'):
                self.stats['questions_skipped'] += 1
            else:
                self.stats['questions_failed'] += 1
    
    def _print_exercise_summary(self, exercise: int) -> None:
        """Print summary for completed exercise."""
        
        print(f"\n📊 Exercise {exercise} Summary:")
        print(f"   Questions processed: {self.stats['questions_processed']}")
        print(f"   Successful: {self.stats['questions_successful']}")
        print(f"   Failed: {self.stats['questions_failed']}")
        print(f"   Skipped: {self.stats['questions_skipped']}")
        print(f"   Correct answers: {self.stats['correct_answers']}")
        print(f"   Incorrect answers: {self.stats['incorrect_answers']}")
        
        if self.stats['questions_processed'] > 0:
            success_rate = (self.stats['questions_successful'] / self.stats['questions_processed']) * 100
            print(f"   Success rate: {success_rate:.1f}%")
        
        if self.stats['correct_answers'] + self.stats['incorrect_answers'] > 0:
            accuracy = (self.stats['correct_answers'] / (self.stats['correct_answers'] + self.stats['incorrect_answers'])) * 100
            print(f"   Answer accuracy: {accuracy:.1f}%")
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.automator:
            await self.automator.cleanup()


@click.command()
@click.option('--exercises', '-e', multiple=True, type=int, 
              help='Exercise numbers to process. Use multiple times for multiple exercises.')
@click.option('--min-question', default=1, type=int,
              help='Minimum question number to process')
@click.option('--max-question', default=20, type=int,
              help='Maximum question number to process')
@click.option('--url', '-u', 
              default="https://esercizi.zanichelli.it/argomento/Pittura-rinascimentale/x2rnbu-x2rnih-hv05y-2n_5c",
              help='Exercise list URL')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--config', '-c', default='config.json', help='Configuration file path')
def main(exercises, min_question, max_question, url, headless, config):
    """
    Zanichelli Question Answerer - Simple multiple choice testing.
    
    This tool systematically tests multiple choice questions by clicking the first option
    and scraping the correct answers from the feedback interface.
    
    Examples:
        python 3_question_answerer.py -e 1 --min-question 1 --max-question 10
        python 3_question_answerer.py -e 2 -e 3
        python 3_question_answerer.py -e 1 --headless
    """
    
    if not exercises:
        click.echo(click.style("❌ No exercises specified. Use -e option.", fg='red'))
        sys.exit(1)
    
    click.echo(click.style("🤖 Zanichelli Question Answerer - Simple Mode", fg='cyan', bold=True))
    click.echo("=" * 70)
    click.echo(f"Exercises: {', '.join(map(str, exercises))}")
    click.echo(f"Question range: {min_question}-{max_question}")
    click.echo(f"Strategy: Click first option (A) and scrape results")
    click.echo(f"Target: Multiple choice questions only")
    click.echo(f"Headless mode: {headless}")
    click.echo("=" * 70)
    
    async def run_answerer():
        """Run the simple answerer - same pattern as 1_question_downloader.py"""
        
        # Use existing automator as context manager
        answerer = QuestionAnswererSimple(config)
        
        try:
            # Initialize exactly like question downloader
            if not await answerer.initialize(headless=headless):
                return False
            
            overall_stats = {
                'exercises_processed': 0,
                'exercises_successful': 0,
                'total_questions': 0,
                'total_successful': 0,
                'total_correct': 0
            }
            
            # Process each exercise
            for exercise in exercises:
                exercise_index = exercise - 1  # Convert to 0-based
                question_range = range(min_question, max_question + 1)
                
                print(f"\n{'='*70}")
                print(f"📚 Processing Exercise {exercise}")
                print(f"Questions: {min_question}-{max_question}")
                print(f"{'='*70}")
                
                result = await answerer.process_exercise_answers(
                    url=url,
                    exercise_index=exercise_index,
                    question_range=question_range
                )
                
                overall_stats['exercises_processed'] += 1
                
                if result['success']:
                    overall_stats['exercises_successful'] += 1
                    stats = result.get('stats', {})
                    overall_stats['total_questions'] += stats.get('questions_processed', 0)
                    overall_stats['total_successful'] += stats.get('questions_successful', 0)
                    overall_stats['total_correct'] += stats.get('correct_answers', 0)
                    
                    print(f"✅ Exercise {exercise} completed successfully")
                else:
                    print(f"❌ Exercise {exercise} failed")
                    for error in result.get('errors', []):
                        print(f"   Error: {error}")
            
            # Print overall summary
            print(f"\n{'='*70}")
            print(f"🎯 OVERALL SUMMARY")
            print(f"{'='*70}")
            print(f"Exercises processed: {overall_stats['exercises_processed']}")
            print(f"Exercises successful: {overall_stats['exercises_successful']}")
            print(f"Total questions processed: {overall_stats['total_questions']}")
            print(f"Total questions successful: {overall_stats['total_successful']}")
            print(f"Total correct answers: {overall_stats['total_correct']}")
            
            if overall_stats['total_questions'] > 0:
                success_rate = (overall_stats['total_successful'] / overall_stats['total_questions']) * 100
                print(f"Overall success rate: {success_rate:.1f}%")
            
            if overall_stats['total_successful'] > 0:
                accuracy = (overall_stats['total_correct'] / overall_stats['total_successful']) * 100
                print(f"Overall accuracy: {accuracy:.1f}%")
            
            print(f"{'='*70}")
            
            return True
            
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            return False
        
        finally:
            # Always cleanup
            await answerer.cleanup()
    
    success = asyncio.run(run_answerer())
    
    if success:
        click.echo(click.style("\n🎉 Processing completed!", fg='green', bold=True))
        click.echo("\nResults stored in questions/output/{exercise}/json/{question}.json")
        click.echo("Each JSON file now contains a 'test_results' section with discovered answers.")
    else:
        click.echo(click.style("\n❌ Processing failed", fg='red'))
        sys.exit(1)


if __name__ == "__main__":
    main()