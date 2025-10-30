#!/usr/bin/env python3
"""
Zanichelli Exercise Automation Script - Enhanced with Question Interaction

This script automates the process of accessing and starting exercises on the Zanichelli platform.
It now includes intelligent question interaction that automatically detects question types,
performs randomized interactions, clicks "CORREGGI ESERCIZIO", and captures screenshots
with answers revealed.

Features:
- Automatic question type detection (multiple choice, true/false, drag-drop, etc.)
- Randomized question interactions before screenshot capture
- Automatic "CORREGGI ESERCIZIO" button clicking
- Screenshots and HTML capture with correct answers revealed
- Comprehensive error handling and fallback mechanisms

Usage: python 1_question_downloader.py -e 1 -e 2 -e 3

Requirements:
- playwright
- Install with: pip install playwright && playwright install

For detailed documentation on the question interaction system, see:
README_QUESTION_INTERACTION.md
"""

import asyncio
import sys
import click
from pathlib import Path

# Import the refactored modular automator
from modules import ZanichelliExerciseAutomator


@click.command()
@click.option('--exercise', '-e', multiple=True, type=int, help='Exercise numbers to process (1-57). Use multiple times for multiple exercises (e.g., -e 1 -e 3 -e 5). Use --all for all exercises.', required=False)
@click.option('--all', is_flag=True, help='Process all exercises (1-57)')
@click.option('--url', '-u', default="https://esercizi.zanichelli.it/argomento/Pittura-rinascimentale/x2rnbu-x2rnih-hv05y-2n_5c", help='Exercise list URL', show_default=True)
@click.option('--no-login', is_flag=True, help='Skip login process')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--validate-content', is_flag=True, default=True, help='Validate extracted content quality (only for questions mode)')
@click.option('--no-interaction', is_flag=True, help='Disable question interaction system (legacy mode)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output for detailed logging')
@click.option('--config', '-c', default='config.json', help='Configuration file path', show_default=True)
def main(exercise, all, url, no_login, headless, validate_content, no_interaction, verbose, config):
    """Zanichelli Exercise Automation - Unified Processing."""
    
    # Only show header if verbose or if no exercise specified
    if verbose or not (exercise or all):
        click.echo(click.style("Zanichelli Exercise Automation - Unified Processing", fg='cyan', bold=True))
        click.echo("=" * 70)
    
    if all:
        exercise_indices = list(range(57))
        if verbose:
            click.echo("Processing ALL exercise")
    elif exercise:
        # Convert user-provided exercise numbers (1-based) to internal indices (0-based)
        exercise_indices = [ex - 1 for ex in exercise]
        if verbose:
            click.echo(f"Processing exercise: {list(exercise)} (user numbers)")
            click.echo(f"Internal indices: {exercise_indices} (0-based)")
        else:
            click.echo(f"Processing exercise: {list(exercise)}")
    
    if verbose:
        click.echo(f"Login required: {not no_login}")
        click.echo(f"Headless mode: {headless}")
        click.echo(f"Verbose mode: {verbose}")
        click.echo(f"Configuration file: {config}")
        click.echo("=" * 70)
    
    async def run_automation():
        """Run the unified automation process."""
        async with ZanichelliExerciseAutomator(config_path=config, verbose=verbose) as automator:
            try:
                # Initialize browser and components
                if verbose:
                    click.echo("Initializing browser and components...")
                if not await automator.initialize(headless=headless):
                    click.echo(click.style("❌ Failed to initialize automator", fg='red'))
                    return False
                
                if verbose:
                    click.echo(click.style("✅ Initialization successful", fg='green'))
                
                # Process exercise using unified path (works for both single and multiple)
                results = await automator.process_multiple_exercises(
                    url=url,
                    exercise_indices=exercise_indices,
                    login_required=not no_login,
                    process_mode="questions",
                    validate_content=validate_content,
                    enable_interaction=not no_interaction,
                    verbose=verbose
                )
                
                if results['success']:
                    click.echo(click.style(f"✅ Processing completed successfully", fg='green', bold=True))
                    
                    # Always show basic statistics
                    click.echo(f"Exercises processed: {results['exercises_processed']}")
                    click.echo(f"Questions processed: {results['total_questions_processed']}")
                    
                    if verbose:
                        # Display detailed exercise statistics
                        click.echo(f"Exercises successful: {results['exercises_successful']}")
                        click.echo(f"Exercises failed: {results['exercises_failed']}")
                        
                        if results['exercises_processed'] > 0:
                            success_rate = (results['exercises_successful'] / results['exercises_processed']) * 100
                            click.echo(f"Exercise success rate: {success_rate:.1f}%")
                        
                        # Display detailed question statistics
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
                        click.echo(f"- Screenshots (with answers): {base_dir}/data/[exercise_number]/raw/")
                        click.echo(f"- Images: {base_dir}/data/[exercise_number]/imgs/")
                        click.echo(f"- HTML content (with answers): {base_dir}/data/[exercise_number]/raw/")
                        click.echo(f"- Processing logs: {base_dir}/data/[exercise_number]/logs/")
                        
                        # Display warnings/errors if any
                        if results['errors']:
                            click.echo(click.style(f"\nWarnings/Errors ({len(results['errors'])}):", fg='yellow'))
                            for error in results['errors'][:10]:  # Show first 10 errors
                                click.echo(f"  • {error}")
                            if len(results['errors']) > 10:
                                click.echo(f"  • ... and {len(results['errors']) - 10} more errors")
                    elif results['errors']:
                        # Show errors even in non-verbose mode if they exist
                        click.echo(click.style(f"Errors: {len(results['errors'])}", fg='yellow'))
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
            if verbose:
                click.echo(click.style("\n🎉 All done!", fg='green', bold=True))
                click.echo("\n📋 Enhanced Features Active:")
                click.echo("  ✅ Automatic question type detection")
                click.echo("  ✅ Randomized question interactions")
                click.echo("  ✅ Automatic answer revelation (CORREGGI ESERCIZIO)")
                click.echo("  ✅ Screenshots and HTML with correct answers")
            else:
                click.echo(click.style("🎉 All done!", fg='green', bold=True))
        else:
            click.echo(click.style("❌ Processing failed", fg='red'))
            sys.exit(1)
            
    except KeyboardInterrupt:
        click.echo(click.style("\n⚠️ Interrupted by user", fg='yellow'))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"❌ Fatal error: {e}", fg='red'))
        sys.exit(1)


if __name__ == "__main__":
    main()