# Evaluation Results

Generated: 2026-03-27 15:01

## Metrics Overview

Each question type uses a specific metric depending on the task:

- **Single-choice questions** → Exact Match (binary, cleanest metric).
- **Multi-choice and error detection** → F1 score (balances precision and recall).
- **True/False** → evaluated per statement (not per item) to avoid bias from longer questions.
- **Positioning and completion tasks** → accuracy per element/blank.
- **Open-text completion** is stricter (exact matching), so results should be interpreted with caution.

## Leaderboard (Macro-Averaged Score)

| Rank | Model | Macro Avg | MCQ Exact Match | N Evaluated |
|------|-------|-----------|-----------------|-------------|
| 1 | `google_gemini-3.1-pro-preview` | **83.8%** | 98.8% | 375 |
| 2 | `google_gemini-3-flash-preview` | **75.4%** | 96.8% | 871 |
| 3 | `harvard_us.anthropic.claude-opus-4-6-v1` | **67.3%** | 94.6% | 871 |
| 4 | `harvard_us.anthropic.claude-sonnet-4-6` | **64.8%** | 94.3% | 871 |
| 5 | `google_gemini-3.1-flash-lite-preview` | **62.8%** | 92.4% | 871 |
| 6 | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | **53.1%** | 84.0% | 871 |
| 7 | `harvard_us.mistral.pixtral-large-2502-v1:0` | **29.1%** | 28.6% | 871 |
| 8 | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | **12.5%** | 17.0% | 871 |

## Results by Question Type

| Model | MCQ Radio (Exact Match) | MCQ Check (F1) | True/False (Stmt Accuracy) | Positioning (Element Accuracy) | Completion (Closed) (Blank Accuracy) | Completion (Open) (Blank Accuracy) | Select Errors (F1) |
|-------|------|------|------|------|------|------|------|
| `google_gemini-3.1-pro-preview` | 98.8% (n=241) | 85.9% (n=29) | 64.2% (n=25) | 77.8% (n=27) | 94.1% (n=17) | 80.4% (n=26) | 85.6% (n=10) |
| `google_gemini-3-flash-preview` | 96.8% (n=370) | 86.9% (n=117) | 58.9% (n=83) | 73.0% (n=108) | 80.3% (n=69) | 68.2% (n=75) | 63.5% (n=49) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 94.6% (n=370) | 60.9% (n=117) | 82.5% (n=83) | 85.6% (n=108) | 85.9% (n=69) | 23.9% (n=75) | 37.5% (n=49) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 94.3% (n=370) | 85.2% (n=117) | 77.5% (n=83) | 77.3% (n=108) | 47.6% (n=69) | 65.8% (n=75) | 6.2% (n=49) |
| `google_gemini-3.1-flash-lite-preview` | 92.4% (n=370) | 79.1% (n=117) | 76.1% (n=83) | 70.0% (n=108) | 47.2% (n=69) | 63.3% (n=75) | 11.3% (n=49) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 84.0% (n=370) | 75.7% (n=117) | 73.2% (n=83) | 43.0% (n=108) | 26.1% (n=69) | 62.5% (n=75) | 7.5% (n=49) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 28.6% (n=370) | 30.8% (n=117) | 57.7% (n=83) | 37.4% (n=108) | 19.1% (n=69) | 27.4% (n=75) | 3.0% (n=49) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 17.0% (n=370) | 9.4% (n=117) | 49.8% (n=83) | 0.0% (n=108) | 5.8% (n=69) | 4.6% (n=75) | 0.9% (n=49) |

## Detailed Results with 95% CI

**MCQ Radio** (Primary metric: Exact Match)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 98.8% | [96.4%, 99.6%] | 241 |
| `google_gemini-3-flash-preview` | 96.8% | [94.4%, 98.1%] | 370 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 94.6% | [91.8%, 96.5%] | 370 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 94.3% | [91.5%, 96.3%] | 370 |
| `google_gemini-3.1-flash-lite-preview` | 92.4% | [89.3%, 94.7%] | 370 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 84.0% | [80.0%, 87.4%] | 370 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 28.6% | [24.3%, 33.5%] | 370 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 17.0% | [13.5%, 21.2%] | 370 |

**MCQ Check** (Primary metric: F1)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 85.9% | [69.1%, 94.3%] | 29 |
| `google_gemini-3-flash-preview` | 86.9% | [79.5%, 91.8%] | 117 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 60.9% | [51.9%, 69.3%] | 117 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 85.2% | [77.7%, 90.5%] | 117 |
| `google_gemini-3.1-flash-lite-preview` | 79.1% | [70.9%, 85.5%] | 117 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 75.7% | [67.2%, 82.6%] | 117 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 30.8% | [23.1%, 39.6%] | 117 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 9.4% | [5.3%, 16.1%] | 117 |

