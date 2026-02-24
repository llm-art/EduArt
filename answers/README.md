# LLM Evaluation Results

## Overview

This directory contains the results of evaluating Large Language Models (LLMs) on Italian art history questions.

- **Creation Date**: 2026-02-24 12:33:28
- **Version**: 0.3
- **Total Exercises**: 860
- **Total Questions**: 860
- **Questions with Images**: 426

## Available Models

| Model Name | Version | Input Cost ($/1M) | Output Cost ($/1M) | Reasoning |
|------------|---------|-------------------|--------------------|-----------|
| google/gemini-3-flash-preview | N/A | $0.50 | $3.00 | ✗ |
| google/gemini-3-pro-preview | N/A | $2.00 | $12.00 | ✗ |
| harvard/us.anthropic.claude-sonnet-4-5-20250929-v1:0 | N/A | $3.00 | $15.00 | ✗ |
| harvard/us.mistral.pixtral-large-2502-v1:0 | N/A | $2.00 | $6.00 | ✗ |
| openai/gpt-4.1-2025-04-14 | 2025-04-14 | $2.00 | $8.00 | ✗ |
| openai/gpt-5-mini-2025-08-07 | 2025-08-07 | $0.25 | $2.00 | ✗ |
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

- **positioning**: 108 questions
- **true_false**: 72 questions
- **select_errors**: 48 questions
- **multiple_choice_check**: 116 questions
- **completion_open**: 76 questions
- **multiple_choice_radio**: 370 questions
- **completion_closed**: 70 questions

## Model Performance Summary

| Model | Accuracy | Correct/Total | Input Tokens | Output Tokens | Actual Cost |
|-------|----------|---------------|--------------|---------------|-------------|
| google/gemini-3-flash-preview | 73.4% | 608/860 | 1,121,319 | 1,196,610 | $4.1505 |
| google/gemini-3-pro-preview | 65.5% | 159/241 | 283,245 | 548,612 | $7.1498 |
| harvard/us.anthropic.claude-sonnet-4-5-20250929-v1:0 | 65.5% | 564/860 | 1,084,355 | 83,907 | $4.5117 |
| harvard/us.mistral.pixtral-large-2502-v1:0 | 35.6% | 313/860 | 796,928 | 99,169 | $2.1889 |
| openai/gpt-4.1-2025-04-14 | 63.9% | 562/860 | 917,966 | 55,484 | $2.2798 |
| openai/gpt-5-mini-2025-08-07 | 62.0% | 534/860 | 967,675 | 734,559 | $1.7110 |
| openai/gpt-5.2-2025-12-11 | 51.3% | 440/860 | 970,317 | 52,211 | $2.4290 |

## Performance by Model and Question Type

### google/gemini-3-flash-preview

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| completion_closed | 70 | 21 | 50 | 71.4% | 0.845 | 0.845 | 0.845 |
| completion_open | 76 | 10 | 11 | 14.5% | 0.611 | 0.611 | 0.611 |
| multiple_choice_check | 116 | 92 | 105 | 90.5% | 0.937 | 0.951 | 0.940 |
| multiple_choice_radio | 370 | 253 | 357 | 96.5% | 0.965 | 0.965 | 0.965 |
| positioning | 108 | 9 | 76 | 70.4% | 0.763 | 0.763 | 0.763 |
| select_errors | 48 | 13 | 0 | 0.0% | - | - | - |
| true_false | 72 | 28 | 9 | 12.5% | 0.402 | 0.402 | 0.402 |

**By Disciplinary Domain**

| Disciplinary Domain | Questions | Correct | Accuracy | Precision | Recall | F1 |
|---------------------|-----------|---------|----------|-----------|--------|----|
| architectural_history | 167 | 130 | 77.8% | 0.831 | 0.831 | 0.831 |
| art_history | 693 | 478 | 69.0% | 0.801 | 0.804 | 0.802 |

