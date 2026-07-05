# Format Compliance Analysis

Generated: 2026-05-03 14:55  
Condition: `default`

## Background

Low scores on certain question types may reflect **format non-compliance** rather than lack of domain knowledge. Two failure modes are common:

1. **Task confusion on Select Errors.** The prompt asks models to identify incorrect words in a passage and return them as a list. Many models instead return a single `TRUE`/`FALSE` value (confusing the task with True/False) or a single descriptive string (e.g. attempting to name the artwork rather than listing its textual errors). These responses score F1 = 0 regardless of the model's actual art-historical knowledge.
2. **Non-JSON responses.** Some models emit reasoning text or free-form prose instead of the required JSON structure. When `llm_answer` is a raw string rather than a list of `{id, text}` objects, the evaluator cannot extract any answer and every element scores 0.

## Metric Definitions

| Symbol | Definition |
|--------|------------|
| **F1** | Reported F1 score over the full set of Select Errors questions, including responses with wrong format (which contribute F1 = 0). |
| **F1\*** | F1 computed **only** on responses where the model returned the correct format (multiple error-word items). This isolates domain knowledge from format compliance — it answers: *when the model understood the task, how well did it identify the errors?* |
| **Compliance** | Percentage of Select Errors responses where the model returned the correct format (a list of multiple error words). |
| **T/F confusion** | Responses containing a single `TRUE` or `FALSE` value, indicating the model misinterpreted Select Errors as a True/False question. |
| **Single text** | Responses containing a single non-T/F string (e.g. an artwork title or description), indicating the model attempted a different task. |
| **Other wrong** | Non-list responses (raw reasoning text), empty responses, or other unparseable formats. |

## Table 1 — Select Errors: Format Classification

Each response to a Select Errors question is classified into one of four categories based on its structure. The gap between F1 and F1\* quantifies how much of the score deficit is attributable to format non-compliance versus actual domain-knowledge failure.

| Model | N | Correct format | T/F confusion | Single text | Other wrong | Compliance | F1 | F1\* |
|-------|---|----------------|---------------|-------------|-------------|------------|-----|------|
| `google_gemini-3-flash-preview` | 49 | 42 | 0 | 4 | 3 | 86% | 63.5% | 73.2% |
| `google_gemini-3.1-flash-lite-preview` | 49 | 23 | 12 | 14 | 0 | 47% | 11.3% | 21.5% |
| `google_gemini-3.1-pro-preview` | 49 | 47 | 1 | 1 | 0 | 96% | 78.8% | 82.1% |
| `harvard_mistral.mistral-large-3-675b-instruct` | 49 | 13 | 19 | 17 | 0 | 27% | 8.8% | 33.0% |
| `harvard_qwen.qwen3-vl-235b-a22b` | 49 | 8 | 37 | 4 | 0 | 16% | 6.8% | 41.4% |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | 49 | 8 | 5 | 36 | 0 | 16% | 7.6% | 46.2% |
| `harvard_us.anthropic.claude-opus-4-6-v1` | 49 | 32 | 0 | 0 | 17 | 65% | 37.5% | 57.5% |
| `harvard_us.anthropic.claude-sonnet-4-6` | 49 | 11 | 19 | 13 | 6 | 22% | 6.2% | 27.7% |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | 49 | 1 | 2 | 0 | 46 | 2% | 0.9% | 46.2% |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | 49 | 4 | 0 | 0 | 45 | 8% | 3.0% | 36.7% |
| `openai_gpt-5.4-2026-03-05` | 49 | 13 | 25 | 11 | 0 | 27% | 11.7% | 44.2% |
| `openai_gpt-5.4-mini-2026-03-17` | 49 | 8 | 33 | 8 | 0 | 16% | 4.7% | 28.9% |
| `openai_gpt-5.4-nano-2026-03-17` | 49 | 8 | 37 | 4 | 0 | 16% | 1.7% | 10.6% |

> **Reading example:** GPT-5.4 returns the correct format for 13/49 questions (27% compliance). Its reported F1 is 11.7%, but on the 13 correctly-formatted responses it achieves F1\* = 44.2% — the remaining 36 questions score 0 purely due to format failure (51% returned TRUE/FALSE, 22% returned a single text).

