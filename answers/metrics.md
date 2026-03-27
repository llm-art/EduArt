# Evaluation Metrics

This document describes the evaluation metrics used for each question type, with concrete examples from the dataset.

---

## 1. `multiple_choice_radio` (370 items)

**Task**: Select the single correct option from a list of choices.

**Primary metric**: **Exact Match** -- 1 if the predicted option matches the ground truth, 0 otherwise.

### Example (Question 0001)

```json
{
  "ground_truth": [{"id": "C", "description": "Annunciation"}],
  "llm_response": [{"id": "C"}],
  "exact_match": 1.0
}
```

### Scoring

| Metric | Definition |
|--------|-----------|
| **Exact Match** | 1 if predicted ID = ground-truth ID, 0 otherwise |
| Partial credit | None -- binary outcome |

**Notes**: If the LLM returns multiple IDs (wrong format), credit is given if the correct answer is among the predicted set. This is the cleanest question type with no ambiguity in evaluation.

---

## 2. `multiple_choice_check` (117 items)

**Task**: Select all correct options from a list (multiple selection).

**Primary metric**: **F1 Score** -- harmonic mean of precision and recall over the selected option set.

### Example (Question 0207)

```json
{
  "ground_truth": [{"id": "A"}, {"id": "B"}, {"id": "E"}],
  "llm_response": [{"id": "A"}, {"id": "B"}, {"id": "E"}],
  "precision": 1.0,
  "recall": 1.0,
  "f1": 1.0,
  "exact_match": 1.0,
  "jaccard": 1.0
}
```

### Partial credit example

```json
{
  "ground_truth": ["A", "C", "D"],
  "llm_response": ["A", "C", "E"],
  "tp": 2,
  "precision": 0.667,
  "recall": 0.667,
  "f1": 0.667,
  "exact_match": 0.0,
  "jaccard": 0.5
}
```

### Scoring

| Metric | Definition |
|--------|-----------|
| **F1 Score** (primary) | 2 x Precision x Recall / (Precision + Recall) |
| Subset accuracy (exact match) | 1 if predicted set = ground-truth set exactly |
| Precision | Correct selections / total selections |
| Recall | Correct selections / total correct options |
| Jaccard similarity | |intersection| / |union| of predicted and ground-truth sets |

**Notes**: The LLM may return answers in TRUE/FALSE format (e.g., `[{"id": "A", "text": "TRUE"}, {"id": "B", "text": "FALSE"}]`). In this case, only IDs marked TRUE/VERO are extracted as the selected set.

---

## 3. `true_false` (83 items)

**Task**: For each statement in the item, classify it as True or False.

**Primary metric**: **Statement-level Accuracy** -- proportion of individual statements correctly classified.

### Example (Question 0210)

```json
{
  "ground_truth": [
    {"id": "A", "text": "True"},
    {"id": "B", "text": "True"},
    {"id": "C", "text": "False"},
    {"id": "D", "text": "False"},
    {"id": "E", "text": "False"}
  ],
  "llm_response": [{"id": "A"}, {"id": "B"}],
  "evaluation": {
    "A": {"gt": "True",  "pred": "True",  "correct": true},
    "B": {"gt": "True",  "pred": "True",  "correct": true},
    "C": {"gt": "False", "pred": "False", "correct": true},
    "D": {"gt": "False", "pred": "",      "correct": false},
    "E": {"gt": "False", "pred": "",      "correct": false}
  },
  "statement_accuracy": 0.6,
  "exact_match": 0.0
}
```

### Scoring

| Metric | Definition |
|--------|-----------|
| **Statement Accuracy** (primary) | Correct statements / total statements |
| Item-level Exact Match | 1 if all statements correct, 0 otherwise |

**Text normalisation**: The evaluator normalises T/F values: `true`, `vero`, `t`, `v`, `1` map to True; everything else maps to False. This handles Italian (`Vero`/`Falso`) and English (`True`/`False`) equivalently.

**Notes**: Items vary from 3 to 8+ statements. Item-level exact match penalises longer items disproportionately -- an item with 8 statements is much harder to get exactly right than one with 3. Statement-level accuracy is therefore the primary metric.

