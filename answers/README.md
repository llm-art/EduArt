# Evaluation Results

Generated: 2026-05-27 10:10

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
| 1 | `google_gemini-3.1-pro-preview` | **82.8%** | 95.7% | 871 |
| 2 | `openai_gpt-5.5-2026-04-23` | **80.0%** | 95.1% | 871 |
| 3 | `google_gemini-3-flash-preview` | **75.4%** | 96.8% | 871 |
| 4 | `google_gemini-3.5-flash` | **68.9%** | 96.5% | 871 |
| 5 | `openai_gpt-5.4-2026-03-05` | **67.9%** | 91.3% | 871 |
| 6 | `harvard_us.anthropic.claude-opus-4-6-v1` | **67.3%** | 94.6% | 871 |
| 7 | `harvard_us.anthropic.claude-sonnet-4-6` | **64.8%** | 94.3% | 871 |
| 8 | `harvard_qwen.qwen3-vl-235b-a22b` | **64.5%** | 88.6% | 871 |
| 9 | `google_gemini-3.1-flash-lite-preview` | **62.8%** | 92.4% | 871 |
| 10 | `harvard_mistral.mistral-large-3-675b-instruct` | **58.8%** | 84.6% | 871 |
| 11 | `openai_gpt-5.4-mini-2026-03-17` | **54.9%** | 82.7% | 871 |
| 12 | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | **53.1%** | 84.0% | 871 |
| 13 | `openai_gpt-5.4-nano-2026-03-17` | **40.1%** | 62.7% | 871 |
| 14 | `harvard_us.mistral.pixtral-large-2502-v1:0` | **29.1%** | 28.6% | 871 |
| 15 | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | **12.5%** | 17.0% | 871 |

## Results by Question Type

| Model | MCQ Radio (Exact Match) | MCQ Check (F1) | True/False (Stmt Accuracy) | Positioning (Element Accuracy) | Completion (Closed) (Blank Accuracy) | Completion (Open) (Blank Accuracy) | Select Errors (F1) |
|-------|------|------|------|------|------|------|------|
| `google_gemini-3.1-pro-preview` | 95.7% (n=370) | 89.7% (n=117) | 66.3% (n=83) | 84.0% (n=108) | 92.0% (n=69) | 73.4% (n=75) | 78.8% (n=49) |
| `openai_gpt-5.5-2026-04-23` | 95.1% (n=370) | 85.7% (n=117) | 74.6% (n=83) | 89.3% (n=108) | 93.7% (n=69) | 72.0% (n=75) | 49.2% (n=49) |
| `google_gemini-3-flash-preview` | 96.8% (n=370) | 86.9% (n=117) | 58.9% (n=83) | 73.0% (n=108) | 80.3% (n=69) | 68.2% (n=75) | 63.5% (n=49) |
| `google_gemini-3.5-flash` | 96.5% (n=370) | 83.2% (n=117) | 58.7% (n=83) | 84.9% (n=108) | 75.5% (n=69) | 70.9% (n=75) | 12.8% (n=49) |
| `openai_gpt-5.4-2026-03-05` | 91.3% (n=370) | 80.9% (n=117) | 83.3% (n=83) | 75.7% (n=108) | 66.4% (n=69) | 66.1% (n=75) | 11.7% (n=49) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 94.6% (n=370) | 60.9% (n=117) | 82.5% (n=83) | 85.6% (n=108) | 85.9% (n=69) | 23.9% (n=75) | 37.5% (n=49) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 94.3% (n=370) | 85.2% (n=117) | 77.5% (n=83) | 77.3% (n=108) | 47.6% (n=69) | 65.8% (n=75) | 6.2% (n=49) |
| `harvard_qwen.qwen3-vl-235b-a22b` | 88.6% (n=370) | 73.1% (n=117) | 69.0% (n=83) | 84.3% (n=108) | 74.6% (n=69) | 54.9% (n=75) | 6.8% (n=49) |
| `google_gemini-3.1-flash-lite-preview` | 92.4% (n=370) | 79.1% (n=117) | 76.1% (n=83) | 70.0% (n=108) | 47.2% (n=69) | 63.3% (n=75) | 11.3% (n=49) |
| `harvard_mistral.mistral-large-3-675b-instruct` | 84.6% (n=370) | 70.5% (n=117) | 81.0% (n=83) | 76.8% (n=108) | 26.7% (n=69) | 63.4% (n=75) | 8.8% (n=49) |
| `openai_gpt-5.4-mini-2026-03-17` | 82.7% (n=370) | 72.4% (n=117) | 67.0% (n=83) | 73.1% (n=108) | 22.9% (n=69) | 61.5% (n=75) | 4.7% (n=49) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 84.0% (n=370) | 75.7% (n=117) | 73.2% (n=83) | 43.0% (n=108) | 26.1% (n=69) | 62.5% (n=75) | 7.5% (n=49) |
| `openai_gpt-5.4-nano-2026-03-17` | 62.7% (n=370) | 60.6% (n=117) | 57.3% (n=83) | 44.1% (n=108) | 19.1% (n=69) | 34.9% (n=75) | 1.7% (n=49) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 28.6% (n=370) | 30.8% (n=117) | 57.7% (n=83) | 37.4% (n=108) | 19.1% (n=69) | 27.4% (n=75) | 3.0% (n=49) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 17.0% (n=370) | 9.4% (n=117) | 49.8% (n=83) | 0.0% (n=108) | 5.8% (n=69) | 4.6% (n=75) | 0.9% (n=49) |

## Detailed Results with 95% CI

**MCQ Radio** (Primary metric: Exact Match)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 95.7% | [93.1%, 97.3%] | 370 |
| `openai_gpt-5.5-2026-04-23` | 95.1% | [92.4%, 96.9%] | 370 |
| `google_gemini-3-flash-preview` | 96.8% | [94.4%, 98.1%] | 370 |
| `google_gemini-3.5-flash` | 96.5% | [94.1%, 97.9%] | 370 |
| `openai_gpt-5.4-2026-03-05` | 91.3% | [88.0%, 93.8%] | 370 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 94.6% | [91.8%, 96.5%] | 370 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 94.3% | [91.5%, 96.3%] | 370 |
| `harvard_qwen.qwen3-vl-235b-a22b` | 88.6% | [85.0%, 91.5%] | 370 |
| `google_gemini-3.1-flash-lite-preview` | 92.4% | [89.3%, 94.7%] | 370 |
| `harvard_mistral.mistral-large-3-675b-instruct` | 84.6% | [80.6%, 87.9%] | 370 |
| `openai_gpt-5.4-mini-2026-03-17` | 82.7% | [78.5%, 86.2%] | 370 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 84.0% | [80.0%, 87.4%] | 370 |
| `openai_gpt-5.4-nano-2026-03-17` | 62.7% | [57.7%, 67.5%] | 370 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 28.6% | [24.3%, 33.5%] | 370 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 17.0% | [13.5%, 21.2%] | 370 |

**MCQ Check** (Primary metric: F1)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 89.7% | [82.9%, 94.0%] | 117 |
| `openai_gpt-5.5-2026-04-23` | 85.7% | [78.2%, 90.9%] | 117 |
| `google_gemini-3-flash-preview` | 86.9% | [79.5%, 91.8%] | 117 |
| `google_gemini-3.5-flash` | 83.2% | [75.4%, 88.9%] | 117 |
| `openai_gpt-5.4-2026-03-05` | 80.9% | [72.9%, 87.0%] | 117 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 60.9% | [51.9%, 69.3%] | 117 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 85.2% | [77.7%, 90.5%] | 117 |
| `harvard_qwen.qwen3-vl-235b-a22b` | 73.1% | [64.4%, 80.3%] | 117 |
| `google_gemini-3.1-flash-lite-preview` | 79.1% | [70.9%, 85.5%] | 117 |
| `harvard_mistral.mistral-large-3-675b-instruct` | 70.5% | [61.7%, 78.0%] | 117 |
| `openai_gpt-5.4-mini-2026-03-17` | 72.4% | [63.7%, 79.7%] | 117 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 75.7% | [67.2%, 82.6%] | 117 |
| `openai_gpt-5.4-nano-2026-03-17` | 60.6% | [51.6%, 69.0%] | 117 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 30.8% | [23.1%, 39.6%] | 117 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 9.4% | [5.3%, 16.1%] | 117 |

