#!/usr/bin/env python3
"""Generate per-item and summary metadata for the dataset.

Textual features:   word count (spaCy, language-specific), token count (o200k_base),
                    number of options, avg option length.
Image features:     resolution (width x height), file size, colour mode.
Structural features (type-specific):
  - positioning:       number of elements to arrange
  - true_false:        number of individual statements
  - completion_closed: number of blanks, word-bank-to-blank ratio
  - completion_open:   number of blanks
"""

import json
import os
import re
import csv
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import spacy
import tiktoken
from PIL import Image as PILImage

BASE = Path(__file__).resolve().parent
METADATA_DIR = BASE / "metadata"
IMGS_DIR = BASE / "imgs"
OUT_DIR = BASE / "metadata" / "stats"
OUT_DIR.mkdir(parents=True, exist_ok=True)

enc = tiktoken.get_encoding("o200k_base")
nlp_it = spacy.load("it_core_news_sm", disable=["parser", "ner", "lemmatizer"])
nlp_en = spacy.load("en_core_web_sm", disable=["parser", "ner", "lemmatizer"])


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------

def _option_texts(choices):
    """Extract flat list of option text strings from any choice format."""
    texts = []
    if not choices:
        return texts
    for c in choices:
        if isinstance(c, dict):
            if "text" in c:
                texts.append(c["text"])
            elif "options" in c:
                for o in c["options"]:
                    texts.append(str(o))
        elif isinstance(c, str):
            texts.append(c)
    return texts


def _count_blanks(question_text):
    """Count placeholders like [A], [B], ... in the question text."""
    if not question_text:
        return 0
    return len(re.findall(r"\[[A-Z]\]", question_text))


def _word_count(text, lang="it"):
    """Word count using spaCy language-specific tokenizer."""
    if not text:
        return 0
    nlp = nlp_en if lang == "en" else nlp_it
    doc = nlp(text)
    return sum(1 for tok in doc if not tok.is_space and not tok.is_punct)


# ------------------------------------------------------------------
# load items
# ------------------------------------------------------------------

items = {}
for f in sorted(METADATA_DIR.glob("*.json")):
    items[f.stem] = json.loads(f.read_text(encoding="utf-8"))

print(f"Loaded {len(items)} questions")

# ------------------------------------------------------------------
# per-item features
# ------------------------------------------------------------------

per_item = []

for qid, m in items.items():
    qt = m.get("question_text") or ""
    choices = m.get("choices") or []
    answers = m.get("answers") or []
    qtype = m.get("type", "unknown")
    opt_texts = _option_texts(choices)

    # --- textual features ---
    lang = m.get("language", "it")
    q_tokens = len(enc.encode(qt))
    q_words = _word_count(qt, lang)
    n_options = len(opt_texts)
    opt_token_lengths = [len(enc.encode(t)) for t in opt_texts]
    avg_option_tokens = float(np.mean(opt_token_lengths)) if opt_token_lengths else 0.0

    # total text = question_text + all option texts
    all_text = " ".join([qt] + opt_texts).strip()
    total_tokens = len(enc.encode(all_text)) if all_text else 0
    total_words = _word_count(all_text, lang)

    row = {
        "qid": qid,
        "type": qtype,
        "language": m.get("language", "unknown"),
        "has_image": bool(m.get("has_image")),
        "q_tokens": q_tokens,
        "q_words": q_words,
        "total_tokens": total_tokens,
        "total_words": total_words,
        "n_options": n_options,
        "avg_option_tokens": round(avg_option_tokens, 2),
    }

    # --- image features ---
    if m.get("has_image"):
        img_path = IMGS_DIR / f"{qid}.jpg"
        if img_path.exists():
            try:
                img = PILImage.open(img_path)
                w, h = img.size
                row["img_width"] = w
                row["img_height"] = h
                row["img_resolution"] = w * h
                row["img_file_size_kb"] = round(img_path.stat().st_size / 1024, 1)
                row["img_colour_mode"] = img.mode
            except Exception:
                pass

    # --- structural features (type-specific) ---
    if qtype == "positioning":
        row["n_elements"] = _count_blanks(qt)
    elif qtype == "true_false":
        row["n_statements"] = len(choices)
    elif qtype in ("completion_closed", "completion_open"):
        n_blanks = _count_blanks(qt)
        row["n_blanks"] = n_blanks
        if qtype == "completion_closed" and n_blanks > 0:
            # word bank = total options across all blanks
            word_bank_size = sum(
                len(c.get("options", [])) if isinstance(c, dict) else 0
                for c in choices
            )
            row["word_bank_size"] = word_bank_size
            row["word_bank_to_blank_ratio"] = round(word_bank_size / n_blanks, 2)

    per_item.append(row)

