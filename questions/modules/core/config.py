"""Configuration classes for the question processing pipeline."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class DownloadConfig:
    """Configuration for question downloading."""
    exercises: List[int]
    url: str = "https://esercizi.zanichelli.it/argomento/Pittura-rinascimentale/x2rnbu-x2rnih-hv05y-2n_5c"
    headless: bool = True
    validate_content: bool = True
    config_path: str = "config.json"
    max_exercises: int = 57
    no_login: bool = False
    
    def validate(self) -> None:
        """Validate configuration parameters."""
        if not self.exercises:
            raise ValueError("At least one exercise must be specified")
            
        for exercise in self.exercises:
            if not 1 <= exercise <= self.max_exercises:
                raise ValueError(f"Exercise {exercise} out of range 1-{self.max_exercises}")
    
    @classmethod
    def from_cli_args(cls, exercises: List[int], all_exercises: bool = False, **kwargs) -> 'DownloadConfig':
        """Create configuration from CLI arguments."""
        if all_exercises:
            exercises = list(range(1, kwargs.get('max_exercises', 57) + 1))
        
        config = cls(exercises=exercises, **kwargs)
        config.validate()
        return config


@dataclass
class ProcessorConfig:
    """Configuration for question processing."""
    exercise: int
    min_question: int = 1
    max_question: int = 20
    force_ocr: bool = False
    verbose: bool = False
    batch_size: int = 1
    metadata_ai: bool = True
    
    def validate(self) -> None:
        """Validate processing configuration."""
        if self.exercise < 1:
            raise ValueError("Exercise number must be positive")
        if self.min_question < 1:
            raise ValueError("Minimum question number must be positive")
        if self.max_question < self.min_question:
            raise ValueError("Maximum question must be >= minimum question")
    
    @classmethod
    def from_cli_args(cls, **kwargs) -> 'ProcessorConfig':
        """Create configuration from CLI arguments."""
        config = cls(**kwargs)
        config.validate()
        return config


@dataclass
class AnswerConfig:
    """Configuration for answer generation."""
    exercise: int
    min_question: int = 1
    max_question: int = 20
    submission_url: Optional[str] = None
    enable_submission: bool = False
    base_path: str = "structured"
    
    def validate(self) -> None:
        """Validate answer configuration."""
        if self.exercise < 1:
            raise ValueError("Exercise number must be positive")
        if self.min_question < 1:
            raise ValueError("Minimum question number must be positive")
        if self.max_question < self.min_question:
            raise ValueError("Maximum question must be >= minimum question")
        if self.enable_submission and not self.submission_url:
            raise ValueError("Submission URL required when submission is enabled")
    
    @classmethod
    def from_cli_args(cls, url: Optional[str] = None, **kwargs) -> 'AnswerConfig':
        """Create configuration from CLI arguments."""
        enable_submission = url is not None
        config = cls(
            submission_url=url,
            enable_submission=enable_submission,
            **kwargs
        )
        config.validate()
        return config


@dataclass
class PipelineConfig:
    """Overall pipeline configuration combining all stages."""
    download: Optional[DownloadConfig] = None
    processor: Optional[ProcessorConfig] = None
    answer: Optional[AnswerConfig] = None
    
    def validate(self) -> None:
        """Validate all configurations."""
        if self.download:
            self.download.validate()
        if self.processor:
            self.processor.validate()
        if self.answer:
            self.answer.validate()