# LLM Evaluation Results

## Overview

This directory contains the results of evaluating Large Language Models (LLMs) on Italian art history questions.

- **Creation Date**: 2026-01-30 12:09:06
- **Version**: 0.3
- **Total Exercises**: 370
- **Total Questions**: 370
- **Questions with Images**: 256

## Available Models

| Model Name | Version | Input Cost ($/1M) | Output Cost ($/1M) | Reasoning |
|------------|---------|-------------------|--------------------|-----------|
| google/gemini-3-flash-preview | N/A | $0.50 | $3.00 | ✗ |
| google/gemini-3-pro-preview | N/A | $2.00 | $12.00 | ✗ |
| harvard/us.anthropic.claude-sonnet-4-5-20250929-v1:0 | N/A | $3.00 | $15.00 | ✗ |
| harvard/us.mistral.pixtral-large-2502-v1:0 | N/A | $2.00 | $6.00 | ✗ |
| openai/gpt-4.1-2025-04-14 | 2025-04-14 | $2.00 | $8.00 | ✗ |
| openai/gpt-5-mini-2025-08-07 | 2025-08-07 | $0.25 | $2.00 | ✗ |
| openai/gpt-5-nano-2025-08-07 | 2025-08-07 | $0.05 | $0.40 | ✗ |
| openai/gpt-5.2-2025-12-11 | 2025-12-11 | $1.75 | $14.00 | ✗ |

## Directory Structure

```
answers/
├── metadata.json          # Comprehensive evaluation metadata
├── README.md             # This file
├── google_gemini-2.5-flash-lite/
│   ├── 0001.json         # Results for question 0001
│   ├── 0002.json         # Results for question 0002
│   └── ...               # More question results
├── openai_gpt-4o/
│   ├── 0001.json         # Results for question 0001
│   └── ...               # More question results
└── ...                   # More model folders
```

## Question Types Distribution

- **multiple_choice_radio**: 370 questions
- **multiple_choice_check**: 6 questions
- **true_false**: 3 questions
- **completion_closed**: 2 questions
- **select_errors**: 2 questions
- **positioning**: 2 questions
- **completion_open**: 1 questions

## Model Performance Summary

| Model | Accuracy | Correct/Total | Input Tokens | Output Tokens | Actual Cost |
|-------|----------|---------------|--------------|---------------|-------------|
| google/gemini-3-flash-preview | 96.5% | 357/370 | 518,285 | 208,229 | $0.8838 |
| google/gemini-3-pro-preview | 95.1% | 352/370 | 521,735 | 316,602 | $4.8427 |
| harvard/us.anthropic.claude-sonnet-4-5-20250929-v1:0 | 72.4% | 268/370 | 538,947 | 33,898 | $2.1253 |
| harvard/us.mistral.pixtral-large-2502-v1:0 | 54.3% | 201/370 | 246,088 | 22,190 | $0.6253 |
| openai/gpt-4.1-2025-04-14 | 93.5% | 346/370 | 461,380 | 7,400 | $0.9820 |
| openai/gpt-5-mini-2025-08-07 | 25.0% | 9/21 | 17,025 | 23,625 | $0.0515 |
| openai/gpt-5-nano-2025-08-07 | 83.5% | 309/370 | 562,893 | 547,207 | $0.2470 |
| openai/gpt-5.2-2025-12-11 | 88.6% | 328/370 | 528,743 | 8,521 | $1.0446 |

## Performance by Model and Question Type

### google/gemini-3-flash-preview

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| multiple_choice_radio | 370 | 253 | 357 | 96.5% | 0.965 | 0.965 | 0.965 |

### google/gemini-3-pro-preview

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| multiple_choice_radio | 370 | 253 | 352 | 95.1% | 0.951 | 0.951 | 0.951 |

### harvard/us.anthropic.claude-sonnet-4-5-20250929-v1:0

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| multiple_choice_radio | 370 | 253 | 268 | 72.4% | 0.724 | 0.724 | 0.724 |

### harvard/us.mistral.pixtral-large-2502-v1:0

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| multiple_choice_radio | 370 | 253 | 201 | 54.3% | 0.543 | 0.543 | 0.543 |

### openai/gpt-4.1-2025-04-14

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| multiple_choice_radio | 370 | 253 | 346 | 93.5% | 0.935 | 0.935 | 0.935 |

### openai/gpt-5-mini-2025-08-07

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| completion_closed | 2 | 1 | 2 | 100.0% | 1.000 | 1.000 | 1.000 |
| completion_open | 1 | 0 | 0 | 0.0% | 0.000 | 0.000 | 0.000 |
| multiple_choice_check | 6 | 6 | 5 | 83.3% | 0.833 | 0.778 | 0.786 |
| multiple_choice_radio | 5 | 5 | 2 | 40.0% | 0.400 | 0.400 | 0.400 |
| positioning | 2 | 0 | 0 | 0.0% | 0.667 | 0.667 | 0.667 |
| select_errors | 2 | 0 | 0 | 0.0% | - | - | - |
| true_false | 3 | 3 | 0 | 0.0% | 0.533 | 0.533 | 0.533 |

### openai/gpt-5-nano-2025-08-07

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| multiple_choice_radio | 370 | 253 | 309 | 83.5% | 0.835 | 0.835 | 0.835 |

### openai/gpt-5.2-2025-12-11

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| multiple_choice_radio | 370 | 253 | 328 | 88.6% | 0.886 | 0.886 | 0.886 |


