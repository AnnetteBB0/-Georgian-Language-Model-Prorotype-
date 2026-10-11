"""Georgian grammar, punctuation, and stylistic rules with optional Stanza analysis."""

from __future__ import annotations

import importlib.util
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from preprocessor import GEORGIAN_CHAR_RE, Token, iter_tokens, normalize_text
from verbal_system_rules import get_verbal_system_rules, verbal_system_meta
from verbal_system_checker import (
    run_verbal_system_checks,
    verbal_system_engine_meta,
)
from gr_grammar_rules import get_gr_grammar_rules, gr_grammar_meta
from gr_grammar_checker import (
    run_gr_grammar_checks,
    gr_grammar_engine_meta,
)

_RULES_DIR = Path(__file__).resolve().parent / "Rules"
_GRAMMAR2_DIR = Path(__file__).resolve().parent / "grammar2"
_DESKTOP_GG_DIR = Path(__file__).resolve().parent / "georgian_grammar"
_alignment_checker: Any = None
_alignment_loading_error: Exception | None = None
_grammar2_agreement_checker: Any = None
_grammar2_loading_error: Exception | None = None
_desktop_gg_checker: Any = None
_desktop_gg_loading_error: Exception | None = None
_gr_grammar_checker: Any = None
_gr_grammar_loading_error: Exception | None = None


def _load_alignment_checker() -> Any:
    global _alignment_checker, _alignment_loading_error
    if _alignment_checker is not None or _alignment_loading_error is not None:
        return _alignment_checker
    try:
        rules_dir = _RULES_DIR
        ct_path = rules_dir / "Case transitions.py"
        ac_path = rules_dir / "alignment_checker.py"
        if not ct_path.is_file() or not ac_path.is_file():
            raise FileNotFoundError("Rules files missing")

        ct_spec = importlib.util.spec_from_file_location(
            "cgc_rules_case_transitions", str(ct_path)
        )
        if ct_spec is None or ct_spec.loader is None:
            raise ImportError("Could not build spec for Case transitions")
        ct_mod = importlib.util.module_from_spec(ct_spec)
        sys.modules[ct_spec.name] = ct_mod
        ct_spec.loader.exec_module(ct_mod)

        ac_spec = importlib.util.spec_from_file_location(
            "cgc_rules_alignment_checker", str(ac_path)
        )
        if ac_spec is None or ac_spec.loader is None:
            raise ImportError("Could not build spec for alignment_checker")
        ac_mod = importlib.util.module_from_spec(ac_spec)
        sys.modules[ac_spec.name] = ac_mod
        ac_spec.loader.exec_module(ac_mod)
        _alignment_checker = ac_mod
        return _alignment_checker
    except Exception as exc:  # pragma: no cover - defensive
        _alignment_loading_error = exc
        return None


def _load_grammar2_agreement_checker() -> Any:
    global _grammar2_agreement_checker, _grammar2_loading_error
    if (
        _grammar2_agreement_checker is not None
        or _grammar2_loading_error is not None
    ):
        return _grammar2_agreement_checker
    try:
        grammar2_dir = _GRAMMAR2_DIR
        ac_path = grammar2_dir / "agreement_checker.py"
        if not ac_path.is_file():
            raise FileNotFoundError("Grammar 2 agreement_checker.py missing")

        ac_spec = importlib.util.spec_from_file_location(
            "cgc_grammar2_agreement_checker", str(ac_path)
        )
        if ac_spec is None or ac_spec.loader is None:
            raise ImportError("Could not build spec for grammar2 agreement_checker")
        ac_mod = importlib.util.module_from_spec(ac_spec)
        sys.modules[ac_spec.name] = ac_mod
        ac_spec.loader.exec_module(ac_mod)
        _grammar2_agreement_checker = ac_mod
        return _grammar2_agreement_checker
    except Exception as exc:  # pragma: no cover - defensive
        _grammar2_loading_error = exc
        return None


def _load_desktop_gg_checker() -> Any:
    global _desktop_gg_checker, _desktop_gg_loading_error
    if _desktop_gg_checker is not None or _desktop_gg_loading_error is not None:
        return _desktop_gg_checker
    try:
        ac_path = _DESKTOP_GG_DIR / "agreement_checker.py"
        if not ac_path.is_file():
            raise FileNotFoundError("georgian_grammar agreement_checker.py missing")

        ac_spec = importlib.util.spec_from_file_location(
            "cgc_desktop_georgian_grammar_checker", str(ac_path)
        )
        if ac_spec is None or ac_spec.loader is None:
            raise ImportError(
                "Could not build spec for georgian_grammar agreement_checker"
            )
        ac_mod = importlib.util.module_from_spec(ac_spec)
        sys.modules[ac_spec.name] = ac_mod
        ac_spec.loader.exec_module(ac_mod)
        _desktop_gg_checker = ac_mod
        return _desktop_gg_checker
    except Exception as exc:  # pragma: no cover - defensive
        _desktop_gg_loading_error = exc
        return None


