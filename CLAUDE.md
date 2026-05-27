# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This repo builds and evaluates an art-history question-answering benchmark. It contains 880 questions (677 Italian from MyZanichelli textbook exercises, 203 English from AP Art History exams) across 7 question types, plus a multi-provider LLM evaluation pipeline. See [methodology.md](methodology.md) for the authoritative description of dataset construction, prompting strategy, and evaluation metrics.

## Pipeline Architecture

The project is organized as a 4-stage pipeline. Each stage has a top-level entry-point script that delegates to modules under [questions/modules/](questions/modules/).

1. **Scraping → raw artefacts** ([questions/myzanichelli/1_question_downloader.py](questions/myzanichelli/1_question_downloader.py))
   Playwright automation logs into Zanichelli, walks every exercise, captures full-page screenshots, HTML, and images into `questions/myzanichelli/raw/{exercise}/`. Browser session persisted via [browser_state.json](browser_state.json). Built on the `modules/browser`, `modules/workflows`, `modules/files`, `modules/content` packages composed by [modules/automator.py](questions/modules/automator.py).

2. **Vision-LLM extraction → structured JSON** ([questions/myzanichelli/2_question_preprocessor.py](questions/myzanichelli/2_question_preprocessor.py))
   Each screenshot is submitted to Gemini with prompts in [prompts/extract_*.txt](prompts/) to produce the canonical schema (`type`, `question_text`, `choices`, `answers`, `has_image`, `image`, `language`, `question_title`). Output: `questions/myzanichelli/structured/{exercise}/json/{question}.json`. AP Art History items are parsed from PDFs into the same schema.

3. **Bundling → unified dataset** ([dataset_bundler.py](dataset_bundler.py))
   Aggregates all structured records into [dataset/](dataset/): `data/{id}.txt` (model-ready prompt), `metadata/{id}.json` (full record + categorisation), `imgs/{id}.{ext}` (optimised image). IDs are zero-padded `0001`–`0880` in source order. Categorisation (3 axes — art-historical ontology, cultural/disciplinary context, epistemic level) is added by Gemini calls.

4. **Evaluation → per-model scores** ([llm_questioner.py](llm_questioner.py) → [answer_evaluator.py](answer_evaluator.py))
   `llm_questioner.py` queries one or more models on every question; `answer_evaluator.py` then scores the saved responses against ground truth and writes [answers/README.md](answers/README.md) and [answers/metadata.json](answers/metadata.json).

## Evaluation System Internals

- **Provider abstraction**: [questions/modules/llm/](questions/modules/llm/) — `base.py` defines the interface; `factory.py` instantiates providers from `provider/model` strings. Backends: `anthropic`, `openai`, `google`, `harvard` (AWS Bedrock via Harvard HUIT gateway). Models to test come from the `MODELS_TO_TEST` env var (comma-separated).
- **Two prompt conditions**: `default` (answer-only) and `motivation` (chain-of-thought). Results are stored in `answers/{model_name}/{condition}/`. The motivation condition is a paired counterfactual — both run on the same questions to enable paired comparison (see "Cross-Condition Comparison" in answers/README.md).
- **System prompt**: [prompts/system_prompt.txt](prompts/system_prompt.txt) — frames the model as an art-history scholar, mandates strict JSON output (begins with `{`, no markdown). All queries use `temperature=0.0`.
- **Per-type metrics** ([questions/modules/evaluators/level1_evaluators.py](questions/modules/evaluators/level1_evaluators.py)):
  - `multiple_choice_radio` → exact match
  - `multiple_choice_check`, `select_errors` → F1 (correct if F1 ≥ 0.7)
  - `true_false`, `completion_closed`, `positioning` → recall over (id, text) pairs (threshold 0.8)
  - `completion_open` → recall, with caveat that strict matching understates performance
- **Retry policy**: exponential backoff, max 3 attempts (1s/2s/4s), 0.5s inter-call delay. Failures are logged and skipped, never abort the run.

## Common Commands

```bash
# Install
pip install -r requirements.txt
playwright install   # only needed for stage 1 scraping

# Stage 1 — scrape (requires Zanichelli credentials in questions/myzanichelli/config.json)
cd questions/myzanichelli && python 1_question_downloader.py -e 1
python 1_question_downloader.py --all --headless

# Stage 2 — extract structured JSON from screenshots
cd questions/myzanichelli && python 2_question_preprocessor.py

# Stage 3 — bundle dataset
python dataset_bundler.py

# Stage 4 — query models
python llm_questioner.py --models google/gemini-3.1-pro-preview
python llm_questioner.py --models harvard/us.anthropic.claude-opus-4-6-v1 --workers 4
python llm_questioner.py --prompt-condition motivation --start 1 --end 10
python llm_questioner.py --k-runs 3 --models google/gemini-2.5-flash   # reproducibility check

# Stage 4 — evaluate
python answer_evaluator.py                                              # all models, default condition
python answer_evaluator.py --models google_gemini-3.1-pro-preview
python answer_evaluator.py --condition motivation
python answer_evaluator.py --force                                      # re-score existing results

# Browse results in a Flask UI
python website/answer_viewer.py

# Figures / charts for the paper
python eduart_figures.py
```

## Configuration

- `.env` (template in [.env.example](.env.example)) drives both extraction and evaluation. Key vars:
  - `MODEL_TYPE` (`gemini`|`qwen`), `GEMINI_MODEL_NAME`, `GOOGLE_API_KEY` — extraction.
  - `MODELS_TO_TEST`, `HARVARD_API_KEY`, `HARVARD_API_VERSION`, `HARVARD_OPENAI_TIER`, `ANTHROPIC_API_KEY` — evaluation. **OpenAI models are routed through the Harvard gateway**, not the OpenAI API directly — there is no separate `OPENAI_API_KEY`.
- Zanichelli scraping config: `questions/myzanichelli/config.json` (template adjacent).

## Conventions Worth Knowing

- **Question IDs are immutable, zero-padded, 4 digits** (`0001`–`0880`) and assigned by `dataset_bundler.py` in source order. Downstream tools key off this ID.
- **Answer storage layout**: `answers/{provider}_{model_id_with_dots_intact}/{condition}/{qid}.json`. Provider prefix uses `_` not `/` (e.g., `google_gemini-3.1-pro-preview`, `harvard_us.anthropic.claude-opus-4-6-v1`).
- **Ground-truth caveat**: Zanichelli answers come from a vision-LLM extraction and have a measured error rate. Validation protocol (stratified manual sample + cross-model re-extraction) is documented in §3 of [methodology.md](methodology.md). When debugging "wrong" model answers, check the original screenshot before assuming the model failed.
- **`questions/modules/`** is shared by stages 2–4 — it's on `sys.path` via `sys.path.insert(0, .../questions)` in the entry-point scripts, and imported as `from modules.X import Y`. Don't move it.
- **Two top-level evaluator files exist**: [answer_evaluator.py](answer_evaluator.py) is the current scoring entry point; [questions/modules/evaluators/answer_evaluator.py](questions/modules/evaluators/answer_evaluator.py) hosts the per-type scoring functions used during a live `llm_questioner.py` run. Keep metric definitions consistent between them.
