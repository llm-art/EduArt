"""
Refactored Zanichelli Exercise Automator using modular composition.

This is the main orchestrator class that combines all the modular components
to provide a clean, maintainable interface for exercise automation.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from .browser.browser_manager import BrowserManager
from .config.manager import ConfigManager
from .files.manager import FileManager
from .workflows.login import LoginWorkflow
from .workflows.navigation import NavigationWorkflow
from .workflows.question_processor import QuestionProcessorWorkflow
from .content.extractor import ContentExtractor


class ZanichelliExerciseAutomator:
    """
    Refactored main automator class using modular composition.
    
    This class orchestrates all the individual modules to provide
    a clean interface for exercise automation tasks.
    """
    
    def __init__(self, config_path: str = "config.json", base_dir: Optional[Path] = None):
        """
        Initialize the automator with all required components.
        
        Args:
            config_path: Path to configuration file
            base_dir: Base directory for file operations
        """
        # Initialize core managers
        self.config_manager = ConfigManager(config_path)
        self.file_manager = FileManager(base_dir)
        self.browser_manager = BrowserManager()
        
        # Workflow components (initialized after browser setup)
        self.login_workflow: Optional[LoginWorkflow] = None
        self.navigation_workflow: Optional[NavigationWorkflow] = None
        self.question_processor: Optional[QuestionProcessorWorkflow] = None
        self.content_extractor: Optional[ContentExtractor] = None
        
        # State tracking
        self.is_initialized = False
        self.current_exercise = None
        self.current_question = None
    
    async def initialize(self, headless: bool = None) -> bool:
        """
        Initialize the automator and set up browser.
        
        Args:
            headless: Override headless mode setting
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print("Initializing Zanichelli Exercise Automator...")
            
            # Load configuration
            if not self.config_manager.load_config():
                return False
            
            # Get browser configuration
            browser_config = self.config_manager.get_browser_config()
            
            # Override headless setting if provided
            if headless is not None:
                browser_config['headless'] = headless
            
            # Setup browser
            page = await self.browser_manager.setup_browser(**browser_config)
            
            # Initialize workflow components
            self.login_workflow = LoginWorkflow(page, self.config_manager)
            self.navigation_workflow = NavigationWorkflow(page)
            self.question_processor = QuestionProcessorWorkflow(
                page, 
                self.file_manager, 
                self.browser_manager
            )
            self.content_extractor = ContentExtractor(page)
            
            self.is_initialized = True
            print("✅ Automator initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize automator: {e}")
            return False
    
    async def navigate_to_exercise_list(self, url: str) -> bool:
        """
        Navigate to the exercise list page.
        
        Args:
            url: URL of the exercise list page
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Automator not initialized. Call initialize() first.")
        
        try:
            await self.browser_manager.navigate_to_url(url)
            return True
        except Exception as e:
            print(f"❌ Failed to navigate to exercise list: {e}")
            return False
    
    async def perform_login(self) -> bool:
        """
        Perform the complete login process.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Automator not initialized. Call initialize() first.")
        
        return await self.login_workflow.perform_complete_login()
    
    async def start_exercise(self, exercise_index: int = 0) -> bool:
        """
        Start a specific exercise by clicking through the UI flow.
        
        Args:
            exercise_index: Index of the exercise to start (0-based)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            raise RuntimeError("Automator not initialized. Call initialize() first.")
        
        try:
            print(f"Starting exercise {exercise_index + 1}...")
            
            # Click ANTEPRIMA button for specified exercise
            if not await self.navigation_workflow.click_anteprima_button(exercise_index):
                return False
            
            # Click SVOLGI button in modal
            if not await self.navigation_workflow.click_svolgi_button():
                return False
            
            # Click INIZIA button on instruction page
            if not await self.navigation_workflow.click_inizia_button():
                return False
            
            # Get exercise info and store current state
            exercise_info = await self.content_extractor.get_exercise_info(exercise_index)
            self.current_exercise = exercise_info
            
            print(f"✅ Successfully started exercise: {exercise_info['title']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start exercise: {e}")
            return False
    
    async def process_single_exercise(
        self, 
        url: str, 
        exercise_index: int = 0, 
        login_required: bool = True
    ) -> Dict[str, Any]:
        """
        Process a single exercise by taking a screenshot after starting it.
        
        Args:
            url: Exercise list URL
            exercise_index: Index of the exercise (0-based)
            login_required: Whether login is required
            
        Returns:
            Processing results dictionary
        """
        results = {
            'success': False,
            'exercise_index': exercise_index,
            'exercise_info': None,
            'screenshot_path': None,
            'errors': []
        }
        
        try:
            # Navigate to exercise list
            if not await self.navigate_to_exercise_list(url):
                results['errors'].append('Failed to navigate to exercise list')
                return results
            
            # Login if required
            if login_required:
                if not await self.perform_login():
                    results['errors'].append('Login failed')
                    return results
                
                # Navigate back to exercise page if needed
                current_url = await self.browser_manager.get_current_url()
                if url not in current_url:
                    print("Navigating back to exercise page after login...")
                    await self.navigate_to_exercise_list(url)
            
            # Start the exercise
            if not await self.start_exercise(exercise_index):
                results['errors'].append('Failed to start exercise')
                return results
            
            # Get exercise title for screenshot naming
            exercise_title = await self.navigation_workflow.get_exercise_title(exercise_index)
            
            # Take screenshot
            screenshot_name = f"{exercise_title}.png"
            screenshot_path = self.file_manager.get_base_dir() / screenshot_name
            
            await self.browser_manager.take_screenshot(str(screenshot_path))
            
            results.update({
                'success': True,
                'exercise_info': self.current_exercise,
                'screenshot_path': str(screenshot_path)
            })
            
            print(f"✅ Successfully processed single exercise: {exercise_title}")
            
        except Exception as e:
            error_msg = f"Error processing single exercise: {e}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    async def process_all_questions(
        self, 
        url: str, 
        exercise_index: int = 0, 
        login_required: bool = True,
        validate_content: bool = True
    ) -> Dict[str, Any]:
        """
        Process all questions in a single exercise.
        
        Args:
            url: Exercise list URL
            exercise_index: Index of the exercise (0-based)
            login_required: Whether login is required
            validate_content: Whether to validate extracted content
            
        Returns:
            Processing results dictionary
        """
        results = {
            'success': False,
            'exercise_index': exercise_index,
            'exercise_info': None,
            'question_results': None,
            'errors': []
        }
        
        try:
            # Navigate to exercise list
            if not await self.navigate_to_exercise_list(url):
                results['errors'].append('Failed to navigate to exercise list')
                return results
            
            # Login if required
            if login_required:
                if not await self.perform_login():
                    results['errors'].append('Login failed')
                    return results
                
                # Navigate back to exercise page if needed
                current_url = await self.browser_manager.get_current_url()
                if url not in current_url:
                    print("Navigating back to exercise page after login...")
                    await self.navigate_to_exercise_list(url)
            
            # Start the exercise
            if not await self.start_exercise(exercise_index):
                results['errors'].append('Failed to start exercise')
                return results
            
            # Process all questions in the exercise
            exercise_number = self.current_exercise['number']
            question_results = await self.question_processor.process_all_questions_in_exercise(
                exercise_number, 
                validate_content=validate_content
            )
            
            # Handle completion (click TERMINA PROVA if needed)
            try:
                await self.navigation_workflow.click_termina_prova_button()
            except Exception as e:
                print(f"Warning: Could not click TERMINA PROVA button: {e}")
            
            results.update({
                'success': True,
                'exercise_info': self.current_exercise,
                'question_results': question_results
            })
            
            print(f"✅ Successfully processed all questions in exercise {exercise_number}")
            
        except Exception as e:
            error_msg = f"Error processing all questions: {e}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    async def process_multiple_exercises(
        self, 
        url: str, 
        exercise_indices: list = None,
        login_required: bool = True
    ) -> Dict[str, Any]:
        """
        Process multiple exercises.
        
        Args:
            url: Exercise list URL
            exercise_indices: List of exercise indices to process (None for all)
            login_required: Whether login is required
            
        Returns:
            Processing results dictionary
        """
        results = {
            'success': False,
            'exercises_processed': 0,
            'exercises_successful': 0,
            'exercises_failed': 0,
            'exercise_results': [],
            'errors': []
        }
        
        try:
            # Navigate to exercise list
            if not await self.navigate_to_exercise_list(url):
                results['errors'].append('Failed to navigate to exercise list')
                return results
            
            # Login if required
            if login_required:
                if not await self.perform_login():
                    results['errors'].append('Login failed')
                    return results
            
            # Get all exercise cards if no specific indices provided
            if exercise_indices is None:
                cards = await self.navigation_workflow.get_exercise_cards()
                exercise_indices = list(range(len(cards)))
            
            print(f"Processing {len(exercise_indices)} exercises...")
            
            for i, exercise_index in enumerate(exercise_indices):
                print(f"\n--- Processing exercise {exercise_index + 1} ({i + 1}/{len(exercise_indices)}) ---")
                
                try:
                    # Process single exercise
                    exercise_result = await self.process_single_exercise(
                        url, exercise_index, login_required=False  # Already logged in
                    )
                    
                    results['exercise_results'].append(exercise_result)
                    results['exercises_processed'] += 1
                    
                    if exercise_result['success']:
                        results['exercises_successful'] += 1
                        print(f"✅ Completed exercise {exercise_index + 1}")
                    else:
                        results['exercises_failed'] += 1
                        results['errors'].extend(exercise_result['errors'])
                        print(f"❌ Failed exercise {exercise_index + 1}")
                    
                    # Navigate back to exercise list for next exercise
                    if i < len(exercise_indices) - 1:  # Not the last exercise
                        await self.navigation_workflow.navigate_back_to_exercise_list(url)
                        await self.navigation_workflow.wait_for_page_load()
                    
                except Exception as e:
                    error_msg = f"Error processing exercise {exercise_index + 1}: {e}"
                    print(f"❌ {error_msg}")
                    results['errors'].append(error_msg)
                    results['exercises_failed'] += 1
                    
                    # Try to navigate back to main page
                    try:
                        await self.navigate_to_exercise_list(url)
                    except:
                        pass
            
            results['success'] = results['exercises_successful'] > 0
            
            print(f"\n{'='*50}")
            print(f"MULTIPLE EXERCISES PROCESSING COMPLETED!")
            print(f"Processed: {results['exercises_processed']}")
            print(f"Successful: {results['exercises_successful']}")
            print(f"Failed: {results['exercises_failed']}")
            print(f"{'='*50}")
            
        except Exception as e:
            error_msg = f"Error in multiple exercises processing: {e}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        return results
    
    async def cleanup(self) -> None:
        """Clean up resources and close browser."""
        try:
            if self.question_processor:
                await self.question_processor.cleanup_after_processing()
            
            if self.browser_manager:
                await self.browser_manager.cleanup()
            
            print("✅ Cleanup completed")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")
        finally:
            self.is_initialized = False
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state of the automator."""
        return {
            'is_initialized': self.is_initialized,
            'current_exercise': self.current_exercise,
            'current_question': self.current_question,
            'config_loaded': self.config_manager.is_loaded(),
            'browser_ready': self.browser_manager.is_initialized()
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()