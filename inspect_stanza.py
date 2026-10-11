import sys
sys.path.insert(0, "/Users/baskibuskebi/Desktop/CGC/backend")
sys.path.insert(0, "/Users/baskibuskebi/Desktop/CGC/Rules")

import stanza

try:
    nlp = stanza.Pipeline(
        lang="ka",
        processors="tokenize,pos,lemma,depparse",
        use_gpu=False,
        verbose=False,
    )
except Exception as exc:
    print(f"COULD NOT INIT: {exc}")
    raise

samples = [
    "მე წერილს ვწერ.",
    "მე წერილი დავწერე.",
    "მას წერილი აქვს დაწერილი.",
    "მე მიყვარს წიგნი.",
    "წიგნი მაყვარს.",
    "მე დავიდი შკოლაში.",
    "მე მივედი შკოლაში.",
    "მას აქვს კარგი აზრი.",
]

for s in samples:
    print(f"\n=== {s} ===")
    doc = nlp(s)
    for sent in doc.sentences:
        for w in sent.words:
            print(
                f"{w.id:>3} {w.text:<15} lemma={w.lemma:<12} "
                f"upos={w.upos:<6} xpos={str(w.xpos or '-'):<8} "
                f"feats={w.feats or '-'} "
                f"head={w.head:<3} deprel={w.deprel}"
            )