**True/False** (Primary metric: Stmt Accuracy)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 64.2% | [44.7%, 79.9%] | 25 |
| `google_gemini-3-flash-preview` | 58.9% | [48.2%, 68.9%] | 83 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 82.5% | [72.9%, 89.2%] | 83 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 77.5% | [67.4%, 85.1%] | 83 |
| `google_gemini-3.1-flash-lite-preview` | 76.1% | [65.9%, 84.0%] | 83 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 73.2% | [62.8%, 81.6%] | 83 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 57.7% | [47.0%, 67.8%] | 83 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 49.8% | [39.3%, 60.3%] | 83 |

**Positioning** (Primary metric: Element Accuracy)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 77.8% | [59.2%, 89.4%] | 27 |
| `google_gemini-3-flash-preview` | 73.0% | [63.9%, 80.5%] | 108 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 85.6% | [77.7%, 91.0%] | 108 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 77.3% | [68.5%, 84.2%] | 108 |
| `google_gemini-3.1-flash-lite-preview` | 70.0% | [60.8%, 77.9%] | 108 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 43.0% | [34.0%, 52.4%] | 108 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 37.4% | [28.8%, 46.8%] | 108 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 0.0% | [0.0%, 3.4%] | 108 |

**Completion (Closed)** (Primary metric: Blank Accuracy)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 94.1% | [73.0%, 99.0%] | 17 |
| `google_gemini-3-flash-preview` | 80.3% | [69.4%, 87.9%] | 69 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 85.9% | [75.8%, 92.2%] | 69 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 47.6% | [36.2%, 59.2%] | 69 |
| `google_gemini-3.1-flash-lite-preview` | 47.2% | [35.9%, 58.8%] | 69 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 26.1% | [17.2%, 37.5%] | 69 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 19.1% | [11.5%, 29.9%] | 69 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 5.8% | [2.3%, 14.0%] | 69 |

**Completion (Open)** (Primary metric: Blank Accuracy)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 80.4% | [61.8%, 91.3%] | 26 |
| `google_gemini-3-flash-preview` | 68.2% | [57.0%, 77.6%] | 75 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 23.9% | [15.7%, 34.7%] | 75 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 65.8% | [54.5%, 75.5%] | 75 |
| `google_gemini-3.1-flash-lite-preview` | 63.3% | [51.9%, 73.3%] | 75 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 62.5% | [51.2%, 72.6%] | 75 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 27.4% | [18.6%, 38.5%] | 75 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 4.6% | [1.7%, 11.9%] | 75 |

**Select Errors** (Primary metric: F1)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 85.6% | [54.8%, 96.7%] | 10 |
| `google_gemini-3-flash-preview` | 63.5% | [49.5%, 75.6%] | 49 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 37.5% | [25.4%, 51.5%] | 49 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 6.2% | [2.1%, 16.6%] | 49 |
| `google_gemini-3.1-flash-lite-preview` | 11.3% | [5.1%, 23.1%] | 49 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 7.5% | [2.9%, 18.4%] | 49 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 3.0% | [0.7%, 12.1%] | 49 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 0.9% | [0.1%, 8.9%] | 49 |

## Cross-Condition Comparison: `default` vs `motivation`

Paired comparison on questions answered under both conditions. The motivation condition adds chain-of-thought reasoning to the prompt.

### Overall (Paired Scores)

| Model | N Paired | Default | Motivation | Diff | 95% CI | p-value | Improved | Same | Degraded |
|-------|----------|---------|------------|------|--------|---------|----------|------|----------|
| `google_gemini-3-flash-preview` | 871 | 83.2% | 73.3% | -10.0pp | [-12.3, -7.7]pp | 0.000 \* | 48 | 670 | 153 |
| `google_gemini-3.1-flash-lite-preview` | 871 | 75.6% | 62.8% | -12.8pp | [-15.1, -10.5]pp | 0.000 \* | 44 | 629 | 198 |
| `google_gemini-3.1-pro-preview` | 375 | 92.1% | 92.1% | -0.0pp | [-1.1, +1.1]pp | 0.994 | 11 | 355 | 9 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 66.0% | 66.7% | +0.7pp | [-0.8, +2.1]pp | 0.368 | 60 | 749 | 62 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 77.8% | 79.4% | +1.6pp | [-0.0, +3.2]pp | 0.053 | 67 | 759 | 45 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 78.3% | 80.9% | +2.6pp | [+1.0, +4.2]pp | 0.001 \* | 61 | 763 | 47 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 14.1% | 12.5% | -1.7pp | [-3.2, -0.1]pp | 0.042 \* | 24 | 802 | 45 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 30.5% | 28.6% | -1.9pp | [-4.8, +1.0]pp | 0.204 | 136 | 576 | 159 |

