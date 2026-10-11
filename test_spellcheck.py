import unittest

from main import CheckOptions, CheckRequest, check_text
from spellcheck import check_spelling, profile_spelling


class SpellcheckTests(unittest.TestCase):
    def test_known_word_has_no_annotation(self) -> None:
        annotations, _ = check_spelling("გამარჯობა")
        self.assertEqual(annotations, [])

    def test_mixed_script_word_marks_full_token_span(self) -> None:
        text = "ეს არის შეცდომaa."
        annotations, _ = check_spelling(text)

        self.assertEqual(len(annotations), 1)
        annotation = annotations[0]
        self.assertEqual(annotation.word, "შეცდომaa")
        self.assertEqual(text[annotation.start:annotation.end], "შეცდომaa")
        self.assertEqual(annotation.rule_id, "token:mixed_script")
        self.assertEqual(annotation.replacements, [])

    def test_allowlist_skips_annotation(self) -> None:
        annotations, _ = check_spelling(
            "ბრენდი",
            extra_words={"ბრენდი"},
        )
        self.assertEqual(annotations, [])

    def test_short_unknown_word_keeps_suggestions(self) -> None:
        annotations, _ = check_spelling("ტექსტტ")

        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].word, "ტექსტტ")
        self.assertGreater(len(annotations[0].replacements), 0)

    def test_long_unknown_word_skips_suggestions_for_speed(self) -> None:
        annotations, _ = check_spelling("გამარჯობაა")

        self.assertEqual(len(annotations), 1)
        self.assertEqual(annotations[0].word, "გამარჯობაა")
        self.assertEqual(annotations[0].replacements, [])

    def test_api_handler_returns_mixed_script_annotation(self) -> None:
        opts = CheckOptions(
            check_spelling=True, check_grammar=False, check_style=False
        )
        response = check_text(
            CheckRequest(text="ეს არის შეცდომaa.", options=opts)
        )

        annotations = [
            a for a in response.annotations if a["type"] == "spelling"
        ]
        self.assertGreaterEqual(len(annotations), 1)
        annotation = annotations[0]
        self.assertEqual(annotation["word"], "შეცდომaa")
        self.assertEqual(annotation["rule_id"], "token:mixed_script")
        self.assertEqual(annotation["start"], 8)
        self.assertEqual(annotation["end"], 16)

    def test_api_always_includes_baseline_stats(self) -> None:
        opts = CheckOptions(
            check_spelling=True, check_grammar=False, check_style=False
        )
        response = check_text(
            CheckRequest(text="ეს არის ტექსტი.", options=opts)
        )
        self.assertIn("word_count", response.meta)
        self.assertIn("sentence_count", response.meta)
        self.assertIn("lexical_diversity", response.meta)
        self.assertGreaterEqual(response.meta["word_count"], 3)

    def test_profile_spelling_reports_repeated_tokens(self) -> None:
        annotations, _, profile_rows = profile_spelling(
            "ტექსტტ ტექსტტ შეცდომaa"
        )

        self.assertEqual(len(annotations), 3)
        by_word = {row["word"]: row for row in profile_rows}
        self.assertEqual(by_word["ტექსტტ"]["occurrences"], 2)
        self.assertEqual(by_word["ტექსტტ"]["misspell_hits"], 2)
        self.assertGreaterEqual(by_word["ტექსტტ"]["suggestions_generated"], 2)
        self.assertEqual(by_word["შეცდომaa"]["mixed_script_hits"], 1)


if __name__ == "__main__":
    unittest.main()
