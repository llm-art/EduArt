# LLM Evaluation Results

## Overview

This directory contains the results of evaluating Large Language Models (LLMs) on Italian art history questions.

- **Creation Date**: 2025-10-30 13:46:42
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

| Model | Precision | Recall | F1 Score | Input Tokens | Output Tokens | Actual Cost |
|-------|-----------|--------|----------|--------------|---------------|-------------|
| google/gemini-2.5-pro | 0.633 | 0.583 | 0.600 | 6,790 | 8 | $0.0086 |
| google/gemini-2.5-flash | 0.633 | 0.583 | 0.600 | 6,790 | 8 | $0.0021 |
| google/gemini-2.5-flash-lite | 0.267 | 0.233 | 0.248 | 6,790 | 9 | $0.0007 |

## Performance by Question Type

### multiple_choice_check

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-pro | 2 | 2 | 0 | 0.583 | 0.458 | 0.500 | 0.350 | 0.000 | H:0 M:1 L:1 |
| google/gemini-2.5-flash | 2 | 2 | 0 | 0.583 | 0.458 | 0.500 | 0.350 | 0.000 | H:0 M:1 L:1 |
| google/gemini-2.5-flash-lite | 2 | 2 | 0 | 0.667 | 0.583 | 0.619 | 0.450 | 0.000 | H:0 M:2 L:0 |

### multiple_choice_radio

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-pro | 3 | 3 | 2 | 0.667 | 0.667 | 0.667 | 0.667 | 0.667 | H:2 M:0 L:1 |
| google/gemini-2.5-flash | 3 | 3 | 2 | 0.667 | 0.667 | 0.667 | 0.667 | 0.667 | H:2 M:0 L:1 |
| google/gemini-2.5-flash-lite | 3 | 3 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | H:0 M:0 L:3 |


