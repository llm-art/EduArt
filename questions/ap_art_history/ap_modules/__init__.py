"""
AP Art History Modules (ap_modules)

This package contains reusable modules for AP Art History question processing.

Note: Named 'ap_modules' to avoid conflicts with the parent 'modules' directory.
"""

__all__ = [
    'PDFService',
    'parse_answer_key',
    'load_answer_key',
    'load_html_content',
    'count_png_files_in_raw',
    'setup_directories',
    'post_process_question',
    'extract_artwork_images',
    'extract_artwork_images_with_labels',
    'combine_images_side_by_side'
]
