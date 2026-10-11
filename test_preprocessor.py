import unittest

from preprocessor import iter_tokens, normalize_text, normalize_words


class PreprocessorTests(unittest.TestCase):
    def test_normalize_text_uses_nfc(self) -> None:
        self.assertEqual(normalize_text("ა\u0301"), normalize_text(normalize_text("ა\u0301")))

    def test_normalize_words_normalizes_each_entry(self) -> None:
        words = normalize_words({"ბრენდი", "ტესტი"})
        self.assertEqual(words, {"ბრენდი", "ტესტი"})

    def test_iter_tokens_returns_full_mixed_script_token(self) -> None:
        tokens = iter_tokens("ეს არის შეცდომaa.")
        self.assertEqual([token.text for token in tokens], ["ეს", "არის", "შეცდომaa"])
        self.assertTrue(tokens[-1].is_mixed_script)
        self.assertTrue(tokens[-1].should_spellcheck)
        self.assertEqual((tokens[-1].start, tokens[-1].end), (8, 16))

    def test_iter_tokens_skips_plain_latin_as_spellcheck_target(self) -> None:
        tokens = iter_tokens("FooBar და ბრენდი")
        self.assertFalse(tokens[0].should_spellcheck)
        self.assertTrue(tokens[1].should_spellcheck)
        self.assertTrue(tokens[2].should_spellcheck)


if __name__ == "__main__":
    unittest.main()
