"""Grammar 2 rule integration — Agreement rules → grammar annotations.

Exports:
    run_agreement_checks(text, tokens, stanza_document) → list[AlignmentAnnotation]
    agreement_engine_meta() → dict[str, int]

This module lives in the "grammar 2" folder and dynamically loads
"Agreement rules.py" to re-export the rule engine data into backend/grammar.py
through the same plugin-loading path used by Rules/alignment_checker.py.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, FrozenSet, List, Optional, Tuple

_GRAMMAR2_DIR = Path(__file__).resolve().parent
_AGREEMENT_MODULE_PATH = _GRAMMAR2_DIR / "Agreement rules.py"
_spec = importlib.util.spec_from_file_location(
    "grammar2_agreement_rules", str(_AGREEMENT_MODULE_PATH)
)
_agr_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_agr_mod)

AgreementRole = _agr_mod.AgreementRole
CASE_SUFFIX_TO_LABEL = _agr_mod.CASE_SUFFIX_TO_LABEL
CONFUSABLE_PAIRS = _agr_mod.CONFUSABLE_PAIRS
DEMONSTRATIVES_PL = _agr_mod.DEMONSTRATIVES_PL
DEMONSTRATIVES_SG = _agr_mod.DEMONSTRATIVES_SG
DOUBLE_NEGATIVE_PATTERNS = _agr_mod.DOUBLE_NEGATIVE_PATTERNS
DOUBLE_NEGATIVE_VERBS = _agr_mod.DOUBLE_NEGATIVE_VERBS
GeorgianAgreementEngine = _agr_mod.GeorgianAgreementEngine
Number = _agr_mod.Number
PERSONAL_PRONOUN_TO_PERSON = _agr_mod.PERSONAL_PRONOUN_TO_PERSON
Person = _agr_mod.Person
PLURAL_MARKERS_NOUNS = _agr_mod.PLURAL_MARKERS_NOUNS
POSTPOSITION_GOVERNANCE = _agr_mod.POSTPOSITION_GOVERNANCE
Postposition = _agr_mod.Postposition
PROPER_NOUN_LEXICON = _agr_mod.PROPER_NOUN_LEXICON
VERB_PERSON_SUFFIX_RULES = _agr_mod.VERB_PERSON_SUFFIX_RULES
build_confusable_map = _agr_mod.build_confusable_map
detect_case_from_suffix = _agr_mod.detect_case_from_suffix
detect_demonstrative_number = _agr_mod.detect_demonstrative_number
detect_noun_number = _agr_mod.detect_noun_number
is_proper_noun = _agr_mod.is_proper_noun

_BASE_CONFUSABLE_MAP = build_confusable_map()
_CONFUSABLE_MAP: dict[str, Tuple[str, str]] = {}
for standard_form, wrong_form, explanation in CONFUSABLE_PAIRS:
    explanation_lower = explanation.lower()
    wrong_form_clean = wrong_form.strip().lower() if wrong_form else ""
    is_clear_typo = any(
        kw in explanation_lower
        for kw in (
            "typo",
            "one token",
            "not a single token",
            "avoid splitting",
            "do not split",
            "non-standard spacing",
            "avoid non-standard",
            "ensure the correct lemma",
        )
    ) or (" " in wrong_form)
    if is_clear_typo and wrong_form_clean:
        _CONFUSABLE_MAP[wrong_form_clean] = (standard_form, explanation)

_POSTPOSITION_SURFACES = frozenset(pp for pp, _, _ in POSTPOSITION_GOVERNANCE)
_POSTPOSITION_CASE_LABELS = {pp: label for pp, label, _ in POSTPOSITION_GOVERNANCE}
_POSTPOSITION_EXPECTED_SUFFIXES = {
    pp: suffixes for pp, _, suffixes in POSTPOSITION_GOVERNANCE
}


@dataclass(frozen=True)
class AlignmentAnnotation:
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


def _ann(
    start: int,
    end: int,
    type_: str,
    message: str,
    short_message: str,
    replacements: list[str],
    rule_id: str,
    severity: str,
    source: str,
    word: str,
) -> AlignmentAnnotation:
    return AlignmentAnnotation(
        start=start,
        end=end,
        type=type_,
        message=message,
        short_message=short_message,
        replacements=replacements,
        rule_id=rule_id,
        severity=severity,
        source=source,
        word=word,
    )


# =============================================================================
# Rule 1: Postposition case governance
# =============================================================================

def _check_postposition_governance(tokens: list[Any]) -> list[AlignmentAnnotation]:
    out: list[AlignmentAnnotation] = []
    for i, tok in enumerate(tokens):
        surface = tok.text.strip(".,!?…;:\"'“”„")
        lowered = surface.lower()
        if lowered not in _POSTPOSITION_SURFACES:
            continue
        expected_suffixes = _POSTPOSITION_EXPECTED_SUFFIXES[lowered]
        expected_label = _POSTPOSITION_CASE_LABELS[lowered]
        if i == 0:
            continue
        prev_tok = tokens[i - 1]
        prev_surface = prev_tok.text.strip(".,!?…;:\"'“”„")
        prev_lowered = prev_surface.lower()
        actual_case = detect_case_from_suffix(prev_surface)

        matches = any(prev_lowered.endswith(sfx) for sfx in expected_suffixes)
        if matches or actual_case is None:
            continue

        candidate_suffixes: list[str] = sorted(
            expected_suffixes, key=len, reverse=True
        )
        suggestions: list[str] = []
        for sfx in candidate_suffixes:
            base = prev_surface
            for existing_sfx in sorted(
                CASE_SUFFIX_TO_LABEL.keys(), key=len, reverse=True
            ):
                if base.lower().endswith(existing_sfx):
                    base = base[: -len(existing_sfx)]
                    break
            candidate = base + sfx
            if candidate and candidate not in suggestions:
                suggestions.append(candidate)
        suggestions = suggestions[:3]

        actual_label = actual_case or "unrecognised"
        msg = (
            f"Postposition '{surface}' requires {expected_label} case on the "
            f"preceding noun. Found {actual_label}."
        )
        out.append(
            _ann(
                start=prev_tok.start,
                end=prev_tok.end,
                type_="grammar",
                message=msg,
                short_message="Postposition case",
                replacements=suggestions,
                rule_id="grammar:postposition_governance",
                severity="warning",
                source="grammar2-agreement",
                word=prev_surface,
            )
        )
    return out


# =============================================================================
# Rule 2: Confusable / near-homophone pairs
# =============================================================================

def _check_confusable_pairs(tokens: list[Any]) -> list[AlignmentAnnotation]:
    out: list[AlignmentAnnotation] = []
    for tok in tokens:
        raw = tok.text.strip()
        if not raw:
            continue
        stripped = raw.strip(".,!?…;:\"'“”„")
        hit = _CONFUSABLE_MAP.get(stripped.lower()) or _CONFUSABLE_MAP.get(
            raw.lower()
        )
        if hit is None:
            continue
        intended, explanation = hit
        if intended.strip().lower() == stripped.lower():
            continue
        out.append(
            _ann(
                start=tok.start,
                end=tok.end,
                type_="grammar",
                message=explanation,
                short_message="Confusable word",
                replacements=[intended] if intended else [],
                rule_id="grammar:confusable_pair",
                severity="warning",
                source="grammar2-agreement",
                word=tok.text,
            )
        )
    return out


# =============================================================================
# Rule 3: Demonstrative–head noun number agreement
# =============================================================================

def _check_demonstrative_number_agreement(
    tokens: list[Any],
) -> list[AlignmentAnnotation]:
    out: list[AlignmentAnnotation] = []
    for i, tok in enumerate(tokens):
        surface = tok.text.strip(".,!?…;:\"'“”„")
        dem_num = detect_demonstrative_number(surface)
        if dem_num is None:
            continue
        if i >= len(tokens) - 1:
            continue
        for j in range(i + 1, min(i + 4, len(tokens))):
            head_candidate = tokens[j]
            head_surface = head_candidate.text.strip(".,!?…;:\"'“”„")
            noun_num = detect_noun_number(head_surface)
            if noun_num is None:
                continue
            if dem_num == noun_num:
                break
            dem_lbl = "plural" if dem_num == Number.PLURAL else "singular"
            n_lbl = "plural" if noun_num == Number.PLURAL else "singular"
            msg = (
                f"Demonstrative '{surface}' is {dem_lbl} but head noun "
                f"'{head_surface}' is {n_lbl}."
            )
            out.append(
                _ann(
                    start=tok.start,
                    end=head_candidate.end,
                    type_="grammar",
                    message=msg,
                    short_message="Demonstrative number",
                    replacements=[],
                    rule_id="grammar:demonstrative_number",
                    severity="warning",
                    source="grammar2-agreement",
                    word=f"{surface} ... {head_surface}",
                )
            )
            break
    return out


# =============================================================================
# Rule 4: Proper noun capitalisation
# =============================================================================

def _check_proper_noun_capitalisation(tokens: list[Any]) -> list[AlignmentAnnotation]:
    out: list[AlignmentAnnotation] = []
    for tok in tokens:
        raw = tok.text
        surface = raw.strip(".,!?…;:\"'“”„")
        if not surface:
            continue
        if is_proper_noun(surface) and surface[:1].islower():
            suggestion = surface[:1].upper() + surface[1:]
            out.append(
                _ann(
                    start=tok.start,
                    end=tok.end,
                    type_="grammar",
                    message=(
                        f"'{surface}' is a proper noun and should be "
                        f"capitalised as '{suggestion}'."
                    ),
                    short_message="Proper noun cap",
                    replacements=[suggestion],
                    rule_id="grammar:proper_noun_capitalisation",
                    severity="warning",
                    source="grammar2-agreement",
                    word=raw,
                )
            )
    return out


# =============================================================================
# Rule 5: Double-negative collocations
# =============================================================================

def _check_double_negatives(tokens: list[Any]) -> list[AlignmentAnnotation]:
    out: list[AlignmentAnnotation] = []
    lowered_tokens = [
        (i, t.text.strip(".,!?…;:\"'“”„").lower(), t)
        for i, t in enumerate(tokens)
    ]
    for pattern_set, explanation in DOUBLE_NEGATIVE_PATTERNS:
        found_indices: list[tuple[int, Any]] = []
        for pattern in pattern_set:
            for idx, lw, tok in lowered_tokens:
                if lw == pattern:
                    found_indices.append((idx, tok))
                    break
        if len(found_indices) >= len(pattern_set):
            found_indices.sort(key=lambda x: x[0])
            first_idx, first_tok = found_indices[0]
            last_idx, last_tok = found_indices[-1]
            out.append(
                _ann(
                    start=first_tok.start,
                    end=last_tok.end,
                    type_="grammar",
                    message=explanation,
                    short_message="Double negative",
                    replacements=[],
                    rule_id="grammar:double_negative",
                    severity="warning",
                    source="grammar2-agreement",
                    word=" ".join(t.text for _, t in found_indices),
                )
            )
    return out


# =============================================================================
# Rule 6: Subject-verb person/number agreement (lightweight surface hook)
# =============================================================================

def _check_personal_pronoun_verb_agreement(
    tokens: list[Any], stanza_document: Any | None
) -> list[AlignmentAnnotation]:
    out: list[AlignmentAnnotation] = []
    for i, tok in enumerate(tokens):
        surface = tok.text.strip(".,!?…;:\"'“”„").lower()
        if surface not in PERSONAL_PRONOUN_TO_PERSON:
            continue
        pronoun_person = PERSONAL_PRONOUN_TO_PERSON[surface]
        pronoun_number = (
            Number.PLURAL
            if surface in {"ჩვენ", "თქვენ", "ისინი", "მათ"}
            else Number.SINGULAR
        )
        for j in range(i + 1, min(i + 8, len(tokens))):
            candidate = tokens[j]
            cand_surface = candidate.text.strip(".,!?…;:\"'“”„")
            lowered_cand = cand_surface.lower()
            is_verb = False
            if stanza_document is not None:
                for sent in getattr(stanza_document, "sentences", []) or []:
                    for w in sent.words:
                        if (
                            int(getattr(w, "start_char", -1) or -1) == candidate.start
                            and getattr(w, "upos", "") == "VERB"
                        ):
                            is_verb = True
                            break
                    if is_verb:
                        break
            else:
                for suffix, vp, vn in VERB_PERSON_SUFFIX_RULES:
                    if lowered_cand.endswith(suffix):
                        is_verb = True
                        break
            if not is_verb:
                continue
            _matching: list[str] = []
            for suffix, vp, vn in VERB_PERSON_SUFFIX_RULES:
                if vp == pronoun_person and vn == pronoun_number:
                    _matching.append(suffix)
            break
    return out


# =============================================================================
# Public entry points
# =============================================================================

def run_agreement_checks(
    text: str, tokens: list[Any], stanza_document: Any | None = None
) -> list[AlignmentAnnotation]:
    if not tokens:
        return []

    annotations: list[AlignmentAnnotation] = []
    annotations.extend(_check_postposition_governance(tokens))
    annotations.extend(_check_confusable_pairs(tokens))
    annotations.extend(_check_demonstrative_number_agreement(tokens))
    annotations.extend(_check_proper_noun_capitalisation(tokens))
    annotations.extend(_check_double_negatives(tokens))
    annotations.extend(
        _check_personal_pronoun_verb_agreement(tokens, stanza_document)
    )
    return annotations


def agreement_engine_meta() -> dict[str, int]:
    return {
        "grammar2_postposition_count": len(POSTPOSITION_GOVERNANCE),
        "grammar2_confusable_count": len(CONFUSABLE_PAIRS),
        "grammar2_proper_noun_count": len(PROPER_NOUN_LEXICON),
        "grammar2_double_negative_patterns": len(DOUBLE_NEGATIVE_PATTERNS),
        "grammar2_verb_person_rules": len(VERB_PERSON_SUFFIX_RULES),
    }
