"""Type definitions and data classes for the question processing pipeline."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from enum import Enum


class QuestionType(Enum):
    """Enumeration of supported question types."""
    MULTIPLE_CHOICE_RADIO = "multiple_choice_radio"
    MULTIPLE_CHOICE_CHECK = "multiple_choice_check"
    TRUE_FALSE = "true_false"
    SELECT_ERRORS = "select_errors"
    HIGHLIGHT_ERRORS = "highlight_errors"
    POSITIONING = "positioning"
    COMPLETION_OPEN = "completion_open"
    COMPLETION_CLOSED = "completion_closed"
    UNKNOWN = "unknown"


class ProcessingStatus(Enum):
    """Enumeration of processing statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class AICallMetadata:
    """Metadata for AI model calls."""
    description: str
    model_name: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    processing_time: Optional[float] = None
    timestamp: Optional[str] = None


@dataclass
class Choice:
    """Represents a multiple choice option."""
    id: str
    text: str
    is_correct: Optional[bool] = None

@dataclass
class Answer:
    """Represents the correct answer for a question."""
    id: str
    description: Optional[str] = None
    note: Optional[str] = None

@dataclass
class QuestionData:
    """Structured question data."""
    exercise: int
    question: int
    type: str = "unknown"
    answers: Optional[Answer] = None
    question_title: Optional[str] = None
    question_text: Optional[str] = None
    choices: Optional[List[Choice]] = None
    image_path: Optional[str] = None
    ocr_text: Optional[str] = None
    language: str = "it"
    has_image: bool = False
    ai_calls: Optional[List[AICallMetadata]] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization processing."""
        if self.choices and isinstance(self.choices, list) and len(self.choices) > 0:
            # Handle different choice formats based on question type
            if self.type == "completion_closed":
                # completion_closed has format: [{"id": "BLANK_1", "options": ["choice1", "choice2"]}]
                # Keep as-is, don't convert to Choice objects
                pass
            elif self.type == "positioning":
                # positioning has format: ["choice1", "choice2", "choice3"]
                # Keep as-is, don't convert to Choice objects
                pass
            elif isinstance(self.choices[0], dict):
                # Standard multiple choice format: [{"id": "A", "text": "option text"}]
                # Convert to Choice objects, but only if they have the right structure
                converted_choices = []
                for choice in self.choices:
                    if isinstance(choice, dict):
                        if "text" in choice and "id" in choice:
                            # Standard Choice format
                            converted_choices.append(Choice(**choice))
                        elif "options" in choice:
                            # completion_closed format - keep as dict
                            converted_choices.append(choice)
                        else:
                            # Unknown dict format - keep as-is
                            converted_choices.append(choice)
                    else:
                        # Not a dict - keep as-is
                        converted_choices.append(choice)
                self.choices = converted_choices
    
    @property
    def question_type(self) -> QuestionType:
        """Get the question type as an enum."""
        try:
            return QuestionType(self.type)
        except ValueError:
            return QuestionType.UNKNOWN


@dataclass
class ProcessingResult:
    """Result of question processing."""
    success: bool
    question_data: Optional[QuestionData] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    status: ProcessingStatus = ProcessingStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def mark_completed(self, question_data: QuestionData, processing_time: float = None):
        """Mark the result as completed."""
        self.success = True
        self.question_data = question_data
        self.status = ProcessingStatus.COMPLETED
        if processing_time:
            self.processing_time = processing_time
    
    def mark_failed(self, error: str):
        """Mark the result as failed."""
        self.success = False
        self.error = error
        self.status = ProcessingStatus.FAILED


@dataclass
class AnswerResult:
    """Result of answer generation."""
    success: bool
    generated_answer: Optional[str] = None
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None
    used_image: bool = False
    processing_time: Optional[float] = None
    
    def mark_completed(self, answer: str, model: str, confidence: float = None, 
                      raw_response: str = None, used_image: bool = False, 
                      processing_time: float = None):
        """Mark the answer result as completed."""
        self.success = True
        self.generated_answer = answer
        self.model_used = model
        self.confidence = confidence
        self.raw_response = raw_response
        self.used_image = used_image
        if processing_time:
            self.processing_time = processing_time
    
    def mark_failed(self, error: str):
        """Mark the answer result as failed."""
        self.success = False
        self.error = error


@dataclass
class SubmissionResult:
    """Result of answer submission."""
    success: bool
    submitted_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    error: Optional[str] = None
    submission_time: Optional[float] = None
    
    def mark_completed(self, submitted_answer: str, correct_answer: str = None, 
                      is_correct: bool = None, submission_time: float = None):
        """Mark the submission result as completed."""
        self.success = True
        self.submitted_answer = submitted_answer
        self.correct_answer = correct_answer
        self.is_correct = is_correct
        if submission_time:
            self.submission_time = submission_time
    
    def mark_failed(self, error: str):
        """Mark the submission result as failed."""
        self.success = False
        self.error = error


@dataclass
class PipelineResult:
    """Overall result of the complete pipeline."""
    exercise: int
    question: int
    processing_result: Optional[ProcessingResult] = None
    answer_result: Optional[AnswerResult] = None
    submission_result: Optional[SubmissionResult] = None
    total_time: Optional[float] = None
    
    @property
    def success(self) -> bool:
        """Check if the entire pipeline was successful."""
        results = [self.processing_result, self.answer_result, self.submission_result]
        active_results = [r for r in results if r is not None]
        return all(r.success for r in active_results) if active_results else False
    
    @property
    def errors(self) -> List[str]:
        """Get all errors from the pipeline."""
        errors = []
        if self.processing_result and self.processing_result.error:
            errors.append(f"Processing: {self.processing_result.error}")
        if self.answer_result and self.answer_result.error:
            errors.append(f"Answer: {self.answer_result.error}")
        if self.submission_result and self.submission_result.error:
            errors.append(f"Submission: {self.submission_result.error}")
        return errors


@dataclass
class BatchResult:
    """Result of batch processing multiple questions."""
    exercise: int
    total_questions: int
    successful_questions: int = 0
    failed_questions: int = 0
    results: List[PipelineResult] = field(default_factory=list)
    total_time: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_questions == 0:
            return 0.0
        return (self.successful_questions / self.total_questions) * 100
    
    def add_result(self, result: PipelineResult):
        """Add a pipeline result to the batch."""
        self.results.append(result)
        if result.success:
            self.successful_questions += 1
        else:
            self.failed_questions += 1