def _load_gr_grammar_checker() -> Any:
    global _gr_grammar_checker, _gr_grammar_loading_error
    if _gr_grammar_checker is not None or _gr_grammar_loading_error is not None:
        return _gr_grammar_checker
    try:
        gr_rules = get_gr_grammar_rules()
        if not gr_rules.is_loaded():
            raise FileNotFoundError("gr.json not found or invalid")
        _gr_grammar_checker = gr_rules
        return _gr_grammar_checker
    except Exception as exc:  # pragma: no cover - defensive
        _gr_grammar_loading_error = exc
        return None

SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:!?…])")
MISSING_SPACE_AFTER_PUNCT_RE = re.compile(r"([,.;:!?…])([^\s,.;:!?…])")
DOUBLE_SPACE_RE = re.compile(r" {2,}")
REPEATED_PUNCT_RE = re.compile(r"([,.;:!?…])\1+")

SENTENCE_END_RE = re.compile(r"[.!?…]\s+")
LOWER_START_RE = re.compile(r"(?:^|(?<=[.!?…]\s))([\u10A0-\u10FF])")

GEORGIAN_QUOTES_OPEN = "„"
GEORGIAN_QUOTES_CLOSE = "“"
MISUSED_QUOTES_RE = re.compile(r'["\']([^"\']*?)["\']')
MISSING_CLOSE_QUOTE_RE = re.compile(r"„[^“]*$")
MISSING_OPEN_QUOTE_RE = re.compile(r"^[^„]*“")

EM_DASH = "—"
SPACE_AROUND_DASH_RE = re.compile(r"(\S)—(\S)")
WRONG_DASH_CHAR_RE = re.compile(r"(?<=\s)--?(?=\s)")

LONG_SENTENCE_THRESHOLD = 45
VERY_LONG_SENTENCE_THRESHOLD = 60

FILLER_WORDS = {
    "ფაქტიურად",
    "რეალურად",
    "სინამდვილეში",
    "საუკეთესო რაც შეიძლება",
    "ერთი რამ",
    "იმედოა",
    "ალბათ",
    "ზოგადად",
    "გაიგოს",
    "ამის მიუხედავად",
    "რადგანაც",
    "იქნება",
}

OVERUSED_WORDS = {
    "ძალიან": 3,
    "კარგი": 3,
    "მნიშვნელოვანი": 3,
    "საუკეთესო": 2,
    "რუსულად": 3,
}

_stanza_pipeline: Any | None = None
_stanza_ready = False
_stanza_attempted = False


@dataclass(frozen=True)
class GrammarAnnotation:
    start: int
    end: int
    type: str
    message: str
    short_message: str
    replacements: list[str]
    rule_id: str
    severity: str
    source: str
    word: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "type": self.type,
            "message": self.message,
            "short_message": self.short_message,
            "replacements": self.replacements,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "source": self.source,
            "word": self.word,
        }


def get_stanza_pipeline() -> Any | None:
    global _stanza_pipeline, _stanza_ready, _stanza_attempted

    if _stanza_attempted:
        return _stanza_pipeline if _stanza_ready else None

    _stanza_attempted = True
    try:
        import stanza

        _stanza_pipeline = stanza.Pipeline(
            lang="ka",
            processors="tokenize,pos,lemma,depparse",
            use_gpu=False,
            verbose=False,
        )
        _stanza_ready = True
    except Exception:
        _stanza_pipeline = None
        _stanza_ready = False

    return _stanza_pipeline if _stanza_ready else None


def warm_grammar_resources() -> None:
    get_stanza_pipeline()
    _load_alignment_checker()
    _load_grammar2_agreement_checker()
    _load_desktop_gg_checker()
    get_verbal_system_rules()
    _load_gr_grammar_checker()


def _same_word(left: Token, right: Token) -> bool:
    return left.text == right.text and bool(GEORGIAN_CHAR_RE.search(left.text))


def _annotations_overlap(
    a: GrammarAnnotation, b: GrammarAnnotation
) -> bool:
    return not (a.end <= b.start or b.end <= a.start)


def _dedupe_annotations(
    annotations: list[GrammarAnnotation],
) -> list[GrammarAnnotation]:
    deduped: list[GrammarAnnotation] = []
    seen_spans: set[tuple[int, int, str]] = set()

    for ann in sorted(annotations, key=lambda x: (x.start, x.end, x.rule_id)):
        span = (ann.start, ann.end, ann.rule_id)
        if span in seen_spans:
            continue
        conflict = False
        for existing in deduped:
            if _annotations_overlap(ann, existing) and ann.rule_id.replace(
                "stanza_", ""
            ) == existing.rule_id.replace("stanza_", ""):
                conflict = True
                break
        if not conflict:
            deduped.append(ann)
            seen_spans.add(span)

    return deduped


