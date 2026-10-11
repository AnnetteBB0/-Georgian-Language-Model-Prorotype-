import sys
sys.path.insert(0, "/Users/baskibuskebi/Desktop/CGC/Rules")
from alignment_checker import (
    classify_screeve,
    extract_case,
    build_verb_lexicon,
    find_arguments,
    _VERB_LEXICON,
    run_case_alignment_checks,
    GeorgianAlignmentEngine,
    VerbConjugation,
    ScreeveSeries,
)
import stanza

nlp = stanza.Pipeline(
    lang="ka",
    processors="tokenize,pos,lemma,depparse",
    use_gpu=False,
    verbose=False,
)

cases = [
    "ის წიგნი მაყვარს.",
    "მე წერილს ვწერ.",
    "მე მივედი შკოლაში.",
]

for text in cases:
    print(f"\n========== {text} ==========")
    doc = nlp(text)
    for sent in doc.sentences:
        for w in sent.words:
            upos = w.upos
            lemma = w.lemma or ""
            lemma_in_lexicon = (lemma.lower() in _VERB_LEXICON) or (lemma in _VERB_LEXICON)
            text_in_lexicon = (w.text.lower() in _VERB_LEXICON) or (w.text in _VERB_LEXICON)
            ser = classify_screeve(w)
            subj, obj = find_arguments(sent, w)
            if upos == "VERB" or lemma_in_lexicon or text_in_lexicon:
                print(f"{w.id:>3} {w.text:<12} lemma={w.lemma:<10} "
                      f"upos={w.upos:<6} feats={w.feats or '-'} "
                      f"in_lex={lemma_in_lexicon or text_in_lexicon} series={ser} deprel={w.deprel}")
                if subj:
                    print(f"       subj={subj.text}, case={extract_case(subj)}, feats={subj.feats}")
                if obj:
                    print(f"       obj={obj.text}, case={extract_case(obj)}, feats={obj.feats}")
                lex_used = _VERB_LEXICON.get(lemma.lower()) or _VERB_LEXICON.get(lemma) or _VERB_LEXICON.get(w.text.lower()) or _VERB_LEXICON.get(w.text)
                if lex_used and ser:
                    exp = GeorgianAlignmentEngine.get_expected_cases(lex_used, ser)
                    print(f"       EXPECTED subj={exp.subject_case}, obj={exp.direct_object_case}")
    anns = run_case_alignment_checks(doc, text)
    print(f"  Annotations ({len(anns)}):")
    for a in anns:
        print(f"   - [{a.start}-{a.end}] {a.word} :: {a.message}")
