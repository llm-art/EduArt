"""
Browser automation utilities for Zanichelli exercise automation.

This module provides browser management, interaction patterns, and selector strategies.
"""

from .browser_manager import BrowserManager
from .selectors import SelectorStrategies
from .interactions import InteractionHandler

__all__ = ['BrowserManager', 'SelectorStrategies', 'InteractionHandler']