**By Language**

| Language | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------|-----------|---------|----------|-----------|--------|----|
| en | 203 | 201 | 99.0% | 0.990 | 0.990 | 0.990 |
| it | 657 | 407 | 61.9% | 0.745 | 0.748 | 0.746 |

**By Epistemic Level**

| Epistemic Level | Questions | Correct | Accuracy | Precision | Recall | F1 |
|-----------------|-----------|---------|----------|-----------|--------|----|
| contextual_knowledge | 313 | 191 | 61.0% | 0.751 | 0.753 | 0.751 |
| factual_identification | 504 | 393 | 78.0% | 0.860 | 0.861 | 0.860 |
| interpretive_reasoning | 43 | 24 | 55.8% | 0.573 | 0.590 | 0.580 |

**By Cultural Tradition**

| Cultural Tradition | Questions | Correct | Accuracy | Precision | Recall | F1 |
|--------------------|-----------|---------|----------|-----------|--------|----|
| eastern | 2 | 2 | 100.0% | 1.000 | 1.000 | 1.000 |
| middle_east | 23 | 23 | 100.0% | 1.000 | 1.000 | 1.000 |
| western | 835 | 583 | 69.8% | 0.801 | 0.803 | 0.801 |

**By Art Historical Category**

| Art Historical | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------------|-----------|---------|----------|-----------|--------|----|
| authorship | 527 | 329 | 62.4% | 0.743 | 0.746 | 0.744 |
| materials_and_techniques | 219 | 143 | 65.3% | 0.813 | 0.815 | 0.813 |
| object_and_work_type | 357 | 247 | 69.2% | 0.804 | 0.807 | 0.805 |
| style_and_period | 570 | 360 | 63.2% | 0.761 | 0.763 | 0.761 |
| subject_matter_and_iconography | 411 | 266 | 64.7% | 0.766 | 0.770 | 0.767 |

### google/gemini-3-pro-preview

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| completion_closed | 22 | 10 | 17 | 77.3% | 0.886 | 0.886 | 0.886 |
| completion_open | 35 | 5 | 15 | 42.9% | 0.750 | 0.750 | 0.750 |
| multiple_choice_check | 43 | 35 | 39 | 90.7% | 0.932 | 0.884 | 0.900 |
| multiple_choice_radio | 52 | 19 | 49 | 94.2% | 0.942 | 0.942 | 0.942 |
| positioning | 45 | 1 | 37 | 82.2% | 0.856 | 0.856 | 0.856 |
| select_errors | 15 | 6 | 0 | 0.0% | - | - | - |
| true_false | 29 | 8 | 2 | 6.9% | 0.290 | 0.290 | 0.290 |

**By Disciplinary Domain**

| Disciplinary Domain | Questions | Correct | Accuracy | Precision | Recall | F1 |
|---------------------|-----------|---------|----------|-----------|--------|----|
| architectural_history | 53 | 39 | 73.6% | 0.780 | 0.780 | 0.780 |
| art_history | 188 | 120 | 63.8% | 0.747 | 0.735 | 0.739 |

**By Language**

| Language | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------|-----------|---------|----------|-----------|--------|----|
| it | 241 | 159 | 66.0% | 0.754 | 0.745 | 0.748 |

**By Epistemic Level**

| Epistemic Level | Questions | Correct | Accuracy | Precision | Recall | F1 |
|-----------------|-----------|---------|----------|-----------|--------|----|
| contextual_knowledge | 106 | 71 | 67.0% | 0.762 | 0.741 | 0.749 |
| factual_identification | 127 | 83 | 65.4% | 0.751 | 0.751 | 0.751 |
| interpretive_reasoning | 8 | 5 | 62.5% | 0.698 | 0.708 | 0.699 |

**By Cultural Tradition**

| Cultural Tradition | Questions | Correct | Accuracy | Precision | Recall | F1 |
|--------------------|-----------|---------|----------|-----------|--------|----|
| western | 241 | 159 | 66.0% | 0.754 | 0.745 | 0.748 |

