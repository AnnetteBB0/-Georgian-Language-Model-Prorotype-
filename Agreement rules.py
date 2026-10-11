# -*- coding: utf-8 -*-
"""Grammar 2 — Georgian morphosyntactic agreement &amp; usage rules.

Authoritative source for:
  * Postposition case-governance rules (თან, ში, ზე, დან, …)
  * Confusable / near-homophone word pairs
  * Demonstrative (ეს/ის/იგი) governance patterns
  * Proper noun lexicon for capitalisation checks
  * Subject–verb person/number agreement matrix
  * Adjective–noun number agreement
  * Double-negative collocation restrictions

This module is imported dynamically by ``grammar 2/agreement_checker.py`` and
re-exported into ``backend/grammar.py`` through the same plugin-loading path
used by ``Rules/Case transitions.py``.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


# =============================================================================
# Enumerations (mirror shape of Case transitions.py so plugin wrappers fit)
# =============================================================================


class Number(Enum):
    SINGULAR = "Singular (მხოლოვნი)"
    PLURAL = "Plural (მრავლოვნი)"


class Person(Enum):
    FIRST = "1st person (პიროვნება I)"
    SECOND = "2nd person (პიროვნება II)"
    THIRD = "3rd person (პიროვნება III)"


class Postposition(Enum):
    """Georgian postpositions with their governing case."""

    TAN = ("თან", "მიცემითი (Dative)")
    SHI = ("ში", "მდებარეობითი (Adverbial / Genitive governing)")
    ZE = ("ზე", "მდებარეობითი (Adverbial / Genitive governing)")
    DAN = ("დან", "მდებარეობითი (Adverbial / Genitive governing)")
    IDAN = ("იდან", "მდებარეობითი (Adverbial / Genitive governing)")
    GAMO = ("გამო", "ნათესაობითი (Genitive)")
    GAR = ("გარეთ", "ნათესაობითი (Genitive)")
    SHUA = ("შუაში", "ნათესაობითი (Genitive)")
    SEDGI = ("სედგი", "მოთხრობითი (Ergative)")
    MIJER = ("მიხედვით", "ნათესაობითი (Genitive)")
    GANACHART = ("განახორციელებს", None)
    TVIS = ("თვის", "მიცემითი (Dative)")
    NAPOV = ("ნახევრად", None)
    DROIS = ("დროს", "მცემითი (Dative)")
    PIROBA = ("პირობაში", "მდებარეობითი (Adverbial)")

    def __init__(self, surface: str, required_case_label: Optional[str]):
        self.surface = surface
        self.required_case_label = required_case_label


class AgreementRole(Enum):
    SUBJECT = "Subject"
    DIRECT_OBJECT = "Direct object"
    MODIFIER = "Modifier"
    HEAD = "Head"


# =============================================================================
# Postposition governance: surface suffix → required case
# =============================================================================

POSTPOSITION_GOVERNANCE: List[Tuple[str, str, FrozenSet[str]]] = [
    ("თან", "Dative", frozenset({"ს", "თან"})),
    ("თვის", "Dative", frozenset({"ს", "თან"})),
    ("შემდეგ", "Genitive", frozenset({"ის"})),
    ("გამო", "Genitive", frozenset({"ის"})),
    ("გან", "Genitive", frozenset({"ის"})),
    ("შუაში", "Genitive", frozenset({"ის"})),
    ("მიხედვით", "Genitive", frozenset({"ის"})),
    ("შუამავლად", "Genitive", frozenset({"ის"})),
    ("გარეთ", "Genitive", frozenset({"ის"})),
    ("სხვა", "Genitive", frozenset({"ის"})),
    ("ზოგიერთი", "Genitive", frozenset({"ის"})),
    ("ში", "Adverbial / Genitive", frozenset({"ში", "ის"})),
    ("ზე", "Adverbial / Genitive", frozenset({"ზე", "ის"})),
    ("დან", "Adverbial / Genitive", frozenset({"დან", "ის"})),
    ("იდან", "Adverbial / Genitive", frozenset({"იდან", "ის"})),
    ("თითო", "Instrumental", frozenset({"ით", "ებით"})),
    ("მერე", "Instrumental", frozenset({"ით", "ებით"})),
    ("გზა", "Instrumental", frozenset({"ით", "ებით"})),
    ("სედგი", "Ergative", frozenset({"მა"})),
    ("მაგრით", "Instrumental", frozenset({"ით", "ებით"})),
    ("ჯერ", "Instrumental", frozenset({"ით", "ებით"})),
]

CASE_SUFFIX_TO_LABEL: Dict[str, str] = {
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


def detect_case_from_suffix(word: str) -> Optional[str]:
    """Best-guess case label from Georgian surface suffix.

    Matches the longest possible suffix first so ``-ებით`` wins over ``-ით``.
    """
    lowered = word.lower()
    for suffix in sorted(CASE_SUFFIX_TO_LABEL.keys(), key=len, reverse=True):
        if lowered.endswith(suffix):
            return CASE_SUFFIX_TO_LABEL[suffix]
    return None


# =============================================================================
# Confusable near-homophone pairs (spelling-level rule)
# =============================================================================

CONFUSABLE_PAIRS: List[Tuple[str, str, str]] = [
    (
        "მაგრამ",
        "მაგრიმ",
        "მაგრამ = 'however/but'; მაგრიმ = 'I/you will resemble' — usually a typo.",
    ),
    (
        "როგორც",
        "როგორ ც",
        "როგორც = 'as/like'; როგორ ც is not a single token — check spacing.",
    ),
    (
        "ასევე",
        "ასეულ ე ვ რ",
        "ასევე = 'also/too'; avoid splitting into separate tokens.",
    ),
    (
        "ამიტომ",
        "ამ მით ომ",
        "ამიტომ = 'therefore'; one token, not three.",
    ),
    (
        "ამიტომაც",
        "ამიტომ ა ც",
        "ამიტომაც = 'that is why' (emphatic); one token.",
    ),
    (
        "მიუხედავად",
        "მიუხე დავად",
        "მიუხედავად = 'despite'; infinitive-like form, one token.",
    ),
    (
        "შეიძლება",
        "შეიძლ ობა",
        "შეიძლება = 'it is possible'; standard orthography.",
    ),
    (
        "უნდებლობს",
        "უნდე ბლობს",
        "უნდებლობს / უნდა — 'must'; avoid non-standard spacing.",
    ),
    (
        "საკმარისი",
        "საკმარ ისი",
        "საკმარისი = 'enough/sufficient'; do not split.",
    ),
    (
        "განსაკუთრებით",
        "განსაკუთ რებით",
        "განსაკუთრებით = 'especially/particularly'; one adverb token.",
    ),
    (
        "მნიშვნელოვანი",
        "მნიშვნელოვანი — typo variants",
        "Ensure the correct lemma მნიშვნელოვანი ('important') is used.",
    ),
    (
        "გაზრდა",
        "გაზდა",
        "გაზრდა = 'increase/growth'; გაზდა = aorist of გაზრდის — context distinguishes.",
    ),
    (
        "დასრულება",
        "დასრულების",
        "დასრულება (nom) vs დასრულების (gen) — verify case matches governor.",
    ),
    (
        "საუკეთესო",
        "საუკეთესოთი",
        "საუკეთესო = 'best' (nom); საუკეთესოთი = instrumental — watch agreement.",
    ),
    (
        "იყო",
        "იყოს",
        "იყო (past 3sg of 'be') vs იყოს (aorist subjunctive) — verify tense.",
    ),
    (
        "აქვს",
        "ჰქონდა",
        "აქვს = present 'has'; ჰქონდა = past 'had' — tense matching across clauses.",
    ),
    (
        "უნდა",
        "უნდებოდა",
        "უნდა = present/future obligation; უნდა + past verb vs უნდა + present.",
    ),
    (
        "შემიძლია",
        "შემეძლო",
        "შემიძლია (present 'I can') vs შემეძლო (past 'I could').",
    ),
    (
        "წერი",
        "წერილ",
        "წერი = 'letter/line'; წერილი = full 'letter (message)' — avoid truncating.",
    ),
    (
        "წიგნი",
        "წიგნის",
        "წიგნი (nom) vs წიგნის (gen/dat) — check noun phrase governance.",
    ),
]


def build_confusable_map() -> Dict[str, Tuple[str, str]]:
    """Return ``{wrong_surface: (intended_surface, explanation)}``."""
    out: Dict[str, Tuple[str, str]] = {}
    for wrong, intended, explanation in CONFUSABLE_PAIRS:
        out[wrong] = (intended, explanation)
    return out


# =============================================================================
# Proper noun lexicon (geographic, personal, organisations — used for cap-check)
# =============================================================================

PROPER_NOUN_LEXICON: FrozenSet[str] = frozenset(
    [
        "საქართველო",
        "ამერიკა",
        "საშტატო ამერიკა",
        "რუსეთი",
        "თურქეთი",
        "გერმანია",
        "საფრანგეთი",
        "იტალია",
        "ესპანეთი",
        "ბრიტანეთი",
        "იაპონია",
        "ჩინეთი",
        "ინდოეთი",
        "ბრაზილია",
        "ანგლი",
        "კანადა",
        "ავსტრალია",
        "ევროპა",
        "აზია",
        "აფრიკა",
        "თბილისი",
        "ქუთაისი",
        "ბათუმი",
        "რუსთავი",
        "ზუგდიდი",
        "გორი",
        "მცხეთა",
        "ფოთი",
        "ტბილსი",
        "ვაშინგტონი",
        "ნიუ-იორკი",
        "ლონდონი",
        "პარიზი",
        "ბერლინი",
        "მოსკოვი",
        "ანკარა",
        "სტამბოლი",
        "ტოკიო",
        "პეკინი",
        "კახეთი",
        "კარტლი",
        "იმერეთი",
        "გურია",
        "აჭარა",
        "სამეგრელო",
        "სვანეთი",
        "თუშეთი",
        "ჰევსურეთი",
        "რე ჩი",
        "ლეჩხუმი",
        "ყაზბეგი",
        "კავკასია",
        "ქართული",
        "ინგლისური",
        "რუსული",
        "გერმანული",
        "საფრანგული",
        "იტალიური",
        "ესპანური",
        "ჩინური",
        "იაპონური",
        "ქართველი",
        "გერმანელი",
        "საფრანგი",
        "ამერიკელი",
        "ბრიტანელი",
        "რუსი",
        "თურქი",
        "მტკვარი",
        "რიონი",
        "ყაზბეგი",
        "ყრურძამი",
        "ყაურიზი",
        "მგარული",
        "ბაქურიანი",
        "გუდაური",
        "შეობი",
        "შოთა",
        "რუსთაველი",
        "ილია",
        "ჭავჭავაძე",
        "აკაკი",
        "წერეთელი",
        "გალაკტიონ",
        "ტაბიძე",
        "ნიკოლოზ",
        "ბარათაშვილი",
        "ზვიად",
        "ამირანაშვილი",
    ]
)


def is_proper_noun(word: str) -> bool:
    """Case-insensitive proper-noun lookup."""
    return word.strip(".,!?…;:\"'“”„").lower() in PROPER_NOUN_LEXICON


# =============================================================================
# Subject–verb person agreement matrix (Series I, II, III patterns)
# =============================================================================

PERSONAL_PRONOUN_TO_PERSON: Dict[str, Person] = {
    "მე": Person.FIRST,
    "ჩვენ": Person.FIRST,
    "შენ": Person.SECOND,
    "თქვენ": Person.SECOND,
    "ის": Person.THIRD,
    "ისინი": Person.THIRD,
    "მაგ": Person.THIRD,
    "მას": Person.THIRD,
    "მინდ": Person.THIRD,
    "მათ": Person.THIRD,
}

VERB_PERSON_SUFFIX_RULES: List[Tuple[str, Person, Number]] = [
    ("ბ", Person.FIRST, Number.SINGULAR),
    ("ი", Person.SECOND, Number.SINGULAR),
    ("ს", Person.THIRD, Number.SINGULAR),
    ("თ", Person.FIRST, Number.PLURAL),
    ("თ", Person.SECOND, Number.PLURAL),
    ("ენ", Person.THIRD, Number.PLURAL),
    ("ნენ", Person.THIRD, Number.PLURAL),
    ("ე", Person.FIRST, Number.SINGULAR),
    ("ე", Person.SECOND, Number.SINGULAR),
    ("ა", Person.THIRD, Number.SINGULAR),
    ("ეთ", Person.FIRST, Number.PLURAL),
    ("ათ", Person.THIRD, Number.PLURAL),
    ("ოდი", Person.FIRST, Number.SINGULAR),
    ("ოდ", Person.SECOND, Number.SINGULAR),
    ("და", Person.THIRD, Number.SINGULAR),
    ("ოდნენ", Person.THIRD, Number.PLURAL),
]

PLURAL_MARKERS_NOUNS: FrozenSet[str] = frozenset(["ები", "ეფი", "ოები", "აები"])


def detect_noun_number(word: str) -> Optional[Number]:
    lowered = word.lower()
    for marker in sorted(PLURAL_MARKERS_NOUNS, key=len, reverse=True):
        if lowered.endswith(marker):
            return Number.PLURAL
    if lowered.endswith("ი") or lowered.endswith("ა") or lowered.endswith("ო"):
        return Number.SINGULAR
    return None


# =============================================================================
# Demonstrative agreement helpers (ეს / ის / იგი / იმ / ამ)
# =============================================================================

DEMONSTRATIVES_SG: FrozenSet[str] = frozenset(
    ["ეს", "ის", "იგი", "ამ", "იმ", "ამან", "იმან", "ამის", "იმის", "ამას", "იმას"]
)
DEMONSTRATIVES_PL: FrozenSet[str] = frozenset(
    ["ესინი", "ისინი", "იგინი", "ამინი", "იმინი", "ამებს", "იმებს", "ამების", "იმების"]
)


def detect_demonstrative_number(word: str) -> Optional[Number]:
    lw = word.lower()
    if lw in DEMONSTRATIVES_PL:
        return Number.PLURAL
    if lw in DEMONSTRATIVES_SG:
        return Number.SINGULAR
    return None


# =============================================================================
# Double negative collocation list
# =============================================================================

DOUBLE_NEGATIVE_VERBS: FrozenSet[str] = frozenset(
    ["ვერ", "არ", "ვერაფერი", "არაფერი", "არავინ", "არასდროს", "არც", "არცერთი"]
)

DOUBLE_NEGATIVE_PATTERNS: List[Tuple[FrozenSet[str], str]] = [
    (
        frozenset({"არ", "ვერ"}),
        "არ + ვერ adjacent is emphatic but double; prefer single neg carrier.",
    ),
    (
        frozenset({"არ", "არაფერი"}),
        "არ + არაფერი: 'არაფერი' already carries neg; drop 'არ'.",
    ),
    (
        frozenset({"არ", "არავინ"}),
        "არ + არავინ: 'არავინ' already carries neg; drop 'არ'.",
    ),
    (
        frozenset({"ვერ", "ვერაფერი"}),
        "ვერ + ვერაფერი: double negative; choose one neg carrier.",
    ),
]


# =============================================================================
# Public API — mirrors GeorgianAlignmentEngine shape for plugin wrapper
# =============================================================================


class GeorgianAgreementEngine:
    """Rule engine for Grammar 2: postposition, agreement &amp; usage rules."""

    @staticmethod
    def postposition_expected_case_suffixes(postposition: str) -> FrozenSet[str]:
        """Return the set of acceptable host suffixes for a postposition."""
        for surf, _label, suffixes in POSTPOSITION_GOVERNANCE:
            if postposition.lower() == surf.lower():
                return suffixes
        return frozenset()

    @staticmethod
    def postposition_case_label(postposition: str) -> Optional[str]:
        for surf, label, _suffixes in POSTPOSITION_GOVERNANCE:
            if postposition.lower() == surf.lower():
                return label
        return None

    @staticmethod
    def confusable_suggestion(word: str) -> Optional[Tuple[str, str]]:
        return build_confusable_map().get(word.strip().lower())

    @staticmethod
    def demonstrative_matches(
        demonstrative: str, head_noun: str
    ) -> Tuple[bool, Optional[Number], Optional[Number]]:
        dem_num = detect_demonstrative_number(demonstrative)
        noun_num = detect_noun_number(head_noun)
        if dem_num is None or noun_num is None:
            return True, dem_num, noun_num
        return dem_num == noun_num, dem_num, noun_num


__all__ = [
    "AgreementRole",
    "CASE_SUFFIX_TO_LABEL",
    "CONFUSABLE_PAIRS",
    "CASE_SUFFIX_TO_LABEL",
    "DEMONSTRATIVES_PL",
    "DEMONSTRATIVES_SG",
    "DOUBLE_NEGATIVE_PATTERNS",
    "DOUBLE_NEGATIVE_VERBS",
    "GeorgianAgreementEngine",
    "Number",
    "PERSONAL_PRONOUN_TO_PERSON",
    "PLURAL_MARKERS_NOUNS",
    "POSTPOSITION_GOVERNANCE",
    "Person",
    "Postposition",
    "PROPER_NOUN_LEXICON",
    "VERB_PERSON_SUFFIX_RULES",
    "build_confusable_map",
    "detect_case_from_suffix",
    "detect_demonstrative_number",
    "detect_noun_number",
    "is_proper_noun",
]
