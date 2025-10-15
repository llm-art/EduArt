"""
Question processing workflow for Zanichelli exercise automation.

This module handles the complete workflow for processing individual questions,
including content extraction, image downloading, and file saving.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
from playwright.async_api import Page

from ..content.extractor import ContentExtractor
from ..content.processor import ContentProcessor
from ..content.validator import ContentValidator
from ..files.manager import FileManager
from ..files.downloader import ContentDownloader
from ..browser.browser_manager import BrowserManager
from ..interactions.handler import QuestionInteractionHandler


class QuestionProcessorWorkflow:
    """Handles the complete workflow for processing questions."""
    
    def __init__(
        self, 
        page: Page, 
        file_manager: FileManager,
        browser_manager: BrowserManager
    ):
        self.page = page
        self.file_manager = file_manager
        self.browser_manager = browser_manager
        self.extractor = ContentExtractor(page)
        self.processor = ContentProcessor(page)
        self.validator = ContentValidator()
        self.interaction_handler = QuestionInteractionHandler(page)
    
    async def process_single_question(
        self,
        question_number: int,
        exercise_number: int,
        validate_content: bool = True,
        enable_interaction: bool = True
    ) -> Dict[str, Any]:
        """
        Process a single question completely.
        
        Args:
            question_number: Question number (1-based)
            exercise_number: Exercise number
            validate_content: Whether to validate extracted content
            
        Returns:
            Processing results dictionary
        """
        print(f"Processing question {question_number}...")
        
        results = {
            'question_number': question_number,
            'exercise_number': exercise_number,
            'success': False,
            'content': None,
            'validation': None,
            'files_created': [],
            'images_downloaded': [],
            'errors': []
        }
        
        try:
            # Ensure the page is fully loaded
            await self.page.wait_for_load_state('networkidle')
            await self.page.wait_for_timeout(1000)
            
            # Step 1: Extract initial question content (for type detection)
            print(f"Step 1: Extracting initial content for question {question_number}...")
            content = await self.extractor.extract_question_content(question_number)
            results['content'] = content
            
            # Step 2: Perform question interaction (NEW) - only if enabled
            if enable_interaction:
                print(f"Step 2: Performing question interaction for question {question_number}...")
                interaction_results = await self.interaction_handler.process_question_interaction(content)
                results['interaction_results'] = interaction_results
                
                # Add interaction errors to main results
                if interaction_results.get('errors'):
                    results['errors'].extend([f"Interaction: {error}" for error in interaction_results['errors']])
            else:
                print(f"Step 2: Skipping question interaction (disabled) for question {question_number}...")
                results['interaction_results'] = {
                    'success': True,
                    'question_type': 'interaction_disabled',
                    'interaction_performed': False,
                    'correggi_clicked': False,
                    'errors': []
                }
            
            # Step 3: Take screenshot (with or without interaction results)
            screenshot_description = "with results" if enable_interaction else "without interaction"
            print(f"Step 3: Taking screenshot {screenshot_description} for question {question_number}...")
            screenshot_path = await self._take_question_screenshot(question_number, exercise_number)
            if screenshot_path:
                results['files_created'].append(str(screenshot_path))
            
            # Step 4: Extract final content (with answers revealed)
            print(f"Step 4: Extracting final content with answers for question {question_number}...")
            final_content = await self.extractor.extract_question_content(question_number)
            results['final_content'] = final_content
            
            # Use final content for validation and saving
            content_to_use = final_content if final_content.get('html') else content
            
            # Step 5: Validate content if requested
            if validate_content:
                validation = self.validator.validate_question_content(content_to_use)
                results['validation'] = validation
                
                if not validation['is_valid']:
                    print(f"⚠️ Content validation failed for question {question_number}")
                    for issue in validation['issues']:
                        results['errors'].append(f"Validation: {issue}")
            
            # Step 6: Save HTML content (with answers)
            html_file = await self._save_question_content(content_to_use, question_number, exercise_number)
            if html_file:
                results['files_created'].append(str(html_file))
            
            # Step 7: Process and download images
            images_downloaded = await self._process_question_images(question_number, exercise_number)
            results['images_downloaded'] = images_downloaded
            
            # Add image file paths to files_created
            for img_info in images_downloaded:
                results['files_created'].append(str(img_info['path']))
            
            results['success'] = True
            print(f"✓ Successfully processed question {question_number} with interaction")
            
        except Exception as e:
            error_msg = f"Error processing question {question_number}: {e}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    async def process_all_questions_in_exercise(
        self,
        exercise_number: int,
        max_questions: Optional[int] = None,
        validate_content: bool = True,
        enable_interaction: bool = True
    ) -> Dict[str, Any]:
        """
        Process all questions in an exercise.
        
        Args:
            exercise_number: Exercise number
            max_questions: Maximum number of questions to process (None for all)
            validate_content: Whether to validate extracted content
            
        Returns:
            Processing results for all questions
        """
        print(f"Processing all questions in exercise {exercise_number}...")
        
        # Create directories for the exercise
        self.file_manager.create_exercise_directories(exercise_number)
        
        # Get total number of questions
        total_questions = await self.processor.get_total_questions()
        if max_questions:
            total_questions = min(total_questions, max_questions)
        
        print(f"Starting to process {total_questions} questions...")
        
        results = {
            'exercise_number': exercise_number,
            'total_questions': total_questions,
            'questions_processed': 0,
            'questions_successful': 0,
            'questions_failed': 0,
            'question_results': [],
            'summary': {},
            'errors': []
        }
        
        question_count = 0
        
        while question_count < total_questions:
            try:
                # Get current question number
                current_question = await self.processor.get_current_question_number()
                
                # Process the current question
                question_result = await self.process_single_question(
                    current_question,
                    exercise_number,
                    validate_content,
                    enable_interaction
                )
                
                results['question_results'].append(question_result)
                results['questions_processed'] += 1
                
                if question_result['success']:
                    results['questions_successful'] += 1
                else:
                    results['questions_failed'] += 1
                    results['errors'].extend(question_result['errors'])
                
                question_count += 1
                
                # Check if this is the last question
                if await self.processor.is_last_question():
                    print(f"Reached last question ({current_question}) - ensuring screenshot is captured")
                    
                    # CRITICAL FIX: Ensure the last question screenshot is properly taken
                    # The screenshot should already be taken in process_single_question, but let's verify
                    await self.page.wait_for_timeout(2000)  # Give time for any final rendering
                    
                    break
                else:
                    # Navigate to next question
                    from .navigation import NavigationWorkflow
                    nav_workflow = NavigationWorkflow(self.page)
                    
                    print(f"Moving to next question from {current_question}...")
                    success = await nav_workflow.navigate_to_next_question()
                    
                    if not success:
                        error_msg = f"Failed to navigate to next question after {current_question}"
                        print(f"❌ {error_msg}")
                        results['errors'].append(error_msg)
                        break
                    
                    await self.page.wait_for_timeout(1000)
                    
            except Exception as e:
                error_msg = f"Error in question processing loop: {e}"
                print(f"❌ {error_msg}")
                results['errors'].append(error_msg)
                
                # Try to continue with next question
                try:
                    if not await self.processor.is_last_question():
                        from .navigation import NavigationWorkflow
                        nav_workflow = NavigationWorkflow(self.page)
                        await nav_workflow.navigate_to_next_question()
                        continue
                    else:
                        break
                except:
                    break
        
        # Generate summary
        results['summary'] = self._generate_processing_summary(results)
        
        print(f"\n{'='*50}")
        print(f"EXERCISE {exercise_number} PROCESSING COMPLETED!")
        print(f"{'='*50}")
        print(f"Questions processed: {results['questions_processed']}")
        print(f"Successful: {results['questions_successful']}")
        print(f"Failed: {results['questions_failed']}")
        
        return results
    
    async def _take_question_screenshot(self, question_number: int, exercise_number: int) -> Optional[Path]:
        """Take a screenshot of the current question."""
        try:
            screenshot_path = self.file_manager.get_screenshot_path(question_number, exercise_number)
            return await self.browser_manager.take_screenshot(str(screenshot_path), full_page=True)
        except Exception as e:
            print(f"❌ Error taking screenshot for question {question_number}: {e}")
            return None
    
    async def _save_question_content(
        self, 
        content: Dict[str, Any], 
        question_number: int, 
        exercise_number: int
    ) -> Optional[Path]:
        """Save question content to HTML file."""
        try:
            if content.get('html'):
                return self.file_manager.save_html_content(
                    content['html'], 
                    question_number, 
                    exercise_number,
                    f"Question {question_number}"
                )
        except Exception as e:
            print(f"❌ Error saving content for question {question_number}: {e}")
            return None
    
    async def _process_question_images(self, question_number: int, exercise_number: int) -> List[Dict[str, Any]]:
        """Process and download images for the current question."""
        try:
            print(f"Processing images for question {question_number}...")
            
            # Detect images in the current question
            images = await self.extractor.detect_question_images()
            
            if not images:
                print(f"No images found in question {question_number}")
                return []
            
            # Get images directory
            dirs = self.file_manager.get_exercise_directories(exercise_number)
            imgs_dir = dirs['imgs']
            
            # Download images
            async with ContentDownloader() as downloader:
                # Filter content images
                filtered_images = downloader.filter_content_images(images)
                
                # Prepare image info for download
                image_info_list = []
                for img in filtered_images:
                    src = img.get('src', '')
                    if src:
                        # Normalize URL
                        normalized_src = downloader.normalize_image_url(src, self.page.url)
                        image_info_list.append({
                            'src': normalized_src,
                            'alt': img.get('alt', '')
                        })
                
                # Download images
                downloaded_images = await downloader.download_multiple_images(
                    image_info_list, 
                    question_number, 
                    imgs_dir
                )
                
                return downloaded_images
                
        except Exception as e:
            print(f"❌ Error processing images for question {question_number}: {e}")
            return []
    
    def _generate_processing_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of processing results."""
        summary = {
            'success_rate': 0.0,
            'total_files_created': 0,
            'total_images_downloaded': 0,
            'content_validation_stats': {
                'validated': 0,
                'valid': 0,
                'invalid': 0
            },
            'file_types': {
                'screenshots': 0,
                'html_files': 0,
                'images': 0
            }
        }
        
        if results['questions_processed'] > 0:
            summary['success_rate'] = results['questions_successful'] / results['questions_processed']
        
        # Analyze question results
        for question_result in results['question_results']:
            # Count files
            files_created = question_result.get('files_created', [])
            summary['total_files_created'] += len(files_created)
            
            # Count file types
            for file_path in files_created:
                if file_path.endswith('.png'):
                    summary['file_types']['screenshots'] += 1
                elif file_path.endswith('.html'):
                    summary['file_types']['html_files'] += 1
                else:
                    summary['file_types']['images'] += 1
            
            # Count images
            images_downloaded = question_result.get('images_downloaded', [])
            summary['total_images_downloaded'] += len(images_downloaded)
            
            # Validation stats
            validation = question_result.get('validation')
            if validation:
                summary['content_validation_stats']['validated'] += 1
                if validation.get('is_valid'):
                    summary['content_validation_stats']['valid'] += 1
                else:
                    summary['content_validation_stats']['invalid'] += 1
        
        return summary
    
    async def cleanup_after_processing(self) -> None:
        """Perform cleanup after processing is complete."""
        try:
            # Any cleanup operations can be added here
            print("Processing cleanup completed")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def get_processing_statistics(self, results: Dict[str, Any]) -> str:
        """
        Get formatted processing statistics.
        
        Args:
            results: Processing results dictionary
            
        Returns:
            Formatted statistics string
        """
        stats = []
        
        stats.append(f"Exercise {results['exercise_number']} Processing Statistics")
        stats.append("=" * 50)
        stats.append(f"Total Questions: {results['total_questions']}")
        stats.append(f"Questions Processed: {results['questions_processed']}")
        stats.append(f"Successful: {results['questions_successful']}")
        stats.append(f"Failed: {results['questions_failed']}")
        
        summary = results.get('summary', {})
        if summary:
            success_rate = summary.get('success_rate', 0.0)
            stats.append(f"Success Rate: {success_rate:.1%}")
            stats.append(f"Total Files Created: {summary.get('total_files_created', 0)}")
            stats.append(f"Total Images Downloaded: {summary.get('total_images_downloaded', 0)}")
            
            file_types = summary.get('file_types', {})
            stats.append(f"Screenshots: {file_types.get('screenshots', 0)}")
            stats.append(f"HTML Files: {file_types.get('html_files', 0)}")
            stats.append(f"Image Files: {file_types.get('images', 0)}")
        
        if results.get('errors'):
            stats.append(f"\nErrors ({len(results['errors'])}):")
            for error in results['errors'][:5]:  # Show first 5 errors
                stats.append(f"  - {error}")
            if len(results['errors']) > 5:
                stats.append(f"  ... and {len(results['errors']) - 5} more errors")
        
        return "\n".join(stats)