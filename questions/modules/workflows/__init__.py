"""
High-level workflows for Zanichelli exercise automation.

This module contains workflow orchestrators that combine multiple components
to perform complex automation tasks.
"""

from .login import LoginWorkflow
from .navigation import NavigationWorkflow
from .question_processor import QuestionProcessorWorkflow

__all__ = ['LoginWorkflow', 'NavigationWorkflow', 'QuestionProcessorWorkflow']