def repeated_word_rules(tokens: list[Token]) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []
    index = 0

    while index < len(tokens) - 1:
        current = tokens[index]
        nxt = tokens[index + 1]

        if _same_word(current, nxt):
            annotations.append(
                GrammarAnnotation(
                    start=current.start,
                    end=nxt.end,
                    type="grammar",
                    message="Repeated word",
                    short_message="Repeated word",
                    replacements=[current.text],
                    rule_id="grammar:repeated_word",
                    severity="warning",
                    source="rules",
                    word=f"{current.text} {nxt.text}",
                )
            )
            index += 2
            continue

        index += 1

    return annotations


def punctuation_spacing_rules(text: str) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []

    for match in SPACE_BEFORE_PUNCT_RE.finditer(text):
        punctuation = match.group(1)
        annotations.append(
            GrammarAnnotation(
                start=match.start(),
                end=match.end(),
                type="grammar",
                message="Unexpected space before punctuation",
                short_message="Spacing",
                replacements=[punctuation],
                rule_id="grammar:space_before_punctuation",
                severity="warning",
                source="rules",
                word=match.group(),
            )
        )

    for match in MISSING_SPACE_AFTER_PUNCT_RE.finditer(text):
        punctuation = match.group(1)
        next_char = match.group(2)
        if next_char.isspace():
            continue
        annotations.append(
            GrammarAnnotation(
                start=match.start(),
                end=match.end(),
                type="grammar",
                message="Missing space after punctuation",
                short_message="Spacing",
                replacements=[f"{punctuation} {next_char}"],
                rule_id="grammar:missing_space_after_punctuation",
                severity="warning",
                source="rules",
                word=match.group(),
            )
        )

    return annotations


def double_space_rules(text: str) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []

    for match in DOUBLE_SPACE_RE.finditer(text):
        annotations.append(
            GrammarAnnotation(
                start=match.start(),
                end=match.end(),
                type="grammar",
                message="Multiple consecutive spaces",
                short_message="Spacing",
                replacements=[" "],
                rule_id="grammar:double_space",
                severity="warning",
                source="rules",
                word=match.group(),
            )
        )

    return annotations


def repeated_punctuation_rules(text: str) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []

    for match in REPEATED_PUNCT_RE.finditer(text):
        punctuation = match.group(1)
        annotations.append(
            GrammarAnnotation(
                start=match.start(),
                end=match.end(),
                type="grammar",
                message="Repeated punctuation mark",
                short_message="Punctuation",
                replacements=[punctuation],
                rule_id="grammar:repeated_punctuation",
                severity="warning",
                source="rules",
                word=match.group(),
            )
        )

    return annotations


def sentence_capitalization_rules(text: str) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []

    if not text:
        return annotations

    for match in LOWER_START_RE.finditer(text):
        lower_char = match.group(1)
        upper_char = lower_char.upper()
        if lower_char != upper_char:
            annotations.append(
                GrammarAnnotation(
                    start=match.start(1),
                    end=match.end(1),
                    type="grammar",
                    message="Sentence should start with a capital letter",
                    short_message="Capitalization",
                    replacements=[upper_char],
                    rule_id="grammar:sentence_capitalization",
                    severity="warning",
                    source="rules",
                    word=lower_char,
                )
            )

    return annotations


def georgian_quotation_rules(text: str) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []

    for match in MISUSED_QUOTES_RE.finditer(text):
        inner = match.group(1)
        annotations.append(
            GrammarAnnotation(
                start=match.start(),
                end=match.end(),
                type="style",
                message="Consider using Georgian quotation marks „…“",
                short_message="Quotation style",
                replacements=[f"„{inner}“"],
                rule_id="style:georgian_quotes",
                severity="info",
                source="rules",
                word=match.group(),
            )
        )

    for match in MISSING_CLOSE_QUOTE_RE.finditer(text):
        annotations.append(
            GrammarAnnotation(
                start=match.start(),
                end=len(text),
                type="grammar",
                message="Missing closing quotation mark “",
                short_message="Unclosed quote",
                replacements=[match.group() + "“"],
                rule_id="grammar:unclosed_quote",
                severity="warning",
                source="rules",
                word=match.group(),
            )
        )

    for match in MISSING_OPEN_QUOTE_RE.finditer(text):
        annotations.append(
            GrammarAnnotation(
                start=0,
                end=match.end(),
                type="grammar",
                message="Missing opening quotation mark „",
                short_message="Missing quote open",
                replacements=["„" + match.group()],
                rule_id="grammar:unopened_quote",
                severity="warning",
                source="rules",
                word=match.group(),
            )
        )

    return annotations


def dash_punctuation_rules(text: str) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []

    for match in SPACE_AROUND_DASH_RE.finditer(text):
        annotations.append(
            GrammarAnnotation(
                start=match.start(),
                end=match.end(),
                type="grammar",
                message="Em-dash should have spaces on both sides",
                short_message="Dash spacing",
                replacements=[f"{match.group(1)} — {match.group(2)}"],
                rule_id="grammar:dash_spacing",
                severity="info",
                source="rules",
                word=match.group(),
            )
        )

    for match in WRONG_DASH_CHAR_RE.finditer(text):
        annotations.append(
            GrammarAnnotation(
                start=match.start(),
                end=match.end(),
                type="style",
                message="Consider using an em-dash — instead of hyphens",
                short_message="Dash style",
                replacements=[EM_DASH],
                rule_id="style:em_dash",
                severity="info",
                source="rules",
                word=match.group(),
            )
        )

    return annotations


