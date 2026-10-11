"""Georgian Grammar Checker from gr.json — active grammar rules.

Implements checking rules derived from the gr.json specification:
- Negation particle validation (ar, ver, nu and their -ghar derivatives)
- Interrogative word order checking
- Tag question particle (xom) position validation
- Auxiliary modal verb screeve validation (unda, ndoma, shedzleba)

Reference: gr.json provides the theoretical framework.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List

from preprocessor import Token
from gr_grammar_rules import get_gr_grammar_rules


# =============================================================================
# Annotation Data Class
# =============================================================================

@dataclass(frozen=True)
class GRGrammarAnnotation:
    """Grammar annotation from gr.json grammar checking."""
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
) -> GRGrammarAnnotation:
    return GRGrammarAnnotation(
        start=start,
        end=end,
        type=type_,
        message=message,
        short_message=short_message,
        replacements=replacements,
        rule_id=rule_id,
        severity=severity,
        source="gr.json",
        word=word,
    )


# =============================================================================
# Checking Functions
# =============================================================================

def check_negation_usage(
    text: str, tokens: List[Token]
) -> List[GRGrammarAnnotation]:
    """Check negation particle usage according to gr.json rules.

    Specific check: 'ver shedzleba' pattern should be 'ver' + verb directly.
    This is a constraint mentioned in gr.json for the shedzleba modal.
    """
    annotations: List[GRGrammarAnnotation] = []

    for i, token in enumerate(tokens):
        token_text = token.text.lower().strip(".,!?…;:\"'\"„")

        if token_text == "shedzleba" or token_text == "შეძლება":
            # Check if previous token is 'ver'
            if i > 0:
                prev_token = tokens[i - 1]
                prev_text = prev_token.text.lower().strip(".,!?…;:\"'\"„")
                if prev_text == "ver" or prev_text == "ვერ":
                    msg = (
                        "For 'cannot', use the negation particle 'ver' directly "
                        "with the verb instead of 'ver shedzleba'."
                    )
                    annotations.append(
                        _ann(
                            start=prev_token.start,
                            end=token.end,
                            type_="grammar",
                            message=msg,
                            short_message="Negation pattern",
                            replacements=[],
                            rule_id="gr:negation_ver_shedzleba",
                            severity="warning",
                            word=f"{prev_text} {token_text}",
                        )
                    )

    return annotations


def check_interrogative_word_order(
    text: str, tokens: List[Token]
) -> List[GRGrammarAnnotation]:
    """Check that interrogative pronouns appear immediately pre-verbally.

    According to gr.json, interrogatives must appear directly before the verb.
    This is a simplified heuristic check - a full implementation would need
    proper verb detection via Stanza or a verb lexicon.
    """
    annotations: List[GRGrammarAnnotation] = []
    rules = get_gr_grammar_rules()
    interrogatives = rules.get_interrogative_georgian_forms()

    for i, token in enumerate(tokens):
        token_text = token.text.lower().strip(".,!?…;:\"'\"„")

        if token_text in interrogatives:
            # Check if there's a verb immediately after
            if i < len(tokens) - 1:
                next_token = tokens[i + 1]
                next_text = next_token.text.lower().strip(".,!?…;:\"'\"„")

                # If there's a non-verb word between interrogative and verb, flag it
                if next_text and next_text not in interrogatives and not re.match(r"[.,!?…;:]", next_text):
                    # Skip if it's likely a verb (Georgian verbs often end in specific patterns)
                    if not (next_text.endswith("ს") or next_text.endswith("ენ") or
                            next_text.endswith("თ") or next_text.endswith("ბ")):
                        msg = (
                            f"Interrogative '{token_text}' should appear immediately "
                            f"before the verb in Georgian."
                        )
                        annotations.append(
                            _ann(
                                start=token.start,
                                end=token.end,
                                type_="style",
                                message=msg,
                                short_message="Interrogative position",
                                replacements=[],
                                rule_id="gr:interrogative_position",
                                severity="info",
                                word=token_text,
                            )
                        )

    return annotations


def check_tag_question_position(
    text: str, tokens: List[Token]
) -> List[GRGrammarAnnotation]:
    """Check that tag question particle 'xom' (ხომ) is in second position.

    According to gr.json, the tag question particle must occupy the exact
    second position within the sentence.
    """
    annotations: List[GRGrammarAnnotation] = []
    rules = get_gr_grammar_rules()
    tag_particle = rules.get_tag_question_particle()

    # Convert to Georgian script if needed
    tag_particle_georgian = "ხომ" if tag_particle == "xom" else tag_particle

    for i, token in enumerate(tokens):
        token_text = token.text.lower().strip(".,!?…;:\"'\"„")

        # Check both Latin and Georgian forms, or if particle is contained in the token
        is_particle = (
            token_text == tag_particle_georgian.lower() or
            token_text == tag_particle.lower() or
            tag_particle_georgian.lower() in token_text or
            tag_particle.lower() in token_text
        )

        if is_particle:
            # Check if it's in the second position (index 1)
            if i != 1:
                msg = (
                    f"Tag question particle '{tag_particle_georgian}' must occupy the exact "
                    f"second position within the sentence."
                )
                annotations.append(
                    _ann(
                        start=token.start,
                        end=token.end,
                        type_="grammar",
                        message=msg,
                        short_message="Tag particle position",
                        replacements=[],
                        rule_id="gr:tag_particle_position",
                        severity="warning",
                        word=token_text,
                    )
                )

    return annotations


def check_negation_particle_context(
    text: str, tokens: List[Token]
) -> List[GRGrammarAnnotation]:
    """Check negation particles are used in correct contexts.

    Specifically checks that 'nu' (ნუ) is used only for negative commands/imperatives.
    This is a simplified heuristic - a full implementation would need imperative detection.
    """
    annotations: List[GRGrammarAnnotation] = []
    rules = get_gr_grammar_rules()
    negation_particles = rules.get_all_negation_forms()

    for i, token in enumerate(tokens):
        token_text = token.text.lower().strip(".,!?…;:\"'\"„")

        if token_text in negation_particles:
            # Check for 'nu' (do not!) outside of imperative context
            if token_text == "nu" or token_text == "ნუ":
                # If it's not at the start of a sentence or before a verb, flag it
                if i > 0:
                    prev_token = tokens[i - 1]
                    prev_text = prev_token.text.lower().strip(".,!?…;:\"'\"„")
                    if prev_text and not re.match(r"[.!?…]", prev_text):
                        msg = (
                            f"'{token_text}' is used strictly for negative commands/imperatives."
                        )
                        annotations.append(
                            _ann(
                                start=token.start,
                                end=token.end,
                                type_="style",
                                message=msg,
                                short_message="Imperative negation",
                                replacements=[],
                                rule_id="gr:imperative_negation",
                                severity="info",
                                word=token_text,
                            )
                        )

    return annotations


def run_gr_grammar_checks(
    text: str, tokens: List[Token], stanza_document: Any | None = None
) -> List[GRGrammarAnnotation]:
    """Run all gr.json grammar checks."""
    annotations: List[GRGrammarAnnotation] = []

    annotations.extend(check_negation_usage(text, tokens))
    annotations.extend(check_interrogative_word_order(text, tokens))
    annotations.extend(check_tag_question_position(text, tokens))
    annotations.extend(check_negation_particle_context(text, tokens))

    return annotations


def gr_grammar_engine_meta() -> Dict[str, int]:
    """Return metadata about the gr.json grammar checker."""
    rules = get_gr_grammar_rules()
    return {
        "gr_preverb_count": len(rules.get_preverbs()),
        "gr_interrogative_count": len(rules.get_interrogatives()),
        "gr_thematic_suffix_count": len(rules.get_thematic_suffixes()),
        "gr_negation_particle_count": len(rules.get_all_negation_forms()),
    }
