# LLM Evaluation Results

## Overview

This directory contains the results of evaluating Large Language Models (LLMs) on Italian art history questions.

- **Creation Date**: 2025-10-23 13:22:42
- **Version**: 0.3
- **Total Exercises**: 76
- **Total Questions**: 76
- **Questions with Images**: 32

## Directory Structure

```
answers/
├── metadata.json          # Comprehensive evaluation metadata
├── README.md             # This file
└── data/                 # Individual question results organized by model
    ├── google_gemini-2.5-flash-lite/
    │   ├── 5_1.json      # Results for question 1 from exercise 5
    │   ├── 5_2.json      # Results for question 2 from exercise 5
    │   └── ...           # More question results
    ├── openai_gpt-4o/
    │   ├── 5_1.json      # Results for question 1 from exercise 5
    │   └── ...           # More question results
    └── ...               # More model folders
```

## Question Types Distribution

- **multiple_choice_check**: 18 questions
- **true_false**: 8 questions
- **positioning**: 23 questions
- **select_errors**: 6 questions
- **completion_closed**: 9 questions
- **multiple_choice_radio**: 9 questions
- **multiple_choice**: 3 questions

## Model Performance Summary

| Model | Precision | Recall | F1 Score | Input Tokens | Output Tokens | Actual Cost |
|-------|-----------|--------|----------|--------------|---------------|-------------|
| google/gemini-2.5-pro | 0.645 | 0.645 | 0.645 | 63,301 | 877 | $0.0879 |
| google/gemini-2.5-flash-lite | 0.421 | 0.421 | 0.421 | 63,301 | 879 | $0.0067 |
| google/gemini-2.5-flash | 0.513 | 0.513 | 0.513 | 63,301 | 2,106 | $0.0243 |

## Performance by Question Type

### completion_closed

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score |
|-------|-----------|-------------|---------|-----------|--------|-----------|
| google/gemini-2.5-pro | 9 | 0 | 8 | 0.889 | 0.889 | 0.889 |
| google/gemini-2.5-flash-lite | 9 | 0 | 5 | 0.556 | 0.556 | 0.556 |
| google/gemini-2.5-flash | 9 | 0 | 7 | 0.778 | 0.778 | 0.778 |

### multiple_choice

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score |
|-------|-----------|-------------|---------|-----------|--------|-----------|
| google/gemini-2.5-pro | 3 | 0 | 3 | 1.000 | 1.000 | 1.000 |
| google/gemini-2.5-flash-lite | 3 | 0 | 1 | 0.333 | 0.333 | 0.333 |
| google/gemini-2.5-flash | 3 | 0 | 3 | 1.000 | 1.000 | 1.000 |

### multiple_choice_check

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score |
|-------|-----------|-------------|---------|-----------|--------|-----------|
| google/gemini-2.5-pro | 18 | 14 | 8 | 0.444 | 0.444 | 0.444 |
| google/gemini-2.5-flash-lite | 18 | 14 | 3 | 0.167 | 0.167 | 0.167 |
| google/gemini-2.5-flash | 18 | 14 | 3 | 0.167 | 0.167 | 0.167 |

### multiple_choice_radio

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score |
|-------|-----------|-------------|---------|-----------|--------|-----------|
| google/gemini-2.5-pro | 9 | 6 | 8 | 0.889 | 0.889 | 0.889 |
| google/gemini-2.5-flash-lite | 9 | 6 | 5 | 0.556 | 0.556 | 0.556 |
| google/gemini-2.5-flash | 9 | 6 | 6 | 0.667 | 0.667 | 0.667 |

### positioning

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score |
|-------|-----------|-------------|---------|-----------|--------|-----------|
| google/gemini-2.5-pro | 23 | 6 | 17 | 0.739 | 0.739 | 0.739 |
| google/gemini-2.5-flash-lite | 23 | 6 | 13 | 0.565 | 0.565 | 0.565 |
| google/gemini-2.5-flash | 23 | 6 | 15 | 0.652 | 0.652 | 0.652 |

### select_errors

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score |
|-------|-----------|-------------|---------|-----------|--------|-----------|
| google/gemini-2.5-pro | 6 | 2 | 0 | 0.000 | 0.000 | 0.000 |
| google/gemini-2.5-flash-lite | 6 | 2 | 0 | 0.000 | 0.000 | 0.000 |
| google/gemini-2.5-flash | 6 | 2 | 0 | 0.000 | 0.000 | 0.000 |

### true_false

| Model | Questions | With Images | Correct | Precision | Recall | F1 Score |
|-------|-----------|-------------|---------|-----------|--------|-----------|
| google/gemini-2.5-pro | 8 | 4 | 5 | 0.625 | 0.625 | 0.625 |
| google/gemini-2.5-flash-lite | 8 | 4 | 5 | 0.625 | 0.625 | 0.625 |
| google/gemini-2.5-flash | 8 | 4 | 5 | 0.625 | 0.625 | 0.625 |


