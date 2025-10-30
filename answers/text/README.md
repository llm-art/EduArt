# LLM Evaluation Results

## Overview

This directory contains the results of evaluating Large Language Models (LLMs) on Italian art history questions.

- **Creation Date**: 2025-10-30 13:58:04
- **Version**: 0.3
- **Total Exercises**: 5
- **Total Questions**: 5
- **Questions with Images**: 5

## Directory Structure

```
answers/
├── metadata.json          # Comprehensive evaluation metadata
├── README.md             # This file
└── data/                 # Individual question results organized by model
    ├── google_gemini-2.5-flash-lite/
    │   ├── 0001.json     # Results for question 0001
    │   ├── 0002.json     # Results for question 0002
    │   └── ...           # More question results
    ├── openai_gpt-4o/
    │   ├── 0001.json     # Results for question 0001
    │   └── ...           # More question results
    └── ...               # More model folders
```

## Question Types Distribution

- **multiple_choice_radio**: 3 questions
- **multiple_choice_check**: 2 questions

## Model Performance Summary

| Model | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence | Input Tokens | Output Tokens | Actual Cost |
|-------|-----------|--------|----------|---------|-------------|------------|--------------|---------------|-------------|
| google/gemini-2.5-flash-lite | 0.883 | 0.900 | 0.886 | 0.830 | 0.600 | H:4 M:1 L:0 | 6,755 | 11 | $0.0007 |
| google/gemini-2.5-flash | 0.800 | 0.700 | 0.733 | 0.700 | 0.600 | H:3 M:1 L:1 | 6,755 | 8 | $0.0020 |
| google/gemini-2.5-pro | 1.000 | 0.900 | 0.933 | 0.900 | 0.800 | H:4 M:1 L:0 | 6,755 | 8 | $0.0085 |

## Performance by Question Type

### multiple_choice_check

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-flash-lite | 2 | 2 | 1 | 0.708 | 0.750 | 0.714 | 0.575 | 0.000 | H:1 M:1 L:0 |
| google/gemini-2.5-flash | 2 | 2 | 1 | 1.000 | 0.750 | 0.833 | 0.750 | 0.500 | H:1 M:1 L:0 |
| google/gemini-2.5-pro | 2 | 2 | 1 | 1.000 | 0.750 | 0.833 | 0.750 | 0.500 | H:1 M:1 L:0 |

### multiple_choice_radio

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-flash-lite | 3 | 3 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | H:3 M:0 L:0 |
| google/gemini-2.5-flash | 3 | 3 | 2 | 0.667 | 0.667 | 0.667 | 0.667 | 0.667 | H:2 M:0 L:1 |
| google/gemini-2.5-pro | 3 | 3 | 3 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | H:3 M:0 L:0 |


