"""Georgian Verbal System Rules — loaded from rules1.json.

This module provides access to the Georgian verbal system specification including:
- Screeve series (Series I, II, III) with their subseries
- Verb classes (1-4, stative, irregular) with syntactic patterns
- Morphological and semantic descriptions

This data is primarily reference/documentation but can be used for:
- Providing educational context in grammar annotations
- Validating verb classifications against known patterns
- Meta-information about the Georgian grammar system
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


_RULES1_PATH = Path(__file__).resolve().parent / "rules1.json"


@dataclass(frozen=True)
class ScreeveInfo:
    """Information about a Georgian screeve (tense/mood form)."""
    name: str
    meaning: str
    english_equivalents: List[str]


@dataclass(frozen=True)
class VerbClassInfo:
    """Information about a Georgian verb class."""
    type: str
    syntax: Dict[str, Any]
    semantics: Optional[str]
    sub_types: Optional[List[str]]
    examples: List[str]


class VerbalSystemRules:
    """Loader and accessor for Georgian verbal system rules from rules1.json."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return

        try:
            with open(_RULES1_PATH, "r", encoding="utf-8") as f:
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
        return self._data.get("version", "unknown")

    @property
    def grammar_system(self) -> str:
        """Return the grammar system name."""
        self._load()
        return self._data.get("grammar_system", "unknown")

    def get_screeve_series(self, series: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific screeve series (e.g., 'series_1')."""
        self._load()
        screeves = self._data.get("screeves", {})
        return screeves.get(series)

    def get_all_screeve_series(self) -> Dict[str, Dict[str, Any]]:
        """Get all screeve series information."""
        self._load()
        return self._data.get("screeves", {})

    def get_verb_class(self, class_name: str) -> Optional[VerbClassInfo]:
        """Get information about a specific verb class (e.g., 'class_1')."""
        self._load()
        classes = self._data.get("verb_classes", {})
        class_data = classes.get(class_name)

        if class_data is None:
            return None

        return VerbClassInfo(
            type=class_data.get("type", ""),
            syntax=class_data.get("syntax", {}),
            semantics=class_data.get("semantics"),
            sub_types=class_data.get("sub_types"),
            examples=class_data.get("examples", []),
        )

    def get_all_verb_classes(self) -> Dict[str, VerbClassInfo]:
        """Get all verb class information."""
        self._load()
        classes = self._data.get("verb_classes", {})
        result: Dict[str, VerbClassInfo] = {}

        for class_name, class_data in classes.items():
            result[class_name] = VerbClassInfo(
                type=class_data.get("type", ""),
                syntax=class_data.get("syntax", {}),
                semantics=class_data.get("semantics"),
                sub_types=class_data.get("sub_types"),
                examples=class_data.get("examples", []),
            )

        return result

    def get_screeve_by_path(self, series: str, subseries: str, screeve: str) -> Optional[ScreeveInfo]:
        """Get a specific screeve by its path (e.g., series_1 -> present_subseries -> present_indicative)."""
        self._load()
        screeves = self._data.get("screeves", {})
        series_data = screeves.get(series)

        if series_data is None:
            return None

        # Handle different structures between series
        if "subseries" in series_data:
            subseries_data = series_data.get("subseries", {}).get(subseries)
            if subseries_data is None:
                return None
            screeve_data = subseries_data.get(screeve)
        elif "screeves" in series_data:
            screeve_data = series_data.get("screeves", {}).get(screeve)
        else:
            return None

        if screeve_data is None:
            return None

        return ScreeveInfo(
            name=screeve,
            meaning=screeve_data.get("meaning", ""),
            english_equivalents=screeve_data.get("english_equivalent", []),
        )

    def get_verb_class_examples(self, class_name: str) -> List[str]:
        """Get example verbs for a specific class."""
        class_info = self.get_verb_class(class_name)
        return class_info.examples if class_info else []

    def is_loaded(self) -> bool:
        """Check if the rules file was successfully loaded."""
        self._load()
        return bool(self._data)


# Global instance
_verbal_system_rules: Optional[VerbalSystemRules] = None


def get_verbal_system_rules() -> VerbalSystemRules:
    """Get the global VerbalSystemRules instance."""
    global _verbal_system_rules
    if _verbal_system_rules is None:
        _verbal_system_rules = VerbalSystemRules()
    return _verbal_system_rules


def verbal_system_meta() -> Dict[str, Any]:
    """Return metadata about the verbal system rules for engine status."""
    rules = get_verbal_system_rules()
    return {
        "verbal_system_version": rules.version,
        "verbal_system_name": rules.grammar_system,
        "verbal_system_loaded": rules.is_loaded(),
        "screeve_series_count": len(rules.get_all_screeve_series()),
        "verb_class_count": len(rules.get_all_verb_classes()),
    }
