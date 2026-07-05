# EduArt

**EduArt: An educational-level benchmark for evaluating art history knowledge in large language models**

> Submitted to *Computational Humanities Research* (CHR), 2026
>
> Authors: anonymous
>
> Paper: anonymous

---

## Overview

EduArt is a benchmark for evaluating multimodal large language models on art-historical knowledge and visual reasoning at educational level. It comprises **871 human-authored questions** drawn from two real educational sources — Italian secondary-school exercises (MyZanichelli) and United States AP Art History exams (College Board) — spanning **7 question formats** and **2 languages**.

Twelve models from six provider families were evaluated under two conditions — a **default** answer-only condition and a **motivation** condition requiring a written justification — and the benchmark was characterized using Classical Test Theory and a logistic regression isolating the effects of format, language, image presence, and model. Multiple-choice accuracy saturates near ceiling for several models, while the same models fall far lower on formats that require producing rather than recognizing content (e.g., open completion, error identification), indicating that art-historical knowledge and the ability to deploy it are distinct capabilities.

---

## Dataset at a Glance

| | |
|---|---|
| Total questions | 871 |
| Languages | Italian 668 · English 203 |
| Sources | MyZanichelli exercises (57 exercises, theme: *Pittura rinascimentale* / Renaissance painting) · College Board AP Art History released exams (2013–2024) |
| Questions with images | 436 (435 image-absent) |
| Distinct images | 261 |
| Question types | 7 |
| Models evaluated | 12 |
| Prompt conditions | 2 (default, motivation) |

---

## Dataset Description

### Sources

**Italian corpus** (668 questions): Exercises collected from the MyZanichelli digital exercise platform (Zanichelli, an Italian academic publisher), restricted to the *Pittura rinascimentale* (Renaissance painting) theme — 57 exercises in total. Each screenshot was extracted into a canonical JSON schema by independently running two vision-LLM extractions (Google Gemini 3 Flash and Anthropic Claude Sonnet 4.5) and manually reconciling discrepancies.

**English corpus** (203 questions): Single-answer multiple-choice items parsed from released College Board Advanced Placement (AP) Art History examinations, covering the years 2013–2024.

### Question Types

| Type | Count | Evaluation metric (as scored) |
|---|---:|---|
| Multiple-choice – single answer (radio) | 370 | Exact match |
| Multiple-choice – multi-select (check) | 117 | F1 over selected options |
| True / False | 83 | Statement-level accuracy |
| Positioning (drag word into text) | 108 | Element-level accuracy |
| Completion – closed (constrained word bank) | 69 | Blank-level accuracy, normalized exact match |
| Completion – open (unconstrained) | 75 | Blank-level accuracy, fuzzy string match |
| Select errors (identify incorrect words in text) | 49 | F1 over predicted vs. ground-truth error sets |
| **Total** | **871** | |

### Item Length

Word counts (spaCy language-specific tokenizers) and token counts (`o200k_base` encoder), across title, instruction, body text, and options where present:

| Metric | Mean | Median | Std | Min | Max |
|---|---:|---:|---:|---:|---:|
| Word count | 53.4 | 54.0 | 32.9 | 4 | 148 |
| Token count | 91.2 | 92.0 | 59.0 | 8 | 250 |

### Images

436 of 871 questions (435 are image-absent) are flagged as having an associated artwork image, drawn from 261 distinct images (some AP items share an image; each question is still treated as a separate item).

| Metric | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| Width (px) | 470 | 297 | 180 | 1568 |
| Height (px) | 463 | 193 | 194 | 1568 |
| File size (KB) | 213.3 | 55.4 | 61.5 | 435.0 |

---

## Repository Structure

```
.
├── dataset/                      Canonical dataset bundle
│   ├── data/{0001–0871}.txt      Model-ready prompt text (one file per question)
│   ├── metadata/{id}.json        Full structured record + categorisation
│   └── imgs/{id}.jpg             Optimised artwork images (RGB JPEG)
├── questions/
│   ├── myzanichelli/             Scraping (stage 1) & extraction (stage 2)
│   └── modules/                  Shared LLM, browser, and evaluation modules
├── answers/
│   ├── {provider}_{model}/       Per-model response directories
│   │   ├── default/              Answer-only condition
│   │   └── motivation/           Motivation (justification) condition
│   ├── README.md                 Full evaluation results & statistics
│   └── metadata.json             Aggregate scores (all models × all types)
├── prompts/                      System prompt & answer-question prompt templates
├── llm_questioner.py             Stage 4a — query models
├── answer_evaluator.py           Stage 4b — score responses
└── dataset_bundler.py            Stage 3 — bundle dataset
```

Question IDs are zero-padded 4-digit integers (`0001`–`0871`) assigned by source order and treated as immutable keys throughout the pipeline.