---

## 4. `positioning` (108 items)

**Task**: Match elements to positions or fill blanks with the correct term from a list.

**Primary metric**: **Element-level Accuracy** -- proportion of elements correctly placed.

### Example (Question 0220)

```json
{
  "ground_truth": [
    {"id": "A", "description": "Mantova"},
    {"id": "B", "description": "Mantegna"},
    {"id": "C", "description": "San Giorgio"},
    {"id": "D", "description": "1474"},
    {"id": "E", "description": "illusionistico"},
    {"id": "F", "description": "prospettiva"}
  ],
  "llm_response": [
    {"id": "A", "text": "Mantova"},
    {"id": "B", "text": "Mantegna"},
    {"id": "C", "text": "San Giorgio"},
    {"id": "D", "text": "1474"},
    {"id": "E", "text": "illusionistico"},
    {"id": "F", "text": "prospettiva"}
  ],
  "element_accuracy": 1.0,
  "exact_match": 1.0
}
```

### Partial credit example

```json
{
  "ground_truth": {"A": "Roma", "B": "1455", "C": "Donatello", "D": "bronzo"},
  "llm_response": {"A": "Roma", "B": "1460", "C": "Donatello", "D": "marmo"},
  "evaluation": {
    "A": {"gt": "Roma",      "pred": "Roma",      "correct": true},
    "B": {"gt": "1455",      "pred": "1460",      "correct": false},
    "C": {"gt": "Donatello", "pred": "Donatello", "correct": true},
    "D": {"gt": "bronzo",    "pred": "marmo",     "correct": false}
  },
  "element_accuracy": 0.5,
  "exact_match": 0.0
}
```

### Scoring

| Metric | Definition |
|--------|-----------|
| **Element Accuracy** (primary) | Correct placements / total elements |
| Exact Match | 1 if all elements correct |
| Kendall's tau | Rank correlation (only for numeric ordering tasks) |

**Text matching**: Comparison uses normalised strings (lowercase, accent-removed, punctuation-stripped). `"San Giorgio"` matches `"san giorgio"`.

**Kendall's tau**: Computed only when all values are numeric (e.g., chronological ordering). Measures rank correlation: 1.0 = perfect order, -1.0 = reversed, 0 = random.

---

## 5. `completion_closed` (69 items)

**Task**: Fill blanks in a text from a constrained word bank.

**Primary metric**: **Blank-level Accuracy** -- proportion of blanks correctly filled.

### Example (Question 0212)

```json
{
  "ground_truth": [
    {"id": "A", "description": "San Giorgio"},
    {"id": "B", "description": "Mantova"},
    {"id": "C", "description": "sfondamento"},
    {"id": "D", "description": "volta"},
    {"id": "E", "description": "Gonzaga"},
    {"id": "F", "description": "Cardinale"},
    {"id": "G", "description": "Francesco"}
  ],
  "llm_response": [
    {"id": "A", "text": "San Giorgio"},
    {"id": "B", "text": "Mantova"},
    {"id": "C", "text": "sfondamento"},
    {"id": "D", "text": "volta"},
    {"id": "E", "text": "Gonzaga"},
    {"id": "F", "text": "Cardinale"},
    {"id": "G", "text": "Francesco"}
  ],
  "blank_accuracy": 1.0,
  "exact_match": 1.0
}
```

### Scoring

| Metric | Definition |
|--------|-----------|
| **Blank Accuracy** (primary) | Correct blanks / total blanks |
| Item-level Exact Match | 1 if all blanks correct |

**Text matching**: Same normalisation as positioning -- case-insensitive, accent-insensitive, punctuation-stripped. `"Chiaroscuro"` matches `"chiaroscuro"`.

**Notes**: Since answers are drawn from a constrained word bank, responses outside the vocabulary indicate a format error rather than a knowledge error.

---

## 6. `completion_open` (75 items)

**Task**: Fill blanks with free-text answers (no word bank).

**Primary metric**: **Blank-level Accuracy** -- proportion of blanks correctly filled using normalised string matching.

### Example (Question 0223)

