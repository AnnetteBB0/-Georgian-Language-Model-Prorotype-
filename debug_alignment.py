import sys
sys.path.insert(0, "/Users/baskibuskebi/Desktop/CGC/Rules")
from alignment_checker import (
    classify_screeve,
    extract_case,
    build_verb_lexicon,
    find_arguments,
    _VERB_LEXICON,
)
import stanza

nlp = stanza.Pipeline(
    lang="ka",
    processors="tokenize,pos,lemma,depparse",
    use_gpu=False,
    verbose=False,
)

cases = [
    "მე მწერალმა წერილს დავწერე.",   # case 2
    "მე წერილს ვწერ.",                # case 3
    "ის წიგნი მაყვარს.",              # case 6
    "მას წიგნი მაყვარს.",             # case 5 correct
]

for text in cases:
    print(f"\n========== {text} ==========")
    doc = nlp(text)
    for sent in doc.sentences:
        for w in sent.words:
            print(f"{w.id:>3} {w.text:<12} lemma={w.lemma:<10} "
                  f"upos={w.upos:<6} "
                  f"feats={w.feats or '-'} "
                  f"head={w.head:<3} deprel={w.deprel}")
            if w.upos == "VERB":
                ser = classify_screeve(w)
                subj, obj = find_arguments(sent, w)
                print(f"      -> classified series: {ser}")
                lex = _VERB_LEXICON.get((w.lemma or "").lower())
                print(f"      -> lexicon: lemma={(w.lemma or '').lower()} in_lexicon={lex is not None}")
                if subj:
                    print(f"      -> subj_node={subj.text} subj_case={extract_case(subj)} (UD: {subj.feats})")
                if obj:
                    print(f"      -> obj_node={obj.text} obj_case={extract_case(obj)} (UD: {obj.feats})")
            if w.upos == "NOUN":
                lex = _VERB_LEXICON.get((w.lemma or "").lower())
                if lex:
                    print(f"      -> NOUN but LEXICON HAS VERB {w.lemma} conj={lex.conjugation.value}")