### By Question Type (Paired)

| Model | Type | N | Default | Motivation | Diff |
|-------|------|---|---------|------------|------|
| `google_gemini-3-flash-preview` | Completion (Closed) | 69 | 80.3% | 44.2% | -36.0pp |
| `google_gemini-3-flash-preview` | Completion (Open) | 75 | 68.2% | 66.9% | -1.3pp |
| `google_gemini-3-flash-preview` | MCQ Check | 117 | 86.9% | 71.5% | -15.4pp |
| `google_gemini-3-flash-preview` | MCQ Radio | 370 | 96.8% | 94.9% | -1.9pp |
| `google_gemini-3-flash-preview` | Positioning | 108 | 73.0% | 45.8% | -27.2pp |
| `google_gemini-3-flash-preview` | Select Errors | 49 | 63.5% | 54.8% | -8.8pp |
| `google_gemini-3-flash-preview` | True/False | 83 | 58.9% | 56.0% | -2.9pp |
| `google_gemini-3.1-flash-lite-preview` | Completion (Closed) | 69 | 47.2% | 12.2% | -35.0pp |
| `google_gemini-3.1-flash-lite-preview` | Completion (Open) | 75 | 63.3% | 60.3% | -3.0pp |
| `google_gemini-3.1-flash-lite-preview` | MCQ Check | 117 | 79.1% | 45.8% | -33.3pp |
| `google_gemini-3.1-flash-lite-preview` | MCQ Radio | 370 | 92.4% | 90.0% | -2.4pp |
| `google_gemini-3.1-flash-lite-preview` | Positioning | 108 | 70.0% | 47.3% | -22.7pp |
| `google_gemini-3.1-flash-lite-preview` | Select Errors | 49 | 11.3% | 9.2% | -2.0pp |
| `google_gemini-3.1-flash-lite-preview` | True/False | 83 | 76.1% | 62.0% | -14.1pp |
| `google_gemini-3.1-pro-preview` | Completion (Closed) | 17 | 94.1% | 94.1% | +0.0pp |
| `google_gemini-3.1-pro-preview` | Completion (Open) | 26 | 80.4% | 79.1% | -1.3pp |
| `google_gemini-3.1-pro-preview` | MCQ Check | 29 | 85.9% | 84.8% | -1.1pp |
| `google_gemini-3.1-pro-preview` | MCQ Radio | 241 | 98.8% | 98.8% | +0.0pp |
| `google_gemini-3.1-pro-preview` | Positioning | 27 | 77.8% | 81.5% | +3.7pp |
| `google_gemini-3.1-pro-preview` | Select Errors | 10 | 85.6% | 85.9% | +0.3pp |
| `google_gemini-3.1-pro-preview` | True/False | 25 | 64.2% | 62.6% | -1.6pp |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | Completion (Closed) | 69 | 26.1% | 23.7% | -2.4pp |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | Completion (Open) | 75 | 62.5% | 61.9% | -0.6pp |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | MCQ Check | 117 | 75.7% | 76.5% | +0.9pp |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | MCQ Radio | 370 | 84.0% | 83.2% | -0.8pp |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | Positioning | 108 | 43.0% | 55.9% | +12.9pp |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | Select Errors | 49 | 7.5% | 5.4% | -2.2pp |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | True/False | 83 | 73.2% | 69.5% | -3.7pp |
| `harvard_us.anthropic.claude-opus-4-6-v1` | Completion (Closed) | 69 | 85.9% | 85.6% | -0.2pp |
| `harvard_us.anthropic.claude-opus-4-6-v1` | Completion (Open) | 75 | 23.9% | 40.0% | +16.0pp |
| `harvard_us.anthropic.claude-opus-4-6-v1` | MCQ Check | 117 | 60.9% | 62.8% | +1.9pp |
| `harvard_us.anthropic.claude-opus-4-6-v1` | MCQ Radio | 370 | 94.6% | 95.7% | +1.1pp |
| `harvard_us.anthropic.claude-opus-4-6-v1` | Positioning | 108 | 85.6% | 85.1% | -0.5pp |
| `harvard_us.anthropic.claude-opus-4-6-v1` | Select Errors | 49 | 37.5% | 30.3% | -7.2pp |
| `harvard_us.anthropic.claude-opus-4-6-v1` | True/False | 83 | 82.5% | 82.3% | -0.1pp |
| `harvard_us.anthropic.claude-sonnet-4-6` | Completion (Closed) | 69 | 47.6% | 88.5% | +40.9pp |
| `harvard_us.anthropic.claude-sonnet-4-6` | Completion (Open) | 75 | 65.8% | 60.2% | -5.6pp |
| `harvard_us.anthropic.claude-sonnet-4-6` | MCQ Check | 117 | 85.2% | 84.1% | -1.1pp |
| `harvard_us.anthropic.claude-sonnet-4-6` | MCQ Radio | 370 | 94.3% | 94.0% | -0.3pp |
| `harvard_us.anthropic.claude-sonnet-4-6` | Positioning | 108 | 77.3% | 77.2% | -0.1pp |
| `harvard_us.anthropic.claude-sonnet-4-6` | Select Errors | 49 | 6.2% | 9.2% | +3.0pp |
| `harvard_us.anthropic.claude-sonnet-4-6` | True/False | 83 | 77.5% | 76.8% | -0.7pp |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | Completion (Closed) | 69 | 5.8% | 0.0% | -5.8pp |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | Completion (Open) | 75 | 4.6% | 2.8% | -1.8pp |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | MCQ Check | 117 | 9.4% | 5.0% | -4.4pp |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | MCQ Radio | 370 | 17.0% | 16.0% | -1.1pp |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | Positioning | 108 | 0.0% | 0.0% | +0.0pp |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | Select Errors | 49 | 0.9% | 1.3% | +0.3pp |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | True/False | 83 | 49.8% | 49.8% | +0.0pp |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | Completion (Closed) | 69 | 19.1% | 28.4% | +9.3pp |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | Completion (Open) | 75 | 27.4% | 15.4% | -12.0pp |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | MCQ Check | 117 | 30.8% | 35.9% | +5.1pp |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | MCQ Radio | 370 | 28.6% | 24.6% | -4.0pp |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | Positioning | 108 | 37.4% | 33.2% | -4.1pp |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | Select Errors | 49 | 3.0% | 2.4% | -0.7pp |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | True/False | 83 | 57.7% | 57.7% | +0.0pp |