**True/False** (Primary metric: Stmt Accuracy)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 66.3% | [55.7%, 75.6%] | 83 |
| `openai_gpt-5.5-2026-04-23` | 74.6% | [64.3%, 82.8%] | 83 |
| `google_gemini-3-flash-preview` | 58.9% | [48.2%, 68.9%] | 83 |
| `google_gemini-3.5-flash` | 58.7% | [47.9%, 68.7%] | 83 |
| `openai_gpt-5.4-2026-03-05` | 83.3% | [73.8%, 89.8%] | 83 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 82.5% | [72.9%, 89.2%] | 83 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 77.5% | [67.4%, 85.1%] | 83 |
| `harvard_qwen.qwen3-vl-235b-a22b` | 69.0% | [58.4%, 77.9%] | 83 |
| `google_gemini-3.1-flash-lite-preview` | 76.1% | [65.9%, 84.0%] | 83 |
| `harvard_mistral.mistral-large-3-675b-instruct` | 81.0% | [71.2%, 88.0%] | 83 |
| `openai_gpt-5.4-mini-2026-03-17` | 67.0% | [56.3%, 76.2%] | 83 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 73.2% | [62.8%, 81.6%] | 83 |
| `openai_gpt-5.4-nano-2026-03-17` | 57.3% | [46.6%, 67.4%] | 83 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 57.7% | [47.0%, 67.8%] | 83 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 49.8% | [39.3%, 60.3%] | 83 |

**Positioning** (Primary metric: Element Accuracy)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 84.0% | [75.9%, 89.7%] | 108 |
| `openai_gpt-5.5-2026-04-23` | 89.3% | [82.1%, 93.8%] | 108 |
| `google_gemini-3-flash-preview` | 73.0% | [63.9%, 80.5%] | 108 |
| `google_gemini-3.5-flash` | 84.9% | [77.0%, 90.5%] | 108 |
| `openai_gpt-5.4-2026-03-05` | 75.7% | [66.8%, 82.8%] | 108 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 85.6% | [77.7%, 91.0%] | 108 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 77.3% | [68.5%, 84.2%] | 108 |
| `harvard_qwen.qwen3-vl-235b-a22b` | 84.3% | [76.3%, 90.0%] | 108 |
| `google_gemini-3.1-flash-lite-preview` | 70.0% | [60.8%, 77.9%] | 108 |
| `harvard_mistral.mistral-large-3-675b-instruct` | 76.8% | [68.0%, 83.8%] | 108 |
| `openai_gpt-5.4-mini-2026-03-17` | 73.1% | [64.1%, 80.6%] | 108 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 43.0% | [34.0%, 52.4%] | 108 |
| `openai_gpt-5.4-nano-2026-03-17` | 44.1% | [35.1%, 53.5%] | 108 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 37.4% | [28.8%, 46.8%] | 108 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 0.0% | [0.0%, 3.4%] | 108 |

**Completion (Closed)** (Primary metric: Blank Accuracy)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 92.0% | [83.2%, 96.4%] | 69 |
| `openai_gpt-5.5-2026-04-23` | 93.7% | [85.4%, 97.5%] | 69 |
| `google_gemini-3-flash-preview` | 80.3% | [69.4%, 87.9%] | 69 |
| `google_gemini-3.5-flash` | 75.5% | [64.2%, 84.2%] | 69 |
| `openai_gpt-5.4-2026-03-05` | 66.4% | [54.7%, 76.4%] | 69 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 85.9% | [75.8%, 92.2%] | 69 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 47.6% | [36.2%, 59.2%] | 69 |
| `harvard_qwen.qwen3-vl-235b-a22b` | 74.6% | [63.2%, 83.4%] | 69 |
| `google_gemini-3.1-flash-lite-preview` | 47.2% | [35.9%, 58.8%] | 69 |
| `harvard_mistral.mistral-large-3-675b-instruct` | 26.7% | [17.7%, 38.1%] | 69 |
| `openai_gpt-5.4-mini-2026-03-17` | 22.9% | [14.6%, 34.1%] | 69 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 26.1% | [17.2%, 37.5%] | 69 |
| `openai_gpt-5.4-nano-2026-03-17` | 19.1% | [11.5%, 29.9%] | 69 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 19.1% | [11.5%, 29.9%] | 69 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 5.8% | [2.3%, 14.0%] | 69 |

**Completion (Open)** (Primary metric: Blank Accuracy)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 73.4% | [62.4%, 82.1%] | 75 |
| `openai_gpt-5.5-2026-04-23` | 72.0% | [61.0%, 80.9%] | 75 |
| `google_gemini-3-flash-preview` | 68.2% | [57.0%, 77.6%] | 75 |
| `google_gemini-3.5-flash` | 70.9% | [59.8%, 79.9%] | 75 |
| `openai_gpt-5.4-2026-03-05` | 66.1% | [54.8%, 75.8%] | 75 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 23.9% | [15.7%, 34.7%] | 75 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 65.8% | [54.5%, 75.5%] | 75 |
| `harvard_qwen.qwen3-vl-235b-a22b` | 54.9% | [43.7%, 65.7%] | 75 |
| `google_gemini-3.1-flash-lite-preview` | 63.3% | [51.9%, 73.3%] | 75 |
| `harvard_mistral.mistral-large-3-675b-instruct` | 63.4% | [52.1%, 73.4%] | 75 |
| `openai_gpt-5.4-mini-2026-03-17` | 61.5% | [50.2%, 71.7%] | 75 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 62.5% | [51.2%, 72.6%] | 75 |
| `openai_gpt-5.4-nano-2026-03-17` | 34.9% | [25.1%, 46.2%] | 75 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 27.4% | [18.6%, 38.5%] | 75 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 4.6% | [1.7%, 11.9%] | 75 |

**Select Errors** (Primary metric: F1)

| Model | Mean | 95% CI | N |
|-------|------|--------|---|
| `google_gemini-3.1-pro-preview` | 78.8% | [65.5%, 87.9%] | 49 |
| `openai_gpt-5.5-2026-04-23` | 49.2% | [35.8%, 62.7%] | 49 |
| `google_gemini-3-flash-preview` | 63.5% | [49.5%, 75.6%] | 49 |
| `google_gemini-3.5-flash` | 12.8% | [6.1%, 24.9%] | 49 |
| `openai_gpt-5.4-2026-03-05` | 11.7% | [5.4%, 23.6%] | 49 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 37.5% | [25.4%, 51.5%] | 49 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 6.2% | [2.1%, 16.6%] | 49 |
| `harvard_qwen.qwen3-vl-235b-a22b` | 6.8% | [2.4%, 17.4%] | 49 |
| `google_gemini-3.1-flash-lite-preview` | 11.3% | [5.1%, 23.1%] | 49 |
| `harvard_mistral.mistral-large-3-675b-instruct` | 8.8% | [3.6%, 20.0%] | 49 |
| `openai_gpt-5.4-mini-2026-03-17` | 4.7% | [1.4%, 14.6%] | 49 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 7.5% | [2.9%, 18.4%] | 49 |
| `openai_gpt-5.4-nano-2026-03-17` | 1.7% | [0.3%, 10.2%] | 49 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 3.0% | [0.7%, 12.1%] | 49 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 0.9% | [0.1%, 8.9%] | 49 |

## Cross-Condition Comparison: `default` vs `motivation`

Paired comparison on questions answered under both conditions. The motivation condition adds chain-of-thought reasoning to the prompt.

### Overall (Paired Scores)