---

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and populate the environment file
cp .env.example .env
```

Edit `.env` and add the relevant API keys:

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Gemini models (direct) |
| `ANTHROPIC_API_KEY` | Claude models (direct) |
| `HARVARD_API_KEY` | Institutional AWS Bedrock / OpenAI-compatible gateway (routes OpenAI, Anthropic, Mistral, Qwen models used in the evaluation) |

> **Note**: In this project OpenAI models are routed through the institutional gateway above, not the OpenAI API directly — no separate `OPENAI_API_KEY` is needed.

---

## Reproducing the Evaluation

The dataset bundle (`dataset/`) is included in the repository. Stages 1–2 (scraping and vision extraction) require institutional MyZanichelli credentials and are not needed to reproduce the evaluation results.

```bash
# Query a single model (default condition)
python llm_questioner.py --models google/gemini-3.1-pro-preview

# Query with a required justification (motivation condition)
python llm_questioner.py --prompt-condition motivation --models google/gemini-3.1-pro-preview

# Evaluate all available model responses
python answer_evaluator.py

# Evaluate a specific model
python answer_evaluator.py --models google_gemini-3.1-pro-preview

# Evaluate the motivation condition
python answer_evaluator.py --condition motivation

# Reproducibility check (k independent runs)
python llm_questioner.py --k-runs 3 --models google/gemini-3.1-pro-preview
```

Temperature is configured per provider rather than uniformly: 0 for Anthropic Claude models and for open-weight models accessed via AWS Bedrock; 1 with a fixed seed (where the API permits) for Google Gemini models; and the provider default of 1 for GPT-5.x models, which do not expose temperature as a configurable parameter. Each question/model/condition combination is evaluated in a single forward pass. Full pipeline documentation — including stages 1–2 and all CLI flags — is in [CLAUDE.md](CLAUDE.md).

---

## Key Results

### Leaderboard (macro-average across the 7 question formats, default condition, *n* = 871)

| Rank | Model | Macro Avg | MCQ Exact Match | 95% CI (MCQ) |
|---:|---|---:|---:|---:|
| 1 | Gemini 3.1 Pro Preview | **82.8%** | 95.7% | [93.1%, 97.3%] |
| 2 | GPT-5.5 | **80.0%** | 95.1% | [92.4%, 96.9%] |
| 3 | Gemini 3.5 Flash | **68.9%** | 96.5% | [94.1%, 97.9%] |
| 4 | Claude Opus 4.6 | **67.3%** | 94.6% | [91.8%, 96.5%] |
| 5 | Claude Sonnet 4.6 | **64.8%** | 94.3% | [91.5%, 96.3%] |
| 6 | Qwen3-VL-235B | **64.5%** | 88.6% | [85.0%, 91.5%] |
| 7 | Gemini 3.1 Flash Lite Preview | **62.8%** | 92.4% | [89.3%, 94.7%] |
| 8 | Mistral Large 3 675B | **58.8%** | 84.6% | [80.6%, 87.9%] |
| 9 | GPT-5.4 Mini | **54.9%** | 82.7% | [78.5%, 86.2%] |
| 10 | Claude Haiku 4.5 | **53.1%** | 84.0% | [80.0%, 87.4%] |
| 11 | GPT-5.4 Nano | **40.1%** | 62.7% | [57.7%, 67.5%] |
| 12 | Pixtral Large | **29.1%** | 28.6% | [24.3%, 33.5%] |

Six models exceed 90% MCQ exact match, with the top five (Gemini 3.1 Pro Preview, GPT-5.5, Gemini 3.5 Flash, Claude Opus 4.6, Claude Sonnet 4.6) showing overlapping confidence intervals. Full per-type breakdowns are in [answers/README.md](answers/README.md).

### Item-Level Psychometrics (Classical Test Theory)

Difficulty (*p*, proportion of models answering correctly) across all 871 items — mean *p* = 0.696, SD = 0.232:

| Category | *p* range | Count |
|---|---|---:|
| Very Easy | ≥ 0.90 | 195 |
| Easy | 0.70–0.89 | 316 |
| Medium | 0.30–0.69 | 295 |
| Hard | 0.10–0.29 | 40 |
| Very Hard | < 0.10 | 25 |

Discrimination (point-biserial correlation, r_pb) by question type — computed on 831 of 871 items (the remaining 40, including 37 MCQ-radio items, were answered correctly by all 12 models and have zero variance):

| Type | N | Mean r_pb | Good (≥.30) | Fair (.10–.29) | Poor (<.10) |
|---|---:|---:|---:|---:|---:|
| MCQ radio | 333 | 0.608 | 305 | 11 | 17 |
| Completion (open) | 75 | 0.532 | 67 | 6 | 2 |
| Positioning | 106 | 0.505 | 84 | 16 | 6 |
| Completion (closed) | 69 | 0.501 | 58 | 9 | 2 |
| MCQ check | 117 | 0.471 | 91 | 18 | 8 |
| Select errors | 48 | 0.445 | 45 | 3 | 0 |
| True/False | 83 | 0.245 | 34 | 25 | 24 |
| **All items** | **831** | **0.514** | **684** | **88** | **59** |

Mean discrimination across the benchmark is 0.514, with 82.3% of estimable items classified as good discriminators.

### Question Format Effects

A logistic regression on item-level accuracy (*n* = 10,452 observations = 871 items × 12 models; reference category: MCQ radio, no image, English, Gemini 3.1 Flash Lite Preview) isolates format as an independent predictor, controlling for image presence, language, and model:

| Predictor | Odds Ratio | 95% CI | *p* |
|---|---:|---|---|
| MCQ check | 1.655 | [1.35, 2.04] | <.001 |
| True/false | 0.939 | [0.77, 1.15] | .546 |
| Positioning | 0.727 | [0.60, 0.88] | <.001 |
| Completion (closed) | 0.256 | [0.21, 0.31] | <.001 |
| Completion (open) | 0.432 | [0.35, 0.53] | <.001 |
| Select errors | 0.045 | [0.04, 0.06] | <.001 |
| Image present | 0.765 | [0.67, 0.88] | <.001 |
| Language: Italian | 0.459 | [0.38, 0.56] | <.001 |

MCQ check is the only non-reference format with higher odds than MCQ radio (attributable to partial-credit F1 scoring rather than genuine simplicity); true/false does not differ significantly from MCQ radio. All other formats show significantly lower odds of a correct response. No model ranks consistently across formats: GPT-5.5 leads on positioning (89.3%), Gemini 3.1 Pro Preview leads on select errors (78.8%) while GPT-5.4 Nano scores 1.7%, and Gemini 3.5 Flash leads MCQ radio (96.5%) but scores 58.7% on true/false. The spread between a model's best and worst format exceeds 50 percentage points for 10 of the 12 models — only Gemini 3.1 Pro Preview (29.4 pp) and GPT-5.5 (45.9 pp) show narrower spreads.

### Image Presence and Language

Raw accuracy is higher on image-present items for 11 of 12 models (+6.0 pp for Mistral Large 3 to +18.5 pp for Claude Sonnet 4.6; the exception is Pixtral Large at −9.2 pp), but the image-present and image-absent subsets are not matched on type or language. After controlling for question type, language, and model in the logistic regression above, image presence is associated with **lower** odds of a correct response (OR = 0.765, 95% CI [0.67, 0.88], *p* < .001) — i.e., once other factors are accounted for, images make items genuinely harder, consistent with visual interpretation being a real source of difficulty rather than an aid.

Italian-language items also show significantly lower odds of a correct response than English items (OR = 0.459, 95% CI [0.38, 0.56], *p* < .001), controlling for format, image presence, and model.

### Motivation Condition

Requiring models to justify their answer changes accuracy in a predominantly negative, model-family-dependent direction. All three Claude models improve (largest: Claude Sonnet 4.6, +2.6 pp), while both Gemini models and all three GPT models degrade (largest degradations: Gemini 3.1 Flash Lite Preview, −12.8 pp, and GPT-5.4 Nano, −6.7 pp). Mistral Large 3 also improves slightly (+0.4 pp), while Qwen3-VL-235B (−1.8 pp) and Pixtral Large (−1.9 pp) show small declines.

Mean paired difference (motivation − default) by question type, averaged across the twelve models:

| Question Type | Mean Δ (pp) | Range (pp) |
|---|---:|---|
| Completion (closed) | +2.0 | [−35.0, +40.9] |
| Select errors | −0.7 | [−13.1, +16.1] |
| MCQ radio | −0.9 | [−4.0, +1.1] |
| Completion (open) | −2.7 | [−16.6, +16.0] |
| MCQ check | −4.1 | [−33.3, +5.1] |
| True/false | −4.6 | [−14.1, +0.8] |
| Positioning | −4.6 | [−26.7, +12.9] |

### Summary

- **Format is a strong independent predictor of accuracy**: models exceeding 94% on MCQ can fall to 23.9% on open completion (Claude Opus 4.6) or 6.2% on error identification (Claude Sonnet 4.6).
- **MCQ saturates**: six models score 92–97% with overlapping confidence intervals, and 37 MCQ-radio items are answered correctly by every model, carrying no diagnostic signal.
- **Images and Italian-language items are independently harder**, once format and model are controlled for — despite raw image-present accuracy being higher for most models before controlling for confounds.
- **The motivation (justification) condition helps Claude models and hurts Gemini and GPT models**, indicating that the effect of elicited reasoning on accuracy is family-dependent rather than universal.
- **The benchmark is well-calibrated**: item difficulty spans the full range (mean *p* = 0.696, SD = 0.232) and discrimination is strong for the large majority of items (mean r_pb = 0.514, 82.3% good discriminators).

---

## Citation

If you use EduArt in your research, please cite:

```bibtex
@inproceedings{eduart2026,
  title     = {{EduArt}: An educational-level benchmark for evaluating
               art history knowledge in large language models},
  author    = {[Author names]},
  booktitle = {Proceedings of the Computational Humanities Research
               Conference (CHR)},
  year      = {2026},
  url       = {[preprint URL — coming soon]}
}
```

---

## Data & License

**Code** is released under the MIT License.

**Dataset**: The English subset is derived from publicly available AP Art History exams (College Board, 2013–2024). The Italian subset is extracted from MyZanichelli copyrighted materials and is made available for **non-commercial research use only**.
