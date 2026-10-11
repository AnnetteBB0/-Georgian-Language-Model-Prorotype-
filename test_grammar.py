import unittest

from grammar import check_grammar
from main import CheckOptions, CheckRequest, check_text


class GrammarRuleTests(unittest.TestCase):
    def _rule_ids(self, annotations):
        return [a.rule_id for a in annotations]

    def test_repeated_word_rule_present(self) -> None:
        annotations, _, meta = check_grammar("ეს ეს ტექსტია.")
        rule_ids = self._rule_ids(annotations)
        self.assertIn("grammar:repeated_word", rule_ids)
        repeated = next(
            a for a in annotations if a.rule_id == "grammar:repeated_word"
        )
        self.assertEqual(repeated.replacements, ["ეს"])
        self.assertEqual(repeated.word, "ეს ეს")
        self.assertEqual(
            meta["grammar_engine"],
            "rules+optional-stanza+alignment+grammar2+desktop",
        )
        self.assertIn("alignment_lexicon_size", meta)
        self.assertIn("grammar2_postposition_count", meta)
        self.assertIn("desktop_postposition_count", meta)

    def test_capitalization_rule_lowercase_sentence_start(self) -> None:
        annotations, _, _ = check_grammar("ეს არის ტექსტი.")
        rule_ids = self._rule_ids(annotations)
        self.assertIn("grammar:sentence_capitalization", rule_ids)

    def test_capitalization_rule_uppercase_no_issue(self) -> None:
        annotations, _, _ = check_grammar("ეს არის ტექსტი.".replace("ე", "ე"))
        text = "ეს არის ტექსტი."
        cap = text[0].upper() + text[1:]
        annotations, _, _ = check_grammar(cap)
        rule_ids = self._rule_ids(annotations)
        self.assertNotIn("grammar:sentence_capitalization", rule_ids)

    def test_spacing_rules(self) -> None:
        annotations, _, _ = check_grammar("გამარჯობა ,როგორ ხარ?")
        rule_ids = self._rule_ids(annotations)
        self.assertIn("grammar:space_before_punctuation", rule_ids)
        self.assertIn("grammar:missing_space_after_punctuation", rule_ids)

    def test_double_space_rule(self) -> None:
        annotations, _, _ = check_grammar("გამარჯობა  როგორ ხარ?")
        rule_ids = self._rule_ids(annotations)
        self.assertIn("grammar:double_space", rule_ids)

    def test_repeated_punctuation_rule(self) -> None:
        annotations, _, _ = check_grammar("გამარჯობა.. როგორ ხარ?")
        rule_ids = self._rule_ids(annotations)
        self.assertIn("grammar:repeated_punctuation", rule_ids)

    def test_georgian_quotation_style(self) -> None:
        annotations, _, _ = check_grammar('მან თქვა "გამარჯობა".')
        rule_ids = self._rule_ids(annotations)
        self.assertIn("style:georgian_quotes", rule_ids)
        quotes = next(
            a for a in annotations if a.rule_id == "style:georgian_quotes"
        )
        self.assertEqual(quotes.replacements, ["„გამარჯობა“"])
        self.assertEqual(quotes.type, "style")

    def test_unclosed_quote(self) -> None:
        annotations, _, _ = check_grammar("მან თქვა „გამარჯობა.")
        rule_ids = self._rule_ids(annotations)
        self.assertIn("grammar:unclosed_quote", rule_ids)

    def test_dash_style_rule(self) -> None:
        annotations, _, _ = check_grammar("დღეს - შენი დაბადების დღეა.")
        rule_ids = self._rule_ids(annotations)
        self.assertIn("style:em_dash", rule_ids)
        em = next(a for a in annotations if a.rule_id == "style:em_dash")
        self.assertEqual(em.replacements, ["—"])

    def test_sentence_length_rule(self) -> None:
        long_sentence = "ეს არის " + "ძალიან " * 20 + "გრძელი წინადადება."
        annotations, _, _ = check_grammar(long_sentence)
        rule_ids = self._rule_ids(annotations)
        has_long = any(
            rid in rule_ids
            for rid in ("style:long_sentence", "style:very_long_sentence")
        )
        self.assertTrue(has_long)

    def test_filler_word_rule(self) -> None:
        annotations, _, _ = check_grammar("ალბათ ეს არის სწორი.")
        rule_ids = self._rule_ids(annotations)
        self.assertIn("style:filler_word", rule_ids)
        filler = next(
            a for a in annotations if a.rule_id == "style:filler_word"
        )
        self.assertEqual(filler.word, "ალბათ")
        self.assertEqual(filler.type, "style")

    def test_overused_word_rule(self) -> None:
        text = "ძალიან ძალიან ძალიან ძალიან კარგი ტექსტია."
        annotations, _, _ = check_grammar(text)
        rule_ids = self._rule_ids(annotations)
        self.assertIn("style:overused_word", rule_ids)

    def test_no_duplicate_repeated_word_annotations(self) -> None:
        annotations, _, _ = check_grammar("ეს ეს ტექსტია.")
        repeated_count = sum(
            1
            for rid in self._rule_ids(annotations)
            if rid in ("grammar:repeated_word", "grammar:stanza_repeated_lemma")
        )
        self.assertLessEqual(repeated_count, 1)

    def test_text_stats_are_computed(self) -> None:
        text = "გამარჯობა. როგორ ხარ? მე კარგად ვარ. ეს არის მეოთხე წინადადება."
        _, _, meta = check_grammar(text)
        self.assertIn("word_count", meta)
        self.assertIn("sentence_count", meta)
        self.assertIn("unique_word_count", meta)
        self.assertIn("lexical_diversity", meta)
        self.assertGreaterEqual(meta["word_count"], 8)
        self.assertGreaterEqual(meta["sentence_count"], 2)


