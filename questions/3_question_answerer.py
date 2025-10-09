#!/usr/bin/env python3
"""
Main orchestrator for the question answering and submission pipeline.
"""

import asyncio
import click
from pathlib import Path
from typing import List, Optional
import time

from modules.answer_generator import QuestionAnswerer
from modules.zanichelli_submitter import ZanichelliAnswerSubmitter
from modules.json_manager import JSONManager


class AnswerPipeline:
  def __init__(self):
    self.answerer = QuestionAnswerer()
    self.submitter = ZanichelliAnswerSubmitter()
    self.json_manager = JSONManager()

  async def process_single_question(
      self,
      question: any,
  ) -> dict:
    """Process a single question - generate answer and optionally submit."""
    print(f"\n{'=' * 60}")
    print(f"PROCESSING QUESTION {question['exercise']}/{question['question']}")
    print(f"{'=' * 60}")

    result = {
        'exercise': question['exercise'],
        'question': question['question'],
        'success': False,
        'generated_answer': None,
        'correct_answer': None,
        'is_correct': None,
        'error': None
    }

    try:

      # Show question summary
      summary = self.json_manager.get_question_summary(question['exercise'], question['question'])
      print(f"Question: {summary}")

      # Generate answer using LLM
      print("\n--- GENERATING ANSWER ---")
      answer_result = self.answerer.answer_question(question)

      print("\n--- UPDATING JSON FILE ---")
      question["generated_answer"] = answer_result
      
      question = self.json_manager.update_question(question)

    except Exception as e:
      error_msg = f"Error processing question /{question}: {e}"
      result['error'] = error_msg
      

    return result

@click.command()
@click.option('--exercise', '-e', type=int, required=True, help='Exercise number to process')
@click.option('--min-question', type=int, default=1, help='Minimum question number (inclusive)')
@click.option('--max-question', type=int, default=20, help='Maximum question number (inclusive)')
@click.option('--url', '-u', help='Zanichelli exercise URL (required for submission)')
def main(exercise, min_question, max_question, url):
  """Main CLI interface for the answer pipeline."""

  print("Starting Answer Pipeline")

  # Create range from min to max
  pipeline = AnswerPipeline()
  all_questions = pipeline.json_manager.load_all_questions(exercise, min_question, max_question)
  print(f"Processing questions {min_question} to {max_question}: {len(all_questions)}")

  # Process single question
  for question in all_questions:
    result = asyncio.run(pipeline.process_single_question(
        question=question,
    ))

  print(f"\n{'=' * 50}")
  print(f"SINGLE QUESTION RESULT")
  print(f"{'=' * 50}")

if __name__ == "__main__":
  main()