def sentence_length_rules(text: str) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []

    sentences = re.split(r"(?<=[.!?…])\s+", text.strip())
    cursor = 0

    for sentence in sentences:
        s_len = len(sentence)
        if s_len >= VERY_LONG_SENTENCE_THRESHOLD:
            annotations.append(
                GrammarAnnotation(
                    start=cursor,
                    end=cursor + s_len,
                    type="style",
                    message=f"Very long sentence ({s_len} chars). Consider splitting for readability.",
                    short_message="Long sentence",
                    replacements=[],
                    rule_id="style:very_long_sentence",
                    severity="warning",
                    source="rules",
                    word=sentence[:30] + ("…" if s_len > 30 else ""),
                )
            )
        elif s_len >= LONG_SENTENCE_THRESHOLD:
            annotations.append(
                GrammarAnnotation(
                    start=cursor,
                    end=cursor + s_len,
                    type="style",
                    message=f"Long sentence ({s_len} chars). Consider splitting for clarity.",
                    short_message="Long sentence",
                    replacements=[],
                    rule_id="style:long_sentence",
                    severity="info",
                    source="rules",
                    word=sentence[:30] + ("…" if s_len > 30 else ""),
                )
            )
        cursor += s_len + 1

    return annotations


def filler_word_rules(tokens: list[Token]) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []

    for token in tokens:
        if token.text.lower() in FILLER_WORDS:
            annotations.append(
                GrammarAnnotation(
                    start=token.start,
                    end=token.end,
                    type="style",
                    message=f"'{token.text}' is a filler word. Consider removing if not necessary.",
                    short_message="Filler word",
                    replacements=[],
                    rule_id="style:filler_word",
                    severity="info",
                    source="rules",
                    word=token.text,
                )
            )

    return annotations


def overused_word_rules(tokens: list[Token]) -> list[GrammarAnnotation]:
    annotations: list[GrammarAnnotation] = []
    word_counts: dict[str, list[Token]] = {}

    for token in tokens:
        if not token.should_spellcheck:
            continue
        key = token.text.lower()
        word_counts.setdefault(key, []).append(token)

    for word, occurrences in word_counts.items():
        threshold = OVERUSED_WORDS.get(word)
        if threshold and len(occurrences) > threshold:
            for token in occurrences[threshold:]:
                annotations.append(
                    GrammarAnnotation(
                        start=token.start,
                        end=token.end,
                        type="style",
                        message=f"'{word}' used {len(occurrences)} times. Consider synonyms.",
                        short_message="Overused word",
                        replacements=[],
                        rule_id="style:overused_word",
                        severity="info",
                        source="rules",
                        word=token.text,
                    )
                )

    return annotations


def stanza_repeated_lemma_rules(document: Any | None) -> list[GrammarAnnotation]:
    if document is None:
        return []

    annotations: list[GrammarAnnotation] = []

    for sentence in document.sentences:
        words = sentence.words
        index = 0

        while index < len(words) - 1:
            current = words[index]
            nxt = words[index + 1]

            if (
                current.lemma
                and current.lemma == nxt.lemma
                and current.lemma not in {"-", "_"}
                and bool(GEORGIAN_CHAR_RE.search(current.text))
                and current.text.lower() != nxt.text.lower()
            ):
                annotations.append(
                    GrammarAnnotation(
                        start=current.start_char,
                        end=nxt.end_char,
                        type="grammar",
                        message=f"Repeated word form ({current.lemma})",
                        short_message="Repeated lemma",
                        replacements=[current.text],
                        rule_id="grammar:stanza_repeated_lemma",
                        severity="warning",
                        source="stanza",
                        word=f"{current.text} {nxt.text}",
                    )
                )
                index += 2
                continue

            index += 1

    return annotations


def run_stanza_analysis(text: str) -> tuple[Any | None, dict[str, Any]]:
    pipeline = get_stanza_pipeline()
    if pipeline is None:
        return None, {
            "stanza_available": False,
            "stanza_used": False,
            "sentence_count": 0,
            "token_count": 0,
        }

    document = pipeline(text)
    sentence_count = len(document.sentences)
    token_count = sum(len(sentence.words) for sentence in document.sentences)
    return document, {
        "stanza_available": True,
        "stanza_used": True,
        "sentence_count": sentence_count,
        "token_count": token_count,
    }


