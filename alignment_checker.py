"""Alignment rule integration — Georgian case-transition engine → grammar annotations.

Exports:
    run_case_alignment_checks(document, text) → list[GrammarAnnotation]
    build_verb_lexicon() → dict[lemma, VerbLexeme]

This module lives outside the backend package so the Rules folder stays the
authoritative source for the alignment engine; the checker re-exports the user's
enumerations and GeorgianAlignmentEngine from Case transitions.py.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

_RULES_DIR = Path(__file__).resolve().parent
_CASE_MODULE_PATH = _RULES_DIR / "Case transitions.py"
_spec = importlib.util.spec_from_file_location(
    "case_transitions_rules", str(_CASE_MODULE_PATH)
)
_case_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_case_mod)  # type: ignore[union-attr]

ClauseArguments = _case_mod.ClauseArguments
GeorgianAlignmentEngine = _case_mod.GeorgianAlignmentEngine
GrammaticalCase = _case_mod.GrammaticalCase
ScreeveSeries = _case_mod.ScreeveSeries
SemanticRole = _case_mod.SemanticRole
UD_CASE_TO_GEORGIAN = _case_mod.UD_CASE_TO_GEORGIAN
VerbConjugation = _case_mod.VerbConjugation
VerbLexeme = _case_mod.VerbLexeme
VerbTransitivity = _case_mod.VerbTransitivity

# =============================================================================
# Georgian surface suffix → case (fallback for noisy pronouns / rare lemmas)
# =============================================================================

_CASE_SUFFIX_RULES: list[tuple[str, GrammaticalCase]] = [
    ("თი", GrammaticalCase.VOCATIVE),
    ("თა", GrammaticalCase.VOCATIVE),
    ("ოვით", GrammaticalCase.INSTRUMENTAL),
    ("ებით", GrammaticalCase.INSTRUMENTAL),
    ("ით", GrammaticalCase.INSTRUMENTAL),
    ("თან", GrammaticalCase.DATIVE),
    ("ში", GrammaticalCase.ADVERBIAL),
    ("შია", GrammaticalCase.ADVERBIAL),
    ("ზე", GrammaticalCase.ADVERBIAL),
    ("დან", GrammaticalCase.ADVERBIAL),
    ("იდან", GrammaticalCase.ADVERBIAL),
    ("ის", GrammaticalCase.GENITIVE),
    ("ს", GrammaticalCase.DATIVE),
    ("ო", GrammaticalCase.VOCATIVE),
    ("მა", GrammaticalCase.ERGATIVE),
]

_PERSONAL_PRONOUN_CASE: dict[tuple[str, str], GrammaticalCase] = {
    ("მე", "1"): GrammaticalCase.ERGATIVE,
    ("ჩვენ", "1"): GrammaticalCase.ERGATIVE,
    ("შენ", "2"): GrammaticalCase.ERGATIVE,
    ("თქვენ", "2"): GrammaticalCase.ERGATIVE,
    ("ის", "3"): GrammaticalCase.NOMINATIVE,
    ("ისინი", "3"): GrammaticalCase.NOMINATIVE,
}

_SYNCRETIC_PERSONAL_PRONOUNS = {
    "მე",
    "ჩვენ",
    "შენ",
    "თქვენ",
}


def _is_syncretic_personal_pronoun(word: Any) -> bool:
    text = getattr(word, "text", "") or ""
    lemma = getattr(word, "lemma", "") or ""
    upos = getattr(word, "upos", "") or ""
    if upos not in {"PRON", "NOUN"}:
        return False
    return (
        text.lower() in _SYNCRETIC_PERSONAL_PRONOUNS
        or lemma.lower() in _SYNCRETIC_PERSONAL_PRONOUNS
    )


def _syncretic_equivalent(case: GrammaticalCase) -> set[GrammaticalCase]:
    if case in {GrammaticalCase.NOMINATIVE, GrammaticalCase.ERGATIVE}:
        return {GrammaticalCase.NOMINATIVE, GrammaticalCase.ERGATIVE}
    return {case}

# =============================================================================
# Seed verb lexicon — 1st / 2nd / 3rd / 4th conjugations
# =============================================================================


def build_verb_lexicon() -> dict[str, VerbLexeme]:
    """Return the hand-curated seed lexicon keyed by lemma.

    Lemma keys match the values produced by Stanza's ka lemmatizer (usually 3sg
    present for transitive/intransitive, but citation forms vary; this table
    contains multiple aliases per lexeme in a separate step below).
    """

    lexemes: list[VerbLexeme] = [
        # --- 1st Conjugation — Transitive / Active ---------------------------
        VerbLexeme("წერს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("წერ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("კითხულობს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("კითხულ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("ყურობს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("ყურ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("ნახავს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("ხედავს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("ხედ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("აკეთებს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("აკეთ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("გადაწერს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("გადაწერ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("დაუწერს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("დაუწერ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("უკეთებს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("უკეთ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("უკითხავს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("უკითხავ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("წაიკითხავს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("წაიკითხავ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("გამოგიგზავნის", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("გამოგიგზავნ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("გიგზავნის", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("გიგზავნ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("იყიდავს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("იყიდავ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("იყიდის", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("იყიდ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("მოუყიდავს", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        VerbLexeme("მოუყიდავ", VerbConjugation.FIRST, VerbTransitivity.TRANSITIVE),
        # --- 2nd Conjugation — Patientive intransitive -----------------------
        VerbLexeme(
            "იცოცხლობს",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "ცოცხლობ",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "სძილავს",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "სძილავ",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "ნინებს",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "ნინებ",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "გარდაერთ",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "შევიდა",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "შოვიდა",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "მოვიდა",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "მიდის",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "მიდ",
            VerbConjugation.SECOND,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        # --- 3rd Conjugation — Medial / Agentive intransitive ----------------
        VerbLexeme(
            "სცევს", VerbConjugation.THIRD, VerbTransitivity.INTRANSITIVE, SemanticRole.AGENT
        ),
        VerbLexeme(
            "სცევ", VerbConjugation.THIRD, VerbTransitivity.INTRANSITIVE, SemanticRole.AGENT
        ),
        VerbLexeme(
            "სმს", VerbConjugation.THIRD, VerbTransitivity.INTRANSITIVE, SemanticRole.AGENT
        ),
        VerbLexeme(
            "სმ", VerbConjugation.THIRD, VerbTransitivity.INTRANSITIVE, SemanticRole.AGENT
        ),
        VerbLexeme(
            "სიცილობს",
            VerbConjugation.THIRD,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.AGENT,
        ),
        VerbLexeme(
            "სიცილობ",
            VerbConjugation.THIRD,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.AGENT,
        ),
        VerbLexeme(
            "კვრდია",
            VerbConjugation.THIRD,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.AGENT,
        ),
        VerbLexeme(
            "კვრდი",
            VerbConjugation.THIRD,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.AGENT,
        ),
        VerbLexeme(
            "მივიდა",
            VerbConjugation.THIRD,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.AGENT,
        ),
        VerbLexeme(
            "მიდედი",
            VerbConjugation.THIRD,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.AGENT,
        ),
        VerbLexeme(
            "დავიდა",
            VerbConjugation.THIRD,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.AGENT,
        ),
        VerbLexeme(
            "დავიდი",
            VerbConjugation.THIRD,
            VerbTransitivity.INTRANSITIVE,
            SemanticRole.AGENT,
        ),
        # --- 4th Conjugation — Inverted / Affective --------------------------
        VerbLexeme(
            "ყვარს",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "ყვარ",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "მაყვარი",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "მაყვარს",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "მიყვარს",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "მიყვარი",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "გიყვარს",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "გიყვარი",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "აგონებს",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "აგონებ",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "სცინის",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "სცინ",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "აქვს",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "ჰქონდა",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "აქონდა",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "მინდავს",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
        VerbLexeme(
            "მინდავ",
            VerbConjugation.FOURTH,
            VerbTransitivity.TRANSITIVE,
            SemanticRole.PATIENT_EXPERIENCER,
        ),
    ]

    result: dict[str, VerbLexeme] = {}
    for lexeme in lexemes:
        result[lexeme.lemma] = lexeme
    return result


_VERB_LEXICON = build_verb_lexicon()


# =============================================================================
# Helper: minimal GrammarAnnotation-shaped dataclass
# (re-declared here to avoid a circular backend import; converted downstream)
# =============================================================================


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


# =============================================================================
# Screeve-series classifier
# =============================================================================

_AORIST_PERSONAL_SUFFIX = re.compile(
    r"(?:ე|ი|ეს|ენ|ეთ|ა|ათ)$"
)
_IMPERFECT_SUFFIXES = re.compile(
    r"(?:ოდ|ოდი|დი|დიათ|ოდნენ|ოდნენ)$"
)


def classify_screeve(verb: Any) -> Optional[ScreeveSeries]:
    """Best-effort classification of a Stanza verb into I / II / III.

    Robust to ka model quirks (Tense=Past + Aspect=Imp used for Aorists).
    """

    feats: dict[str, str] = {}
    if getattr(verb, "feats", None):
        for piece in str(verb.feats).split("|"):
            if "=" in piece:
                k, v = piece.split("=", 1)
                feats[k] = v

    tense = feats.get("Tense", "")
    aspect = feats.get("Aspect", "")
    mood = feats.get("Mood", "")
    surface = getattr(verb, "text", "") or ""
    subcat = feats.get("Subcat", "")
    has_aorist_suffix = bool(_AORIST_PERSONAL_SUFFIX.search(surface))
    has_imperfect_suffix = bool(_IMPERFECT_SUFFIXES.search(surface))

    if mood == "Cnd":
        return ScreeveSeries.SERIES_I
    if tense in {"Pres", "Fut"}:
        return ScreeveSeries.SERIES_I

    if tense == "Pqp":
        return ScreeveSeries.SERIES_II

    if tense == "Past":
        if has_aorist_suffix and subcat == "Tran":
            return ScreeveSeries.SERIES_II
        if has_imperfect_suffix:
            return ScreeveSeries.SERIES_I
        if has_aorist_suffix:
            return ScreeveSeries.SERIES_II
        if aspect == "Imp" and not has_aorist_suffix:
            return ScreeveSeries.SERIES_I
        return ScreeveSeries.SERIES_II

    if aspect == "Perf" or has_aorist_suffix:
        return ScreeveSeries.SERIES_II

    return None


# =============================================================================
# Case extractor (UD feats → Georgian case, with surface-form suffix fallback)
# =============================================================================


def extract_case(word: Any) -> Optional[GrammaticalCase]:
    feats: dict[str, str] = {}
    if getattr(word, "feats", None):
        for piece in str(word.feats).split("|"):
            if "=" in piece:
                k, v = piece.split("=", 1)
                feats[k] = v

    text = getattr(word, "text", "") or ""
    lowered = text.lower()
    lemma = getattr(word, "lemma", "") or ""
    person = feats.get("Person", "")

    # --- Syncletic 1/2-pronouns override: ignore stanza feats, always treat as Nom/Erg
    if lowered in _SYNCRETIC_PERSONAL_PRONOUNS or lemma.lower() in _SYNCRETIC_PERSONAL_PRONOUNS:
        return GrammaticalCase.ERGATIVE

    key = (lowered, person)
    if key in _PERSONAL_PRONOUN_CASE:
        return _PERSONAL_PRONOUN_CASE[key]
    if lemma == "მაგ" and lowered == "მაგ":
        return GrammaticalCase.NOMINATIVE
    if lemma == "მას" and lowered == "მას":
        return GrammaticalCase.DATIVE

    ud_case = feats.get("Case")
    if ud_case and ud_case in UD_CASE_TO_GEORGIAN:
        return UD_CASE_TO_GEORGIAN[ud_case]

    for suffix, case in _CASE_SUFFIX_RULES:
        if lowered.endswith(suffix):
            return case

    return None


# =============================================================================
# Series-III perfect-cluster detector
# =============================================================================

_AUX_INVERTED_LEMMAS = {"აქვს", "ჰქონდა", "აქონდა"}


def find_perfect_cluster(sentence: Any) -> dict[str, str]:
    """Return mapping of verb_id → 'main_lemma' for Ser-III aux+participle pairs.

    When we have e.g.  `მას წერილი აქვს დაწერილი`, the governing head is `აქვს`
    (4th conj always-inverted), so the standard 4th-conj case mapping Dative
    subject + Nominative object already applies.  The participle `დაწერილი`
    provides the *semantic* lemma.  We keep this mapping for diagnostics but
    do not currently need it to choose expected cases — the 4th-conj rule is
    sufficient.  Hook is preserved for a future more precise classifier.
    """

    return {}


# =============================================================================
# Dependency walk — subject/object extraction per verb
# =============================================================================

_SUBJECT_DEPRELS = {"nsubj", "nsubj:outer", "nsubj:pass", "nsubj:caus"}
_OBJECT_DEPRELS = {"obj", "iobj"}

_PERSONAL_PRONOUN_FORMS = {
    "მე",
    "ჩვენ",
    "შენ",
    "თქვენ",
    "ის",
    "ისინი",
    "მაგ",
    "მას",
    "მინდ",
    "ჩვენ",
    "მათ",
    "შენგან",
    "იმ",
}


def _looks_like_personal_pronoun(word: Any) -> bool:
    text = (getattr(word, "text", "") or "").lower()
    lemma = (getattr(word, "lemma", "") or "").lower().rstrip("(ი)").rstrip("ი)")
    upos = getattr(word, "upos", "") or ""
    if upos == "PRON":
        return True
    return text in _PERSONAL_PRONOUN_FORMS or lemma in _PERSONAL_PRONOUN_FORMS


def _children(sentence: Any, head_id: str) -> list[Any]:
    out: list[Any] = []
    for word in sentence.words:
        if str(getattr(word, "head", "")) == str(head_id):
            out.append(word)
    return out


def _collect_descendants(sentence: Any, head_id: str, depth: int = 0) -> list[Any]:
    if depth > 3:
        return []
    out: list[Any] = []
    direct = _children(sentence, head_id)
    out.extend(direct)
    for child in direct:
        out.extend(_collect_descendants(sentence, str(getattr(child, "id", "")), depth + 1))
    return out


def find_arguments(sentence: Any, verb: Any) -> tuple[Optional[Any], Optional[Any]]:
    verb_id = str(getattr(verb, "id", ""))

    def root_id() -> str:
        for w in sentence.words:
            if str(getattr(w, "deprel", "") or "") == "root":
                return str(getattr(w, "id", ""))
        return verb_id

    search_ids = {verb_id}
    rid = root_id()
    if rid != verb_id:
        search_ids.add(rid)
    candidates: list[tuple[int, Any]] = []
    object_node: Optional[Any] = None
    object_forbidden = False

    for sid in search_ids:
        for word in _collect_descendants(sentence, sid, depth=2) + _children(sentence, sid):
            deprel = str(getattr(word, "deprel", "") or "")
            wid = str(getattr(word, "id", ""))
            if wid == verb_id:
                continue
            if deprel in _SUBJECT_DEPRELS:
                priority = 10
                if _looks_like_personal_pronoun(word):
                    priority += 100
                candidates.append((priority, word))
            elif _looks_like_personal_pronoun(word) and word not in {c for _, c in candidates}:
                candidates.append((50, word))
            if deprel in _OBJECT_DEPRELS and object_node is None:
                object_node = word
            if deprel == "obl":
                case_obl = extract_case(word)
                if case_obl in {GrammaticalCase.NOMINATIVE, GrammaticalCase.DATIVE}:
                    if (
                        object_node is None
                        and deprel not in {"advcl", "acl"}
                        and getattr(word, "upos", "") in {"NOUN", "PROPN", "PRON", "ADJ"}
                    ):
                        if case_obl == GrammaticalCase.NOMINATIVE:
                            object_node = word
                        elif case_obl == GrammaticalCase.DATIVE:
                            if getattr(word, "feats") and "NameType=Geo" in str(word.feats or ""):
                                object_forbidden = True
                            else:
                                object_node = word
                    else:
                        object_forbidden = True

    if object_forbidden:
        object_node = None

    if candidates:
        candidates.sort(key=lambda t: -t[0])
        subject_node: Optional[Any] = candidates[0][1]
    else:
        subject_node = None

    if subject_node is None:
        for word in sentence.words:
            if _looks_like_personal_pronoun(word):
                subject_node = word
                break

    return subject_node, object_node


# =============================================================================
# Annotation renderer (produces AlignmentAnnotation records)
# =============================================================================


def _make_alignment_annotation(
    anchor: Any,
    verb_text: str,
    series: ScreeveSeries,
    argument_label: str,
    expected_case: Optional[GrammaticalCase],
    actual_case: Optional[GrammaticalCase],
    conjugation: VerbConjugation,
) -> AlignmentAnnotation:
    expected_text = (
        expected_case.value if expected_case else "no direct object"
    )
    actual_text = actual_case.value if actual_case else "unrecognized"
    message = (
        f"{argument_label} case mismatch for '{verb_text}' ({series.value}, "
        f"Conj {conjugation.value}).  Required: {expected_text}.  Found: {actual_text}."
    )
    short = f"{argument_label.lower()} case"
    start = int(getattr(anchor, "start_char", 0) or 0)
    end = int(getattr(anchor, "end_char", start + len(verb_text)) or (start + len(verb_text)))
    return AlignmentAnnotation(
        start=start,
        end=end,
        type="grammar",
        message=message,
        short_message=short,
        replacements=[],
        rule_id="grammar:case_alignment",
        severity="warning",
        source="alignment-engine",
        word=getattr(anchor, "text", verb_text) or verb_text,
    )


# =============================================================================
# Public entry point
# =============================================================================


def run_case_alignment_checks(document: Any, text: str) -> list[AlignmentAnnotation]:
    if document is None:
        return []

    annotations: list[AlignmentAnnotation] = []

    for sentence in getattr(document, "sentences", []) or []:
        for verb in sentence.words:
            upos = getattr(verb, "upos", None)
            lemma_raw = getattr(verb, "lemma", "") or ""
            lemma_low = lemma_raw.lower()
            lexeme = _VERB_LEXICON.get(lemma_low) or _VERB_LEXICON.get(lemma_raw)

            if lexeme is None and upos in {"NOUN", "ADJ"}:
                surface_low = (getattr(verb, "text", "") or "").lower()
                lexeme = _VERB_LEXICON.get(surface_low) or _VERB_LEXICON.get(
                    getattr(verb, "text", "") or ""
                )

            if lexeme is not None and lexeme.conjugation == VerbConjugation.FOURTH:
                upos = "VERB"
            elif lexeme is None and upos in {"NOUN", "ADJ"}:
                pass

            if upos != "VERB":
                continue
            if lexeme is None:
                continue

            if (getattr(verb, "lemma", "") or "") in _AUX_INVERTED_LEMMAS or (
                getattr(verb, "text", "") or ""
            ) in _AUX_INVERTED_LEMMAS:
                lexeme = VerbLexeme(
                    lemma=lemma_low,
                    conjugation=VerbConjugation.FOURTH,
                    transitivity=VerbTransitivity.TRANSITIVE,
                    semantic_role=SemanticRole.PATIENT_EXPERIENCER,
                )

            series = classify_screeve(verb)
            if series is None and lexeme.conjugation == VerbConjugation.FOURTH:
                series = ScreeveSeries.SERIES_I
            if series is None:
                continue

            expected = GeorgianAlignmentEngine.get_expected_cases(lexeme, series)
            subject_node, object_node = find_arguments(sentence, verb)
            actual_subj = extract_case(subject_node) if subject_node else None
            actual_obj = extract_case(object_node) if object_node else None

            valid, _ = GeorgianAlignmentEngine.validate_alignment(
                lexeme, series, actual_subj, actual_obj
            )
            if valid:
                continue

            subject_mismatch = False
            if (
                expected.subject_case is not None
                and actual_subj is not None
                and expected.subject_case != actual_subj
            ):
                if (
                    _is_syncretic_personal_pronoun(subject_node)
                    and actual_subj in _syncretic_equivalent(expected.subject_case)
                ):
                    pass
                else:
                    subject_mismatch = True
            elif (
                expected.subject_case is None
                and actual_subj is not None
                and subject_node is not None
            ):
                subject_mismatch = True

            object_mismatch = False
            if (
                expected.direct_object_case is None
                and actual_obj is not None
                and object_node is not None
            ):
                object_mismatch = True
            elif (
                expected.direct_object_case is not None
                and actual_obj is not None
                and expected.direct_object_case != actual_obj
            ):
                object_mismatch = True

            if subject_mismatch and subject_node is not None:
                annotations.append(
                    _make_alignment_annotation(
                        anchor=subject_node,
                        verb_text=getattr(verb, "text", "") or "",
                        series=series,
                        argument_label="Subject",
                        expected_case=expected.subject_case,
                        actual_case=actual_subj,
                        conjugation=lexeme.conjugation,
                    )
                )

            if object_mismatch and object_node is not None:
                annotations.append(
                    _make_alignment_annotation(
                        anchor=object_node,
                        verb_text=getattr(verb, "text", "") or "",
                        series=series,
                        argument_label="Direct object",
                        expected_case=expected.direct_object_case,
                        actual_case=actual_obj,
                        conjugation=lexeme.conjugation,
                    )
                )

    return annotations


def alignment_engine_meta() -> dict[str, int]:
    return {
        "alignment_lexicon_size": len(_VERB_LEXICON),
    }
