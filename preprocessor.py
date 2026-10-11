"""Text normalization and tokenization helpers for Georgian text checking."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Full user-visible tokens, including mixed Georgian/Latin words like "შეცდომaa".
# `\w` is Unicode-aware in Python, so this covers Georgian, Latin and digits.
TOKEN_RE = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)
GEORGIAN_CHAR_RE = re.compile(r"[\u10A0-\u10FF]")
LATIN_CHAR_RE = re.compile(r"[A-Za-z]")
LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int
    has_georgian: bool
    has_latin: bool

    @property
    def is_mixed_script(self) -> bool:
        return self.has_georgian and self.has_latin

    @property
    def should_spellcheck(self) -> bool:
        return self.has_georgian and bool(LETTER_RE.search(self.text))


def normalize_text(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def normalize_words(words: set[str] | None) -> set[str]:
    if not words:
        return set()
    return {normalize_text(word) for word in words}


def iter_tokens(text: str) -> list[Token]:
    normalized = normalize_text(text)
    tokens: list[Token] = []

    for match in TOKEN_RE.finditer(normalized):
        token_text = match.group()
        tokens.append(
            Token(
                text=token_text,
                start=match.start(),
                end=match.end(),
                has_georgian=bool(GEORGIAN_CHAR_RE.search(token_text)),
                has_latin=bool(LATIN_CHAR_RE.search(token_text)),
            )
        )

    return tokens