class GrammarAPITests(unittest.TestCase):
    def test_api_includes_grammar_repeated_word_annotation(self) -> None:
        opts = CheckOptions(
            check_spelling=False, check_grammar=True, check_style=False
        )
        response = check_text(
            CheckRequest(text="ეს ეს ტექსტია.", options=opts)
        )
        rule_ids = [a["rule_id"] for a in response.annotations]
        self.assertIn("grammar:repeated_word", rule_ids)
        self.assertIn("grammar_ms", response.meta)
        self.assertIn("stanza_available", response.meta)
        self.assertIn("word_count", response.meta)

    def test_api_can_disable_grammar_and_style(self) -> None:
        opts = CheckOptions(
            check_spelling=False, check_grammar=False, check_style=False
        )
        response = check_text(
            CheckRequest(text="ეს ეს ტექსტია.", options=opts)
        )
        self.assertEqual(response.annotations, [])
        self.assertEqual(response.meta["grammar_ms"], 0)

    def test_api_can_disable_style_only(self) -> None:
        opts = CheckOptions(
            check_spelling=False, check_grammar=True, check_style=False
        )
        response = check_text(
            CheckRequest(
                text='ალბათ მან თქვა "გამარჯობა". ეს ეს იქნა.', options=opts
            )
        )
        rule_ids = [a["rule_id"] for a in response.annotations]
        self.assertIn("grammar:repeated_word", rule_ids)
        self.assertNotIn("style:filler_word", rule_ids)
        self.assertNotIn("style:georgian_quotes", rule_ids)

    def test_api_can_disable_grammar_only(self) -> None:
        opts = CheckOptions(
            check_spelling=False, check_grammar=False, check_style=True
        )
        response = check_text(
            CheckRequest(
                text='ალბათ მან თქვა "გამარჯობა". ეს ეს იქნა.', options=opts
            )
        )
        rule_ids = [a["rule_id"] for a in response.annotations]
        self.assertNotIn("grammar:repeated_word", rule_ids)
        self.assertIn("style:filler_word", rule_ids)