def compute_text_stats(
    text: str, tokens: list[Token], stanza_meta: dict[str, Any]
) -> dict[str, Any]:
    georgian_tokens = [t for t in tokens if t.should_spellcheck]
    word_count = len(georgian_tokens)
    unique_words = len({t.text.lower() for t in georgian_tokens})

    if stanza_meta.get("sentence_count"):
        sentence_count = stanza_meta["sentence_count"]
    else:
        parts = re.split(r"[.!?…]", text)
        sentence_count = max(1, len([p for p in parts if p.strip()]))

    avg_word_length = (
        round(sum(len(t.text) for t in georgian_tokens) / word_count, 2)
        if word_count
        else 0
    )
    avg_sentence_length_words = (
        round(word_count / sentence_count, 2) if sentence_count else 0
    )
    avg_sentence_length_chars = (
        round(len(text) / sentence_count, 2) if sentence_count else 0
    )

    lex_diversity = (
        round(unique_words / word_count, 3) if word_count else 0
    )

    return {
        "char_count": len(text),
        "word_count": word_count,
        "unique_word_count": unique_words,
        "sentence_count": sentence_count,
        "avg_word_length_chars": avg_word_length,
        "avg_sentence_length_words": avg_sentence_length_words,
        "avg_sentence_length_chars": avg_sentence_length_chars,
        "lexical_diversity": lex_diversity,
    }


def stanza_case_alignment_rules(
    document: Any | None, text: str
) -> list[GrammarAnnotation]:
    if document is None:
        return []

    checker = _load_alignment_checker()
    if checker is None:
        return []

    try:
        raw = checker.run_case_alignment_checks(document, text)
    except Exception:  # pragma: no cover - defensive
        return []

    out: list[GrammarAnnotation] = []
    for item in raw:
        out.append(
            GrammarAnnotation(
                start=item.start,
                end=item.end,
                type=item.type,
                message=item.message,
                short_message=item.short_message,
                replacements=list(item.replacements or []),
                rule_id=item.rule_id,
                severity=item.severity,
                source=item.source,
                word=item.word,
            )
        )
    return out


def grammar2_agreement_rules(
    text: str, tokens: list[Token], stanza_document: Any | None
) -> list[GrammarAnnotation]:
    checker = _load_grammar2_agreement_checker()
    if checker is None:
        return []

    try:
        raw = checker.run_agreement_checks(text, tokens, stanza_document)
    except Exception:  # pragma: no cover - defensive
        return []

    out: list[GrammarAnnotation] = []
    for item in raw:
        out.append(
            GrammarAnnotation(
                start=item.start,
                end=item.end,
                type=item.type,
                message=item.message,
                short_message=item.short_message,
                replacements=list(item.replacements or []),
                rule_id=item.rule_id,
                severity=item.severity,
                source=item.source,
                word=item.word,
            )
        )
    return out


def desktop_georgian_grammar_rules(
    text: str, tokens: list[Token], stanza_document: Any | None
) -> list[GrammarAnnotation]:
    checker = _load_desktop_gg_checker()
    if checker is None:
        return []

    try:
        raw = checker.run_agreement_checks(text, tokens, stanza_document)
    except Exception:  # pragma: no cover - defensive
        return []

    out: list[GrammarAnnotation] = []
    for item in raw:
        out.append(
            GrammarAnnotation(
                start=item.start,
                end=item.end,
                type=item.type,
                message=item.message,
                short_message=item.short_message,
                replacements=list(item.replacements or []),
                rule_id=item.rule_id,
                severity=item.severity,
                source=item.source,
                word=item.word,
            )
        )
    return out