> **Note**: Diff is in percentage points (pp). p-values from paired t-test. \* = significant at α=0.05.

## Item Analysis (CTT & IRT)

Analysis across **16 examinees** (model × condition) and **871 items**.

### Classical Test Theory (CTT)

| Statistic | Mean | SD | Min | Max |
|-----------|------|----|-----|-----|
| Item Difficulty (p) | 0.607 | 0.219 | 0.000 | 1.000 |
| Discrimination (r_pb) | 0.652 | 0.234 | -0.203 | 0.974 |

**Item Difficulty Distribution**

| Category | p Range | Count |
|----------|---------|-------|
| Very Easy | ≥ 0.90 | 34 |
| Easy | 0.70 – 0.89 | 360 |
| Medium | 0.30 – 0.69 | 385 |
| Hard | 0.10 – 0.29 | 70 |
| Very Hard | < 0.10 | 22 |

**Item Discrimination Distribution**

| Category | r_pb Range | Count |
|----------|------------|-------|
| Good | ≥ 0.30 | 777 |
| Fair | 0.10 – 0.29 | 55 |
| Poor | < 0.10 | 11 |

### Item Response Theory — Rasch Model (1PL)

- Converged: Yes (21 iterations)
- Person Separation Reliability: 0.996
- Estimable items: 843 / 871 (28 items with zero variance excluded)
- Item difficulty (b) range: [-6.00, 6.00]

**Examinee Ability Estimates (θ)**

| Model / Condition | θ |
|-------------------|---|
| `google_gemini-3.1-pro-preview/default` | +2.044 |
| `google_gemini-3.1-pro-preview/motivation` | +2.043 |
| `google_gemini-3-flash-preview/default` | +1.482 |
| `harvard_us.anthropic.claude-sonnet-4-6/motivation` | +1.246 |
| `harvard_us.anthropic.claude-opus-4-6-v1/motivation` | +1.114 |
| `harvard_us.anthropic.claude-sonnet-4-6/default` | +1.013 |
| `harvard_us.anthropic.claude-opus-4-6-v1/default` | +0.974 |
| `google_gemini-3.1-flash-lite-preview/default` | +0.796 |
| `google_gemini-3-flash-preview/motivation` | +0.611 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0/motivation` | +0.145 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0/default` | +0.102 |
| `google_gemini-3.1-flash-lite-preview/motivation` | -0.107 |
| `harvard_us.mistral.pixtral-large-2502-v1:0/default` | -2.101 |
| `harvard_us.mistral.pixtral-large-2502-v1:0/motivation` | -2.229 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0/default` | -3.468 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0/motivation` | -3.666 |

