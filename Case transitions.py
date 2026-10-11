# -*- coding: utf-8 -*-
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ScreeveSeries(Enum):
    SERIES_I = "სერია I (Present/Future)"
    SERIES_II = "სერია II (Aorist)"
    SERIES_III = "სერია III (Perfective/Inverted)"


class VerbTransitivity(Enum):
    TRANSITIVE = "Transitive"
    INTRANSITIVE = "Intransitive"


class VerbConjugation(Enum):
    FIRST = 1
    SECOND = 2
    THIRD = 3
    FOURTH = 4


class SemanticRole(Enum):
    AGENT = "Agent"
    PATIENT_EXPERIENCER = "Patient/Experiencer"
    ZERO_ARGUMENT = "Zero-Place"


class GrammaticalCase(Enum):
    NOMINATIVE = "სახელობითი (Nominative)"
    ERGATIVE = "მოთხრობითი (Ergative)"
    DATIVE = "მიცემითი (Dative)"
    GENITIVE = "ნათესაობითი (Genitive)"
    INSTRUMENTAL = "ხელსაწყოთი (Instrumental)"
    ADVERBIAL = "მდებარეობითი (Adverbial)"
    VOCATIVE = "წარდგომითი (Vocative)"


UD_CASE_TO_GEORGIAN: Dict[str, GrammaticalCase] = {
    "Nom": GrammaticalCase.NOMINATIVE,
    "Erg": GrammaticalCase.ERGATIVE,
    "Dat": GrammaticalCase.DATIVE,
    "Gen": GrammaticalCase.GENITIVE,
    "Ins": GrammaticalCase.INSTRUMENTAL,
    "Loc": GrammaticalCase.ADVERBIAL,
    "Voc": GrammaticalCase.VOCATIVE,
}


class VerbLexeme:
    __slots__ = ("lemma", "conjugation", "transitivity", "semantic_role")

    def __init__(
        self,
        lemma: str,
        conjugation: VerbConjugation,
        transitivity: VerbTransitivity,
        semantic_role: SemanticRole = SemanticRole.AGENT,
    ) -> None:
        self.lemma = lemma
        self.conjugation = conjugation
        self.transitivity = transitivity
        self.semantic_role = semantic_role


class ClauseArguments:
    __slots__ = ("subject_case", "direct_object_case", "indirect_object_case")

    def __init__(
        self,
        subject_case: Optional[GrammaticalCase] = None,
        direct_object_case: Optional[GrammaticalCase] = None,
        indirect_object_case: Optional[GrammaticalCase] = None,
    ) -> None:
        self.subject_case = subject_case
        self.direct_object_case = direct_object_case
        self.indirect_object_case = indirect_object_case


class GeorgianAlignmentEngine:
    """
    Georgian morphosyntactic alignment engine based on the three screeve series:
      * Series I  (Present / Future / Imperfect / Conditional) — Nominative syntax.
      * Series II (Aorist / Optative)                          — Split-Ergative / Split-S.
      * Series III (Perfect / Pluperfect / Evidential)         — Inversion (Dative subjects).

    References (abbreviated from traditional Kartvelian grammar):
      - 1st Conjugation : Transitive / Active.
      - 2nd Conjugation : Intransitive / Passive / Inchoative (Patientive subject).
      - 3rd Conjugation : Medial / Intransitive-Active (Agentive subject).
      - 4th Conjugation : Inverted / Indirect / Affective (emotions, possession, …).
    """

    @staticmethod
    def get_expected_cases(
        verb: VerbLexeme, series: ScreeveSeries
    ) -> ClauseArguments:
        if series == ScreeveSeries.SERIES_I:
            if verb.conjugation == VerbConjugation.FOURTH:
                return ClauseArguments(
                    subject_case=GrammaticalCase.DATIVE,
                    direct_object_case=GrammaticalCase.NOMINATIVE,
                )
            if verb.transitivity == VerbTransitivity.TRANSITIVE:
                return ClauseArguments(
                    subject_case=GrammaticalCase.NOMINATIVE,
                    direct_object_case=GrammaticalCase.DATIVE,
                )
            return ClauseArguments(
                subject_case=GrammaticalCase.NOMINATIVE, direct_object_case=None
            )

        if series == ScreeveSeries.SERIES_II:
            if verb.conjugation == VerbConjugation.FOURTH:
                return ClauseArguments(
                    subject_case=GrammaticalCase.DATIVE,
                    direct_object_case=GrammaticalCase.NOMINATIVE,
                )
            if verb.transitivity == VerbTransitivity.TRANSITIVE:
                return ClauseArguments(
                    subject_case=GrammaticalCase.ERGATIVE,
                    direct_object_case=GrammaticalCase.NOMINATIVE,
                )
            if verb.semantic_role == SemanticRole.ZERO_ARGUMENT:
                return ClauseArguments(None, None, None)

            if (
                verb.conjugation == VerbConjugation.SECOND
                or verb.semantic_role == SemanticRole.PATIENT_EXPERIENCER
            ):
                return ClauseArguments(
                    subject_case=GrammaticalCase.NOMINATIVE, direct_object_case=None
                )
            if (
                verb.conjugation == VerbConjugation.THIRD
                or verb.semantic_role == SemanticRole.AGENT
            ):
                return ClauseArguments(
                    subject_case=GrammaticalCase.ERGATIVE, direct_object_case=None
                )

        if series == ScreeveSeries.SERIES_III:
            if verb.conjugation == VerbConjugation.FIRST:
                return ClauseArguments(
                    subject_case=GrammaticalCase.DATIVE,
                    direct_object_case=GrammaticalCase.NOMINATIVE,
                )
            if verb.conjugation == VerbConjugation.THIRD:
                return ClauseArguments(
                    subject_case=GrammaticalCase.DATIVE, direct_object_case=None
                )
            if verb.conjugation == VerbConjugation.SECOND:
                return ClauseArguments(
                    subject_case=GrammaticalCase.NOMINATIVE, direct_object_case=None
                )
            if verb.conjugation == VerbConjugation.FOURTH:
                return ClauseArguments(
                    subject_case=GrammaticalCase.DATIVE,
                    direct_object_case=GrammaticalCase.NOMINATIVE,
                )

        return ClauseArguments()

    @classmethod
    def validate_alignment(
        cls,
        verb: VerbLexeme,
        series: ScreeveSeries,
        actual_subject_case: Optional[GrammaticalCase],
        actual_direct_object_case: Optional[GrammaticalCase] = None,
    ) -> Tuple[bool, List[str]]:
        expected = cls.get_expected_cases(verb, series)
        errors: List[str] = []
        is_valid = True

        if expected.subject_case != actual_subject_case:
            is_valid = False
            errors.append(
                f"Subject: {expected.subject_case.value if expected.subject_case else 'none'} "
                f"required, got {actual_subject_case.value if actual_subject_case else 'none'}."
            )

        if expected.direct_object_case != actual_direct_object_case:
            is_valid = False
            errors.append(
                f"Direct object: {expected.direct_object_case.value if expected.direct_object_case else 'none'} "
                f"required, got {actual_direct_object_case.value if actual_direct_object_case else 'none'}."
            )

        return is_valid, errors