**By Art Historical Category**

| Art Historical | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------------|-----------|---------|----------|-----------|--------|----|
| authorship | 179 | 115 | 64.2% | 0.729 | 0.721 | 0.723 |
| materials_and_techniques | 56 | 39 | 69.6% | 0.781 | 0.769 | 0.774 |
| object_and_work_type | 111 | 71 | 64.0% | 0.736 | 0.732 | 0.733 |
| style_and_period | 186 | 122 | 65.6% | 0.753 | 0.741 | 0.745 |
| subject_matter_and_iconography | 128 | 78 | 60.9% | 0.717 | 0.705 | 0.708 |

### harvard/us.anthropic.claude-sonnet-4-5-20250929-v1:0

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| completion_closed | 70 | 21 | 40 | 57.1% | 0.864 | 0.864 | 0.864 |
| completion_open | 76 | 10 | 13 | 17.1% | 1.000 | 1.000 | 1.000 |
| multiple_choice_check | 116 | 92 | 79 | 68.1% | 0.833 | 0.845 | 0.818 |
| multiple_choice_radio | 370 | 253 | 345 | 93.2% | 0.932 | 0.932 | 0.932 |
| positioning | 108 | 9 | 79 | 73.1% | 0.868 | 0.868 | 0.868 |
| select_errors | 48 | 13 | 0 | 0.0% | - | - | - |
| true_false | 72 | 28 | 8 | 11.1% | 0.471 | 0.471 | 0.471 |

**By Disciplinary Domain**

| Disciplinary Domain | Questions | Correct | Accuracy | Precision | Recall | F1 |
|---------------------|-----------|---------|----------|-----------|--------|----|
| architectural_history | 167 | 125 | 74.9% | 0.834 | 0.834 | 0.832 |
| art_history | 693 | 439 | 63.3% | 0.800 | 0.802 | 0.797 |

**By Language**

| Language | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------|-----------|---------|----------|-----------|--------|----|
| en | 203 | 197 | 97.0% | 0.970 | 0.970 | 0.970 |
| it | 657 | 367 | 55.9% | 0.750 | 0.753 | 0.747 |

**By Epistemic Level**

| Epistemic Level | Questions | Correct | Accuracy | Precision | Recall | F1 |
|-----------------|-----------|---------|----------|-----------|--------|----|
| contextual_knowledge | 313 | 163 | 52.1% | 0.746 | 0.753 | 0.742 |
| factual_identification | 504 | 383 | 76.0% | 0.863 | 0.861 | 0.861 |
| interpretive_reasoning | 43 | 18 | 41.9% | 0.568 | 0.572 | 0.567 |

**By Cultural Tradition**

| Cultural Tradition | Questions | Correct | Accuracy | Precision | Recall | F1 |
|--------------------|-----------|---------|----------|-----------|--------|----|
| unknown | 860 | 564 | 65.6% | 0.807 | 0.808 | 0.804 |

### harvard/us.mistral.pixtral-large-2502-v1:0

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| completion_closed | 70 | 21 | 11 | 15.7% | 0.275 | 0.275 | 0.275 |
| completion_open | 76 | 10 | 9 | 11.8% | 0.900 | 0.900 | 0.900 |
| multiple_choice_check | 116 | 92 | 40 | 34.5% | 0.613 | 0.688 | 0.636 |
| multiple_choice_radio | 370 | 253 | 218 | 58.9% | 0.589 | 0.589 | 0.589 |
| positioning | 108 | 9 | 30 | 27.8% | 0.760 | 0.760 | 0.760 |
| select_errors | 48 | 13 | 0 | 0.0% | - | - | - |
| true_false | 72 | 28 | 5 | 6.9% | 0.391 | 0.391 | 0.391 |

**By Disciplinary Domain**

