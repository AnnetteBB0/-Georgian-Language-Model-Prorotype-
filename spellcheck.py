"""Georgian spell checking via Hunspell (spylls)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from spylls.hunspell import Dictionary

from preprocessor import Token, iter_tokens, normalize_text, normalize_words

DICT_DIR = Path(__file__).parent / "dictionaries" / "ka_GE"
DICT_BASENAME = DICT_DIR / "ka_GE"
MAX_SUGGESTION_WORD_LENGTH = 8

_dictionary: Dictionary | None = None


@dataclass(frozen=True)
class Annotation:
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

    def to_dict(self) -> dict:
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


@dataclass
class TokenProfile:
    word: str
    occurrences: int = 0
    lookup_ms: float = 0.0
    suggest_ms: float = 0.0
    mixed_script_hits: int = 0
    misspell_hits: int = 0
    suggestions_generated: int = 0

    @property
    def total_ms(self) -> float:
        return self.lookup_ms + self.suggest_ms

    def to_dict(self) -> dict[str, Any]:
        return {
            "word": self.word,
            "occurrences": self.occurrences,
            "lookup_ms": round(self.lookup_ms, 3),
            "suggest_ms": round(self.suggest_ms, 3),
            "total_ms": round(self.total_ms, 3),
            "mixed_script_hits": self.mixed_script_hits,
            "misspell_hits": self.misspell_hits,
            "suggestions_generated": self.suggestions_generated,
        }


@dataclass(frozen=True)
class WordDecision:
    is_known: bool
    is_mixed_script: bool
    suggestions: tuple[str, ...] = field(default_factory=tuple)
    lookup_ms: float = 0.0
    suggest_ms: float = 0.0


def get_dictionary() -> Dictionary:
    global _dictionary
    if _dictionary is None:
        if not DICT_BASENAME.with_suffix(".dic").exists():
            raise FileNotFoundError(
                f"Dictionary not found at {DICT_DIR}. "
                "Download ka_GE.aff and ka_GE.dic from "
                "https://github.com/gamag/ka_GE.spell/tree/master/dictionaries"
            )
        _dictionary = Dictionary.from_files(str(DICT_BASENAME))
    return _dictionary


@lru_cache(maxsize=50_000)
def cached_lookup(word: str) -> bool:
    return bool(get_dictionary().lookup(word))


@lru_cache(maxsize=20_000)
def cached_suggestions(word: str, max_suggestions: int) -> tuple[str, ...]:
    suggestions = list(get_dictionary().suggest(word))[:max_suggestions]
    return tuple(suggestions)


def should_generate_suggestions(token: Token) -> bool:
    return (
        not token.is_mixed_script
        and len(token.text) <= MAX_SUGGESTION_WORD_LENGTH
    )


def update_profile(
    profiles: dict[str, TokenProfile],
    word: str,
    *,
    lookup_ms: float = 0.0,
    suggest_ms: float = 0.0,
    mixed_script_hit: bool = False,
    misspell_hit: bool = False,
    suggestions_generated: int = 0,
) -> None:
    profile = profiles.setdefault(word, TokenProfile(word=word))
    profile.occurrences += 1
    profile.lookup_ms += lookup_ms
    profile.suggest_ms += suggest_ms
    if mixed_script_hit:
        profile.mixed_script_hits += 1
    if misspell_hit:
        profile.misspell_hits += 1
    profile.suggestions_generated += suggestions_generated


def _check_spelling_internal(
    text: str,
    *,
    extra_words: set[str] | None = None,
    max_suggestions: int = 5,
    collect_profile: bool = False,
) -> tuple[list[Annotation], int, list[dict[str, Any]]]:
    allowlist = normalize_words(extra_words)
    normalized = normalize_text(text)
    annotations: list[Annotation] = []
    profiles: dict[str, TokenProfile] = {}
    request_cache: dict[str, WordDecision] = {}

    start_ms = time.perf_counter()

    for token in iter_tokens(normalized):
        word = token.text

        if not token.should_spellcheck:
            continue

        if word in allowlist:
            continue

        decision = request_cache.get(word)
        decision_was_created = decision is None
        if decision_was_created:
            if token.is_mixed_script:
                decision = WordDecision(
                    is_known=False,
                    is_mixed_script=True,
                )
            else:
                lookup_started = time.perf_counter()
                is_known = cached_lookup(word)
                lookup_ms = (time.perf_counter() - lookup_started) * 1000

                suggestions: tuple[str, ...] = ()
                suggest_ms = 0.0
                if not is_known and should_generate_suggestions(token):
                    suggest_started = time.perf_counter()
                    suggestions = cached_suggestions(word, max_suggestions)
                    suggest_ms = (time.perf_counter() - suggest_started) * 1000

                decision = WordDecision(
                    is_known=is_known,
                    is_mixed_script=False,
                    suggestions=suggestions,
                    lookup_ms=lookup_ms,
                    suggest_ms=suggest_ms,
                )
            request_cache[word] = decision

        if decision.is_mixed_script:
            if collect_profile:
                update_profile(
                    profiles,
                    word,
                    mixed_script_hit=True,
                )
            annotations.append(
                Annotation(
                    start=token.start,
                    end=token.end,
                    type="spelling",
                    message="Mixed Georgian and Latin characters in one word",
                    short_message="Mixed script",
                    replacements=[],
                    rule_id="token:mixed_script",
                    severity="error",
                    source="tokenizer",
                    word=word,
                )
            )
            continue

        if collect_profile:
            if decision.is_known:
                update_profile(
                    profiles,
                    word,
                    lookup_ms=decision.lookup_ms if decision_was_created else 0.0,
                )
            else:
                update_profile(
                    profiles,
                    word,
                    lookup_ms=decision.lookup_ms if decision_was_created else 0.0,
                    suggest_ms=decision.suggest_ms if decision_was_created else 0.0,
                    misspell_hit=True,
                    suggestions_generated=len(decision.suggestions),
                )

        if decision.is_known:
            continue

        annotations.append(
            Annotation(
                start=token.start,
                end=token.end,
                type="spelling",
                message="Unknown word",
                short_message="Spelling",
                replacements=list(decision.suggestions),
                rule_id="hunspell:unknown",
                severity="error",
                source="hunspell",
                word=word,
            )
        )

    elapsed_ms = int((time.perf_counter() - start_ms) * 1000)
    profile_rows = [
        profile.to_dict()
        for profile in sorted(
            profiles.values(),
            key=lambda item: (item.total_ms, item.occurrences),
            reverse=True,
        )
    ]
    return annotations, elapsed_ms, profile_rows


def check_spelling(
    text: str,
    *,
    extra_words: set[str] | None = None,
    max_suggestions: int = 5,
) -> tuple[list[Annotation], int]:
    """
    Check Georgian words in text and return annotations plus elapsed milliseconds.

    Offsets use Python string indices (Unicode code points). For Georgian Mkhedruli
    characters these match JavaScript UTF-16 code unit indices in modern browsers.
    """
    annotations, elapsed_ms, _ = _check_spelling_internal(
        text,
        extra_words=extra_words,
        max_suggestions=max_suggestions,
        collect_profile=False,
    )
    return annotations, elapsed_ms


def profile_spelling(
    text: str,
    *,
    extra_words: set[str] | None = None,
    max_suggestions: int = 5,
) -> tuple[list[Annotation], int, list[dict[str, Any]]]:
    return _check_spelling_internal(
        text,
        extra_words=extra_words,
        max_suggestions=max_suggestions,
        collect_profile=True,
    )
