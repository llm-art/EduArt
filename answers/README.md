# LLM Evaluation Results

## Overview

This directory contains the results of evaluating Large Language Models (LLMs) on Italian art history questions.

- **Creation Date**: 2026-01-15 19:16:08
- **Version**: 0.3
- **Total Exercises**: 370
- **Total Questions**: 370
- **Questions with Images**: 253

## Available Models

| Model Name | Version | Input Cost ($/1M) | Output Cost ($/1M) | Reasoning |
|------------|---------|-------------------|--------------------|-----------|
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

## Model Performance Summary

| Model | Accuracy | Correct/Total | Input Tokens | Output Tokens | Actual Cost |
|-------|----------|---------------|--------------|---------------|-------------|
| harvard/us.anthropic.claude-sonnet-4-5-20250929-v1:0 | 72.4% | 268/370 | 538,947 | 33,898 | $2.1253 |
| harvard/us.mistral.pixtral-large-2502-v1:0 | 54.3% | 201/370 | 246,088 | 22,190 | $0.6253 |
| openai/gpt-4.1-2025-04-14 | 94.1% | 348/370 | 424,750 | 10,501 | $0.9335 |
| openai/gpt-5-mini-2025-08-07 | 84.6% | 313/370 | 492,113 | 193,975 | $0.5110 |
| openai/gpt-5-nano-2025-08-07 | 83.5% | 309/370 | 562,893 | 547,207 | $0.2470 |
| openai/gpt-5.2-2025-12-11 | 88.6% | 328/370 | 528,743 | 8,521 | $1.0446 |

## Performance by Model and Question Type

### harvard/us.anthropic.claude-sonnet-4-5-20250929-v1:0

| Question Type | Questions | With Images | Correct | Accuracy |
|---------------|-----------|-------------|---------|----------|
| multiple_choice_radio | 370 | 253 | 268 | 72.4% |

### harvard/us.mistral.pixtral-large-2502-v1:0

| Question Type | Questions | With Images | Correct | Accuracy |
|---------------|-----------|-------------|---------|----------|
| multiple_choice_radio | 370 | 253 | 201 | 54.3% |

### openai/gpt-4.1-2025-04-14

| Question Type | Questions | With Images | Correct | Accuracy |
|---------------|-----------|-------------|---------|----------|
| multiple_choice_radio | 370 | 253 | 348 | 94.1% |

### openai/gpt-5-mini-2025-08-07

| Question Type | Questions | With Images | Correct | Accuracy |
|---------------|-----------|-------------|---------|----------|
| multiple_choice_radio | 370 | 253 | 313 | 84.6% |

### openai/gpt-5-nano-2025-08-07

| Question Type | Questions | With Images | Correct | Accuracy |
|---------------|-----------|-------------|---------|----------|
| multiple_choice_radio | 370 | 253 | 309 | 83.5% |

### openai/gpt-5.2-2025-12-11

| Question Type | Questions | With Images | Correct | Accuracy |
|---------------|-----------|-------------|---------|----------|
| multiple_choice_radio | 370 | 253 | 328 | 88.6% |


