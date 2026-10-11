"""Georgian Verbal System Checker — active grammar rules based on rules1.json.

Implements checking rules derived from the Georgian verbal system specification:
- Verb lexicon with class assignments (1-4, stative, irregular)
- Screeve detection from surface forms
- Case alignment checking based on verb class + screeve series
- Subject/object presence validation

Reference: rules1.json provides the theoretical framework.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from preprocessor import Token
from verbal_system_rules import get_verbal_system_rules


# =============================================================================
# Verb Lexicon: Georgian verbs mapped to their classes
# =============================================================================

_VERB_LEXICON: Dict[str, str] = {
    # Class 1: Transitive Verbs (require subject + direct object)
    "წერს": "class_1",
    "წერ": "class_1",
    "კითხულობს": "class_1",
    "კითხულ": "class_1",
    "ხედავს": "class_1",
    "ხედ": "class_1",
    "ყურობს": "class_1",
    "ყურ": "class_1",
    "აკეთებს": "class_1",
    "აკეთ": "class_1",
    "აქვს": "class_1",
    "ჭამს": "class_1",
    "ჭამ": "class_1",
    "სვამს": "class_1",
    "სვა": "class_1",
    "აღარტყებს": "class_1",
    "აღარტყე": "class_1",
    "ანადგებს": "class_1",
    "ანადგე": "class_1",
    "გადასცემს": "class_1",
    "გადასცე": "class_1",
    "იღებს": "class_1",
    "იღებ": "class_1",
    "იყიდებს": "class_1",
    "იყიდ": "class_1",
    "ყიდულობს": "class_1",
    "ყიდულ": "class_1",
    "აშენებს": "class_1",
    "აშენ": "class_1",
    "ახსნის": "class_1",
    "ახსნ": "class_1",
    "მოკლავს": "class_1",
    "მოკლავ": "class_1",
    "გაავრცელებს": "class_1",
    "გაავრცელ": "class_1",

    # Class 2: Intransitive Verbs (subject only, patientive semantics)
    "იცოცხლობს": "class_2",
    "ცოცხლობ": "class_2",
    "სძილავს": "class_2",
    "სძილავ": "class_2",
    "ნინებს": "class_2",
    "ნინებ": "class_2",
    "მოკვდება": "class_2",
    "მოკვდებ": "class_2",
    "გარდაიცვლება": "class_2",
    "გარდაიცვლ": "class_2",
    "შემოდის": "class_2",
    "შემოდი": "class_2",
    "მოდის": "class_2",
    "მოდ": "class_2",
    "გადადის": "class_2",
    "გადად": "class_2",
    "შემოვიდა": "class_2",
    "მოვიდა": "class_2",
    "აღიზამდა": "class_2",
    "გახდა": "class_2",
    "დახდა": "class_2",
    "გარდაიქმნა": "class_2",
    "მოხდა": "class_2",
    "ხდება": "class_2",

    # Class 3: Medial Verbs (agentive, often motion/weather)
    "ცურავს": "class_3",
    "ცურავ": "class_3",
    "მოძრაობს": "class_3",
    "მოძრაობ": "class_3",
    "მოდის": "class_3",  # can be class 2 or 3 depending on context
    "მოდ": "class_3",
    "მიდის": "class_3",
    "მიდ": "class_3",
    "ვარდება": "class_3",
    "თოვს": "class_3",
    "თოვ": "class_3",
    "თოვდება": "class_3",
    "ყინულობს": "class_3",
    "ყინულობ": "class_3",
    "მღერობს": "class_3",
    "მღერობ": "class_3",
    "ტირის": "class_3",
    "ტირ": "class_3",
    "იცინებს": "class_3",
    "იცინ": "class_3",
    "სწავლობს": "class_3",
    "სწავლობ": "class_3",
    "ისწავლებს": "class_3",
    "ისწავლ": "class_3",
    "ვარჯიშობს": "class_3",
    "ვარჯიშობ": "class_3",

    # Class 4: Indirect Verbs (inversion, dative subject)
    "უნდა": "class_4",
    "უნდ": "class_4",
    "შეუძლია": "class_4",
    "შეუძლ": "class_4",
    "მოუწოდებს": "class_4",
    "მოუწოდებ": "class_4",
    "ეძინება": "class_4",
    "ეძინ": "class_4",
    "სძინებს": "class_4",
    "სძინ": "class_4",
    "მოსწონს": "class_4",
    "მოსწონ": "class_4",
    "ეზიზებს": "class_4",
    "ეზიზ": "class_4",
    "აკლდება": "class_4",
    "აკლდ": "class_4",
    "მოახლობს": "class_4",
    "მოახლობ": "class_4",
    "მოჯერდება": "class_4",
    "მოჯერდ": "class_4",
    "შეეშინება": "class_4",
    "შეეშინ": "class_4",
    "სიამოვნებს": "class_4",
    "სიამოვნ": "class_4",
    "გაბედულებს": "class_4",
    "გაბედულ": "class_4",
    "შეურაცხდება": "class_4",
    "შეურაცხდ": "class_4",

    # Stative Verbs (pseudo-class, resemble class 4)
    "კიდება": "stative",
    "კიდ": "stative",
    "დგას": "stative",
    "დგა": "stative",
    "დგამს": "stative",
    "დგამ": "stative",
    "მდევს": "stative",
    "მდევ": "stative",
    "მდება": "stative",
    "მდე": "stative",

    # Irregular Verbs (mostly class 2 intransitive, different stems)
    "არის": "irregular",
    "იყო": "irregular",
    "იქნება": "irregular",
    "მოდის": "irregular",
    "მოდ": "irregular",
    "მოვიდა": "irregular",
    "ამბობს": "irregular",
    "ამბობ": "irregular",
    "თქვა": "irregular",
    "უპასუხა": "irregular",
    "მისცა": "irregular",
    "აღმოაჩინა": "irregular",
}


# =============================================================================
# Screeve Detection: Suffix patterns for Series I, II, III
# =============================================================================

# Series I: Present/Future/Imperfect/Conditional
_SERIES_I_SUFFIXES = frozenset([
    "ს",  # 3sg present: წერს
    "ბ",  # 1sg present: წერბ
    "ი",  # 2sg present: წერი
    "თ",  # 1pl/2pl present: წერთ
    "ენ",  # 3pl present: წერენ
    "ოდი",  # 1sg imperfect: წეროდი
    "ოდ",  # 2sg imperfect: წეროდ
    "ოდა",  # 3sg imperfect: წეროდა
    "ოდნენ",  # 3pl imperfect: წეროდნენ
    "და",  # aorist-like but present context: დახდა
])

# Series II: Aorist/Optative
_SERIES_II_SUFFIXES = frozenset([
    "ა",  # 3sg aorist: დაწერა
    "ეს",  # 3sg aorist: დაწერეს
    "ე",  # 1sg/2sg aorist: დაწერე
    "ეთ",  # 1pl aorist: დაწერეთ
    "ენ",  # 3pl aorist: დაწერენ
    "ო",  # optative: დაწერო
    "ოს",  # optative: დაწეროს
    "ოთ",  # optative: დაწეროთ
    "ონ",  # optative: დაწერონ
])

# Series III: Perfect/Pluperfect/Subjunctive
_SERIES_III_SUFFIXES = frozenset([
    "ავს",  # 3sg present perfect: დაწერავს
    "ავ",  # 1sg/2sg present perfect: დაწერავ
    "ათ",  # 1pl present perfect: დაწერათ
    "ან",  # 3pl present perfect: დაწერან
    "ევს",  # 3sg pluperfect: დაწერევს
    "ევ",  # 1sg/2sg pluperfect: დაწერევ
    "ეთ",  # 1pl pluperfect: დაწერეთ
    "ენ",  # 3pl pluperfect: დაწერენ
])


def detect_screeve_series(verb: str) -> Optional[str]:
    """Detect screeve series from verb suffix patterns."""
    verb_lower = verb.lower()

    # Check for Series III suffixes (longest first)
    for suffix in sorted(_SERIES_III_SUFFIXES, key=len, reverse=True):
        if verb_lower.endswith(suffix):
            return "series_3"

    # Check for Series II suffixes
    for suffix in sorted(_SERIES_II_SUFFIXES, key=len, reverse=True):
        if verb_lower.endswith(suffix):
            return "series_2"

    # Check for Series I suffixes
    for suffix in sorted(_SERIES_I_SUFFIXES, key=len, reverse=True):
        if verb_lower.endswith(suffix):
            return "series_1"

    # Default to Series I for bare stems
    return "series_1"


# =============================================================================
# Case Suffix Detection
# =============================================================================

_CASE_SUFFIXES: Dict[str, str] = {
    "მა": "ergative",
    "მ": "ergative",
    "ნ": "ergative",  # For pronouns like მან, ჩვენმან
    "ი": "nominative",
    "ს": "dative",
    "თან": "dative",
    "ის": "genitive",
    "ით": "instrumental",
    "ებით": "instrumental",
    "ოვით": "instrumental",
    "ში": "adverbial",
    "ზე": "adverbial",
    "დან": "adverbial",
    "იდან": "adverbial",
    "ო": "vocative",
    "თა": "vocative",
    "თი": "vocative",
}

# Personal pronouns with their surface forms (base forms are nominative)
# In Georgian, pronouns change case with suffixes, so we detect from suffix
_PERSONAL_PRONOUN_BASES: Set[str] = {
    "მე",  # 1sg
    "ჩვენ",  # 1pl
    "შენ",  # 2sg
    "თქვენ",  # 2pl
    "ის",  # 3sg
    "ისინი",  # 3pl
}


def detect_case_from_suffix(word: str) -> Optional[str]:
    """Detect grammatical case from word suffix or personal pronoun."""
    word_lower = word.lower().strip(".,!?…;:\"'\"„")

    # For pronouns, strip potential suffixes and check base
    for base in _PERSONAL_PRONOUN_BASES:
        if word_lower == base:
            return "nominative"
        if word_lower.startswith(base) and len(word_lower) > len(base):
            suffix = word_lower[len(base):]
            if suffix in _CASE_SUFFIXES:
                return _CASE_SUFFIXES[suffix]

    # Check suffix-based cases for other words
    for suffix in sorted(_CASE_SUFFIXES.keys(), key=len, reverse=True):
        if word_lower.endswith(suffix):
            return _CASE_SUFFIXES[suffix]

    return None


# =============================================================================
# Expected Case Alignment Rules
# =============================================================================

def get_expected_subject_case(verb_class: str, screeve_series: str) -> Optional[str]:
    """Return expected subject case based on verb class and screeve series."""
    if verb_class == "class_1":
        # Transitive: Series I → Nominative, Series II → Ergative, Series III → Dative
        if screeve_series == "series_1":
            return "nominative"
        elif screeve_series == "series_2":
            return "ergative"
        elif screeve_series == "series_3":
            return "dative"

    elif verb_class == "class_2":
        # Intransitive patientive: Always Nominative
        return "nominative"

    elif verb_class == "class_3":
        # Medial agentive: Series I → Nominative, Series II → Ergative, Series III → Dative
        if screeve_series == "series_1":
            return "nominative"
        elif screeve_series == "series_2":
            return "ergative"
        elif screeve_series == "series_3":
            return "dative"

    elif verb_class == "class_4":
        # Indirect: Always Dative (inversion)
        return "dative"

    elif verb_class == "stative":
        # Stative: Resembles class 4, typically Nominative or Dative
        return "nominative"

    elif verb_class == "irregular":
        # Irregular: Context-dependent, default to Nominative
        return "nominative"

    return None


def get_expected_object_case(verb_class: str, screeve_series: str) -> Optional[str]:
    """Return expected direct object case based on verb class and screeve series."""
    if verb_class == "class_1":
        # Transitive: Series I → Dative, Series II → Nominative, Series III → Nominative
        if screeve_series == "series_1":
            return "dative"
        elif screeve_series == "series_2":
            return "nominative"
        elif screeve_series == "series_3":
            return "nominative"

    elif verb_class == "class_4":
        # Indirect: Object is Nominative
        return "nominative"

    # Other classes don't require direct objects
    return None


# =============================================================================
# Annotation Data Class
# =============================================================================

@dataclass(frozen=True)
class VerbalSystemAnnotation:
    """Grammar annotation from verbal system checking."""
    start: int
    end: int
    type: str
    message: str
    short_message: str
    replacements: List[str]
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
    replacements: List[str],
    rule_id: str,
    severity: str,
    word: str,
) -> VerbalSystemAnnotation:
    return VerbalSystemAnnotation(
        start=start,
        end=end,
        type=type_,
        message=message,
        short_message=short_message,
        replacements=replacements,
        rule_id=rule_id,
        severity=severity,
        source="verbal_system",
        word=word,
    )


# =============================================================================
# Checking Functions
# =============================================================================

def check_verb_case_alignment(
    tokens: List[Token], stanza_document: Any | None = None
) -> List[VerbalSystemAnnotation]:
    """Check verb case alignment based on verb class and screeve series."""
    annotations: List[VerbalSystemAnnotation] = []

    for i, token in enumerate(tokens):
        verb_text = token.text.strip(".,!?…;:\"'\"„")
        verb_lower = verb_text.lower()

        # Look up verb class
        verb_class = _VERB_LEXICON.get(verb_lower)
        if not verb_class:
            continue

        # Detect screeve series
        screeve_series = detect_screeve_series(verb_text)

        # Get expected cases
        expected_subject = get_expected_subject_case(verb_class, screeve_series)
        expected_object = get_expected_object_case(verb_class, screeve_series)

        # Look for subject (simplified: check previous tokens)
        if expected_subject and i > 0:
            subject_token = tokens[i - 1]
            subject_text = subject_token.text.strip(".,!?…;:\"'\"„")
            subject_case = detect_case_from_suffix(subject_text)

            if subject_case and subject_case != expected_subject:
                # Case mismatch detected
                msg = (
                    f"Verb '{verb_text}' ({verb_class}, {screeve_series}) expects "
                    f"subject in {expected_subject} case, but found {subject_case}."
                )
                annotations.append(
                    _ann(
                        start=subject_token.start,
                        end=subject_token.end,
                        type_="grammar",
                        message=msg,
                        short_message="Subject case",
                        replacements=[],
                        rule_id="verbal:subject_case_alignment",
                        severity="warning",
                        word=subject_text,
                    )
                )

        # For transitive verbs, check for object presence
        if verb_class == "class_1" and expected_object:
            # Simple check: look for object in next 3 tokens
            found_object = False
            for j in range(i + 1, min(i + 4, len(tokens))):
                obj_token = tokens[j]
                obj_text = obj_token.text.strip(".,!?…;:\"'\"„")
                obj_case = detect_case_from_suffix(obj_text)
                if obj_case == expected_object:
                    found_object = True
                    break

            if not found_object:
                msg = (
                    f"Transitive verb '{verb_text}' ({screeve_series}) typically "
                    f"requires a direct object in {expected_object} case."
                )
                annotations.append(
                    _ann(
                        start=token.start,
                        end=token.end,
                        type_="style",
                        message=msg,
                        short_message="Missing object",
                        replacements=[],
                        rule_id="verbal:missing_direct_object",
                        severity="info",
                        word=verb_text,
                    )
                )

    return annotations


def check_indirect_verb_inversion(
    tokens: List[Token], stanza_document: Any | None = None
) -> List[VerbalSystemAnnotation]:
    """Check that class 4 (indirect) verbs have dative subjects."""
    annotations: List[VerbalSystemAnnotation] = []

    for i, token in enumerate(tokens):
        verb_text = token.text.strip(".,!?…;:\"'\"„")
        verb_lower = verb_text.lower()

        verb_class = _VERB_LEXICON.get(verb_lower)
        if verb_class != "class_4":
            continue

        # Check for subject with dative case
        if i > 0:
            subject_token = tokens[i - 1]
            subject_text = subject_token.text.strip(".,!?…;:\"'\"„")
            subject_case = detect_case_from_suffix(subject_text)

            if subject_case and subject_case != "dative":
                msg = (
                    f"Indirect verb '{verb_text}' requires dative subject "
                    f"(inversion), but found {subject_case} case."
                )
                annotations.append(
                    _ann(
                        start=subject_token.start,
                        end=subject_token.end,
                        type_="grammar",
                        message=msg,
                        short_message="Inversion subject",
                        replacements=[],
                        rule_id="verbal:indirect_verb_inversion",
                        severity="warning",
                        word=subject_text,
                    )
                )

    return annotations


def run_verbal_system_checks(
    text: str, tokens: List[Token], stanza_document: Any | None = None
) -> List[VerbalSystemAnnotation]:
    """Run all verbal system grammar checks."""
    annotations: List[VerbalSystemAnnotation] = []

    annotations.extend(check_verb_case_alignment(tokens, stanza_document))
    annotations.extend(check_indirect_verb_inversion(tokens, stanza_document))

    return annotations


def verbal_system_engine_meta() -> Dict[str, int]:
    """Return metadata about the verbal system checker."""
    return {
        "verbal_system_verb_lexicon_size": len(_VERB_LEXICON),
        "verbal_system_screeve_i_suffixes": len(_SERIES_I_SUFFIXES),
        "verbal_system_screeve_ii_suffixes": len(_SERIES_II_SUFFIXES),
        "verbal_system_screeve_iii_suffixes": len(_SERIES_III_SUFFIXES),
    }
