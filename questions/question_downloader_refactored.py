#!/usr/bin/env python3
"""
Zanichelli Exercise Automation Script - Refactored Version

This script automates the process of accessing and starting exercises on the Zanichelli platform.
It uses a modular architecture for better maintainability and extensibility.

Usage: python question_downloader_refactored.py

Requirements:
- playwright
- Install with: pip install playwright && playwright install
"""

import asyncio
import sys
import click
from pathlib import Path

# Import the refactored modular automator
from modules import ZanichelliExerciseAutomator


@click.command()
@click.option('--exercise', '-e', default=1, type=int, help='Exercise number to process (1-57)', show_default=True)
@click.option('--url', '-u', default="https://esercizi.zanichelli.it/argomento/Pittura-rinascimentale/x2rnbu-x2rnih-hv05y-2n_5c", help='Exercise list URL', show_default=True)
@click.option('--no-login', is_flag=True, help='Skip login process')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--single-exercise', is_flag=True, help='Process single exercise (screenshot only)')
@click.option('--validate-content', is_flag=True, default=True, help='Validate extracted content quality')
@click.option('--config', '-c', default='config.json', help='Configuration file path', show_default=True)
def main(exercise, url, no_login, headless, single_exercise, validate_content, config):
    """Zanichelli Exercise Automation - Refactored Modular Version."""
    
    # Convert 1-based exercise number to 0-based index
    exercise_index = exercise - 1
    
    # Validate exercise number
    if exercise < 1 or exercise > 57:
        click.echo(click.style(f"❌ Error: Exercise number must be between 1 and 57, got {exercise}", fg='red'))
        sys.exit(1)
    
    # Display startup information
    click.echo(click.style("Zanichelli Exercise Automation - Refactored Version", fg='cyan', bold=True))
    click.echo("=" * 60)
    
    if single_exercise:
        click.echo(f"Processing single exercise {exercise} (screenshot only)")
    else:
        click.echo(f"Processing all questions in exercise {exercise}")
    
    click.echo(f"Exercise index: {exercise_index} (0-based)")
    click.echo(f"Login required: {not no_login}")
    click.echo(f"Headless mode: {headless}")
    click.echo(f"Content validation: {validate_content}")
    click.echo(f"Configuration file: {config}")
    
    if not single_exercise:
        click.echo("Screenshots and images will be saved in data/{exercise_number}/ directories")
    
    click.echo("=" * 60)
    
    async def run_automation():
        """Run the automation process."""
        # Initialize the automator with configuration
        async with ZanichelliExerciseAutomator(config_path=config) as automator:
            try:
                # Initialize browser and components
                if not await automator.initialize(headless=headless):
                    click.echo(click.style("❌ Failed to initialize automator", fg='red'))
                    return False
                
                if single_exercise:
                    # Process single exercise (screenshot only)
                    results = await automator.process_single_exercise(
                        url=url,
                        exercise_index=exercise_index,
                        login_required=not no_login
                    )
                    
                    if results['success']:
                        click.echo(click.style(f"\n🎉 Single exercise processing completed!", fg='green', bold=True))
                        click.echo(f"Exercise: {results['exercise_info']['title']}")
                        click.echo(f"Screenshot: {results['screenshot_path']}")
                    else:
                        click.echo(click.style(f"\n❌ Single exercise processing failed", fg='red'))
                        for error in results['errors']:
                            click.echo(f"  - {error}")
                        return False
                
                else:
                    # Process all questions in exercise
                    results = await automator.process_all_questions(
                        url=url,
                        exercise_index=exercise_index,
                        login_required=not no_login,
                        validate_content=validate_content
                    )
                    
                    if results['success']:
                        click.echo(click.style(f"\n🎉 All questions processing completed!", fg='green', bold=True))
                        
                        # Display detailed statistics
                        question_results = results['question_results']
                        if question_results:
                            stats = automator.question_processor.get_processing_statistics(question_results)
                            click.echo(f"\n{stats}")
                            
                            # Display file locations
                            exercise_number = results['exercise_info']['number']
                            base_dir = automator.file_manager.get_base_dir()
                            click.echo(f"\nFiles saved in:")
                            click.echo(f"- Screenshots: {base_dir}/data/{exercise_number}/raw/")
                            click.echo(f"- Images: {base_dir}/data/{exercise_number}/imgs/")
                            click.echo(f"- HTML content: {base_dir}/data/{exercise_number}/raw/")
                    else:
                        click.echo(click.style(f"\n❌ Questions processing failed", fg='red'))
                        for error in results['errors']:
                            click.echo(f"  - {error}")
                        return False
                
                return True
                
            except Exception as e:
                click.echo(click.style(f"❌ Fatal error: {e}", fg='red'))
                return False
    
    # Run the automation
    try:
        success = asyncio.run(run_automation())
        
        if success:
            click.echo(click.style("\n✅ Automation completed successfully!", fg='green', bold=True))
            click.echo("\nUsage examples:")
            click.echo("• Process exercise 2: python question_downloader_refactored.py --exercise 2")
            click.echo("• Process exercise 3: python question_downloader_refactored.py -e 3")
            click.echo("• Single exercise mode: python question_downloader_refactored.py -e 1 --single-exercise")
            click.echo("• Headless mode: python question_downloader_refactored.py -e 1 --headless")
            click.echo("• Without login: python question_downloader_refactored.py -e 1 --no-login")
            click.echo("• Custom config: python question_downloader_refactored.py -e 1 -c my_config.json")
        else:
            click.echo(click.style("\n❌ Automation failed. Check the error messages above.", fg='red'))
            click.echo("\nTroubleshooting:")
            click.echo("1. Make sure config.json exists with your credentials")
            click.echo("2. Copy config.json.template to config.json and fill in your details")
            click.echo("3. Check your internet connection")
            click.echo("4. Verify the exercise page loads correctly")
            click.echo("5. Try running with --headless flag if you encounter display issues")
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo(click.style("\nAutomation interrupted by user", fg='yellow'))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Fatal error: {e}", fg='red'))
        sys.exit(1)