```json
{
  "ground_truth": [
    {"id": "A", "description": "1475"},
    {"id": "B", "description": "piccola"},
    {"id": "C", "description": "arco"},
    {"id": "D", "description": "gotico"},
    {"id": "E", "description": "vano"},
    {"id": "F", "description": "accesso"},
    {"id": "G", "description": "teatrale"}
  ],
  "llm_response": [
    {"id": "A", "text": "1475"},
    {"id": "B", "text": "piccola"},
    {"id": "C", "text": "arco"},
    {"id": "D", "text": "gotico"},
    {"id": "E", "text": "vano"},
    {"id": "F", "text": "proscenio"},
    {"id": "G", "text": "ottica"}
  ],
  "evaluation": {
    "A": {"correct": true},
    "B": {"correct": true},
    "C": {"correct": true},
    "D": {"correct": true},
    "E": {"correct": true},
    "F": {"gt": "accesso",  "pred": "proscenio", "correct": false},
    "G": {"gt": "teatrale", "pred": "ottica",    "correct": false}
  },
  "blank_accuracy": 0.714,
  "exact_match": 0.0
}
```

### Scoring

| Metric | Definition |
|--------|-----------|
| **Blank Accuracy** (primary) | Correct blanks / total blanks |
| Item-level Exact Match | 1 if all blanks correct |

**Limitations**: Normalised string matching is strict -- synonyms score 0. For example, `"proto-Renaissance"` vs `"early Renaissance"` would both be correct but score as a mismatch. For this reason, completion_open results should be interpreted cautiously and ideally supplemented with LLM-as-judge or human evaluation on a subsample.

---

## 7. `select_errors` (49 items)

**Task**: Identify errors in a passage (incorrect terms that should be corrected).

**Primary metric**: **F1 Score** -- over the set of identified errors vs ground-truth errors.

### Example (Question 0213)

```json
{
  "ground_truth": [
    {"error": "1450",     "correct": "1490"},
    {"error": "secondo",  "correct": "primo"},
    {"error": "siepe",    "correct": "transenna"},
    {"error": "a terra",  "correct": "al cielo"},
    {"error": "impudica", "correct": "eroica"},
    {"error": "gotica",   "correct": "classica"}
  ],
  "gt_error_set_normalised": ["1450", "secondo", "siepe", "a terra", "impudica", "gotica"],
  "llm_response": [
    {"id": "A", "text": "1450"},
    {"id": "B", "text": "secondo piano"},
    {"id": "C", "text": "bassa siepe"},
    {"id": "D", "text": "a terra"},
    {"id": "E", "text": "gotica"}
  ],
  "pred_error_set_normalised": ["1450", "secondo piano", "bassa siepe", "a terra", "gotica"],
  "matching": {
    "1450":          "TP (exact match in GT)",
    "secondo piano": "FP (GT has 'secondo', not 'secondo piano')",
    "bassa siepe":   "FP (GT has 'siepe', not 'bassa siepe')",
    "a terra":       "TP (exact match in GT)",
    "gotica":        "TP (exact match in GT)",
    "missing":       ["secondo", "siepe", "impudica"]
  },
  "precision": 0.6,
  "recall": 0.5,
  "f1": 0.545,
  "exact_match": 0.0
}
```

### Scoring

| Metric | Definition |
|--------|-----------|
| **F1 Score** (primary) | 2 x Precision x Recall / (Precision + Recall) |
| Precision | Correctly identified errors / total flagged errors |
| Recall | Correctly identified errors / total actual errors |
| Exact Match | 1 if predicted error set = ground-truth error set exactly |

---

## Text Normalisation

All string comparisons apply the following normalisation pipeline:

1. Convert to lowercase
2. Unicode NFD normalisation, remove combining characters (accents)
3. Remove punctuation
4. Collapse whitespace

This means `"Chiaroscuro"`, `"chiaroscuro"`, and `"chiaro-scuro"` are treated as matches for the first two but not the third (hyphen is punctuation, so `"chiaroscuro"` vs `"chiaroscuro"` would match).

For Italian items, accented characters like `e`, `a`, `u` are normalised to their base forms.
