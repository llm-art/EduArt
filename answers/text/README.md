# LLM Evaluation Results

## Overview

This directory contains the results of evaluating Large Language Models (LLMs) on Italian art history questions.

- **Creation Date**: 2025-10-30 22:49:17
- **Version**: 0.3
- **Total Exercises**: 20
- **Total Questions**: 20
- **Questions with Images**: 0

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

- **multiple_choice_radio**: 10 questions
- **true_false**: 3 questions
- **completion_closed**: 2 questions
- **select_errors**: 2 questions
- **positioning**: 2 questions
- **completion_open**: 1 questions

## Model Performance Summary

| Model | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence | Input Tokens | Output Tokens | Actual Cost |
|-------|-----------|--------|----------|---------|-------------|------------|--------------|---------------|-------------|
| google/gemini-2.5-flash-lite | 0.379 | 0.379 | 0.379 | 0.379 | 0.211 | H:6 M:2 L:11 | 3,172 | 525 | $0.0005 |

## Performance by Question Type

### completion_closed

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-flash-lite | 2 | 0 | 1 | 0.700 | 0.700 | 0.700 | 0.700 | 0.000 | H:1 M:1 L:0 |

### completion_open

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-flash-lite | 1 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | H:0 M:0 L:0 |

### multiple_choice_radio

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-flash-lite | 10 | 0 | 4 | 0.400 | 0.400 | 0.400 | 0.400 | 0.400 | H:4 M:0 L:6 |

### positioning

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-flash-lite | 2 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | H:0 M:0 L:2 |

### select_errors

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-flash-lite | 2 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | H:0 M:0 L:2 |

### true_false

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score | Jaccard | Exact Match | Confidence |
|-------|-----------|-------------|---------|-----------|--------|----------|---------|-------------|------------|
| google/gemini-2.5-flash-lite | 3 | 0 | 1 | 0.600 | 0.600 | 0.600 | 0.600 | 0.000 | H:1 M:1 L:1 |