@click.command()
@click.option('--url', '-u', default="https://esercizi.zanichelli.it/argomento/Pittura-rinascimentale/x2rnbu-x2rnih-hv05y-2n_5c", help='Exercise list URL', show_default=True)
@click.option('--exercises', '-e', help='Comma-separated list of exercise numbers (e.g., "1,3,5") or "all" for all exercises')
@click.option('--no-login', is_flag=True, help='Skip login process')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--config', '-c', default='config.json', help='Configuration file path', show_default=True)
def batch_process(url, exercises, no_login, headless, config):
    """Process multiple exercises in batch mode."""
    
    click.echo(click.style("Zanichelli Exercise Automation - Batch Processing", fg='cyan', bold=True))
    click.echo("=" * 60)
    
    # Parse exercise list
    exercise_indices = []
    if exercises == "all":
        # Process all available exercises (assuming 57 total)
        exercise_indices = list(range(57))
        click.echo("Processing ALL exercises (1-57)")
    elif exercises:
        try:
            exercise_numbers = [int(x.strip()) for x in exercises.split(',')]
            exercise_indices = [n - 1 for n in exercise_numbers]  # Convert to 0-based
            click.echo(f"Processing exercises: {exercises}")
        except ValueError:
            click.echo(click.style("❌ Invalid exercise list format. Use comma-separated numbers or 'all'", fg='red'))
            sys.exit(1)
    else:
        click.echo(click.style("❌ No exercises specified. Use --exercises option", fg='red'))
        sys.exit(1)
    
    click.echo(f"Login required: {not no_login}")
    click.echo(f"Headless mode: {headless}")
    click.echo("=" * 60)
    
    async def run_batch_automation():
        """Run batch automation process."""
        async with ZanichelliExerciseAutomator(config_path=config) as automator:
            try:
                # Initialize browser and components
                if not await automator.initialize(headless=headless):
                    click.echo(click.style("❌ Failed to initialize automator", fg='red'))
                    return False
                
                # Process multiple exercises
                results = await automator.process_multiple_exercises(
                    url=url,
                    exercise_indices=exercise_indices,
                    login_required=not no_login
                )
                
                if results['success']:
                    click.echo(click.style(f"\n🎉 Batch processing completed!", fg='green', bold=True))
                    click.echo(f"Exercises processed: {results['exercises_processed']}")
                    click.echo(f"Successful: {results['exercises_successful']}")
                    click.echo(f"Failed: {results['exercises_failed']}")
                else:
                    click.echo(click.style(f"\n❌ Batch processing failed", fg='red'))
                    for error in results['errors']:
                        click.echo(f"  - {error}")
                    return False
                
                return True
                
            except Exception as e:
                click.echo(click.style(f"❌ Fatal error: {e}", fg='red'))
                return False
    
    # Run the batch automation
    try:
        success = asyncio.run(run_batch_automation())
        
        if success:
            click.echo(click.style("\n✅ Batch automation completed successfully!", fg='green', bold=True))
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo(click.style("\nBatch automation interrupted by user", fg='yellow'))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Fatal error: {e}", fg='red'))
        sys.exit(1)


# Create a CLI group to support multiple commands
@click.group()
def cli():
    """Zanichelli Exercise Automation - Refactored Modular Version."""
    pass


# Add commands to the group
cli.add_command(main, name='process')
cli.add_command(batch_process, name='batch')


if __name__ == "__main__":
    # If called directly, run the main process command
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and not sys.argv[1] in ['process', 'batch']):
        main()
    else:
        cli()