**10 Hardest Items** (lowest p-value)

| Question | Type | p | r_pb | b (Rasch) |
|----------|------|---|------|-----------|
| 0316 | positioning | 0.000 | — | 6.00 |
| 0350 | completion_closed | 0.000 | — | 6.00 |
| 0376 | positioning | 0.000 | — | 6.00 |
| 0560 | positioning | 0.000 | — | 6.00 |
| 0575 | select_errors | 0.000 | — | 6.00 |
| 0678 | multiple_choice_radio | 0.000 | — | 6.00 |
| 0679 | multiple_choice_radio | 0.000 | — | 6.00 |
| 0681 | multiple_choice_radio | 0.000 | — | 6.00 |
| 0689 | multiple_choice_radio | 0.000 | — | 6.00 |
| 0811 | select_errors | 0.000 | — | 6.00 |

**10 Easiest Items** (highest p-value)

| Question | Type | p | r_pb | b (Rasch) |
|----------|------|---|------|-----------|
| 0185 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0342 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0557 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0566 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0685 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0687 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0692 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0695 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0808 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0843 | multiple_choice_radio | 1.000 | — | -6.00 |

**10 Most Discriminating Items** (highest r_pb)

| Question | Type | p | r_pb | b (Rasch) |
|----------|------|---|------|-----------|
| 0712 | multiple_choice_check | 0.665 | 0.974 | -1.17 |
| 0603 | multiple_choice_check | 0.758 | 0.970 | -2.02 |
| 0290 | multiple_choice_check | 0.720 | 0.965 | -1.33 |
| 0528 | multiple_choice_check | 0.704 | 0.963 | -1.51 |
| 0593 | multiple_choice_check | 0.700 | 0.962 | -1.47 |
| 0642 | true_false | 0.829 | 0.959 | -2.78 |
| 0862 | multiple_choice_check | 0.476 | 0.959 | 0.11 |
| 0396 | multiple_choice_radio | 0.714 | 0.959 | -1.60 |
| 0421 | multiple_choice_check | 0.714 | 0.959 | -1.60 |
| 0441 | multiple_choice_radio | 0.714 | 0.959 | -1.60 |

> **Note**: Rasch (1PL) via JMLE. With N≤10 examinees, estimates have high uncertainty. Items with zero variance across examinees are non-estimable.

## Cross-Model Comparison — McNemar's Test (`default`)

Pairwise test of whether two models differ significantly on the same items (binarised at score ≥ 0.5).

