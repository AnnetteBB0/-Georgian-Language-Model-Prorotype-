# CGC Backend

Georgian spell checker API (FastAPI + Hunspell via [spylls](https://github.com/zverok/spylls)).

Current structure:

- `preprocessor.py`: normalization and tokenization
- `spellcheck.py`: Hunspell lookup and annotation creation
- `grammar.py`: grammar rules engine with integrated rule systems
- `main.py`: FastAPI API layer
- `benchmark_spellcheck.py`: quick performance benchmark
- `verbal_system_rules.py`: Georgian verbal system specification loader (from rules1.json)
- `rules1.json`: Georgian verbal system reference data (screeves, verb classes)
- `Rules/`: Georgian case alignment and verb conjugation rules
- `grammar2/`: Postposition governance, confusable words, demonstrative agreement, proper nouns, double negatives
- `georgian_grammar/`: Desktop rules for postpositions, adjective declension, and possessive adjectives

## Setup

```bash
cd backend
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

If your existing virtual environment was created with a different Python interpreter,
recreate it before running the app. A broken venv can fail with errors like
`No module named 'encodings'`.

If you want Stanza-backed Georgian analysis, install dependencies and download the
language model once:

```bash
python -c "import stanza; stanza.download('ka')"
```

The Georgian dictionary (`dictionaries/ka_GE/ka_GE.aff` and `ka_GE.dic`) is included.
Source: [gamag/ka_GE.spell](https://github.com/gamag/ka_GE.spell) (MIT).

## Run locally

```bash
uvicorn main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Try it

```bash
curl -X POST http://127.0.0.1:8000/v1/check \
  -H "Content-Type: application/json" \
  -d '{"text": "გამარჯობა, როგორ ხარ? ეს არის შეცდომaa."}'
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/v1/check` | Check Georgian spelling and grammar |

Request body:

```json
{
  "text": "თქვენი ტექსტი",
  "options": {
    "check_spelling": true,
    "check_grammar": true,
    "extra_words": ["სახელი", "ბრენდი"]
  }
}
```

Response annotations include character `start`/`end` offsets for underlining in the UI.

## Current spellcheck behavior

- Pure Georgian words are checked against Hunspell.
- Request-level allowlisting is supported with `options.extra_words`.
- Mixed-script tokens such as `შეცდომaa` are flagged as a full-token spelling issue.
- Suggestion generation is intentionally skipped for long unknown words to keep live
  checking responsive.

## Current grammar behavior

### Core rules (builtin)
- Repeated-word detection such as `ეს ეს`.
- Basic punctuation spacing checks such as stray spaces before punctuation and
  missing spaces after punctuation.
- Double-space detection such as `სიტყვა  სიტყვა`.
- Repeated punctuation detection such as `..` or `,,`.
- Georgian quotation mark checking („…“ style).
- Sentence capitalization checks.
- Dash/em-dash spacing.
- Sentence length warnings.
- Filler word detection.
- Overused word warnings.
- Optional Stanza-backed repeated-lemma detection when the Georgian model is
  installed locally.

### Rules/ (Case alignment)
- Case alignment checking via `Case transitions.py` with verb lexicon covering
  1st/2nd/3rd/4th conjugations
- Series I/II/III screeve tense classification
- Sentence split validation against alignment lexicon
- Tense alignment checks across clauses

### grammar2/ (Agreement rules)
- Postposition case governance (თან→Dative, გამო→Genitive, etc.)
- Confusable word pair detection (e.g., მაგრამ vs მაგრიმ)
- Demonstrative–noun number agreement (ეს/ის vs -ები/-ეფი)
- Proper noun capitalization (88 entries: countries, cities, personalities)
- Double negative pattern detection (არ+არაფერი, etc.)

### georgian_grammar/ (Desktop rules)
- Desktop postposition governance (-ze, -tan, -shi, -dan, -gan, -tvis, -mde, etc.)
- Suffix-dropping rules (-shi drops dative -ს, -dan drops instrumental -თ)
- Adjective declension (consonant- vs vowel-stem suffix matrices)
- Possessive adjective case agreement (10 paradigms: chem-i, shen-i, amis-i, etc.)

### verbal_system_rules.py (Reference data)
- Georgian verbal system specification from rules1.json
- Screeve series (Series I, II, III) with subseries (present, future, aorist, perfect, etc.)
- Verb classes (1-4, stative, irregular) with syntactic patterns
- Provides educational context and meta-information about Georgian grammar

### verbal_system_checker.py (Active checking)
- Verb lexicon with 70+ Georgian verbs mapped to their classes (1-4, stative, irregular)
- Screeve detection from verb suffixes (Series I, II, III patterns)
- Subject case alignment checking based on verb class + screeve series
  - Class 1 transitive: Series I → Nominative, Series II → Ergative, Series III → Dative
  - Class 4 indirect: Always Dative (inversion)
- Direct object presence validation for transitive verbs
- Inversion checking for class 4 verbs (emotions, internal states)

## Verify locally

Run the lightweight test suite:

```bash
python -m unittest discover -s tests -v
```

Run the spellcheck benchmark:

```bash
python benchmark_spellcheck.py
python benchmark_spellcheck.py --file sample.txt --iterations 20
python benchmark_spellcheck.py --file sample.txt --iterations 20 --top-tokens 10
```

Benchmark output now includes:

- `first_run_ms`: cold-start timing for the first pass
- `warm_avg_ms`: average timing for later passes after cache warm-up
- `top_tokens`: the slowest tokens by combined lookup/suggestion time

Then start the API:

```bash
uvicorn main:app --reload
```
