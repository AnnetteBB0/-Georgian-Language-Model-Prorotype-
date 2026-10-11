"""CGC backend — Georgian spell checker API."""

from __future__ import annotations

import re
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from grammar import (
    check_grammar,
    get_engine_status,
    get_rule_catalog,
    warm_grammar_resources,
)
from preprocessor import iter_tokens, normalize_text
from spellcheck import check_spelling, get_dictionary

MAX_TEXT_LENGTH = 50_000


class CheckOptions(BaseModel):
    check_spelling: bool = True
    check_grammar: bool = True
    check_style: bool = True
    extra_words: list[str] = Field(default_factory=list)


class CheckRequest(BaseModel):
    text: str
    options: CheckOptions = Field(default_factory=CheckOptions)


class CheckResponse(BaseModel):
    request_id: str
    annotations: list[dict[str, Any]]
    meta: dict[str, Any]


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_dictionary()
    warm_grammar_resources()
    yield


app = FastAPI(
    title="CGC — Georgian Language Checker",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _compute_baseline_stats(text: str) -> dict[str, Any]:
    normalized = normalize_text(text)
    tokens = [t for t in iter_tokens(normalized) if t.should_spellcheck]
    word_count = len(tokens)
    unique_words = len({t.text.lower() for t in tokens})
    parts = re.split(r"[.!?…]", normalized)
    sentence_count = max(1, len([p for p in parts if p.strip()]))
    avg_word_length = (
        round(sum(len(t.text) for t in tokens) / word_count, 2)
        if word_count
        else 0
    )
    avg_sentence_length_words = (
        round(word_count / sentence_count, 2) if sentence_count else 0
    )
    avg_sentence_length_chars = (
        round(len(normalized) / sentence_count, 2) if sentence_count else 0
    )
    lex_diversity = round(unique_words / word_count, 3) if word_count else 0

    return {
        "char_count": len(normalized),
        "word_count": word_count,
        "unique_word_count": unique_words,
        "sentence_count": sentence_count,
        "avg_word_length_chars": avg_word_length,
        "avg_sentence_length_words": avg_sentence_length_words,
        "avg_sentence_length_chars": avg_sentence_length_chars,
        "lexical_diversity": lex_diversity,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/rules")
def list_rules() -> dict[str, Any]:
    """Return the static catalog of every rule id known to the engine."""
    return {"rules": get_rule_catalog()}


@app.get("/v1/engine")
def engine_status() -> dict[str, Any]:
    """Return plugin-by-plugin availability, rule counts and metadata."""
    return get_engine_status()


@app.post("/v1/check", response_model=CheckResponse)
def check_text(body: CheckRequest) -> CheckResponse:
    text = body.text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Text exceeds maximum length of {MAX_TEXT_LENGTH} characters",
        )

    annotations: list[dict[str, Any]] = []
    meta: dict[str, Any] = {
        "spell_ms": 0,
        "grammar_ms": 0,
        "grammar_engine": "rules+optional-stanza",
        "stanza_available": False,
        "stanza_used": False,
    }
    meta.update(_compute_baseline_stats(text))

    if body.options.check_spelling:
        spell_annotations, spell_ms = check_spelling(
            text,
            extra_words=set(body.options.extra_words),
        )
        annotations.extend(a.to_dict() for a in spell_annotations)
        meta["spell_ms"] = spell_ms

    if body.options.check_grammar or body.options.check_style:
        grammar_annotations, grammar_ms, grammar_meta = check_grammar(text)
        meta["grammar_ms"] = grammar_ms
        meta.update(grammar_meta)

        include_grammar = body.options.check_grammar
        include_style = body.options.check_style

        for a in grammar_annotations:
            if a.type == "grammar" and include_grammar:
                annotations.append(a.to_dict())
            elif a.type == "style" and include_style:
                annotations.append(a.to_dict())

    annotations.sort(key=lambda annotation: (annotation["start"], annotation["end"]))

    return CheckResponse(
        request_id=str(uuid.uuid4()),
        annotations=annotations,
        meta=meta,
    )