| Disciplinary Domain | Questions | Correct | Accuracy | Precision | Recall | F1 |
|---------------------|-----------|---------|----------|-----------|--------|----|
| architectural_history | 167 | 74 | 44.3% | 0.601 | 0.609 | 0.603 |
| art_history | 693 | 239 | 34.5% | 0.523 | 0.535 | 0.527 |

**By Language**

| Language | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------|-----------|---------|----------|-----------|--------|----|
| en | 203 | 104 | 51.2% | 0.512 | 0.512 | 0.512 |
| it | 657 | 209 | 31.8% | 0.547 | 0.562 | 0.552 |

**By Epistemic Level**

| Epistemic Level | Questions | Correct | Accuracy | Precision | Recall | F1 |
|-----------------|-----------|---------|----------|-----------|--------|----|
| contextual_knowledge | 313 | 96 | 30.7% | 0.533 | 0.557 | 0.540 |
| factual_identification | 504 | 210 | 41.7% | 0.564 | 0.568 | 0.565 |
| interpretive_reasoning | 43 | 7 | 16.3% | 0.279 | 0.291 | 0.284 |

**By Cultural Tradition**

| Cultural Tradition | Questions | Correct | Accuracy | Precision | Recall | F1 |
|--------------------|-----------|---------|----------|-----------|--------|----|
| eastern | 2 | 1 | 50.0% | 0.500 | 0.500 | 0.500 |
| middle_east | 23 | 11 | 47.8% | 0.478 | 0.478 | 0.478 |
| western | 835 | 301 | 36.0% | 0.540 | 0.552 | 0.544 |

**By Art Historical Category**

| Art Historical | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------------|-----------|---------|----------|-----------|--------|----|
| authorship | 527 | 154 | 29.2% | 0.530 | 0.549 | 0.536 |
| materials_and_techniques | 219 | 53 | 24.2% | 0.545 | 0.556 | 0.548 |
| object_and_work_type | 357 | 121 | 33.9% | 0.559 | 0.572 | 0.563 |
| style_and_period | 570 | 163 | 28.6% | 0.519 | 0.534 | 0.523 |
| subject_matter_and_iconography | 411 | 124 | 30.2% | 0.501 | 0.520 | 0.507 |

### openai/gpt-4.1-2025-04-14

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| completion_closed | 70 | 21 | 42 | 60.0% | 0.851 | 0.851 | 0.851 |
| completion_open | 76 | 10 | 17 | 22.4% | 1.000 | 1.000 | 1.000 |
| multiple_choice_check | 116 | 92 | 82 | 70.7% | 0.797 | 0.843 | 0.807 |
| multiple_choice_radio | 370 | 253 | 351 | 94.9% | 0.949 | 0.949 | 0.949 |
| positioning | 108 | 9 | 64 | 59.3% | 0.847 | 0.847 | 0.847 |
| select_errors | 48 | 13 | 0 | 0.0% | - | - | - |
| true_false | 72 | 28 | 6 | 8.3% | 0.400 | 0.400 | 0.400 |

**By Disciplinary Domain**

| Disciplinary Domain | Questions | Correct | Accuracy | Precision | Recall | F1 |
|---------------------|-----------|---------|----------|-----------|--------|----|
| architectural_history | 167 | 120 | 71.9% | 0.826 | 0.832 | 0.828 |
| art_history | 693 | 442 | 63.8% | 0.793 | 0.800 | 0.794 |

**By Language**

| Language | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------|-----------|---------|----------|-----------|--------|----|
| en | 203 | 201 | 99.0% | 0.990 | 0.990 | 0.990 |
| it | 657 | 361 | 54.9% | 0.735 | 0.744 | 0.737 |

**By Epistemic Level**

