import sys
sys.path.insert(0, "/Users/baskibuskebi/Desktop/CGC/Rules")
from alignment_checker import run_case_alignment_checks, alignment_engine_meta

import stanza

nlp = stanza.Pipeline(
    lang="ka",
    processors="tokenize,pos,lemma,depparse",
    use_gpu=False,
    verbose=False,
)

# (Description, text, expected_number_of_alignment_annotations)
cases = [
    ("Ser II Aorist Transitive (correct: Erg + Nom)",
     "მე მწერალმა წერილი დავწერე.", 0),
    ("Ser II Aorist Transitive (WRONG: Dat object instead of Nom)",
     "მე მწერალმა წერილს დავწერე.", 1),
    ("Ser I Present Transitive (correct: Nom + Dat)",
     "მე წერილს ვწერ.", 0),
    ("Ser I Present Transitive (WRONG: Nom object instead of Dat)",
     "მე წერილი ვწერ.", 1),
    ("Ser IV (4th Conj, affective) — correct: Dat subj, Nom obj",
     "მას წიგნი მაყვარს.", 0),
    ("Ser IV (wrong: Nom subject instead of Dat)",
     "ის წიგნი მაყვარს.", 1),
    ("Ser III Perfect (aux აქვს → 4th conj → Dat + Nom)",
     "მას წერილი აქვს დაწერილი.", 0),
    ("Ser II Intransitive 3rd conj medial: subject in Erg (correct)",
     "მე მივედი შკოლაში.", 0),
    ("Ser II Intransitive 2nd conj patientive: subject stays Nom (correct)",
     "მე დავიდი შკოლაში.", 0),
]

print(f"Lexicon size: {alignment_engine_meta()['alignment_lexicon_size']}\n")
for desc, text, expected in cases:
    doc = nlp(text)
    anns = run_case_alignment_checks(doc, text)
    status = "✓" if len(anns) == expected else "✗"
    print(f"{status} [{expected:02d}/{len(anns):02d}] {desc}")
    print(f"  text: {text}")
    for a in anns:
        print(f"   -> {a.rule_id} @ {a.start}-{a.end} ({a.word}) {a.short_message}: {a.message}")
    print()