## Table 2 — Non-JSON (String) Responses by Question Type

When `llm_answer` is a raw string instead of a JSON list, the evaluator cannot extract structured answers and every element scores 0. This table counts such responses per model and question type.

| Model | MCQ Radio | MCQ Check | True/False | Positioning | Compl. Closed | Compl. Open | Select Errors | **Total** |
|-------|---|---|---|---|---|---|---|---|
| `google_gemini-3-flash-preview` | 0/370 | **1**/117 | **2**/83 | **4**/108 | **1**/69 | **1**/75 | **3**/49 | **12**/871 |
| `google_gemini-3.1-flash-lite-preview` | 0/370 | 0/117 | 0/83 | 0/108 | 0/69 | 0/75 | 0/49 | **0**/871 |
| `google_gemini-3.1-pro-preview` | 0/370 | 0/117 | 0/83 | **1**/108 | 0/69 | **1**/75 | 0/49 | **2**/871 |
| `harvard_mistral.mistral-large-3-675b-instruct` | 0/370 | **1**/117 | 0/83 | 0/108 | 0/69 | **1**/75 | 0/49 | **2**/871 |
| `harvard_qwen.qwen3-vl-235b-a22b` | 0/370 | 0/117 | 0/83 | 0/108 | 0/69 | 0/75 | 0/49 | **0**/871 |
| `harvard_us.anthropic.claude-haiku-4-5-20251001-v1:0` | **6**/370 | 0/117 | 0/83 | 0/108 | 0/69 | 0/75 | 0/49 | **6**/871 |
| `harvard_us.anthropic.claude-opus-4-6-v1` | **5**/370 | **32**/117 | **9**/83 | **1**/108 | 0/69 | **48**/75 | **17**/49 | **112**/871 |
| `harvard_us.anthropic.claude-sonnet-4-6` | 0/370 | 0/117 | 0/83 | 0/108 | 0/69 | 0/75 | **6**/49 | **6**/871 |
| `harvard_us.meta.llama4-maverick-17b-instruct-v1:0` | **284**/370 | **97**/117 | **80**/83 | **108**/108 | **45**/69 | **65**/75 | **46**/49 | **725**/871 |
| `harvard_us.mistral.pixtral-large-2502-v1:0` | **212**/370 | **61**/117 | **31**/83 | **55**/108 | **4**/69 | **42**/75 | **45**/49 | **450**/871 |
| `openai_gpt-5.4-2026-03-05` | 0/370 | 0/117 | 0/83 | 0/108 | 0/69 | 0/75 | 0/49 | **0**/871 |
| `openai_gpt-5.4-mini-2026-03-17` | 0/370 | 0/117 | 0/83 | 0/108 | 0/69 | 0/75 | 0/49 | **0**/871 |
| `openai_gpt-5.4-nano-2026-03-17` | 0/370 | 0/117 | 0/83 | 0/108 | 0/69 | 0/75 | 0/49 | **0**/871 |

> Values show non-JSON count / total questions. Bold highlights non-zero failures. Models with high non-JSON rates (Llama4 Maverick: 83%, Pixtral Large: 52%) have their macro-averaged scores dominated by format failure rather than knowledge gaps.

## Interpretation

The **F1 vs F1\*** gap in Table 1 decomposes the Select Errors score deficit into two components:

- **Format-attributable deficit** = F1\* − F1. This is the score improvement that would result from perfect format compliance alone, holding knowledge constant.
- **Knowledge-attributable deficit** = 100% − F1\*. This is the residual gap that remains even when the model understood the task format.

For example, Claude Sonnet scores F1 = 6.2%. Its F1\* = 27.7%, meaning ~21.5 pp of the deficit is format failure and ~72.3 pp is genuine knowledge or error-detection difficulty. By contrast, Gemini Pro's gap is only ~3.3 pp (78.8% → 82.1%), confirming that its high score reflects both format compliance and domain mastery.

Table 2 reveals a broader pattern: Llama4 Maverick and Pixtral Large fail to produce valid JSON for the majority of questions across **all** types, making their aggregate scores largely uninformative about domain knowledge. Claude Opus shows a localised variant: 48/75 Completion (Open) responses are raw strings, explaining its anomalous 23.9% on that type versus 65%+ for comparably-ranked models.