class CaseTransitionTests(unittest.TestCase):
    def _count_rule(self, annotations, rule_id):
        return sum(1 for a in annotations if a.rule_id == rule_id)

    def test_meta_reports_alignment_lexicon_size(self) -> None:
        _, _, meta = check_grammar("გამარჯობა.")
        self.assertIn("alignment_lexicon_size", meta)
        self.assertGreaterEqual(meta["alignment_lexicon_size"], 70)

    def test_1st_conj_series_i_correct_no_mismatch(self) -> None:
        annotations, _, _ = check_grammar("მე წერილს ვწერ.")
        self.assertEqual(self._count_rule(annotations, "grammar:case_alignment"), 0)

    def test_1st_conj_series_i_wrong_nom_object_instead_of_dat(self) -> None:
        annotations, _, _ = check_grammar("მე წერილი ვწერ.")
        self.assertGreaterEqual(
            self._count_rule(annotations, "grammar:case_alignment"), 1
        )
        align = [a for a in annotations if a.rule_id == "grammar:case_alignment"]
        self.assertTrue(any("Direct object" in a.message for a in align))

    def test_1st_conj_series_ii_correct_erg_plus_nom(self) -> None:
        annotations, _, _ = check_grammar("მე მწერალმა წერილი დავწერე.")
        self.assertEqual(self._count_rule(annotations, "grammar:case_alignment"), 0)

    def test_1st_conj_series_ii_wrong_dat_object(self) -> None:
        annotations, _, _ = check_grammar("მე მწერალმა წერილს დავწერე.")
        align = [a for a in annotations if a.rule_id == "grammar:case_alignment"]
        self.assertTrue(any("Direct object" in a.message for a in align))
        self.assertTrue(any("სერია II" in a.message for a in align))

    def test_1st_conj_series_iii_inversion_correct(self) -> None:
        annotations, _, _ = check_grammar("მას წერილი აქვს დაწერილი.")
        self.assertEqual(self._count_rule(annotations, "grammar:case_alignment"), 0)

    def test_4th_conj_inverted_verb_correct_dat_subj_nom_obj(self) -> None:
        annotations, _, _ = check_grammar("მას წიგნი მაყვარს.")
        self.assertEqual(self._count_rule(annotations, "grammar:case_alignment"), 0)

    def test_4th_conj_inverted_verb_wrong_nom_subj(self) -> None:
        annotations, _, _ = check_grammar("ის წიგნი მაყვარს.")
        align = [a for a in annotations if a.rule_id == "grammar:case_alignment"]
        self.assertGreaterEqual(len(align), 1)
        self.assertTrue(any("Subject" in a.message for a in align))
        self.assertTrue(any("Conj 4" in a.message for a in align))

    def test_3rd_conj_intransitive_series_ii_accepts_personal_pronoun(self) -> None:
        annotations, _, _ = check_grammar("მე მივედი შკოლაში.")
        self.assertEqual(self._count_rule(annotations, "grammar:case_alignment"), 0)

    def test_2nd_conj_intransitive_series_ii_no_mismatch(self) -> None:
        annotations, _, _ = check_grammar("მე დავიდი შკოლაში.")
        self.assertEqual(self._count_rule(annotations, "grammar:case_alignment"), 0)

    def test_case_alignment_annotation_has_correct_spans(self) -> None:
        annotations, _, _ = check_grammar("ის წიგნი მაყვარს.")
        align = [a for a in annotations if a.rule_id == "grammar:case_alignment"]
        self.assertTrue(align)
        subject_ann = align[0]
        self.assertEqual(subject_ann.word.lower(), "ის")
        self.assertEqual(subject_ann.start, 0)
        self.assertEqual(subject_ann.end, 2)
        self.assertEqual(subject_ann.severity, "warning")


if __name__ == "__main__":
    unittest.main()