# ------------------------------------------------------------------
# write per-item outputs
# ------------------------------------------------------------------

# JSON
per_item_json = OUT_DIR / "per_item_features.json"
with open(per_item_json, "w", encoding="utf-8") as fh:
    json.dump(per_item, fh, indent=2, ensure_ascii=False)

# CSV
per_item_csv = OUT_DIR / "per_item_features.csv"
all_keys = list(dict.fromkeys(k for r in per_item for k in r))
with open(per_item_csv, "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=all_keys, extrasaction="ignore")
    w.writeheader()
    w.writerows(per_item)

print(f"Wrote {per_item_json}")
print(f"Wrote {per_item_csv}")

# ------------------------------------------------------------------
# summary statistics
# ------------------------------------------------------------------

summary = {}
n = len(per_item)

# --- textual features ---
q_tok_arr = np.array([r["q_tokens"] for r in per_item])
q_word_arr = np.array([r["q_words"] for r in per_item])
t_tok_arr = np.array([r["total_tokens"] for r in per_item])
t_word_arr = np.array([r["total_words"] for r in per_item])
n_opt_arr = np.array([r["n_options"] for r in per_item])
avg_opt_arr = np.array([r["avg_option_tokens"] for r in per_item])

summary["textual_features"] = {
    "question_token_count": {
        "tokenizer": "o200k_base",
        "mean": round(float(np.mean(q_tok_arr)), 1),
        "median": round(float(np.median(q_tok_arr)), 1),
        "std": round(float(np.std(q_tok_arr)), 1),
        "min": int(np.min(q_tok_arr)),
        "max": int(np.max(q_tok_arr)),
    },
    "word_count": {
        "tokenizer": "spacy (it_core_news_sm / en_core_web_sm)",
        "mean": round(float(np.mean(q_word_arr)), 1),
        "median": round(float(np.median(q_word_arr)), 1),
        "std": round(float(np.std(q_word_arr)), 1),
        "min": int(np.min(q_word_arr)),
        "max": int(np.max(q_word_arr)),
    },
    "total_token_count": {
        "description": "question_text + all option texts",
        "tokenizer": "o200k_base",
        "mean": round(float(np.mean(t_tok_arr)), 1),
        "median": round(float(np.median(t_tok_arr)), 1),
        "std": round(float(np.std(t_tok_arr)), 1),
        "min": int(np.min(t_tok_arr)),
        "max": int(np.max(t_tok_arr)),
    },
    "total_word_count": {
        "description": "question_text + all option texts",
        "tokenizer": "spacy (it_core_news_sm / en_core_web_sm)",
        "mean": round(float(np.mean(t_word_arr)), 1),
        "median": round(float(np.median(t_word_arr)), 1),
        "std": round(float(np.std(t_word_arr)), 1),
        "min": int(np.min(t_word_arr)),
        "max": int(np.max(t_word_arr)),
    },
    "number_of_options": {
        "mean": round(float(np.mean(n_opt_arr)), 1),
        "median": int(np.median(n_opt_arr)),
        "min": int(np.min(n_opt_arr)),
        "max": int(np.max(n_opt_arr)),
        "distribution": {str(k): v for k, v in sorted(Counter(n_opt_arr.tolist()).items())},
    },
    "avg_option_length_tokens": {
        "mean": round(float(np.mean(avg_opt_arr[avg_opt_arr > 0])), 1) if np.any(avg_opt_arr > 0) else 0,
        "std": round(float(np.std(avg_opt_arr[avg_opt_arr > 0])), 1) if np.any(avg_opt_arr > 0) else 0,
    },
}

# --- image features ---
img_rows = [r for r in per_item if r.get("img_width")]
if img_rows:
    widths = np.array([r["img_width"] for r in img_rows])
    heights = np.array([r["img_height"] for r in img_rows])
    resolutions = np.array([r["img_resolution"] for r in img_rows])
    filesizes = np.array([r["img_file_size_kb"] for r in img_rows])
    modes = Counter(r.get("img_colour_mode", "unknown") for r in img_rows)

    summary["image_features"] = {
        "count": len(img_rows),
        "resolution": {
            "width": {"mean": round(float(np.mean(widths)), 0), "std": round(float(np.std(widths)), 0),
                       "min": int(np.min(widths)), "max": int(np.max(widths))},
            "height": {"mean": round(float(np.mean(heights)), 0), "std": round(float(np.std(heights)), 0),
                        "min": int(np.min(heights)), "max": int(np.max(heights))},
            "total_pixels": {"mean": round(float(np.mean(resolutions)), 0),
                             "median": round(float(np.median(resolutions)), 0)},
        },
        "file_size_kb": {
            "mean": round(float(np.mean(filesizes)), 1),
            "std": round(float(np.std(filesizes)), 1),
            "min": round(float(np.min(filesizes)), 1),
            "max": round(float(np.max(filesizes)), 1),
        },
        "colour_mode": dict(modes.most_common()),
    }

# --- structural features ---
type_groups = defaultdict(list)
for r in per_item:
    type_groups[r["type"]].append(r)

structural = {}
for t, grp in sorted(type_groups.items()):
    entry = {"count": len(grp)}

    if t == "positioning":
        vals = np.array([r.get("n_elements", 0) for r in grp])
        entry["n_elements"] = {
            "mean": round(float(np.mean(vals)), 1),
            "std": round(float(np.std(vals)), 1),
            "min": int(np.min(vals)),
            "max": int(np.max(vals)),
        }

    elif t == "true_false":
        vals = np.array([r.get("n_statements", 0) for r in grp])
        entry["n_statements"] = {
            "mean": round(float(np.mean(vals)), 1),
            "std": round(float(np.std(vals)), 1),
            "min": int(np.min(vals)),
            "max": int(np.max(vals)),
        }

    elif t == "completion_closed":
        blanks = np.array([r.get("n_blanks", 0) for r in grp])
        ratios = np.array([r.get("word_bank_to_blank_ratio", 0) for r in grp])
        entry["n_blanks"] = {
            "mean": round(float(np.mean(blanks)), 1),
            "std": round(float(np.std(blanks)), 1),
            "min": int(np.min(blanks)),
            "max": int(np.max(blanks)),
        }
        valid_ratios = ratios[ratios > 0]
        if len(valid_ratios):
            entry["word_bank_to_blank_ratio"] = {
                "mean": round(float(np.mean(valid_ratios)), 2),
                "std": round(float(np.std(valid_ratios)), 2),
            }

    elif t == "completion_open":
        blanks = np.array([r.get("n_blanks", 0) for r in grp])
        entry["n_blanks"] = {
            "mean": round(float(np.mean(blanks)), 1),
            "std": round(float(np.std(blanks)), 1),
            "min": int(np.min(blanks)),
            "max": int(np.max(blanks)),
        }

    structural[t] = entry

summary["structural_features"] = structural

# write summary
summary_path = OUT_DIR / "summary.json"
with open(summary_path, "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=2, ensure_ascii=False)

print(f"Wrote {summary_path}")

# ------------------------------------------------------------------
# quick console report
# ------------------------------------------------------------------

tf = summary["textual_features"]
print(f"\n--- Textual Features ---")
print(f"  Token count (stem):  mean={tf['question_token_count']['mean']}, "
      f"median={tf['question_token_count']['median']}, "
      f"std={tf['question_token_count']['std']}")
print(f"  Word count (stem):   mean={tf['word_count']['mean']}, "
      f"median={tf['word_count']['median']}")
print(f"  Token count (total): mean={tf['total_token_count']['mean']}, "
      f"median={tf['total_token_count']['median']}, "
      f"std={tf['total_token_count']['std']}")
print(f"  Word count (total):  mean={tf['total_word_count']['mean']}, "
      f"median={tf['total_word_count']['median']}")
print(f"  Options:      mean={tf['number_of_options']['mean']}, "
      f"range=[{tf['number_of_options']['min']}, {tf['number_of_options']['max']}]")
print(f"  Avg opt len:  mean={tf['avg_option_length_tokens']['mean']} tokens")

if "image_features" in summary:
    imf = summary["image_features"]
    print(f"\n--- Image Features ({imf['count']} items) ---")
    print(f"  Width:     mean={imf['resolution']['width']['mean']}, "
          f"std={imf['resolution']['width']['std']}")
    print(f"  Height:    mean={imf['resolution']['height']['mean']}, "
          f"std={imf['resolution']['height']['std']}")
    print(f"  File size: mean={imf['file_size_kb']['mean']} KB, "
          f"range=[{imf['file_size_kb']['min']}, {imf['file_size_kb']['max']}] KB")
    print(f"  Colour modes: {imf['colour_mode']}")

print(f"\n--- Structural Features ---")
for t, s in structural.items():
    parts = [f"{t} (n={s['count']})"]
    for k, v in s.items():
        if k == "count":
            continue
        if isinstance(v, dict) and "mean" in v:
            parts.append(f"  {k}: mean={v['mean']}, std={v.get('std', '-')}")
    print("  " + "\n  ".join(parts))
