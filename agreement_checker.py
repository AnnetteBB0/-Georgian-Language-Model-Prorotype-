"""Georgian Grammar Desktop Rules integration → grammar annotations.

Source file: georgian_grammar_rules.py (copied from Desktop)
Rule systems exported:
    1. POSTPOSITIONS — Latin-transliterated postposition → governed case
       (we maintain a parallel Georgian-script surface map for token matching)
    2. ADJECTIVE_DECLENSION — consonant- vs vowel-stem adjective suffix matrices
    3. POSSESSIVE_ADJECTIVES — 11 possessive-paradigm case matrices

Public API mirrors Rules/alignment_checker.py and grammar 2/agreement_checker.py.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, FrozenSet, List, Optional, Tuple

_GG_DIR = Path(__file__).resolve().parent
_GG_MODULE_PATH = _GG_DIR / "georgian_grammar_rules.py"
_spec = importlib.util.spec_from_file_location(
    "desktop_georgian_grammar_rules", str(_GG_MODULE_PATH)
)
_gg_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_gg_mod)

GeorgianGrammarRules = _gg_mod.GeorgianGrammarRules
MORPHEME_SLOTS = GeorgianGrammarRules.MORPHEME_SLOTS
POSTPOSITIONS = GeorgianGrammarRules.POSTPOSITIONS
ADJECTIVE_DECLENSION = GeorgianGrammarRules.ADJECTIVE_DECLENSION
POSSESSIVE_ADJECTIVES = GeorgianGrammarRules.POSSESSIVE_ADJECTIVES


# =============================================================================
# Latin transliteration → Georgian script surface map
# The source POSTPOSITIONS keys use Latin script; we need Georgian-script forms
# to match against real tokens.  This mapping is authoritative for the
# desktop-rules postposition set (keeps rule data in its source Latin
# representation per author intent, but produces Georgian-matching behaviour).
# =============================================================================

_LATIN_PP_TO_GEORGIAN: dict[str, Tuple[str, Optional[str], FrozenSet[str]]] = {
    "-vit": ("ვით", "Nominative", frozenset({"ი"})),
    "-ze": ("ზე", "Dative", frozenset({"ს", "თან"})),
    "-tan": ("თან", "Dative", frozenset({"ს", "თან"})),
    "-tan ertad": ("თან ერთად", "Dative", frozenset({"ს", "თან"})),
    "-shi": ("ში", "Dative", frozenset({"ში", "ს", "თან"})),
    "shoris": ("შორის", "Dative", frozenset({"ს", "თან"})),
    "shua": ("შუა", "Dative", frozenset({"ს", "თან"})),
    "-dan": ("დან", "Instrumental", frozenset({"დან", "ით", "ებით"})),
    "-gan": ("გან", "Genitive", frozenset({"ის"})),
    "gamo": ("გამო", "Genitive", frozenset({"ის"})),
    "garda": ("გარდა", "Genitive", frozenset({"ის"})),
    "gareshe": ("გარეშე", "Genitive", frozenset({"ის"})),
    "-tvis": ("თვის", "Genitive", frozenset({"ის"})),
    "mier": ("მიერ", "Genitive", frozenset({"ის"})),
    "magivrad": ("მაგივრად", "Genitive", frozenset({"ის"})),
    "miuxedavad": ("მიუხედავად", "Genitive", frozenset({"ის"})),
    "shesaxeb": ("შესახებ", "Genitive", frozenset({"ის"})),
    "-tsin": ("წინ", "Genitive", frozenset({"ის"})),
    "-mde": ("მდე", "Adverbial", frozenset({"მდე", "ში", "ზე", "დან", "იდან"})),
}

_GEORGIAN_SURFACE_TO_LATIN: dict[str, str] = {
    geo.lower(): lat for lat, (geo, _, _) in _LATIN_PP_TO_GEORGIAN.items()
}

# Map desktop-rules case names to the CASE_SUFFIX_TO_LABEL convention used
# elsewhere in the checker (uppercase-first: "Nominative", "Dative", …).
_CASE_NAME_NORMALISE: dict[str, str] = {
    "nominative": "Nominative",
    "ergative": "Ergative",
    "dative": "Dative",
    "genitive": "Genitive",
    "instrumental": "Instrumental",
    "adverbial": "Adverbial",
    "vocative": "Vocative",
}

_SUFFIX_TO_CASE: dict[str, str] = {
    "მა": "Ergative",
    "ი": "Nominative",
    "ს": "Dative",
    "თან": "Dative",
    "ის": "Genitive",
    "ით": "Instrumental",
    "ებით": "Instrumental",
    "ოვით": "Instrumental",
    "ში": "Adverbial",
    "ზე": "Adverbial",
    "დან": "Adverbial",
    "იდან": "Adverbial",
    "ო": "Vocative",
    "თა": "Vocative",
    "თი": "Vocative",
}


def _detect_case_suffix(word: str) -> Optional[str]:
    lw = word.lower()
    for sfx in sorted(_SUFFIX_TO_CASE.keys(), key=len, reverse=True):
        if lw.endswith(sfx):
            return sfx
    return None


def _detect_case_label(word: str) -> Optional[str]:
    sfx = _detect_case_suffix(word)
    if sfx is None:
        return None
    return _SUFFIX_TO_CASE[sfx]


# =============================================================================
# Suffix-dropping morphotactic rules (the engine's check_suffix_dropping_rule)
# -shi drops dative -s, -dan drops instrumental -t, -mde drops adverbial -d
# We represent them as: (georgian_pp_surface, required_stripped_ending_suffix)
# ending_suffix is what *would* be on the noun if the postposition were not
# dropping it — so for -shi (dative), noun should NOT end in -ს but instead
# carry -ში as the postposition directly.
# =============================================================================

_SUFFIX_DROP_RULES: dict[str, Tuple[str, str]] = {
    "-shi": ("ში", "ს"),  # dative -s must be dropped; noun ends in -ში (postp itself)
    "-dan": ("დან", "თ"),  # instrumental -t/-თ dropped; noun ends in -დან
    "-mde": ("მდე", "ო"),  # adverbial -d (approximated by noun stem check)
}


# =============================================================================
# Possessive adjective surface lookup (Georgian script forms keyed by paradigm)
# =============================================================================

_POSSESSIVE_PARADIGM_LABELS: dict[str, str] = {
    "first_person_singular": "1sg (ჩემი 'my')",
    "second_person_singular": "2sg (შენი 'your')",
    "third_person_singular_proximal": "3sg-prox (ამისი 'this one's')",
    "third_person_singular_medial": "3sg-med (მაგისი 'that one's')",
    "third_person_singular_distal": "3sg-dist (იმისი 'that one's yonder')",
    "first_person_plural": "1pl (ჩვენი 'our')",
    "second_person_plural": "2pl (თქვენი 'your pl.')",
    "third_person_plural_proximal": "3pl-prox (ამათი 'these ones'')",
    "third_person_plural_medial": "3pl-med (მაგათი 'those ones'')",
    "third_person_plural_distal": "3pl-dist (იმათი 'those ones' yonder')",
}

# Georgian-script possessive paradigms mapped from the source Latin case tables.
# Source: chem=ჩემ, shen=შენ, amis=ამის, magis=მაგის, (i)mis=იმის,
#         chven=ჩვენ, tkven=თქვენ, amat=ამათ, magat=მაგათ, (i)mat=იმათ
# Case suffixes: nom=i, erg=ma, dat=s, gen=i, ins=i(s), adv=s, voc=o
_POSSESSIVE_GEORGIAN: dict[str, dict[str, List[str]]] = {
    "ჩემი": {
        "nominative": ["ჩემი"],
        "ergative": ["ჩემმა"],
        "dative": ["ჩემს"],
        "genitive": ["ჩემი"],
        "instrumental": ["ჩემით", "ჩემის"],
        "adverbial": ["ჩემს"],
        "vocative": ["ჩემო"],
    },
    "შენი": {
        "nominative": ["შენი"],
        "ergative": ["შენმა"],
        "dative": ["შენს"],
        "genitive": ["შენი"],
        "instrumental": ["შენით", "შენის"],
        "adverbial": ["შენს"],
        "vocative": [],
    },
    "ამისი": {
        "nominative": ["ამისი"],
        "ergative": ["ამისმა"],
        "dative": ["ამის"],
        "genitive": ["ამისი"],
        "instrumental": ["ამისით", "ამისის"],
        "adverbial": ["ამის"],
        "vocative": [],
    },
    "მაგისი": {
        "nominative": ["მაგისი"],
        "ergative": ["მაგისმა"],
        "dative": ["მაგის"],
        "genitive": ["მაგისი"],
        "instrumental": ["მაგისით", "მაგისის"],
        "adverbial": ["მაგის"],
        "vocative": [],
    },
    "იმისი": {
        "nominative": ["იმისი", "მისი"],
        "ergative": ["იმისმა", "მისმა"],
        "dative": ["იმის", "მის"],
        "genitive": ["იმისი", "მისი"],
        "instrumental": ["იმისით", "მისით"],
        "adverbial": ["იმის", "მის"],
        "vocative": [],
    },
    "ჩვენი": {
        "nominative": ["ჩვენი"],
        "ergative": ["ჩვენმა"],
        "dative": ["ჩვენს"],
        "genitive": ["ჩვენი"],
        "instrumental": ["ჩვენით", "ჩვენის"],
        "adverbial": ["ჩვენს"],
        "vocative": ["ჩვენო"],
    },
    "თქვენი": {
        "nominative": ["თქვენი"],
        "ergative": ["თქვენმა"],
        "dative": ["თქვენს"],
        "genitive": ["თქვენი"],
        "instrumental": ["თქვენით", "თქვენის"],
        "adverbial": ["თქვენს"],
        "vocative": [],
    },
    "ამათი": {
        "nominative": ["ამათი"],
        "ergative": ["ამათმა"],
        "dative": ["ამათ"],
        "genitive": ["ამათი"],
        "instrumental": ["ამათით"],
        "adverbial": ["ამათ"],
        "vocative": [],
    },
    "მაგათი": {
        "nominative": ["მაგათი"],
        "ergative": ["მაგათმა"],
        "dative": ["მაგათ"],
        "genitive": ["მაგათი"],
        "instrumental": ["მაგათით"],
        "adverbial": ["მაგათ"],
        "vocative": [],
    },
    "იმათი": {
        "nominative": ["იმათი", "მათი"],
        "ergative": ["იმათმა", "მათმა"],
        "dative": ["იმათ", "მათ"],
        "genitive": ["იმათი", "მათი"],
        "instrumental": ["იმათით", "მათით"],
        "adverbial": ["იმათ", "მათ"],
        "vocative": [],
    },
}

_POSSESSIVE_LEMMA_TO_PARADIGM: dict[str, str] = {
    "ჩემი": "first_person_singular",
    "შენი": "second_person_singular",
    "ამისი": "third_person_singular_proximal",
    "მაგისი": "third_person_singular_medial",
    "იმისი": "third_person_singular_distal",
    "მისი": "third_person_singular_distal",
    "ჩვენი": "first_person_plural",
    "თქვენი": "second_person_plural",
    "ამათი": "third_person_plural_proximal",
    "მაგათი": "third_person_plural_medial",
    "იმათი": "third_person_plural_distal",
    "მათი": "third_person_plural_distal",
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
        source="desktop-georgian-grammar-rules",
        word=word,
    )


# =============================================================================
# Rule 1: Desktop-rules postposition governance + suffix-drop constraints
# =============================================================================

def _check_desktop_postposition_governance(
    tokens: list[Any],
) -> list[AlignmentAnnotation]:
    out: list[AlignmentAnnotation] = []
    for i, tok in enumerate(tokens):
        surface = tok.text.strip(".,!?…;:\"'“”„")
        lowered = surface.lower()
        latin_key = _GEORGIAN_SURFACE_TO_LATIN.get(lowered)
        if latin_key is None:
            continue
        pp_spec = POSTPOSITIONS.get(latin_key)
        if pp_spec is None:
            continue
        required_case_raw = pp_spec.get("governed_case", "")
        required_case = _CASE_NAME_NORMALISE.get(required_case_raw, required_case_raw)
        geo_surface, _norm, accepted_suffixes = _LATIN_PP_TO_GEORGIAN[latin_key]

        if i == 0:
            continue
        prev_tok = tokens[i - 1]
        prev_surface = prev_tok.text.strip(".,!?…;:\"'“”„")
        prev_lowered = prev_surface.lower()
        actual_case = _detect_case_label(prev_surface)

        matches = any(prev_lowered.endswith(sfx) for sfx in accepted_suffixes)
        if matches:
            drop_rule = _SUFFIX_DROP_RULES.get(latin_key)
            if drop_rule is not None:
                pp_geo_surface, forbidden_suffix = drop_rule
                if latin_key == "-shi":
                    if not prev_lowered.endswith("ში"):
                        suggestions: list[str] = []
                        for sfx in ("ში", "ს"):
                            stripped = prev_surface
                            for esfx in sorted(_SUFFIX_TO_CASE.keys(), key=len, reverse=True):
                                if stripped.lower().endswith(esfx) and esfx != "ში":
                                    stripped = stripped[: -len(esfx)]
                                    break
                            cand = stripped + "ში"
                            if cand and cand not in suggestions:
                                suggestions.append(cand)
                        out.append(
                            _ann(
                                start=prev_tok.start,
                                end=prev_tok.end,
                                type_="grammar",
                                message=(
                                    f"Postposition '{geo_surface}' (-shi) requires "
                                    f"dative case with -s suffix dropped; noun should "
                                    f"end in -ში (attached). Expected Dative. "
                                    f"Found {actual_case or 'unrecognised'}."
                                ),
                                short_message="-shi suffix drop",
                                replacements=suggestions[:3],
                                rule_id="desktop:suffix_dropping_shi",
                                severity="warning",
                                word=prev_surface,
                            )
                        )
                elif latin_key == "-dan":
                    if not prev_lowered.endswith("დან"):
                        suggestions = []
                        stripped = prev_surface
                        for esfx in sorted(_SUFFIX_TO_CASE.keys(), key=len, reverse=True):
                            if stripped.lower().endswith(esfx) and esfx != "დან":
                                stripped = stripped[: -len(esfx)]
                                break
                        cand = stripped + "დან"
                        if cand:
                            suggestions.append(cand)
                        out.append(
                            _ann(
                                start=prev_tok.start,
                                end=prev_tok.end,
                                type_="grammar",
                                message=(
                                    f"Postposition '{geo_surface}' (-dan) governs "
                                    f"Instrumental and requires dropping -თ suffix; "
                                    f"noun should end in -დან (attached). "
                                    f"Found {actual_case or 'unrecognised'}."
                                ),
                                short_message="-dan suffix drop",
                                replacements=suggestions[:3],
                                rule_id="desktop:suffix_dropping_dan",
                                severity="warning",
                                word=prev_surface,
                            )
                        )
            continue

        suggestions = []
        for sfx in sorted(accepted_suffixes, key=len, reverse=True):
            stripped = prev_surface
            for esfx in sorted(_SUFFIX_TO_CASE.keys(), key=len, reverse=True):
                if stripped.lower().endswith(esfx):
                    stripped = stripped[: -len(esfx)]
                    break
            cand = stripped + sfx
            if cand and cand not in suggestions:
                suggestions.append(cand)

        actual_label = actual_case or "unrecognised"
        msg = (
            f"Postposition '{geo_surface}' (from desktop rules, key {latin_key}) "
            f"governs {required_case} case on the preceding noun. "
            f"Found {actual_label}."
        )
        out.append(
            _ann(
                start=prev_tok.start,
                end=prev_tok.end,
                type_="grammar",
                message=msg,
                short_message="Postposition (desktop)",
                replacements=suggestions[:3],
                rule_id="desktop:postposition_governance",
                severity="warning",
                word=prev_surface,
            )
        )
    return out


# =============================================================================
# Rule 2: Adjective declension (consonant- vs vowel-stem suffix check)
#   Consonant-final stems: nom=-i, erg=-ma, dat=∅, gen=-i, ins=-i, adv=∅, voc=-o
#   Vowel-final stems    : no suffix in any case
# =============================================================================

_GEORGIAN_VOWELS = frozenset("აეიოუ")


def _stem_final_class(word: str) -> Optional[str]:
    stripped = word.strip(".,!?…;:\"'“”„")
    if not stripped:
        return None
    lw = stripped.lower()
    core = lw
    for sfx in sorted(_SUFFIX_TO_CASE.keys(), key=len, reverse=True):
        if core.endswith(sfx) and len(core) > len(sfx):
            core = core[: -len(sfx)]
            break
    if not core:
        return None
    last = core[-1]
    if last in _GEORGIAN_VOWELS:
        return "vowel_stem"
    return "consonant_stem"


def _detect_present_case_suffix(word: str) -> Tuple[Optional[str], str]:
    lw = word.strip(".,!?…;:\"'“”„").lower()
    for sfx in sorted(_SUFFIX_TO_CASE.keys(), key=len, reverse=True):
        if lw.endswith(sfx) and len(lw) > len(sfx):
            return sfx, _SUFFIX_TO_CASE[sfx]
    return None, "Nominative"


def _check_adjective_declension(
    tokens: list[Any], stanza_document: Any | None
) -> list[AlignmentAnnotation]:
    out: list[AlignmentAnnotation] = []
    for i, tok in enumerate(tokens):
        raw = tok.text
        surface = raw.strip(".,!?…;:\"'“”„")
        if not surface:
            continue

        is_adj = False
        if stanza_document is not None:
            for sent in getattr(stanza_document, "sentences", []) or []:
                for w in sent.words:
                    if int(getattr(w, "start_char", -1) or -1) == tok.start:
                        if getattr(w, "upos", "") == "ADJ":
                            is_adj = True
                        break
                if is_adj:
                    break
        if not is_adj:
            continue

        actual_sfx, actual_case_lbl = _detect_present_case_suffix(surface)
        stem_class = _stem_final_class(surface)
        if stem_class is None:
            continue

        suffix_matrix = ADJECTIVE_DECLENSION.get(stem_class, {})
        lbl_lower = actual_case_lbl.lower()
        expected_suffix = suffix_matrix.get(lbl_lower)
        if expected_suffix is None:
            continue

        expected_suffix_clean = expected_suffix.replace("-", "")
        actual_suffix_clean = actual_sfx or ""

        matches_decl = False
        if expected_suffix_clean == "" and actual_suffix_clean == "":
            matches_decl = True
        elif expected_suffix_clean == "":
            if stem_class == "vowel_stem":
                matches_decl = True
        elif actual_suffix_clean == expected_suffix_clean:
            matches_decl = True
        elif surface.lower().endswith(expected_suffix_clean):
            matches_decl = True

        if not matches_decl and stem_class == "consonant_stem":
            base = surface
            if actual_sfx and base.lower().endswith(actual_sfx.lower()):
                base = base[: -len(actual_sfx)]
            suggestion = base + expected_suffix_clean
            paradigm_label = "consonant-stem (e.g. did- 'big')"
            out.append(
                _ann(
                    start=tok.start,
                    end=tok.end,
                    type_="grammar",
                    message=(
                        f"Adjective '{surface}' in {actual_case_lbl} case. "
                        f"For {paradigm_label} adjectives, the required suffix "
                        f"is '{expected_suffix}' (∅ = no suffix). "
                        f"Found '{actual_sfx or '∅'}'."
                    ),
                    short_message="Adjective declension",
                    replacements=[suggestion]
                    if suggestion and suggestion != surface
                    else [],
                    rule_id="desktop:adjective_declension",
                    severity="warning",
                    source="desktop-georgian-grammar-rules",
                    word=raw,
                )
            )
    return out


# =============================================================================
# Rule 3: Possessive adjective case-paradigm validator
#    For each detected possessive lemma, verify its surface suffix matches
#    the expected paradigm case when it is immediately adjacent to a head noun
#    whose case suffix we can detect.
# =============================================================================

def _check_possessive_adjective_paradigm(
    tokens: list[Any],
) -> list[AlignmentAnnotation]:
    out: list[AlignmentAnnotation] = []
    for i, tok in enumerate(tokens):
        raw = tok.text
        surface = raw.strip(".,!?…;:\"'“”„")
        lowered = surface.lower()
        lemma = None
        for key_lemma in _POSSESSIVE_LEMMA_TO_PARADIGM.keys():
            kl = key_lemma.lower()
            if lowered.startswith(kl) or lowered == kl:
                lemma = key_lemma
                break
        if lemma is None:
            continue
        paradigm_key = _POSSESSIVE_LEMMA_TO_PARADIGM[lemma]
        paradigm_table = _POSSESSIVE_GEORGIAN.get(lemma, {})

        if i >= len(tokens) - 1:
            continue
        head_tok = tokens[i + 1]
        head_surface = head_tok.text.strip(".,!?…;:\"'“”„")
        head_case = _detect_case_label(head_surface)
        if head_case is None:
            head_case = "Nominative"
        head_case_lower = head_case.lower()
        allowed_forms = paradigm_table.get(head_case_lower, [])
        if not allowed_forms:
            continue

        if lowered in {f.lower() for f in allowed_forms}:
            continue

        suggestions = list(allowed_forms[:3])
        paradigm_label = _POSSESSIVE_PARADIGM_LABELS.get(paradigm_key, paradigm_key)
        out.append(
            _ann(
                start=tok.start,
                end=tok.end,
                type_="grammar",
                message=(
                    f"Possessive '{surface}' ({paradigm_label}) should agree in "
                    f"case with its head noun '{head_surface}' ({head_case}). "
                    f"Expected one of: {', '.join(allowed_forms)}."
                ),
                short_message="Possessive agreement",
                replacements=suggestions,
                rule_id="desktop:possessive_adjective_case",
                severity="warning",
                word=raw,
            )
        )
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
    annotations.extend(_check_desktop_postposition_governance(tokens))
    annotations.extend(_check_adjective_declension(tokens, stanza_document))
    annotations.extend(_check_possessive_adjective_paradigm(tokens))
    return annotations


def agreement_engine_meta() -> dict[str, int]:
    return {
        "desktop_postposition_count": len(POSTPOSITIONS),
        "desktop_adjective_paradigms": len(ADJECTIVE_DECLENSION),
        "desktop_possessive_paradigms": len(POSSESSIVE_ADJECTIVES),
        "desktop_georgian_pp_surfaces": len(_LATIN_PP_TO_GEORGIAN),
        "desktop_possessive_lemmas": len(_POSSESSIVE_GEORGIAN),
    }