def check_grammar(text: str) -> tuple[list[GrammarAnnotation], int, dict[str, Any]]:
    normalized = normalize_text(text)
    tokens = [token for token in iter_tokens(normalized) if token.should_spellcheck]

    start_ms = time.perf_counter()
    stanza_document, meta = run_stanza_analysis(normalized)

    raw_annotations = [
        *repeated_word_rules(tokens),
        *punctuation_spacing_rules(normalized),
        *double_space_rules(normalized),
        *repeated_punctuation_rules(normalized),
        *sentence_capitalization_rules(normalized),
        *georgian_quotation_rules(normalized),
        *dash_punctuation_rules(normalized),
        *sentence_length_rules(normalized),
        *filler_word_rules(tokens),
        *overused_word_rules(tokens),
        *stanza_repeated_lemma_rules(stanza_document),
        *stanza_case_alignment_rules(stanza_document, normalized),
        *grammar2_agreement_rules(normalized, tokens, stanza_document),
        *desktop_georgian_grammar_rules(normalized, tokens, stanza_document),
    ]

    # Add verbal system checks
    verbal_system_annotations = run_verbal_system_checks(
        normalized, tokens, stanza_document
    )
    for vs_ann in verbal_system_annotations:
        raw_annotations.append(
            GrammarAnnotation(
                start=vs_ann.start,
                end=vs_ann.end,
                type=vs_ann.type,
                message=vs_ann.message,
                short_message=vs_ann.short_message,
                replacements=vs_ann.replacements,
                rule_id=vs_ann.rule_id,
                severity=vs_ann.severity,
                source=vs_ann.source,
                word=vs_ann.word,
            )
        )

    # Add gr.json grammar checks
    gr_annotations = run_gr_grammar_checks(normalized, tokens, stanza_document)
    for gr_ann in gr_annotations:
        raw_annotations.append(
            GrammarAnnotation(
                start=gr_ann.start,
                end=gr_ann.end,
                type=gr_ann.type,
                message=gr_ann.message,
                short_message=gr_ann.short_message,
                replacements=gr_ann.replacements,
                rule_id=gr_ann.rule_id,
                severity=gr_ann.severity,
                source=gr_ann.source,
                word=gr_ann.word,
            )
        )

    annotations = _dedupe_annotations(raw_annotations)
    annotations.sort(key=lambda annotation: (annotation.start, annotation.end))

    rule_ids = sorted({a.rule_id for a in annotations})
    stats = compute_text_stats(normalized, tokens, meta)

    checker = _load_alignment_checker()
    if checker is not None:
        try:
            extra_meta = checker.alignment_engine_meta()
            stats.update(extra_meta)
        except Exception:  # pragma: no cover - defensive
            pass

    g2_checker = _load_grammar2_agreement_checker()
    if g2_checker is not None:
        try:
            g2_meta = g2_checker.agreement_engine_meta()
            stats.update(g2_meta)
        except Exception:  # pragma: no cover - defensive
            pass

    desktop_checker = _load_desktop_gg_checker()
    if desktop_checker is not None:
        try:
            desktop_meta = desktop_checker.agreement_engine_meta()
            stats.update(desktop_meta)
        except Exception:  # pragma: no cover - defensive
            pass

    # Add verbal system metadata
    try:
        vs_meta = verbal_system_meta()
        stats.update(vs_meta)
    except Exception:  # pragma: no cover - defensive
        pass

    try:
        vs_checker_meta = verbal_system_engine_meta()
        stats.update(vs_checker_meta)
    except Exception:  # pragma: no cover - defensive
        pass

    # Add gr.json grammar metadata
    try:
        gr_meta = gr_grammar_meta()
        stats.update(gr_meta)
    except Exception:  # pragma: no cover - defensive
        pass

    try:
        gr_checker_meta = gr_grammar_engine_meta()
        stats.update(gr_checker_meta)
    except Exception:  # pragma: no cover - defensive
        pass

    meta["grammar_engine"] = "rules+optional-stanza+alignment+grammar2+desktop+verbal_system+gr.json"
    meta["active_rule_ids"] = rule_ids
    meta.update(stats)

    elapsed_ms = int((time.perf_counter() - start_ms) * 1000)

    return annotations, elapsed_ms, meta


# =============================================================================
# Rule catalog: static registry of every rule id → (source, type, description)
# =============================================================================