| Epistemic Level | Questions | Correct | Accuracy | Precision | Recall | F1 |
|-----------------|-----------|---------|----------|-----------|--------|----|
| contextual_knowledge | 313 | 162 | 51.8% | 0.732 | 0.742 | 0.734 |
| factual_identification | 504 | 381 | 75.6% | 0.861 | 0.865 | 0.862 |
| interpretive_reasoning | 43 | 19 | 44.2% | 0.530 | 0.556 | 0.541 |

**By Cultural Tradition**

| Cultural Tradition | Questions | Correct | Accuracy | Precision | Recall | F1 |
|--------------------|-----------|---------|----------|-----------|--------|----|
| eastern | 2 | 2 | 100.0% | 1.000 | 1.000 | 1.000 |
| middle_east | 23 | 23 | 100.0% | 1.000 | 1.000 | 1.000 |
| western | 835 | 537 | 64.3% | 0.793 | 0.800 | 0.794 |

**By Art Historical Category**

| Art Historical | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------------|-----------|---------|----------|-----------|--------|----|
| authorship | 527 | 284 | 53.9% | 0.727 | 0.737 | 0.730 |
| materials_and_techniques | 219 | 131 | 59.8% | 0.810 | 0.825 | 0.815 |
| object_and_work_type | 357 | 224 | 62.7% | 0.808 | 0.816 | 0.811 |
| style_and_period | 570 | 308 | 54.0% | 0.743 | 0.751 | 0.744 |
| subject_matter_and_iconography | 411 | 228 | 55.5% | 0.736 | 0.750 | 0.740 |

### openai/gpt-5-mini-2025-08-07

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| completion_closed | 70 | 21 | 35 | 50.0% | 0.814 | 0.814 | 0.814 |
| completion_open | 76 | 10 | 9 | 11.8% | 0.900 | 0.900 | 0.900 |
| multiple_choice_check | 116 | 92 | 83 | 71.6% | 0.831 | 0.835 | 0.820 |
| multiple_choice_radio | 370 | 253 | 335 | 90.5% | 0.905 | 0.905 | 0.905 |
| positioning | 108 | 9 | 65 | 60.2% | 0.827 | 0.827 | 0.827 |
| select_errors | 48 | 13 | 0 | 0.0% | - | - | - |
| true_false | 72 | 28 | 7 | 9.7% | 0.471 | 0.471 | 0.471 |

**By Disciplinary Domain**

| Disciplinary Domain | Questions | Correct | Accuracy | Precision | Recall | F1 |
|---------------------|-----------|---------|----------|-----------|--------|----|
| architectural_history | 167 | 123 | 73.7% | 0.826 | 0.827 | 0.826 |
| art_history | 693 | 411 | 59.3% | 0.771 | 0.771 | 0.769 |

**By Language**

| Language | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------|-----------|---------|----------|-----------|--------|----|
| en | 203 | 200 | 98.5% | 0.985 | 0.985 | 0.985 |
| it | 657 | 334 | 50.8% | 0.712 | 0.712 | 0.710 |

**By Epistemic Level**

| Epistemic Level | Questions | Correct | Accuracy | Precision | Recall | F1 |
|-----------------|-----------|---------|----------|-----------|--------|----|
| contextual_knowledge | 313 | 161 | 51.4% | 0.757 | 0.759 | 0.755 |
| factual_identification | 504 | 354 | 70.2% | 0.816 | 0.815 | 0.815 |
| interpretive_reasoning | 43 | 19 | 44.2% | 0.543 | 0.559 | 0.550 |

**By Cultural Tradition**

| Cultural Tradition | Questions | Correct | Accuracy | Precision | Recall | F1 |
|--------------------|-----------|---------|----------|-----------|--------|----|
| eastern | 2 | 2 | 100.0% | 1.000 | 1.000 | 1.000 |
| middle_east | 23 | 23 | 100.0% | 1.000 | 1.000 | 1.000 |
| western | 835 | 509 | 61.0% | 0.775 | 0.775 | 0.773 |

**By Art Historical Category**