| Model A | Model B | N | A✓B✗ | A✗B✓ | χ² | p-value | Favours |
|---------|---------|---|------|------|----|---------|---------| 
| `google_gemini-3-flash-preview` | `google_gemini-3.1-flash-lite-preview` | 871 | 123 | 59 | 21.81 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `google_gemini-3.1-pro-preview` | 375 | 5 | 20 | 7.84 | 0.0051 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 189 | 38 | 99.12 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 116 | 66 | 13.19 | 0.0003 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 99 | 64 | 7.09 | 0.0077 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 633 | 3 | 622.08 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 488 | 26 | 413.46 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3.1-flash-lite-preview` | `google_gemini-3.1-pro-preview` | 375 | 11 | 32 | 9.30 | 0.0023 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 134 | 47 | 40.86 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 100 | 114 | 0.79 | 0.3742 | harvard_us.anthropic.claude-opus-4-6-v1 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 50 | 79 | 6.08 | 0.0137 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 569 | 3 | 558.09 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 434 | 36 | 335.34 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 375 | 70 | 7 | 49.92 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 375 | 35 | 7 | 17.36 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 375 | 29 | 10 | 8.31 | 0.0039 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 375 | 301 | 0 | 299.00 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 375 | 234 | 2 | 226.11 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 81 | 182 | 38.02 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 32 | 148 | 73.47 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 486 | 7 | 463.46 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 359 | 48 | 236.12 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 85 | 100 | 1.06 | 0.3033 | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 594 | 14 | 551.38 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 447 | 35 | 350.46 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 601 | 6 | 581.28 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 448 | 21 | 386.94 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 54 | 222 | 101.05 | 0.0000 \* | harvard_us.mistral.pixtral-large-2502-v1:0 |

> McNemar's test with continuity correction (exact binomial if n<25 discordant pairs). \* = significant at α=0.05.

## Cross-Model Comparison — McNemar's Test (`motivation`)

Pairwise test of whether two models differ significantly on the same items (binarised at score ≥ 0.5).

| Model A | Model B | N | A✓B✗ | A✗B✓ | χ² | p-value | Favours |
|---------|---------|---|------|------|----|---------|---------| 
| `google_gemini-3-flash-preview` | `google_gemini-3.1-flash-lite-preview` | 871 | 151 | 58 | 40.50 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `google_gemini-3.1-pro-preview` | 375 | 2 | 33 | 25.71 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 142 | 91 | 10.73 | 0.0011 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 80 | 131 | 11.85 | 0.0006 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 65 | 145 | 29.72 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `google_gemini-3-flash-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 562 | 0 | 560.00 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 459 | 60 | 305.21 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3.1-flash-lite-preview` | `google_gemini-3.1-pro-preview` | 375 | 8 | 62 | 40.13 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 85 | 127 | 7.93 | 0.0049 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 53 | 197 | 81.80 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 31 | 204 | 125.89 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 472 | 3 | 461.10 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 380 | 74 | 204.90 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 375 | 68 | 5 | 52.66 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 375 | 29 | 10 | 8.31 | 0.0039 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 375 | 22 | 9 | 4.65 | 0.0311 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 375 | 308 | 0 | 306.00 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 375 | 267 | 3 | 256.18 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 71 | 173 | 41.81 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 35 | 166 | 84.08 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 516 | 5 | 499.23 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 394 | 46 | 273.66 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 56 | 85 | 5.56 | 0.0184 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 616 | 3 | 605.08 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 476 | 26 | 401.60 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 645 | 3 | 634.08 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 496 | 17 | 445.39 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 40 | 203 | 108.00 | 0.0000 \* | harvard_us.mistral.pixtral-large-2502-v1:0 |

> McNemar's test with continuity correction (exact binomial if n<25 discordant pairs). \* = significant at α=0.05.

## Breakdown by Language (`default`)

| Model | en | it |
|-------|------|------|
| `google_gemini-3-flash-preview` | 99.0% (n=203) | 78.5% (n=668) |
| `google_gemini-3.1-flash-lite-preview` | 97.5% (n=203) | 69.0% (n=668) |
| `google_gemini-3.1-pro-preview` | 100.0% (n=203) | 82.8% (n=172) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 88.2% (n=203) | 59.3% (n=668) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 97.5% (n=203) | 71.8% (n=668) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 98.5% (n=203) | 72.1% (n=668) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 11.3% (n=203) | 15.0% (n=668) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 28.1% (n=203) | 31.2% (n=668) |

> Welch t-test per model comparing groups. Example: en vs it.

## Breakdown by Image Presence (`default`)

| Model | False | True |
|-------|------|------|
| `google_gemini-3-flash-preview` | 75.0% (n=435) | 91.5% (n=436) |
| `google_gemini-3.1-flash-lite-preview` | 65.6% (n=435) | 85.7% (n=436) |
| `google_gemini-3.1-pro-preview` | 80.9% (n=115) | 97.1% (n=260) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 58.0% (n=435) | 74.1% (n=436) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 73.0% (n=435) | 82.7% (n=436) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 69.0% (n=435) | 87.5% (n=436) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 15.6% (n=435) | 12.8% (n=436) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 35.1% (n=435) | 25.9% (n=436) |

> Welch t-test per model comparing groups. Example: False vs True.

## Breakdown by Language (`motivation`)

| Model | en | it |
|-------|------|------|
| `google_gemini-3-flash-preview` | 99.5% (n=203) | 65.3% (n=668) |
| `google_gemini-3.1-flash-lite-preview` | 98.0% (n=203) | 52.1% (n=668) |
| `google_gemini-3.1-pro-preview` | 100.0% (n=203) | 82.8% (n=172) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 88.7% (n=203) | 60.0% (n=668) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 99.0% (n=203) | 73.5% (n=668) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 98.0% (n=203) | 75.6% (n=668) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 10.8% (n=203) | 13.0% (n=668) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 18.2% (n=203) | 31.8% (n=668) |

> Welch t-test per model comparing groups. Example: en vs it.

## Breakdown by Image Presence (`motivation`)

| Model | False | True |
|-------|------|------|
| `google_gemini-3-flash-preview` | 60.4% (n=435) | 86.1% (n=436) |
| `google_gemini-3.1-flash-lite-preview` | 54.7% (n=435) | 71.0% (n=436) |
| `google_gemini-3.1-pro-preview` | 81.1% (n=115) | 97.0% (n=260) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 59.0% (n=435) | 74.3% (n=436) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 74.0% (n=435) | 84.8% (n=436) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 71.0% (n=435) | 90.7% (n=436) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 14.0% (n=435) | 11.0% (n=436) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 32.5% (n=435) | 24.7% (n=436) |

> Welch t-test per model comparing groups. Example: False vs True.

## Logistic Regression (`default`)

P(correct) ~ question_type + has_image + language + model (n=6,472, threshold=0.5)

Reference categories: type=`multiple_choice_radio`, has_image=False, language=`en`, model=`google_gemini-3-flash-preview`

| Predictor | β | SE | z | p | OR | 95% CI |
|-----------|---|----|----|---|----|---------| 
| intercept | 3.153 | 0.163 | 19.39 | 0.0000 \* | 23.398 | [17.01, 32.18] |
| type:completion_closed | -1.464 | 0.134 | -10.92 | 0.0000 \* | 0.231 | [0.18, 0.30] |
| type:completion_open | -1.114 | 0.133 | -8.35 | 0.0000 \* | 0.328 | [0.25, 0.43] |
| type:multiple_choice_check | 0.084 | 0.132 | 0.64 | 0.5238 | 1.088 | [0.84, 1.41] |
| type:positioning | -0.878 | 0.123 | -7.16 | 0.0000 \* | 0.415 | [0.33, 0.53] |
| type:select_errors | -2.722 | 0.158 | -17.21 | 0.0000 \* | 0.066 | [0.05, 0.09] |
| type:true_false | 0.342 | 0.143 | 2.38 | 0.0171 \* | 1.407 | [1.06, 1.86] |
| has_image:True | -0.288 | 0.091 | -3.16 | 0.0016 \* | 0.750 | [0.63, 0.90] |
| language:it | -0.545 | 0.127 | -4.30 | 0.0000 \* | 0.580 | [0.45, 0.74] |
| model:google_gemini-3.1-flash-lite-preview | -0.622 | 0.141 | -4.40 | 0.0000 \* | 0.537 | [0.41, 0.71] |
| model:google_gemini-3.1-pro-preview | 0.894 | 0.280 | 3.20 | 0.0014 \* | 2.446 | [1.41, 4.23] |
| model:harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 | -1.246 | 0.135 | -9.22 | 0.0000 \* | 0.288 | [0.22, 0.38] |
| model:harvard_us.anthropic.claude-opus-4-6-v1 | -0.503 | 0.143 | -3.51 | 0.0004 \* | 0.605 | [0.46, 0.80] |
| model:harvard_us.anthropic.claude-sonnet-4-6 | -0.366 | 0.145 | -2.52 | 0.0118 \* | 0.694 | [0.52, 0.92] |
| model:harvard_us.meta.llama4-maverick-17b-instruct-v1:0 | -4.115 | 0.150 | -27.47 | 0.0000 \* | 0.016 | [0.01, 0.02] |
| model:harvard_us.mistral.pixtral-large-2502-v1:0 | -2.948 | 0.135 | -21.86 | 0.0000 \* | 0.052 | [0.04, 0.07] |

> OR > 1 means higher odds of correct answer vs reference. \* = p < 0.05.

## Logistic Regression (`motivation`)

P(correct) ~ question_type + has_image + language + model (n=6,472, threshold=0.5)

Reference categories: type=`multiple_choice_radio`, has_image=False, language=`en`, model=`google_gemini-3-flash-preview`

| Predictor | β | SE | z | p | OR | 95% CI |
|-----------|---|----|----|---|----|---------| 
| intercept | 2.353 | 0.145 | 16.22 | 0.0000 \* | 10.515 | [7.91, 13.97] |
| type:completion_closed | -1.572 | 0.133 | -11.85 | 0.0000 \* | 0.208 | [0.16, 0.27] |
| type:completion_open | -1.076 | 0.131 | -8.19 | 0.0000 \* | 0.341 | [0.26, 0.44] |
| type:multiple_choice_check | -0.417 | 0.126 | -3.32 | 0.0009 \* | 0.659 | [0.52, 0.84] |
| type:positioning | -1.063 | 0.119 | -8.91 | 0.0000 \* | 0.345 | [0.27, 0.44] |
| type:select_errors | -2.817 | 0.163 | -17.34 | 0.0000 \* | 0.060 | [0.04, 0.08] |
| type:true_false | 0.212 | 0.139 | 1.53 | 0.1257 | 1.237 | [0.94, 1.62] |
| has_image:True | -0.166 | 0.089 | -1.87 | 0.0620 | 0.847 | [0.71, 1.01] |
| language:it | -0.485 | 0.124 | -3.90 | 0.0001 \* | 0.616 | [0.48, 0.79] |
| model:google_gemini-3.1-flash-lite-preview | -0.619 | 0.117 | -5.31 | 0.0000 \* | 0.539 | [0.43, 0.68] |
| model:google_gemini-3.1-pro-preview | 1.613 | 0.266 | 6.06 | 0.0000 \* | 5.016 | [2.98, 8.45] |
| model:harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 | -0.357 | 0.119 | -3.01 | 0.0027 \* | 0.700 | [0.55, 0.88] |
| model:harvard_us.anthropic.claude-opus-4-6-v1 | 0.424 | 0.130 | 3.27 | 0.0011 \* | 1.529 | [1.19, 1.97] |
| model:harvard_us.anthropic.claude-sonnet-4-6 | 0.716 | 0.136 | 5.25 | 0.0000 \* | 2.047 | [1.57, 2.67] |
| model:harvard_us.meta.llama4-maverick-17b-instruct-v1:0 | -3.542 | 0.140 | -25.38 | 0.0000 \* | 0.029 | [0.02, 0.04] |
| model:harvard_us.mistral.pixtral-large-2502-v1:0 | -2.297 | 0.118 | -19.43 | 0.0000 \* | 0.101 | [0.08, 0.13] |

> OR > 1 means higher odds of correct answer vs reference. \* = p < 0.05.

## Hardest Items (p = 0)

**12** items scored 0 across all models and conditions. **10** additional items scored p < 0.10.

**4 flagged for review** (MCQ radio with p=0 — possible data or extraction errors):

| Question | Type | Flag |
|----------|------|------|
| 0678 | multiple_choice_radio | MCQ radio with p=0 — possible data error or extraction issue |
| 0679 | multiple_choice_radio | MCQ radio with p=0 — possible data error or extraction issue |
| 0681 | multiple_choice_radio | MCQ radio with p=0 — possible data error or extraction issue |
| 0689 | multiple_choice_radio | MCQ radio with p=0 — possible data error or extraction issue |

## Item Discrimination by Question Type

| Type | N | Mean r_pb | Median | Good (≥.30) | Fair (.10–.29) | Poor (<.10) |
|------|---|-----------|--------|-------------|----------------|-------------|
| completion_closed | 67 | 0.549 | 0.585 | 59 | 8 | 0 |
| completion_open | 75 | 0.624 | 0.651 | 71 | 3 | 1 |
| multiple_choice_check | 117 | 0.660 | 0.690 | 111 | 5 | 1 |
| multiple_choice_radio | 354 | 0.763 | 0.827 | 344 | 8 | 2 |
| positioning | 105 | 0.603 | 0.624 | 93 | 11 | 1 |
| select_errors | 46 | 0.450 | 0.470 | 44 | 1 | 1 |
| true_false | 79 | 0.444 | 0.448 | 55 | 19 | 5 |

> Higher mean r_pb indicates better discrimination between strong and weak examinees. MCQ check tends to produce more continuous scores, inflating correlation.

## Metric Definitions

| Question Type | Primary Metric | Description |
|---------------|----------------|-------------|
| multiple_choice_radio | Exact Match | 1 if predicted = ground truth, 0 otherwise |
| multiple_choice_check | F1 Score | Harmonic mean of precision and recall over selected options |
| true_false | Statement Accuracy | Proportion of individual T/F statements correct |
| positioning | Element Accuracy | Proportion of elements correctly placed |
| completion_closed | Blank Accuracy | Proportion of blanks correctly filled (fuzzy match) |
| completion_open | Blank Accuracy | Proportion of blanks correct (normalised string match) |
| select_errors | F1 Score | F1 over identified error set vs ground truth |

### Aggregate Scores

- **Macro Average**: Mean of per-type primary metrics with equal weight per type
- **MCQ Exact Match**: Exact match on multiple_choice_radio items only (cleanest subset)
- **95% CI**: Wilson score interval — better coverage for small samples and extreme proportions
