#!/usr/bin/env python3
"""
Zanichelli Exercise Automation Script - Unified Version

This script automates the process of accessing and starting exercises on the Zanichelli platform.
It uses a modular architecture for better maintainability and extensibility.

Usage: python question_downloader.py -e 1 -e 2 -e 3

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
@click.option('--exercises', '-e', multiple=True, type=int, help='Exercise numbers to process (1-57). Use multiple times for multiple exercises (e.g., -e 1 -e 3 -e 5). Use --all for all exercises.', required=False)
@click.option('--all', is_flag=True, help='Process all exercises (1-57)')
@click.option('--url', '-u', default="https://esercizi.zanichelli.it/argomento/Pittura-rinascimentale/x2rnbu-x2rnih-hv05y-2n_5c", help='Exercise list URL', show_default=True)
@click.option('--no-login', is_flag=True, help='Skip login process')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--validate-content', is_flag=True, default=True, help='Validate extracted content quality (only for questions mode)')
@click.option('--config', '-c', default='config.json', help='Configuration file path', show_default=True)
def main(exercises, all, url, no_login, headless, validate_content, config):
    """Zanichelli Exercise Automation - Unified Processing."""
    
    click.echo(click.style("Zanichelli Exercise Automation - Unified Processing", fg='cyan', bold=True))
    click.echo("=" * 70)
    
    # Parse exercise list
    exercise_indices = []
    
    if all:
        # Process all available exercises (assuming 57 total)
        exercise_indices = list(range(57))
        click.echo("Processing ALL exercises (1-57)")
        click.echo("This will process ALL QUESTIONS in all exercises.")
        if not click.confirm("Are you sure you want to process all 57 exercises?"):
            click.echo("Operation cancelled.")
            sys.exit(0)
    elif exercises:
        # Validate exercise numbers
        exercise_numbers = list(exercises)
        for num in exercise_numbers:
            if num < 1 or num > 57:
                click.echo(click.style(f"❌ Error: Exercise number must be between 1 and 57, got {num}", fg='red'))
                sys.exit(1)
        exercise_indices = [n - 1 for n in exercise_numbers]  # Convert to 0-based
        click.echo(f"Processing exercises: {', '.join(map(str, exercise_numbers))}")
        
        # Warn for large batches
        if len(exercise_indices) > 5:
            click.echo(click.style(f"⚠️ Warning: Processing {len(exercise_indices)} exercises.", fg='yellow'))
            if not click.confirm("Continue?"):
                click.echo("Operation cancelled.")
                sys.exit(0)
    else:
        click.echo(click.style("❌ No exercises specified. Use -e option for exercises or --all for all exercises", fg='red'))
        sys.exit(1)
    
    click.echo("Processing mode: Full question processing (screenshots, HTML, images)")
    click.echo(f"  → Content validation: {validate_content}")
    
    click.echo(f"Login required: {not no_login}")
    click.echo(f"Headless mode: {headless}")
    click.echo(f"Configuration file: {config}")
    click.echo("=" * 70)
    
    async def run_automation():
        """Run the unified automation process."""
        async with ZanichelliExerciseAutomator(config_path=config) as automator:
            try:
                # Initialize browser and components
                click.echo("Initializing browser and components...")
                if not await automator.initialize(headless=headless):
                    click.echo(click.style("❌ Failed to initialize automator", fg='red'))
                    return False
                
                click.echo(click.style("✅ Initialization successful", fg='green'))
                
                # Process exercises using unified path (works for both single and multiple)
                results = await automator.process_multiple_exercises(
                    url=url,
                    exercise_indices=exercise_indices,
                    login_required=not no_login,
                    process_mode="questions",
                    validate_content=validate_content
                )
                
                if results['success']:
                    click.echo(click.style(f"\n✅ Processing completed successfully", fg='green', bold=True))
                    
                    # Display exercise statistics
                    click.echo(f"Exercises processed: {results['exercises_processed']}")
                    click.echo(f"Exercises successful: {results['exercises_successful']}")
                    click.echo(f"Exercises failed: {results['exercises_failed']}")
                    
                    if results['exercises_processed'] > 0:
                        success_rate = (results['exercises_successful'] / results['exercises_processed']) * 100
                        click.echo(f"Exercise success rate: {success_rate:.1f}%")
                    
                    # Display question statistics
                    click.echo(f"\nTotal questions processed: {results['total_questions_processed']}")
                    click.echo(f"Total questions successful: {results['total_questions_successful']}")
                    click.echo(f"Total questions failed: {results['total_questions_failed']}")
                    
                    if results['total_questions_processed'] > 0:
                        question_success_rate = (results['total_questions_successful'] / results['total_questions_processed']) * 100
                        click.echo(f"Question success rate: {question_success_rate:.1f}%")
                        
                        if results['exercises_successful'] > 0:
                            avg_questions_per_exercise = results['total_questions_processed'] / results['exercises_successful']
                            click.echo(f"Average questions per exercise: {avg_questions_per_exercise:.1f}")
                    
                    # Display file locations
                    base_dir = automator.file_manager.get_base_dir()
                    click.echo(f"\nFiles saved in:")
                    click.echo(f"- Screenshots: {base_dir}/data/[exercise_number]/raw/")
                    click.echo(f"- Images: {base_dir}/data/[exercise_number]/imgs/")
                    click.echo(f"- HTML content: {base_dir}/data/[exercise_number]/raw/")
                    
                    # Display warnings/errors if any
                    if results['errors']:
                        click.echo(click.style(f"\nWarnings/Errors ({len(results['errors'])}):", fg='yellow'))
                        for error in results['errors'][:10]:  # Show first 10 errors
                            click.echo(f"  • {error}")
                        if len(results['errors']) > 10:
                            click.echo(f"  • ... and {len(results['errors']) - 10} more errors")
                else:
                    click.echo(click.style(f"\n❌ Processing failed", fg='red'))
                    for error in results['errors']:
                        click.echo(f"  • {error}")
                    return False
                
                return True
                
            except KeyboardInterrupt:
                click.echo(click.style(f"\n⚠️ Processing interrupted by user", fg='yellow'))
                return False
            except Exception as e:
                click.echo(click.style(f"❌ Fatal error: {e}", fg='red'))
                return False
    
    # Run the automation
    try:
        success = asyncio.run(run_automation())
        
        if success:
            click.echo(click.style("\n🎉 All done!", fg='green', bold=True))
            click.echo("\nUsage examples:")
            click.echo("  Single exercise:    python question_downloader.py -e 2")
            click.echo("  Multiple exercises: python question_downloader.py -e 1 -e 3 -e 5")
            click.echo("  All exercises:      python question_downloader.py --all")
            click.echo("  Headless mode:      python question_downloader.py -e 1 --headless")
            click.echo("  Without login:      python question_downloader.py -e 1 --no-login")
        else:
            click.echo(click.style("\n❌ Processing failed", fg='red'))
            click.echo("\nTroubleshooting:")
            click.echo("  • Make sure config.json exists with your credentials")
            click.echo("  • Copy config.json.template to config.json and fill in your details")
            click.echo("  • Check your internet connection")
            click.echo("  • Verify the exercise page loads correctly")
            click.echo("  • Try running with --headless flag if display issues occur")
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo(click.style("\n⚠️ Interrupted by user", fg='yellow'))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"❌ Fatal error: {e}", fg='red'))
        sys.exit(1)


if __name__ == "__main__":
    main()