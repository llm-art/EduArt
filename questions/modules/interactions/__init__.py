"""
Question interaction modules for Zanichelli exercise automation.

This package contains modules for detecting question types and interacting
with different types of questions before capturing screenshots and HTML.
"""

from .detector import QuestionTypeDetector
from .handler import QuestionInteractionHandler
from .strategies import (
    SceltaMultiplaStrategy,
    CompletamentoChiusoStrategy,
    VeroFalsoStrategy,
    PositioningStrategy,
    TrovaErroreStrategy,
    CompletamentoApertoStrategy
)

__version__ = "1.0.0"
__all__ = [
    'QuestionTypeDetector',
    'QuestionInteractionHandler',
    'SceltaMultiplaStrategy',
    'CompletamentoChiusoStrategy', 
    'VeroFalsoStrategy',
    'PositioningStrategy',
    'TrovaErroreStrategy',
    'CompletamentoApertoStrategy'
]