| Art Historical | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------------|-----------|---------|----------|-----------|--------|----|
| authorship | 527 | 263 | 49.9% | 0.708 | 0.711 | 0.707 |
| materials_and_techniques | 219 | 130 | 59.4% | 0.818 | 0.817 | 0.815 |
| object_and_work_type | 357 | 218 | 61.1% | 0.786 | 0.787 | 0.785 |
| style_and_period | 570 | 298 | 52.3% | 0.734 | 0.734 | 0.732 |
| subject_matter_and_iconography | 411 | 227 | 55.2% | 0.742 | 0.747 | 0.742 |

### openai/gpt-5.2-2025-12-11

| Question Type | Questions | With Images | Correct | Accuracy | Precision | Recall | F1 |
|---------------|-----------|-------------|---------|----------|-----------|--------|----|
| completion_closed | 70 | 21 | 2 | 2.9% | 0.029 | 0.029 | 0.029 |
| completion_open | 76 | 10 | 9 | 11.8% | 1.000 | 1.000 | 1.000 |
| multiple_choice_check | 116 | 92 | 69 | 59.5% | 0.770 | 0.795 | 0.773 |
| multiple_choice_radio | 370 | 253 | 326 | 88.1% | 0.881 | 0.881 | 0.881 |
| positioning | 108 | 9 | 25 | 23.1% | 0.296 | 0.296 | 0.296 |
| select_errors | 48 | 13 | 0 | 0.0% | - | - | - |
| true_false | 72 | 28 | 9 | 12.5% | 0.406 | 0.406 | 0.406 |

**By Disciplinary Domain**

| Disciplinary Domain | Questions | Correct | Accuracy | Precision | Recall | F1 |
|---------------------|-----------|---------|----------|-----------|--------|----|
| architectural_history | 167 | 101 | 60.5% | 0.672 | 0.678 | 0.674 |
| art_history | 693 | 339 | 48.9% | 0.601 | 0.604 | 0.601 |

**By Language**

| Language | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------|-----------|---------|----------|-----------|--------|----|
| en | 203 | 192 | 94.6% | 0.946 | 0.946 | 0.946 |
| it | 657 | 248 | 37.7% | 0.501 | 0.506 | 0.501 |

**By Epistemic Level**

| Epistemic Level | Questions | Correct | Accuracy | Precision | Recall | F1 |
|-----------------|-----------|---------|----------|-----------|--------|----|
| contextual_knowledge | 313 | 125 | 39.9% | 0.539 | 0.544 | 0.539 |
| factual_identification | 504 | 299 | 59.3% | 0.671 | 0.673 | 0.671 |
| interpretive_reasoning | 43 | 16 | 37.2% | 0.484 | 0.500 | 0.491 |

**By Cultural Tradition**

| Cultural Tradition | Questions | Correct | Accuracy | Precision | Recall | F1 |
|--------------------|-----------|---------|----------|-----------|--------|----|
| eastern | 2 | 2 | 100.0% | 1.000 | 1.000 | 1.000 |
| middle_east | 23 | 23 | 100.0% | 1.000 | 1.000 | 1.000 |
| western | 835 | 415 | 49.7% | 0.602 | 0.606 | 0.603 |

**By Art Historical Category**

| Art Historical | Questions | Correct | Accuracy | Precision | Recall | F1 |
|----------------|-----------|---------|----------|-----------|--------|----|
| authorship | 527 | 194 | 36.8% | 0.488 | 0.495 | 0.490 |
| materials_and_techniques | 219 | 91 | 41.6% | 0.568 | 0.571 | 0.568 |
| object_and_work_type | 357 | 166 | 46.5% | 0.597 | 0.602 | 0.598 |
| style_and_period | 570 | 226 | 39.6% | 0.530 | 0.533 | 0.529 |
| subject_matter_and_iconography | 411 | 168 | 40.9% | 0.558 | 0.563 | 0.558 |