| Model | N Paired | Default | Motivation | Diff | 95% CI | p-value | Improved | Same | Degraded |
|-------|----------|---------|------------|------|--------|---------|----------|------|----------|
| `google_gemini-3-flash-preview` | 871 | 83.2% | 73.3% | -10.0pp | [-12.3, -7.7]pp | 0.000 \* | 48 | 670 | 153 |
| `google_gemini-3.1-flash-lite-preview` | 871 | 75.6% | 62.8% | -12.8pp | [-15.1, -10.5]pp | 0.000 \* | 44 | 629 | 198 |
| `google_gemini-3.1-pro-preview` | 871 | 87.5% | 86.1% | -1.3pp | [-2.5, -0.2]pp | 0.025 \* | 35 | 770 | 66 |
| `google_gemini-3.5-flash` | 871 | 81.1% | 79.8% | -1.3pp | [-3.0, +0.4]pp | 0.123 | 59 | 742 | 70 |
| `harvard_mistral.mistral-large-3-675b-instruct` | 871 | 70.7% | 71.2% | +0.4pp | [-1.3, +2.2]pp | 0.616 | 82 | 702 | 87 |
| `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 75.5% | 73.7% | -1.8pp | [-2.9, -0.7]pp | 0.001 \* | 39 | 744 | 88 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 66.0% | 66.7% | +0.7pp | [-0.8, +2.1]pp | 0.368 | 60 | 749 | 62 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 77.8% | 79.4% | +1.6pp | [-0.0, +3.2]pp | 0.053 | 67 | 759 | 45 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 78.3% | 80.9% | +2.6pp | [+1.0, +4.2]pp | 0.001 \* | 61 | 763 | 47 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 14.1% | 12.5% | -1.7pp | [-3.2, -0.1]pp | 0.042 \* | 24 | 802 | 45 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 30.5% | 28.6% | -1.9pp | [-4.8, +1.0]pp | 0.204 | 136 | 576 | 159 |
| `openai_gpt-5.4-2026-03-05` | 871 | 78.6% | 78.2% | -0.4pp | [-2.2, +1.4]pp | 0.683 | 80 | 700 | 91 |
| `openai_gpt-5.4-mini-2026-03-17` | 871 | 67.7% | 66.2% | -1.5pp | [-3.4, +0.4]pp | 0.119 | 108 | 635 | 128 |
| `openai_gpt-5.4-nano-2026-03-17` | 871 | 50.3% | 43.6% | -6.7pp | [-9.1, -4.4]pp | 0.000 \* | 96 | 549 | 226 |
| `openai_gpt-5.5-2026-04-23` | 871 | 86.5% | 84.1% | -2.4pp | [-3.9, -1.0]pp | 0.001 \* | 46 | 734 | 91 |

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
| `google_gemini-3.1-pro-preview` | Completion (Closed) | 69 | 92.0% | 87.8% | -4.2pp |
| `google_gemini-3.1-pro-preview` | Completion (Open) | 75 | 73.4% | 73.6% | +0.2pp |
| `google_gemini-3.1-pro-preview` | MCQ Check | 117 | 89.7% | 87.9% | -1.8pp |
| `google_gemini-3.1-pro-preview` | MCQ Radio | 370 | 95.7% | 96.0% | +0.3pp |
| `google_gemini-3.1-pro-preview` | Positioning | 108 | 84.0% | 80.2% | -3.7pp |
| `google_gemini-3.1-pro-preview` | Select Errors | 49 | 78.8% | 77.1% | -1.7pp |
| `google_gemini-3.1-pro-preview` | True/False | 83 | 66.3% | 62.7% | -3.6pp |
| `google_gemini-3.5-flash` | Completion (Closed) | 69 | 75.5% | 67.7% | -7.8pp |
| `google_gemini-3.5-flash` | Completion (Open) | 75 | 70.9% | 69.8% | -1.1pp |
| `google_gemini-3.5-flash` | MCQ Check | 117 | 83.2% | 81.4% | -1.8pp |
| `google_gemini-3.5-flash` | MCQ Radio | 370 | 96.5% | 96.8% | +0.3pp |
| `google_gemini-3.5-flash` | Positioning | 108 | 84.9% | 75.7% | -9.3pp |
| `google_gemini-3.5-flash` | Select Errors | 49 | 12.8% | 29.0% | +16.1pp |
| `google_gemini-3.5-flash` | True/False | 83 | 58.7% | 56.0% | -2.6pp |
| `harvard_mistral.mistral-large-3-675b-instruct` | Completion (Closed) | 69 | 26.7% | 54.0% | +27.3pp |
| `harvard_mistral.mistral-large-3-675b-instruct` | Completion (Open) | 75 | 63.4% | 61.3% | -2.1pp |
| `harvard_mistral.mistral-large-3-675b-instruct` | MCQ Check | 117 | 70.5% | 69.8% | -0.7pp |
| `harvard_mistral.mistral-large-3-675b-instruct` | MCQ Radio | 370 | 84.6% | 81.9% | -2.7pp |
| `harvard_mistral.mistral-large-3-675b-instruct` | Positioning | 108 | 76.8% | 80.2% | +3.4pp |
| `harvard_mistral.mistral-large-3-675b-instruct` | Select Errors | 49 | 8.8% | 8.2% | -0.6pp |
| `harvard_mistral.mistral-large-3-675b-instruct` | True/False | 83 | 81.0% | 73.9% | -7.0pp |
| `harvard_qwen.qwen3-vl-235b-a22b` | Completion (Closed) | 69 | 74.6% | 83.8% | +9.3pp |
| `harvard_qwen.qwen3-vl-235b-a22b` | Completion (Open) | 75 | 54.9% | 53.4% | -1.5pp |
| `harvard_qwen.qwen3-vl-235b-a22b` | MCQ Check | 117 | 73.1% | 66.9% | -6.2pp |
| `harvard_qwen.qwen3-vl-235b-a22b` | MCQ Radio | 370 | 88.6% | 87.8% | -0.8pp |
| `harvard_qwen.qwen3-vl-235b-a22b` | Positioning | 108 | 84.3% | 82.2% | -2.1pp |
| `harvard_qwen.qwen3-vl-235b-a22b` | Select Errors | 49 | 6.8% | 7.5% | +0.7pp |
| `harvard_qwen.qwen3-vl-235b-a22b` | True/False | 83 | 69.0% | 58.5% | -10.5pp |
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
| `openai_gpt-5.4-2026-03-05` | Completion (Closed) | 69 | 66.4% | 78.1% | +11.7pp |
| `openai_gpt-5.4-2026-03-05` | Completion (Open) | 75 | 66.1% | 64.7% | -1.4pp |
| `openai_gpt-5.4-2026-03-05` | MCQ Check | 117 | 80.9% | 75.1% | -5.8pp |
| `openai_gpt-5.4-2026-03-05` | MCQ Radio | 370 | 91.3% | 91.9% | +0.5pp |
| `openai_gpt-5.4-2026-03-05` | Positioning | 108 | 75.7% | 73.7% | -2.0pp |
| `openai_gpt-5.4-2026-03-05` | Select Errors | 49 | 11.7% | 12.2% | +0.5pp |
| `openai_gpt-5.4-2026-03-05` | True/False | 83 | 83.3% | 78.8% | -4.4pp |
| `openai_gpt-5.4-mini-2026-03-17` | Completion (Closed) | 69 | 22.9% | 21.9% | -1.0pp |
| `openai_gpt-5.4-mini-2026-03-17` | Completion (Open) | 75 | 61.5% | 58.1% | -3.4pp |
| `openai_gpt-5.4-mini-2026-03-17` | MCQ Check | 117 | 72.4% | 70.4% | -1.9pp |
| `openai_gpt-5.4-mini-2026-03-17` | MCQ Radio | 370 | 82.7% | 81.3% | -1.4pp |
| `openai_gpt-5.4-mini-2026-03-17` | Positioning | 108 | 73.1% | 70.2% | -2.9pp |
| `openai_gpt-5.4-mini-2026-03-17` | Select Errors | 49 | 4.7% | 4.3% | -0.4pp |
| `openai_gpt-5.4-mini-2026-03-17` | True/False | 83 | 67.0% | 67.8% | +0.8pp |
| `openai_gpt-5.4-nano-2026-03-17` | Completion (Closed) | 69 | 19.1% | 8.9% | -10.2pp |
| `openai_gpt-5.4-nano-2026-03-17` | Completion (Open) | 75 | 34.9% | 18.3% | -16.6pp |
| `openai_gpt-5.4-nano-2026-03-17` | MCQ Check | 117 | 60.6% | 57.0% | -3.6pp |
| `openai_gpt-5.4-nano-2026-03-17` | MCQ Radio | 370 | 62.7% | 62.7% | +0.0pp |
| `openai_gpt-5.4-nano-2026-03-17` | Positioning | 108 | 44.1% | 17.4% | -26.7pp |
| `openai_gpt-5.4-nano-2026-03-17` | Select Errors | 49 | 1.7% | 2.0% | +0.2pp |
| `openai_gpt-5.4-nano-2026-03-17` | True/False | 83 | 57.3% | 49.8% | -7.5pp |
| `openai_gpt-5.5-2026-04-23` | Completion (Closed) | 69 | 93.7% | 91.6% | -2.2pp |
| `openai_gpt-5.5-2026-04-23` | Completion (Open) | 75 | 72.0% | 68.8% | -3.2pp |
| `openai_gpt-5.5-2026-04-23` | MCQ Check | 117 | 85.7% | 78.9% | -6.8pp |
| `openai_gpt-5.5-2026-04-23` | MCQ Radio | 370 | 95.1% | 95.4% | +0.3pp |
| `openai_gpt-5.5-2026-04-23` | Positioning | 108 | 89.3% | 90.1% | +0.8pp |
| `openai_gpt-5.5-2026-04-23` | Select Errors | 49 | 49.2% | 36.1% | -13.1pp |
| `openai_gpt-5.5-2026-04-23` | True/False | 83 | 74.6% | 68.8% | -5.8pp |

> **Note**: Diff is in percentage points (pp). p-values from paired t-test. \* = significant at α=0.05.

## Item Analysis (CTT & IRT)

Analysis across **30 examinees** (model × condition) and **871 items**.

### Classical Test Theory (CTT)

| Statistic | Mean | SD | Min | Max |
|-----------|------|----|-----|-----|
| Item Difficulty (p) | 0.670 | 0.220 | 0.000 | 1.000 |
| Discrimination (r_pb) | 0.597 | 0.217 | -0.152 | 0.954 |

**Item Difficulty Distribution**

| Category | p Range | Count |
|----------|---------|-------|
| Very Easy | ≥ 0.90 | 118 |
| Easy | 0.70 – 0.89 | 359 |
| Medium | 0.30 – 0.69 | 330 |
| Hard | 0.10 – 0.29 | 41 |
| Very Hard | < 0.10 | 23 |

**Item Discrimination Distribution**

| Category | r_pb Range | Count |
|----------|------------|-------|
| Good | ≥ 0.30 | 774 |
| Fair | 0.10 – 0.29 | 64 |
| Poor | < 0.10 | 20 |

### Item Response Theory — Rasch Model (1PL)

- Converged: Yes (19 iterations)
- Person Separation Reliability: 0.995
- Estimable items: 858 / 871 (13 items with zero variance excluded)
- Item difficulty (b) range: [-6.00, 6.00]

**Examinee Ability Estimates (θ)**

| Model / Condition | θ |
|-------------------|---|
| `google_gemini-3.1-pro-preview/default` | +1.671 |
| `openai_gpt-5.5-2026-04-23/default` | +1.551 |
| `google_gemini-3.1-pro-preview/motivation` | +1.506 |
| `openai_gpt-5.5-2026-04-23/motivation` | +1.276 |
| `google_gemini-3-flash-preview/default` | +1.190 |
| `google_gemini-3.5-flash/default` | +0.980 |
| `harvard_us.anthropic.claude-sonnet-4-6/motivation` | +0.958 |
| `google_gemini-3.5-flash/motivation` | +0.860 |
| `harvard_us.anthropic.claude-opus-4-6-v1/motivation` | +0.829 |
| `openai_gpt-5.4-2026-03-05/default` | +0.759 |
| `harvard_us.anthropic.claude-sonnet-4-6/default` | +0.730 |
| `openai_gpt-5.4-2026-03-05/motivation` | +0.727 |
| `harvard_us.anthropic.claude-opus-4-6-v1/default` | +0.692 |
| `google_gemini-3.1-flash-lite-preview/default` | +0.518 |
| `harvard_qwen.qwen3-vl-235b-a22b/default` | +0.507 |
| `harvard_qwen.qwen3-vl-235b-a22b/motivation` | +0.371 |
| `google_gemini-3-flash-preview/motivation` | +0.337 |
| `harvard_mistral.mistral-large-3-675b-instruct/motivation` | +0.185 |
| `harvard_mistral.mistral-large-3-675b-instruct/default` | +0.153 |
| `openai_gpt-5.4-mini-2026-03-17/default` | -0.053 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0/motivation` | -0.118 |
| `openai_gpt-5.4-mini-2026-03-17/motivation` | -0.153 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0/default` | -0.161 |
| `google_gemini-3.1-flash-lite-preview/motivation` | -0.365 |
| `openai_gpt-5.4-nano-2026-03-17/default` | -1.117 |
| `openai_gpt-5.4-nano-2026-03-17/motivation` | -1.514 |
| `harvard_us.mistral.pixtral-large-2502-v1:0/default` | -2.331 |
| `harvard_us.mistral.pixtral-large-2502-v1:0/motivation` | -2.458 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0/default` | -3.670 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0/motivation` | -3.858 |

**10 Hardest Items** (lowest p-value)

| Question | Type | p | r_pb | b (Rasch) |
|----------|------|---|------|-----------|
| 0316 | positioning | 0.000 | — | 6.00 |
| 0376 | positioning | 0.000 | — | 6.00 |
| 0681 | multiple_choice_radio | 0.000 | — | 6.00 |
| 0689 | multiple_choice_radio | 0.000 | — | 6.00 |
| 0811 | select_errors | 0.000 | — | 6.00 |
| 0358 | positioning | 0.033 | 0.077 | 3.92 |
| 0560 | positioning | 0.033 | 0.127 | 3.92 |
| 0679 | multiple_choice_radio | 0.033 | -0.152 | 3.92 |
| 0565 | select_errors | 0.042 | 0.221 | 3.68 |
| 0571 | positioning | 0.044 | 0.030 | 3.61 |

**10 Easiest Items** (highest p-value)

| Question | Type | p | r_pb | b (Rasch) |
|----------|------|---|------|-----------|
| 0693 | multiple_choice_radio | 0.967 | 0.493 | -4.63 |
| 0822 | multiple_choice_radio | 0.967 | 0.493 | -4.63 |
| 0079 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0103 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0185 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0342 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0566 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0685 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0687 | multiple_choice_radio | 1.000 | — | -6.00 |
| 0695 | multiple_choice_radio | 1.000 | — | -6.00 |

**10 Most Discriminating Items** (highest r_pb)

| Question | Type | p | r_pb | b (Rasch) |
|----------|------|---|------|-----------|
| 0712 | multiple_choice_check | 0.765 | 0.954 | -1.48 |
| 0290 | multiple_choice_check | 0.778 | 0.929 | -1.59 |
| 0582 | multiple_choice_check | 0.807 | 0.928 | -1.87 |
| 0665 | positioning | 0.808 | 0.925 | -1.88 |
| 0421 | multiple_choice_check | 0.778 | 0.922 | -1.60 |
| 0372 | completion_open | 0.600 | 0.921 | -0.36 |
| 0363 | completion_open | 0.600 | 0.917 | -0.36 |
| 0662 | completion_open | 0.542 | 0.915 | -0.04 |
| 0842 | completion_open | 0.640 | 0.914 | -0.60 |
| 0622 | multiple_choice_check | 0.831 | 0.912 | -2.12 |

> **Note**: Rasch (1PL) via JMLE. With N≤10 examinees, estimates have high uncertainty. Items with zero variance across examinees are non-estimable.

## Cross-Model Comparison — McNemar's Test (`default`)

Pairwise test of whether two models differ significantly on the same items (binarised at score ≥ 0.5).

| Model A | Model B | N | A✓B✗ | A✗B✓ | χ² | p-value | Favours |
|---------|---------|---|------|------|----|---------|---------| 
| `google_gemini-3-flash-preview` | `google_gemini-3.1-flash-lite-preview` | 871 | 123 | 59 | 21.81 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `google_gemini-3.1-pro-preview` | 871 | 20 | 63 | 21.25 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3-flash-preview` | `google_gemini-3.5-flash` | 871 | 62 | 44 | 2.73 | 0.0987 | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_mistral.mistral-large-3-675b-instruct` | 871 | 171 | 64 | 47.81 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 110 | 59 | 14.79 | 0.0001 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 189 | 38 | 99.12 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 116 | 66 | 13.19 | 0.0003 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 99 | 64 | 7.09 | 0.0077 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 633 | 3 | 622.08 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 488 | 26 | 413.46 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `openai_gpt-5.4-2026-03-05` | 871 | 108 | 75 | 5.60 | 0.0180 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 179 | 60 | 58.26 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 311 | 24 | 244.17 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `openai_gpt-5.5-2026-04-23` | 871 | 34 | 72 | 12.92 | 0.0003 \* | openai_gpt-5.5-2026-04-23 |
| `google_gemini-3.1-flash-lite-preview` | `google_gemini-3.1-pro-preview` | 871 | 29 | 136 | 68.10 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-flash-lite-preview` | `google_gemini-3.5-flash` | 871 | 49 | 95 | 14.06 | 0.0002 \* | google_gemini-3.5-flash |
| `google_gemini-3.1-flash-lite-preview` | `harvard_mistral.mistral-large-3-675b-instruct` | 871 | 105 | 62 | 10.56 | 0.0012 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 63 | 76 | 1.04 | 0.3088 | harvard_qwen.qwen3-vl-235b-a22b |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 134 | 47 | 40.86 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 100 | 114 | 0.79 | 0.3742 | harvard_us.anthropic.claude-opus-4-6-v1 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 50 | 79 | 6.08 | 0.0137 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 569 | 3 | 558.09 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 434 | 36 | 335.34 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `openai_gpt-5.4-2026-03-05` | 871 | 54 | 85 | 6.47 | 0.0109 \* | openai_gpt-5.4-2026-03-05 |
| `google_gemini-3.1-flash-lite-preview` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 104 | 49 | 19.06 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 256 | 33 | 170.53 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `openai_gpt-5.5-2026-04-23` | 871 | 31 | 133 | 62.20 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `google_gemini-3.1-pro-preview` | `google_gemini-3.5-flash` | 871 | 81 | 20 | 35.64 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_mistral.mistral-large-3-675b-instruct` | 871 | 191 | 41 | 95.69 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 117 | 23 | 61.78 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 216 | 22 | 156.51 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 123 | 30 | 55.32 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 111 | 33 | 41.17 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 674 | 1 | 669.01 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 513 | 8 | 487.55 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `openai_gpt-5.4-2026-03-05` | 871 | 114 | 38 | 37.01 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 189 | 27 | 120.00 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 338 | 8 | 312.84 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `openai_gpt-5.5-2026-04-23` | 871 | 35 | 30 | 0.25 | 0.6198 | google_gemini-3.1-pro-preview |
| `google_gemini-3.5-flash` | `harvard_mistral.mistral-large-3-675b-instruct` | 871 | 143 | 54 | 39.31 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 77 | 44 | 8.46 | 0.0036 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 173 | 40 | 81.80 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 107 | 75 | 5.28 | 0.0216 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 74 | 57 | 1.95 | 0.1621 | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 615 | 3 | 604.08 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 464 | 20 | 405.47 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `openai_gpt-5.4-2026-03-05` | 871 | 85 | 70 | 1.26 | 0.2608 | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 148 | 47 | 51.28 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 290 | 21 | 230.95 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `openai_gpt-5.5-2026-04-23` | 871 | 25 | 81 | 28.54 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 53 | 109 | 18.67 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 125 | 81 | 8.98 | 0.0027 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 92 | 149 | 13.01 | 0.0003 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 52 | 124 | 28.64 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 538 | 15 | 492.74 | 0.0000 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 393 | 38 | 290.76 | 0.0000 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `openai_gpt-5.4-2026-03-05` | 871 | 48 | 122 | 31.35 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `harvard_mistral.mistral-large-3-675b-instruct` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 99 | 87 | 0.65 | 0.4199 | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 238 | 58 | 108.25 | 0.0000 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `openai_gpt-5.5-2026-04-23` | 871 | 31 | 176 | 100.17 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 141 | 41 | 53.85 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 89 | 90 | 0.00 | 1.0000 | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 62 | 78 | 1.61 | 0.2049 | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 587 | 8 | 561.49 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 432 | 21 | 371.08 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `openai_gpt-5.4-2026-03-05` | 871 | 57 | 75 | 2.19 | 0.1390 | openai_gpt-5.4-2026-03-05 |
| `harvard_qwen.qwen3-vl-235b-a22b` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 117 | 49 | 27.04 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 261 | 25 | 193.09 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `openai_gpt-5.5-2026-04-23` | 871 | 22 | 111 | 58.23 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 81 | 182 | 38.02 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 32 | 148 | 73.47 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 486 | 7 | 463.46 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 359 | 48 | 236.12 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `openai_gpt-5.4-2026-03-05` | 871 | 30 | 148 | 76.90 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 83 | 115 | 4.85 | 0.0276 \* | openai_gpt-5.4-mini-2026-03-17 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 203 | 67 | 67.50 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `openai_gpt-5.5-2026-04-23` | 871 | 23 | 212 | 150.40 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 85 | 100 | 1.06 | 0.3033 | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 594 | 14 | 551.38 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 447 | 35 | 350.46 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `openai_gpt-5.4-2026-03-05` | 871 | 85 | 102 | 1.37 | 0.2420 | openai_gpt-5.4-2026-03-05 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 158 | 89 | 18.72 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 286 | 49 | 166.26 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `openai_gpt-5.5-2026-04-23` | 871 | 31 | 119 | 50.46 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 601 | 6 | 581.28 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 448 | 21 | 386.94 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `openai_gpt-5.4-2026-03-05` | 871 | 55 | 57 | 0.01 | 0.9247 | openai_gpt-5.4-2026-03-05 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 120 | 36 | 44.16 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 278 | 26 | 207.24 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `openai_gpt-5.5-2026-04-23` | 871 | 20 | 93 | 45.88 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 54 | 222 | 101.05 | 0.0000 \* | harvard_us.mistral.pixtral-large-2502-v1:0 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `openai_gpt-5.4-2026-03-05` | 871 | 8 | 605 | 579.47 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 10 | 521 | 489.83 | 0.0000 \* | openai_gpt-5.4-mini-2026-03-17 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 28 | 371 | 293.14 | 0.0000 \* | openai_gpt-5.4-nano-2026-03-17 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `openai_gpt-5.5-2026-04-23` | 871 | 4 | 672 | 658.12 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | `openai_gpt-5.4-2026-03-05` | 871 | 17 | 446 | 395.65 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 55 | 398 | 258.20 | 0.0000 \* | openai_gpt-5.4-mini-2026-03-17 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 88 | 263 | 86.26 | 0.0000 \* | openai_gpt-5.4-nano-2026-03-17 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | `openai_gpt-5.5-2026-04-23` | 871 | 7 | 507 | 484.44 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `openai_gpt-5.4-2026-03-05` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 129 | 43 | 42.01 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `openai_gpt-5.4-2026-03-05` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 276 | 22 | 214.80 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `openai_gpt-5.4-2026-03-05` | `openai_gpt-5.5-2026-04-23` | 871 | 30 | 101 | 37.40 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `openai_gpt-5.4-mini-2026-03-17` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 226 | 58 | 98.20 | 0.0000 \* | openai_gpt-5.4-mini-2026-03-17 |
| `openai_gpt-5.4-mini-2026-03-17` | `openai_gpt-5.5-2026-04-23` | 871 | 21 | 178 | 122.29 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `openai_gpt-5.4-nano-2026-03-17` | `openai_gpt-5.5-2026-04-23` | 871 | 9 | 334 | 306.05 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |

> McNemar's test with continuity correction (exact binomial if n<25 discordant pairs). \* = significant at α=0.05.

## Cross-Model Comparison — McNemar's Test (`motivation`)

Pairwise test of whether two models differ significantly on the same items (binarised at score ≥ 0.5).

| Model A | Model B | N | A✓B✗ | A✗B✓ | χ² | p-value | Favours |
|---------|---------|---|------|------|----|---------|---------| 
| `google_gemini-3-flash-preview` | `google_gemini-3.1-flash-lite-preview` | 871 | 151 | 58 | 40.50 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `google_gemini-3.1-pro-preview` | 871 | 14 | 133 | 94.72 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3-flash-preview` | `google_gemini-3.5-flash` | 871 | 43 | 103 | 23.84 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3-flash-preview` | `harvard_mistral.mistral-large-3-675b-instruct` | 871 | 138 | 130 | 0.18 | 0.6689 | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 100 | 131 | 3.90 | 0.0484 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 142 | 91 | 10.73 | 0.0011 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 80 | 131 | 11.85 | 0.0006 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `google_gemini-3-flash-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 65 | 145 | 29.72 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `google_gemini-3-flash-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 562 | 0 | 560.00 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 459 | 60 | 305.21 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `openai_gpt-5.4-2026-03-05` | 871 | 95 | 139 | 7.90 | 0.0049 \* | openai_gpt-5.4-2026-03-05 |
| `google_gemini-3-flash-preview` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 150 | 98 | 10.49 | 0.0012 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 313 | 36 | 218.27 | 0.0000 \* | google_gemini-3-flash-preview |
| `google_gemini-3-flash-preview` | `openai_gpt-5.5-2026-04-23` | 871 | 39 | 139 | 55.06 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `google_gemini-3.1-flash-lite-preview` | `google_gemini-3.1-pro-preview` | 871 | 22 | 234 | 173.91 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-flash-lite-preview` | `google_gemini-3.5-flash` | 871 | 31 | 184 | 107.46 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.1-flash-lite-preview` | `harvard_mistral.mistral-large-3-675b-instruct` | 871 | 83 | 168 | 28.11 | 0.0000 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `google_gemini-3.1-flash-lite-preview` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 50 | 174 | 67.54 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 85 | 127 | 7.93 | 0.0049 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 53 | 197 | 81.80 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 31 | 204 | 125.89 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 472 | 3 | 461.10 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 380 | 74 | 204.90 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `openai_gpt-5.4-2026-03-05` | 871 | 42 | 179 | 83.69 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `google_gemini-3.1-flash-lite-preview` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 98 | 139 | 6.75 | 0.0094 \* | openai_gpt-5.4-mini-2026-03-17 |
| `google_gemini-3.1-flash-lite-preview` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 248 | 64 | 107.34 | 0.0000 \* | google_gemini-3.1-flash-lite-preview |
| `google_gemini-3.1-flash-lite-preview` | `openai_gpt-5.5-2026-04-23` | 871 | 18 | 211 | 160.98 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `google_gemini-3.1-pro-preview` | `google_gemini-3.5-flash` | 871 | 84 | 25 | 30.86 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_mistral.mistral-large-3-675b-instruct` | 871 | 172 | 45 | 73.16 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 117 | 29 | 51.84 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 201 | 31 | 123.11 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 109 | 41 | 29.93 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 86 | 47 | 10.86 | 0.0010 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 682 | 1 | 677.01 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 537 | 19 | 480.74 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `openai_gpt-5.4-2026-03-05` | 871 | 119 | 44 | 33.60 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 205 | 34 | 120.92 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 402 | 6 | 382.41 | 0.0000 \* | google_gemini-3.1-pro-preview |
| `google_gemini-3.1-pro-preview` | `openai_gpt-5.5-2026-04-23` | 871 | 52 | 33 | 3.81 | 0.0509 | google_gemini-3.1-pro-preview |
| `google_gemini-3.5-flash` | `harvard_mistral.mistral-large-3-675b-instruct` | 871 | 130 | 62 | 23.38 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 82 | 53 | 5.81 | 0.0160 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 155 | 44 | 60.80 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 96 | 87 | 0.35 | 0.5543 | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 60 | 80 | 2.58 | 0.1083 | harvard_us.anthropic.claude-sonnet-4-6 |
| `google_gemini-3.5-flash` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 622 | 0 | 620.00 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 493 | 34 | 398.03 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `openai_gpt-5.4-2026-03-05` | 871 | 91 | 75 | 1.36 | 0.2443 | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 160 | 48 | 59.24 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 349 | 12 | 312.73 | 0.0000 \* | google_gemini-3.5-flash |
| `google_gemini-3.5-flash` | `openai_gpt-5.5-2026-04-23` | 871 | 38 | 78 | 13.11 | 0.0003 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_qwen.qwen3-vl-235b-a22b` | 871 | 58 | 97 | 9.32 | 0.0023 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 122 | 79 | 8.78 | 0.0031 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 77 | 136 | 15.79 | 0.0001 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 42 | 130 | 44.01 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 558 | 4 | 544.14 | 0.0000 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 421 | 30 | 337.25 | 0.0000 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `openai_gpt-5.4-2026-03-05` | 871 | 55 | 107 | 16.06 | 0.0001 \* | openai_gpt-5.4-2026-03-05 |
| `harvard_mistral.mistral-large-3-675b-instruct` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 118 | 74 | 9.63 | 0.0019 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 306 | 37 | 209.40 | 0.0000 \* | harvard_mistral.mistral-large-3-675b-instruct |
| `harvard_mistral.mistral-large-3-675b-instruct` | `openai_gpt-5.5-2026-04-23` | 871 | 40 | 148 | 60.90 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 871 | 127 | 45 | 38.15 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 71 | 91 | 2.23 | 0.1355 | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 40 | 89 | 17.86 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 596 | 3 | 585.08 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 454 | 24 | 385.02 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `openai_gpt-5.4-2026-03-05` | 871 | 59 | 72 | 1.10 | 0.2944 | openai_gpt-5.4-2026-03-05 |
| `harvard_qwen.qwen3-vl-235b-a22b` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 140 | 57 | 34.13 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 325 | 17 | 275.58 | 0.0000 \* | harvard_qwen.qwen3-vl-235b-a22b |
| `harvard_qwen.qwen3-vl-235b-a22b` | `openai_gpt-5.5-2026-04-23` | 871 | 27 | 96 | 37.59 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.anthropic.claude-opus-4-6-v1` | 871 | 71 | 173 | 41.81 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 35 | 166 | 84.08 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 516 | 5 | 499.23 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 394 | 46 | 273.66 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `openai_gpt-5.4-2026-03-05` | 871 | 46 | 141 | 47.25 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 84 | 83 | 0.00 | 1.0000 | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 263 | 37 | 168.75 | 0.0000 \* | harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | `openai_gpt-5.5-2026-04-23` | 871 | 31 | 182 | 105.63 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.anthropic.claude-sonnet-4-6` | 871 | 56 | 85 | 5.56 | 0.0184 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 616 | 3 | 605.08 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 476 | 26 | 401.60 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `openai_gpt-5.4-2026-03-05` | 871 | 85 | 78 | 0.22 | 0.6384 | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 166 | 63 | 45.43 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 361 | 33 | 271.39 | 0.0000 \* | harvard_us.anthropic.claude-opus-4-6-v1 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | `openai_gpt-5.5-2026-04-23` | 871 | 44 | 93 | 16.82 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 871 | 645 | 3 | 634.08 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 496 | 17 | 445.39 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `openai_gpt-5.4-2026-03-05` | 871 | 74 | 38 | 10.94 | 0.0009 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 162 | 30 | 89.38 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 377 | 20 | 319.23 | 0.0000 \* | harvard_us.anthropic.claude-sonnet-4-6 |
| `harvard_us.anthropic.claude-sonnet-4-6` | `openai_gpt-5.5-2026-04-23` | 871 | 42 | 62 | 3.47 | 0.0624 | openai_gpt-5.5-2026-04-23 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `harvard_us.mistral.pixtral-large-2502-v1:0` | 871 | 40 | 203 | 108.00 | 0.0000 \* | harvard_us.mistral.pixtral-large-2502-v1:0 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `openai_gpt-5.4-2026-03-05` | 871 | 5 | 611 | 594.20 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 12 | 522 | 485.17 | 0.0000 \* | openai_gpt-5.4-mini-2026-03-17 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 11 | 296 | 262.72 | 0.0000 \* | openai_gpt-5.4-nano-2026-03-17 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | `openai_gpt-5.5-2026-04-23` | 871 | 1 | 663 | 658.01 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | `openai_gpt-5.4-2026-03-05` | 871 | 21 | 464 | 402.81 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 45 | 392 | 273.95 | 0.0000 \* | openai_gpt-5.4-mini-2026-03-17 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 113 | 235 | 42.07 | 0.0000 \* | openai_gpt-5.4-nano-2026-03-17 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | `openai_gpt-5.5-2026-04-23` | 871 | 22 | 521 | 456.73 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `openai_gpt-5.4-2026-03-05` | `openai_gpt-5.4-mini-2026-03-17` | 871 | 139 | 43 | 49.59 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `openai_gpt-5.4-2026-03-05` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 343 | 22 | 280.55 | 0.0000 \* | openai_gpt-5.4-2026-03-05 |
| `openai_gpt-5.4-2026-03-05` | `openai_gpt-5.5-2026-04-23` | 871 | 45 | 101 | 20.72 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `openai_gpt-5.4-mini-2026-03-17` | `openai_gpt-5.4-nano-2026-03-17` | 871 | 268 | 43 | 161.34 | 0.0000 \* | openai_gpt-5.4-mini-2026-03-17 |
| `openai_gpt-5.4-mini-2026-03-17` | `openai_gpt-5.5-2026-04-23` | 871 | 28 | 180 | 109.62 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |
| `openai_gpt-5.4-nano-2026-03-17` | `openai_gpt-5.5-2026-04-23` | 871 | 16 | 393 | 345.66 | 0.0000 \* | openai_gpt-5.5-2026-04-23 |

> McNemar's test with continuity correction (exact binomial if n<25 discordant pairs). \* = significant at α=0.05.

## Breakdown by Language (`default`)

| Model | en | it |
|-------|------|------|
| `google_gemini-3-flash-preview` | 99.0% (n=203) | 78.5% (n=668) |
| `google_gemini-3.1-flash-lite-preview` | 97.5% (n=203) | 69.0% (n=668) |
| `google_gemini-3.1-pro-preview` | 100.0% (n=203) | 83.7% (n=668) |
| `google_gemini-3.5-flash` | 99.0% (n=203) | 75.6% (n=668) |
| `harvard_mistral.mistral-large-3-675b-instruct` | 85.7% (n=203) | 66.1% (n=668) |
| `harvard_qwen.qwen3-vl-235b-a22b` | 94.6% (n=203) | 69.7% (n=668) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 88.2% (n=203) | 59.3% (n=668) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 97.5% (n=203) | 71.8% (n=668) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 98.5% (n=203) | 72.1% (n=668) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 11.3% (n=203) | 15.0% (n=668) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 28.1% (n=203) | 31.2% (n=668) |
| `openai_gpt-5.4-2026-03-05` | 96.1% (n=203) | 73.3% (n=668) |
| `openai_gpt-5.4-mini-2026-03-17` | 83.7% (n=203) | 62.8% (n=668) |
| `openai_gpt-5.4-nano-2026-03-17` | 65.5% (n=203) | 45.7% (n=668) |
| `openai_gpt-5.5-2026-04-23` | 99.5% (n=203) | 82.5% (n=668) |

> Welch t-test per model comparing groups. Example: en vs it.

## Breakdown by Image Presence (`default`)

| Model | False | True |
|-------|------|------|
| `google_gemini-3-flash-preview` | 75.0% (n=435) | 91.5% (n=436) |
| `google_gemini-3.1-flash-lite-preview` | 65.6% (n=435) | 85.7% (n=436) |
| `google_gemini-3.1-pro-preview` | 82.1% (n=435) | 92.8% (n=436) |
| `google_gemini-3.5-flash` | 73.6% (n=435) | 88.6% (n=436) |
| `harvard_mistral.mistral-large-3-675b-instruct` | 67.7% (n=435) | 73.7% (n=436) |
| `harvard_qwen.qwen3-vl-235b-a22b` | 70.1% (n=435) | 80.9% (n=436) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 58.0% (n=435) | 74.1% (n=436) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 73.0% (n=435) | 82.7% (n=436) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 69.0% (n=435) | 87.5% (n=436) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 15.6% (n=435) | 12.8% (n=436) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 35.1% (n=435) | 25.9% (n=436) |
| `openai_gpt-5.4-2026-03-05` | 73.4% (n=435) | 83.8% (n=436) |
| `openai_gpt-5.4-mini-2026-03-17` | 61.0% (n=435) | 74.4% (n=436) |
| `openai_gpt-5.4-nano-2026-03-17` | 44.7% (n=435) | 56.0% (n=436) |
| `openai_gpt-5.5-2026-04-23` | 81.4% (n=435) | 91.6% (n=436) |

> Welch t-test per model comparing groups. Example: False vs True.

## Breakdown by Language (`motivation`)

| Model | en | it |
|-------|------|------|
| `google_gemini-3-flash-preview` | 99.5% (n=203) | 65.3% (n=668) |
| `google_gemini-3.1-flash-lite-preview` | 98.0% (n=203) | 52.1% (n=668) |
| `google_gemini-3.1-pro-preview` | 100.0% (n=203) | 81.9% (n=668) |
| `google_gemini-3.5-flash` | 99.0% (n=203) | 73.9% (n=668) |
| `harvard_mistral.mistral-large-3-675b-instruct` | 83.7% (n=203) | 67.3% (n=668) |
| `harvard_qwen.qwen3-vl-235b-a22b` | 95.1% (n=203) | 67.2% (n=668) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 88.7% (n=203) | 60.0% (n=668) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 99.0% (n=203) | 73.5% (n=668) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 98.0% (n=203) | 75.6% (n=668) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 10.8% (n=203) | 13.0% (n=668) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 18.2% (n=203) | 31.8% (n=668) |
| `openai_gpt-5.4-2026-03-05` | 96.5% (n=203) | 72.7% (n=668) |
| `openai_gpt-5.4-mini-2026-03-17` | 84.2% (n=203) | 60.7% (n=668) |
| `openai_gpt-5.4-nano-2026-03-17` | 65.5% (n=203) | 36.9% (n=668) |
| `openai_gpt-5.5-2026-04-23` | 99.5% (n=203) | 79.4% (n=668) |

> Welch t-test per model comparing groups. Example: en vs it.

## Breakdown by Image Presence (`motivation`)

| Model | False | True |
|-------|------|------|
| `google_gemini-3-flash-preview` | 60.4% (n=435) | 86.1% (n=436) |
| `google_gemini-3.1-flash-lite-preview` | 54.7% (n=435) | 71.0% (n=436) |
| `google_gemini-3.1-pro-preview` | 80.2% (n=435) | 92.0% (n=436) |
| `google_gemini-3.5-flash` | 71.2% (n=435) | 88.3% (n=436) |
| `harvard_mistral.mistral-large-3-675b-instruct` | 68.0% (n=435) | 74.3% (n=436) |
| `harvard_qwen.qwen3-vl-235b-a22b` | 68.9% (n=435) | 78.5% (n=436) |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 59.0% (n=435) | 74.3% (n=436) |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 74.0% (n=435) | 84.8% (n=436) |
| `harvard_us.anthropic.claude-sonnet-4-6` | 71.0% (n=435) | 90.7% (n=436) |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 14.0% (n=435) | 11.0% (n=436) |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 32.5% (n=435) | 24.7% (n=436) |
| `openai_gpt-5.4-2026-03-05` | 71.7% (n=435) | 84.7% (n=436) |
| `openai_gpt-5.4-mini-2026-03-17` | 59.7% (n=435) | 72.6% (n=436) |
| `openai_gpt-5.4-nano-2026-03-17` | 34.3% (n=435) | 52.9% (n=436) |
| `openai_gpt-5.5-2026-04-23` | 78.8% (n=435) | 89.3% (n=436) |

> Welch t-test per model comparing groups. Example: False vs True.

## Logistic Regression (`default`)

P(correct) ~ question_type + has_image + language + model (n=13,065, threshold=0.5)

Reference categories: type=`multiple_choice_radio`, has_image=False, language=`en`, model=`google_gemini-3-flash-preview`

| Predictor | β | SE | z | p | OR | 95% CI |
|-----------|---|----|----|---|----|---------| 
| intercept | 3.207 | 0.140 | 22.90 | 0.0000 \* | 24.698 | [18.77, 32.50] |
| type:completion_closed | -1.355 | 0.091 | -14.89 | 0.0000 \* | 0.258 | [0.22, 0.31] |
| type:completion_open | -0.879 | 0.092 | -9.52 | 0.0000 \* | 0.415 | [0.35, 0.50] |
| type:multiple_choice_check | 0.419 | 0.096 | 4.37 | 0.0000 \* | 1.520 | [1.26, 1.84] |
| type:positioning | -0.525 | 0.086 | -6.09 | 0.0000 \* | 0.591 | [0.50, 0.70] |
| type:select_errors | -2.984 | 0.110 | -27.07 | 0.0000 \* | 0.051 | [0.04, 0.06] |
| type:true_false | -0.024 | 0.097 | -0.24 | 0.8075 | 0.977 | [0.81, 1.18] |
| has_image:True | -0.273 | 0.063 | -4.30 | 0.0000 \* | 0.761 | [0.67, 0.86] |
| language:it | -0.696 | 0.091 | -7.64 | 0.0000 \* | 0.499 | [0.42, 0.60] |
| model:google_gemini-3.1-flash-lite-preview | -0.643 | 0.144 | -4.47 | 0.0000 \* | 0.526 | [0.40, 0.70] |
| model:google_gemini-3.1-pro-preview | 0.633 | 0.174 | 3.63 | 0.0003 \* | 1.884 | [1.34, 2.65] |
| model:google_gemini-3.5-flash | -0.206 | 0.151 | -1.36 | 0.1741 | 0.814 | [0.60, 1.10] |
| model:harvard_mistral.mistral-large-3-675b-instruct | -0.978 | 0.140 | -7.01 | 0.0000 \* | 0.376 | [0.29, 0.49] |
| model:harvard_qwen.qwen3-vl-235b-a22b | -0.530 | 0.146 | -3.64 | 0.0003 \* | 0.589 | [0.44, 0.78] |
| model:harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 | -1.276 | 0.137 | -9.34 | 0.0000 \* | 0.279 | [0.21, 0.36] |
| model:harvard_us.anthropic.claude-opus-4-6-v1 | -0.521 | 0.146 | -3.57 | 0.0004 \* | 0.594 | [0.45, 0.79] |
| model:harvard_us.anthropic.claude-sonnet-4-6 | -0.380 | 0.148 | -2.57 | 0.0103 \* | 0.684 | [0.51, 0.91] |
| model:harvard_us.meta.llama4-maverick-17b-instruct-v1:0 | -4.134 | 0.149 | -27.72 | 0.0000 \* | 0.016 | [0.01, 0.02] |
| model:harvard_us.mistral.pixtral-large-2502-v1:0 | -2.972 | 0.135 | -22.06 | 0.0000 \* | 0.051 | [0.04, 0.07] |
| model:openai_gpt-5.4-2026-03-05 | -0.360 | 0.148 | -2.43 | 0.0152 \* | 0.697 | [0.52, 0.93] |
| model:openai_gpt-5.4-mini-2026-03-17 | -1.063 | 0.139 | -7.67 | 0.0000 \* | 0.345 | [0.26, 0.45] |
| model:openai_gpt-5.4-nano-2026-03-17 | -2.051 | 0.133 | -15.42 | 0.0000 \* | 0.129 | [0.10, 0.17] |
| model:openai_gpt-5.5-2026-04-23 | 0.545 | 0.171 | 3.18 | 0.0015 \* | 1.725 | [1.23, 2.41] |

> OR > 1 means higher odds of correct answer vs reference. \* = p < 0.05.

## Logistic Regression (`motivation`)

P(correct) ~ question_type + has_image + language + model (n=13,065, threshold=0.5)

Reference categories: type=`multiple_choice_radio`, has_image=False, language=`en`, model=`google_gemini-3-flash-preview`

| Predictor | β | SE | z | p | OR | 95% CI |
|-----------|---|----|----|---|----|---------| 
| intercept | 2.438 | 0.120 | 20.28 | 0.0000 \* | 11.448 | [9.04, 14.49] |
| type:completion_closed | -1.308 | 0.090 | -14.45 | 0.0000 \* | 0.270 | [0.23, 0.32] |
| type:completion_open | -1.004 | 0.090 | -11.10 | 0.0000 \* | 0.367 | [0.31, 0.44] |
| type:multiple_choice_check | 0.025 | 0.091 | 0.28 | 0.7790 | 1.026 | [0.86, 1.23] |
| type:positioning | -0.787 | 0.083 | -9.45 | 0.0000 \* | 0.455 | [0.39, 0.54] |
| type:select_errors | -2.984 | 0.111 | -26.98 | 0.0000 \* | 0.051 | [0.04, 0.06] |
| type:true_false | -0.299 | 0.092 | -3.23 | 0.0012 \* | 0.742 | [0.62, 0.89] |
| has_image:True | -0.187 | 0.061 | -3.04 | 0.0024 \* | 0.830 | [0.74, 0.94] |
| language:it | -0.684 | 0.090 | -7.61 | 0.0000 \* | 0.505 | [0.42, 0.60] |
| model:google_gemini-3.1-flash-lite-preview | -0.619 | 0.117 | -5.31 | 0.0000 \* | 0.539 | [0.43, 0.68] |
| model:google_gemini-3.1-pro-preview | 1.238 | 0.152 | 8.12 | 0.0000 \* | 3.448 | [2.56, 4.65] |
| model:google_gemini-3.5-flash | 0.517 | 0.132 | 3.90 | 0.0001 \* | 1.677 | [1.29, 2.17] |
| model:harvard_mistral.mistral-large-3-675b-instruct | -0.060 | 0.122 | -0.49 | 0.6244 | 0.942 | [0.74, 1.20] |
| model:harvard_qwen.qwen3-vl-235b-a22b | 0.250 | 0.127 | 1.96 | 0.0496 \* | 1.284 | [1.00, 1.65] |
| model:harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0 | -0.357 | 0.119 | -3.01 | 0.0026 \* | 0.700 | [0.55, 0.88] |
| model:harvard_us.anthropic.claude-opus-4-6-v1 | 0.430 | 0.131 | 3.29 | 0.0010 \* | 1.537 | [1.19, 1.98] |
| model:harvard_us.anthropic.claude-sonnet-4-6 | 0.728 | 0.137 | 5.30 | 0.0000 \* | 2.070 | [1.58, 2.71] |
| model:harvard_us.meta.llama4-maverick-17b-instruct-v1:0 | -3.523 | 0.138 | -25.52 | 0.0000 \* | 0.029 | [0.02, 0.04] |
| model:harvard_us.mistral.pixtral-large-2502-v1:0 | -2.281 | 0.117 | -19.51 | 0.0000 \* | 0.102 | [0.08, 0.13] |
| model:openai_gpt-5.4-2026-03-05 | 0.365 | 0.129 | 2.82 | 0.0048 \* | 1.440 | [1.12, 1.86] |
| model:openai_gpt-5.4-mini-2026-03-17 | -0.364 | 0.119 | -3.06 | 0.0022 \* | 0.695 | [0.55, 0.88] |
| model:openai_gpt-5.4-nano-2026-03-17 | -1.615 | 0.114 | -14.21 | 0.0000 \* | 0.199 | [0.16, 0.25] |
| model:openai_gpt-5.5-2026-04-23 | 0.969 | 0.144 | 6.74 | 0.0000 \* | 2.635 | [1.99, 3.49] |

> OR > 1 means higher odds of correct answer vs reference. \* = p < 0.05.

## Hardest Items (p = 0)

**5** items scored 0 across all models and conditions. **18** additional items scored p < 0.10.

**2 flagged for review** (MCQ radio with p=0 — possible data or extraction errors):

| Question | Type | Flag |
|----------|------|------|
| 0681 | multiple_choice_radio | MCQ radio with p=0 — possible data error or extraction issue |
| 0689 | multiple_choice_radio | MCQ radio with p=0 — possible data error or extraction issue |

## Item Discrimination by Question Type

| Type | N | Mean r_pb | Median | Good (≥.30) | Fair (.10–.29) | Poor (<.10) |
|------|---|-----------|--------|-------------|----------------|-------------|
| completion_closed | 69 | 0.532 | 0.543 | 65 | 4 | 0 |
| completion_open | 75 | 0.657 | 0.662 | 74 | 1 | 0 |
| multiple_choice_check | 117 | 0.622 | 0.622 | 113 | 3 | 1 |
| multiple_choice_radio | 360 | 0.678 | 0.726 | 338 | 15 | 7 |
| positioning | 106 | 0.596 | 0.631 | 99 | 5 | 2 |
| select_errors | 48 | 0.418 | 0.409 | 46 | 2 | 0 |
| true_false | 83 | 0.317 | 0.289 | 39 | 34 | 10 |

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