_BUILTIN_RULE_CATALOG: list[dict[str, str]] = [
    {
        "rule_id": "grammar:repeated_word",
        "source": "builtin-core",
        "type": "grammar",
        "short_name": "Repeated word",
        "description": "Flags adjacent Georgian tokens that are exactly identical.",
    },
    {
        "rule_id": "grammar:punctuation_spacing",
        "source": "builtin-core",
        "type": "grammar",
        "short_name": "Punctuation spacing",
        "description": "Warns about spaces before punctuation and missing spaces after.",
    },
    {
        "rule_id": "grammar:double_space",
        "source": "builtin-core",
        "type": "grammar",
        "short_name": "Double space",
        "description": "Collapses runs of more than one space inside running text.",
    },
    {
        "rule_id": "grammar:repeated_punctuation",
        "source": "builtin-core",
        "type": "grammar",
        "short_name": "Repeated punctuation",
        "description": "Flags duplicate punctuation characters such as '!!' or ',,', suggesting the canonical single character.",
    },
    {
        "rule_id": "grammar:sentence_capitalization",
        "source": "builtin-core",
        "type": "grammar",
        "short_name": "Sentence capitalisation",
        "description": "Requires the first Georgian letter of a sentence to be Mtavruli (uppercase).",
    },
    {
        "rule_id": "grammar:georgian_quotes",
        "source": "builtin-core",
        "type": "grammar",
        "short_name": "Georgian quotation marks",
        "description": "Suggests replacing ASCII quotes with the Georgian „…“ pair and warns about mismatched open/close.",
    },
    {
        "rule_id": "grammar:dash_punctuation",
        "source": "builtin-core",
        "type": "grammar",
        "short_name": "Dash / em-dash",
        "description": "Surrounds em-dashes with the standard Georgian spacing pattern and warns about malformed ASCII dash sequences.",
    },
    {
        "rule_id": "style:sentence_length",
        "source": "builtin-core",
        "type": "style",
        "short_name": "Overlong sentence",
        "description": "Warns when a sentence exceeds the recommended word-count cap.",
    },
    {
        "rule_id": "style:filler_word",
        "source": "builtin-core",
        "type": "style",
        "short_name": "Filler word",
        "description": "Flags common Georgian filler words used for oral pause-stalling.",
    },
    {
        "rule_id": "style:overused_word",
        "source": "builtin-core",
        "type": "style",
        "short_name": "Overused word",
        "description": "Warns when a single high-frequency content word appears too often in a short span.",
    },
    {
        "rule_id": "grammar:stanza_repeated_lemma",
        "source": "stanza-optional",
        "type": "grammar",
        "short_name": "Repeated lemma",
        "description": "Uses the stanza morphological tagger to flag the same lemma appearing back-to-back (e.g. inflected word followed by its base).",
    },
    {
        "rule_id": "grammar:stanza_case_mismatch",
        "source": "stanza-optional",
        "type": "grammar",
        "short_name": "Stanza case mismatch",
        "description": "Cross-checks a small set of frequent preposition–noun case pairs against stanza upos/feats.",
    },
    {
        "rule_id": "alignment:sentence_split",
        "source": "Rules/alignment_checker.py",
        "type": "grammar",
        "short_name": "Sentence split",
        "description": "Compares rule-engine sentence boundaries against the precomputed 72-rule alignment lexicon.",
    },
    {
        "rule_id": "alignment:case_label",
        "source": "Rules/alignment_checker.py",
        "type": "grammar",
        "short_name": "Case alignment",
        "description": "Validates each case-bearing token against its alignment entry in the case-transition rule table.",
    },
    {
        "rule_id": "alignment:tense_shift",
        "source": "Rules/alignment_checker.py",
        "type": "style",
        "short_name": "Tense alignment",
        "description": "Checks Series I/II/III tense markers for agreement within every clause.",
    },
    {
        "rule_id": "grammar:postposition_governance",
        "source": "grammar2/Agreement rules.py",
        "type": "grammar",
        "short_name": "Postposition case",
        "description": "Enforces the expected case suffix on the noun that precedes a postposition (e.g. თან needs Dative, გამო needs Genitive, etc.).",
    },
    {
        "rule_id": "grammar:confusable_pair",
        "source": "grammar2/Agreement rules.py",
        "type": "grammar",
        "short_name": "Confusable word",
        "description": "Replaces near-homophone typo forms with their canonical spellings from the Grammar 2 confusable list.",
    },
    {
        "rule_id": "grammar:demonstrative_number",
        "source": "grammar2/Agreement rules.py",
        "type": "grammar",
        "short_name": "Demonstrative number",
        "description": "Warns when a singular demonstrative (ეს, ის) is paired with a plural head noun (–ები/–ეფი) or vice versa.",
    },
    {
        "rule_id": "grammar:proper_noun_capitalisation",
        "source": "grammar2/Agreement rules.py",
        "type": "grammar",
        "short_name": "Proper noun cap",
        "description": "Capitalises Mtavruli proper noun lemmas drawn from the Grammar 2 lexicon (88 entries: countries, cities, rivers, mountains, personalities, languages).",
    },
    {
        "rule_id": "grammar:double_negative",
        "source": "grammar2/Agreement rules.py",
        "type": "grammar",
        "short_name": "Double negative",
        "description": "Warns on doubled negation patterns such as არ + არაფერი, არ + ვერ, and ვერ + ვერაფერი.",
    },
    {
        "rule_id": "desktop:postposition_governance",
        "source": "georgian_grammar/georgian_grammar_rules.py",
        "type": "grammar",
        "short_name": "Postposition (desktop)",
        "description": "Validates desktop-rule postpositions (-ze, -tan, -shi, -dan, -gan, -tvis, -mde, gamo, garda, mier, shesaxeb, etc.) against their governed case.",
    },
    {
        "rule_id": "desktop:suffix_dropping_shi",
        "source": "georgian_grammar/georgian_grammar_rules.py",
        "type": "grammar",
        "short_name": "-shi suffix drop",
        "description": "Enforces the -shi truncation rule: dative -ს must be dropped and the noun stem should carry -ში attached.",
    },
    {
        "rule_id": "desktop:suffix_dropping_dan",
        "source": "georgian_grammar/georgian_grammar_rules.py",
        "type": "grammar",
        "short_name": "-dan suffix drop",
        "description": "Enforces the -dan truncation rule: instrumental -თ/-ით must be dropped and the noun stem should carry -დან attached.",
    },
    {
        "rule_id": "desktop:adjective_declension",
        "source": "georgian_grammar/georgian_grammar_rules.py",
        "type": "grammar",
        "short_name": "Adjective declension",
        "description": "Checks the declension suffix of a stanza-recognised ADJ against the consonant- vs vowel-stem matrices (-i / -ma / ∅ / -i / -i / ∅ / -o).",
    },
    {
        "rule_id": "desktop:possessive_adjective_case",
        "source": "georgian_grammar/georgian_grammar_rules.py",
        "type": "grammar",
        "short_name": "Possessive agreement",
        "description": "For each of the 10 possessive adjective paradigms (chem-i, shen-i, amis-i, chven-i, tkven-i, amat-i, magat-i, imat-i…) verifies that the surface form agrees in case with its head noun.",
    },
    {
        "rule_id": "verbal:subject_case_alignment",
        "source": "verbal_system_checker.py",
        "type": "grammar",
        "short_name": "Verb subject case",
        "description": "Validates subject case alignment based on verb class and screeve series (e.g., transitive verbs in Series II require ergative subjects).",
    },
    {
        "rule_id": "verbal:missing_direct_object",
        "source": "verbal_system_checker.py",
        "type": "style",
        "short_name": "Missing object",
        "description": "Warns when transitive verbs appear without an expected direct object.",
    },
    {
        "rule_id": "verbal:indirect_verb_inversion",
        "source": "verbal_system_checker.py",
        "type": "grammar",
        "short_name": "Inversion subject",
        "description": "Checks that Class 4 indirect verbs (emotions, internal states) have dative subjects as required by Georgian inversion.",
    },
    {
        "rule_id": "gr:negation_ver_shedzleba",
        "source": "gr.json",
        "type": "grammar",
        "short_name": "Negation pattern",
        "description": "Warns when 'ver shedzleba' is used instead of the correct pattern 'ver' + verb directly.",
    },
    {
        "rule_id": "gr:interrogative_position",
        "source": "gr.json",
        "type": "style",
        "short_name": "Interrogative position",
        "description": "Checks that interrogative pronouns (რა, ვინ, etc.) appear immediately before the verb as required by Georgian syntax.",
    },
    {
        "rule_id": "gr:tag_particle_position",
        "source": "gr.json",
        "type": "grammar",
        "short_name": "Tag particle position",
        "description": "Validates that the tag question particle 'ხომ' (xom) occupies the exact second position within the sentence.",
    },
    {
        "rule_id": "gr:imperative_negation",
        "source": "gr.json",
        "type": "style",
        "short_name": "Imperative negation",
        "description": "Flags when 'ნუ' (nu) is used outside of imperative/command contexts.",
    },
]


