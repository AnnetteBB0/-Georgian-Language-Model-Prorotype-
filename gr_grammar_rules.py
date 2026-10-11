"""Georgian Grammar Rules from gr.json — comprehensive structural grammar rules.

This module provides access to the Georgian grammar specification from gr.json including:
- Verb morphology (preverbs, person markers, version markers, thematic suffixes)
- Negation rules (base particles and derived particles)
- Syntax and word order rules (interrogatives, question types)

This data is primarily reference/documentation but can be used for:
- Providing educational context in grammar annotations
- Validating verb morphology patterns
- Checking negation particle usage
- Validating interrogative word order
- Meta-information about the Georgian grammar system
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


_GR_JSON_PATH = Path(__file__).resolve().parent / "gr.json"


@dataclass(frozen=True)
class PreverbInfo:
    """Information about a Georgian preverb."""
    georgian: str
    romanization: str
    meaning: str


@dataclass(frozen=True)
class PersonMarkerInfo:
    """Information about a person marker."""
    singular: str
    plural: str
    archaic_exceptions: Optional[List[str]] = None


@dataclass(frozen=True)
class InterrogativeInfo:
    """Information about an interrogative pronoun."""
    georgian: str
    romanization: str
    english: str


class GRGrammarRules:
    """Loader and accessor for Georgian grammar rules from gr.json."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return

        try:
            with open(_GR_JSON_PATH, "r", encoding="utf-8") as f:
                self._data = json.load(f)
            self._loaded = True
        except FileNotFoundError:
            self._data = {}
            self._loaded = True
        except json.JSONDecodeError:
            self._data = {}
            self._loaded = True

    @property
    def version(self) -> str:
        """Return the version string from the rules file."""
        self._load()
        return self._data.get("metadata", {}).get("version", "unknown")

    @property
    def language(self) -> str:
        """Return the language name."""
        self._load()
        return self._data.get("metadata", {}).get("language", "unknown")

    @property
    def description(self) -> str:
        """Return the description."""
        self._load()
        return self._data.get("metadata", {}).get("description", "")

    # Verb morphology methods
    def get_preverbs(self) -> List[PreverbInfo]:
        """Get all preverb information."""
        self._load()
        preverbs_data = self._data.get("verb_morphology", {}).get("preverbs", [])
        return [
            PreverbInfo(
                georgian=p.get("georgian", ""),
                romanization=p.get("romanization", ""),
                meaning=p.get("meaning", ""),
            )
            for p in preverbs_data
        ]

    def get_preverb_georgian_forms(self) -> List[str]:
        """Get list of Georgian preverb forms for matching."""
        self._load()
        preverbs = self.get_preverbs()
        forms = []
        for pv in preverbs:
            # Handle forms like "მი-" or "ა- / ამო-"
            variants = pv.georgian.split("/")
            for variant in variants:
                forms.append(variant.strip())
        return forms

    def get_subject_person_marker(self, person: str) -> Optional[PersonMarkerInfo]:
        """Get subject person marker info (S1, S2, S3)."""
        self._load()
        markers = self._data.get("verb_morphology", {}).get("person_markers", {}).get("subject_markers", {})
        person_data = markers.get(person)
        if person_data is None:
            return None
        return PersonMarkerInfo(
            singular=person_data.get("singular", ""),
            plural=person_data.get("plural", ""),
            archaic_exceptions=person_data.get("archaic_exceptions"),
        )

    def get_object_person_marker(self, person: str) -> Optional[PersonMarkerInfo]:
        """Get object person marker info (O1, O2, O3)."""
        self._load()
        markers = self._data.get("verb_morphology", {}).get("person_markers", {}).get("object_markers", {})
        person_data = markers.get(person)
        if person_data is None:
            return None
        return PersonMarkerInfo(
            singular=person_data.get("singular", ""),
            plural=person_data.get("plural", ""),
        )

    def get_thematic_suffixes(self) -> List[str]:
        """Get list of thematic suffixes."""
        self._load()
        return self._data.get("verb_morphology", {}).get("thematic_suffixes", [])

    def get_imperfective_marker(self, verb_class: str) -> Optional[str]:
        """Get imperfective marker for a verb class."""
        self._load()
        markers = self._data.get("verb_morphology", {}).get("imperfective_markers", {})
        return markers.get(f"{verb_class}_verbs")

    # Negation rules methods
    def get_negation_particles(self) -> Dict[str, Dict[str, str]]:
        """Get base negation particles (ar, ver, nu)."""
        self._load()
        return self._data.get("negation_rules", {}).get("base_particles", {})

    def get_derived_negation_particles(self) -> Dict[str, Dict[str, str]]:
        """Get derived negation particles with -ghar suffix."""
        self._load()
        return self._data.get("negation_rules", {}).get("derived_particles_ghar_suffix", {})

    def get_all_negation_forms(self) -> List[str]:
        """Get all negation particle forms for matching."""
        self._load()
        forms = []
        base = self.get_negation_particles()
        derived = self.get_derived_negation_particles()
        forms.extend(base.keys())
        forms.extend(derived.keys())
        return forms

    # Syntax and word order methods
    def get_interrogatives(self) -> List[InterrogativeInfo]:
        """Get all interrogative pronoun information."""
        self._load()
        interrogatives_data = self._data.get("syntax_and_word_order", {}).get("interrogatives", {}).get("lexicon", [])
        return [
            InterrogativeInfo(
                georgian=i.get("georgian", ""),
                romanization=i.get("romanization", ""),
                english=i.get("english", ""),
            )
            for i in interrogatives_data
        ]

    def get_interrogative_georgian_forms(self) -> List[str]:
        """Get list of Georgian interrogative forms for matching."""
        self._load()
        interrogatives = self.get_interrogatives()
        return [i.georgian for i in interrogatives]

    def get_tag_question_particle(self) -> str:
        """Get the tag question particle (xom)."""
        self._load()
        return self._data.get("syntax_and_word_order", {}).get("question_types", {}).get("tag_questions_xom", {}).get("particle", "")

    def get_polite_question_particle(self) -> str:
        """Get the polite question particle (tu)."""
        self._load()
        return self._data.get("syntax_and_word_order", {}).get("question_types", {}).get("polite_questions_tu", {}).get("particle", "")

    def is_loaded(self) -> bool:
        """Check if the rules file was successfully loaded."""
        self._load()
        return bool(self._data)


# Global instance
_gr_grammar_rules: Optional[GRGrammarRules] = None


def get_gr_grammar_rules() -> GRGrammarRules:
    """Get the global GRGrammarRules instance."""
    global _gr_grammar_rules
    if _gr_grammar_rules is None:
        _gr_grammar_rules = GRGrammarRules()
    return _gr_grammar_rules


def gr_grammar_meta() -> Dict[str, Any]:
    """Return metadata about the gr.json grammar rules for engine status."""
    rules = get_gr_grammar_rules()
    interrogatives = rules.get_interrogatives()
    preverbs = rules.get_preverbs()
    return {
        "gr_grammar_version": rules.version,
        "gr_grammar_language": rules.language,
        "gr_grammar_loaded": rules.is_loaded(),
        "gr_preverb_count": len(preverbs),
        "gr_interrogative_count": len(interrogatives),
        "gr_thematic_suffix_count": len(rules.get_thematic_suffixes()),
        "gr_negation_particle_count": len(rules.get_all_negation_forms()),
    }
