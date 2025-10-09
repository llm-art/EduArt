"""Core module containing configuration, types, and exceptions."""

from .config import DownloadConfig, ProcessorConfig, AnswerConfig, PipelineConfig
from .exceptions import (
    ProcessingError, 
    ConfigurationError, 
    OCRError, 
    VisionModelError, 
    SubmissionError,
    FileOperationError,
    ValidationError,
    ModelLoadError,
    NetworkError,
    BrowserAutomationError
)
from .types import (
    QuestionType,
    ProcessingStatus,
    Choice,
    QuestionData,
    ProcessingResult,
    AnswerResult,
    SubmissionResult,
    PipelineResult,
    BatchResult
)

__all__ = [
    # Configuration classes
    'DownloadConfig',
    'ProcessorConfig', 
    'AnswerConfig',
    'PipelineConfig',
    
    # Exception classes
    'ProcessingError',
    'ConfigurationError',
    'OCRError',
    'VisionModelError',
    'SubmissionError',
    'FileOperationError',
    'ValidationError',
    'ModelLoadError',
    'NetworkError',
    'BrowserAutomationError',
    
    # Type definitions
    'QuestionType',
    'ProcessingStatus',
    'Choice',
    'QuestionData',
    'ProcessingResult',
    'AnswerResult',
    'SubmissionResult',
    'PipelineResult',
    'BatchResult'
]