def get_rule_catalog() -> list[dict[str, str]]:
    """Return a stable list of every rule id, source plugin, type and description."""
    return [dict(entry) for entry in _BUILTIN_RULE_CATALOG]


def get_engine_status() -> dict[str, Any]:
    """Return loading/availability info for every plugin engine."""
    stanza_pipeline = get_stanza_pipeline()

    alignment = _load_alignment_checker()
    g2 = _load_grammar2_agreement_checker()
    desktop = _load_desktop_gg_checker()
    verbal_system = get_verbal_system_rules()
    gr_grammar = _load_gr_grammar_checker()

    status: dict[str, Any] = {
        "grammar_engine": "rules+optional-stanza+alignment+grammar2+desktop+verbal_system+gr.json",
        "plugins": {
            "builtin-core": {
                "available": True,
                "rule_count": sum(
                    1
                    for r in _BUILTIN_RULE_CATALOG
                    if r["source"] == "builtin-core"
                ),
            },
            "stanza-optional": {
                "available": stanza_pipeline is not None,
                "rule_count": sum(
                    1
                    for r in _BUILTIN_RULE_CATALOG
                    if r["source"] == "stanza-optional"
                ),
            },
            "Rules/alignment_checker.py": {
                "available": alignment is not None,
                "rule_count": sum(
                    1
                    for r in _BUILTIN_RULE_CATALOG
                    if r["source"] == "Rules/alignment_checker.py"
                ),
                "meta": alignment.alignment_engine_meta()
                if alignment is not None
                else None,
                "loading_error": str(_alignment_loading_error)
                if _alignment_loading_error is not None
                else None,
            },
            "grammar2/Agreement rules.py": {
                "available": g2 is not None,
                "rule_count": sum(
                    1
                    for r in _BUILTIN_RULE_CATALOG
                    if r["source"] == "grammar2/Agreement rules.py"
                ),
                "meta": g2.agreement_engine_meta() if g2 is not None else None,
                "loading_error": str(_grammar2_loading_error)
                if _grammar2_loading_error is not None
                else None,
            },
            "georgian_grammar/georgian_grammar_rules.py": {
                "available": desktop is not None,
                "rule_count": sum(
                    1
                    for r in _BUILTIN_RULE_CATALOG
                    if r["source"] == "georgian_grammar/georgian_grammar_rules.py"
                ),
                "meta": desktop.agreement_engine_meta()
                if desktop is not None
                else None,
                "loading_error": str(_desktop_gg_loading_error)
                if _desktop_gg_loading_error is not None
                else None,
            },
            "rules1.json (Verbal System)": {
                "available": verbal_system.is_loaded(),
                "rule_count": 0,  # Reference data, not checking rules
                "meta": verbal_system_meta(),
                "loading_error": None,
            },
            "verbal_system_checker.py": {
                "available": True,
                "rule_count": sum(
                    1
                    for r in _BUILTIN_RULE_CATALOG
                    if r["source"] == "verbal_system_checker.py"
                ),
                "meta": verbal_system_engine_meta(),
                "loading_error": None,
            },
            "gr.json": {
                "available": gr_grammar is not None and gr_grammar.is_loaded(),
                "rule_count": sum(
                    1
                    for r in _BUILTIN_RULE_CATALOG
                    if r["source"] == "gr.json"
                ),
                "meta": gr_grammar_engine_meta() if gr_grammar is not None else None,
                "loading_error": str(_gr_grammar_loading_error)
                if _gr_grammar_loading_error is not None
                else None,
            },
        },
    }
    return status
