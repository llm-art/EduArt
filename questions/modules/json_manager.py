#!/usr/bin/env python3
"""
JSON file operations for reading questions and updating with answers.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class JSONManager:
  def __init__(self, base_path: str = "structured"):
    self.base_path = Path(base_path)

  def load_question(self, exercise: int, question: int) -> Optional[Dict[str, Any]]:
    """Load a specific question from JSON file."""
    json_path = self.base_path / \
        str(exercise) / "json" / f"{question}.json"

    if not json_path.exists():
      print(f"Question file not found: {json_path}")
      return None

    try:
      with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
      print(f"Loaded question {exercise}/{question}")
      return data
    except Exception as e:
      print(f"Error loading question {exercise}/{question}: {e}")
      return None

  def update_question(self, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update a question JSON file with new data."""
    exercise = data.get('exercise')
    question = data.get('question')+1

    try:
      with open(self.base_path / str(exercise) / "json" / f"{question}.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
      print(f"Updated question {exercise}/{question} successfully")
      return data
    except Exception as e:
      print(f"Error updating question {exercise}/{question}: {e}")
      return data

  def load_all_questions(self, exercise: int, min_question: int, max_question: int) -> List[Dict[str, Any]]:
    """Load all questions for an exercise."""
    questions = []
    exercise_dir = self.base_path / str(exercise) / "json"

    if not exercise_dir.exists():
      print(f"Exercise directory not found: {exercise_dir}")
      return questions

    # Find all JSON files and sort by question number
    json_files = sorted(
        [f for f in exercise_dir.glob("*.json")
         if f.stem.isdigit() and int(f.stem) >= min_question and int(f.stem) <= max_question],
        key=lambda x: int(x.stem)
    )
    print(
      f"Found {len(json_files)} question files for exercise {exercise} in range ({min_question}, {max_question}]")

    for json_file in json_files:
      q_num = int(json_file.stem)
      question_data = self.load_question(exercise, q_num)
      if question_data:
        questions.append(question_data)

    return questions

  def get_available_exercises(self) -> List[int]:
    """Get list of available exercise numbers."""
    exercises = []
    if not self.base_path.exists():
      print(f"❌ Base path not found: {self.base_path}")
      return exercises

    for item in self.base_path.iterdir():
      if item.is_dir() and item.name.isdigit():
        exercises.append(int(item.name))

    exercises = sorted(exercises)
    print(f"Available exercises: {exercises}")
    return exercises

  def get_question_summary(self, exercise: int, question: int) -> str:
    """Get a summary string for a question."""
    question_data = self.load_question(exercise, question)
    if not question_data:
      return f"Question {exercise}/{question}: Not found"

    q_type = question_data.get('type', 'unknown')
    title = question_data.get('question_title', 'No title')
    text = question_data.get('question_text', 'No text')[:50] + "..."
    has_image = "📷" if question_data.get('image') else "📄"

    return f"Q{question} ({q_type}) {has_image}: {title} - {text}"


if __name__ == "__main__":
  # Simple test
  manager = JSONManager()

  # Test getting available exercises
  exercises = manager.get_available_exercises()
  print(f"Available exercises: {exercises}")

  if exercises:
    # Test loading first exercise
    first_exercise = exercises[0]
    questions = manager.load_all_questions(first_exercise)
    print(f"Questions in exercise {first_exercise}: {len(questions)}")

    if questions:
      # Show summary of first question
      first_q = questions[0]
      summary = manager.get_question_summary(
        first_exercise, first_q['question'])
      print(f"First question: {summary}")
