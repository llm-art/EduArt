"""
File management utilities for Zanichelli exercise automation.

This module handles file operations, directory management, and content downloading.
"""

from .manager import FileManager
from .downloader import ContentDownloader

__all__ = ['FileManager', 'ContentDownloader']