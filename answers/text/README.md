# LLM Evaluation Results

## Overview

This directory contains the results of evaluating Large Language Models (LLMs) on Italian art history questions.

- **Creation Date**: 2025-11-07 16:54:44
- **Version**: 0.3
- **Total Exercises**: 20
- **Total Questions**: 20
- **Questions with Images**: 14

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

- **multiple_choice_radio**: 4 questions
- **multiple_choice_check**: 6 questions
- **true_false**: 3 questions
- **completion_closed**: 2 questions
- **select_errors**: 2 questions
- **positioning**: 2 questions
- **completion_open**: 1 questions

## Model Performance Summary

| Model | Precision | Recall | F1 Score | Exact Match | Input Tokens | Output Tokens | Actual Cost |
|-------|-----------|--------|----------|-------------|--------------|---------------|-------------|
| google/gemini-2.5-flash-lite | 0.689 | 0.568 | 0.586 | 0.105 | 1,772 | 1,003 | $0.0006 |

## Performance by Model and Question Type

### google/gemini-2.5-flash-lite

| Question Type | Questions | With Images | Correct | Precision | Recall | F1 Score |
|---------------|-----------|-------------|---------|-----------|--------|----------|
| completion_closed | 2 | 1 | 2 | 1.000 | 0.845 | 0.916 |
| completion_open | 1 | 0 | 0 | 0.000 | 0.000 | 0.000 |
| multiple_choice_check | 6 | 6 | 3 | 0.681 | 0.833 | 0.744 |
| multiple_choice_radio | 4 | 4 | 1 | 0.250 | 0.250 | 0.250 |
| positioning | 2 | 0 | 1 | 1.000 | 0.667 | 0.788 |
| select_errors | 2 | 0 | 0 | 0.500 | 0.083 | 0.143 |
| true_false | 3 | 3 | 1 | 1.000 | 0.533 | 0.657 |


