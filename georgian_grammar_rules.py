# georgian_grammar_rules.py
"""
Georgian Grammar Rules Engine
Derived from provided grammatical specifications for:
1. Adpositions (Postpositions) and Case Government
2. Adjective Declension (Consonant vs. Vowel final stems)
3. Possessive Adjectives Declension

Designed for integration into TraeAI grammar checking systems.
"""

class GeorgianGrammarRules:
    # --- 1. ADPOSITIONS & POSTPOSITIONS ---
    # Morpheme Order: noun_root + plural_suffix + case_suffix (+ postposition)
    MORPHEME_SLOTS = ["noun_root", "plural_suffix", "case_suffix", "postposition"]
    
    POSTPOSITIONS = {
        # nominative
        "-vit": {"meaning": "like", "governed_case": "nominative", "notes": "Can take dative in elongated form (-avit)"},
        # dative
        "-ze": {"meaning": "on", "governed_case": "dative", "notes": ""},
        "-tan": {"meaning": "at, near", "governed_case": "dative", "notes": ""},
        "-tan ertad": {"meaning": "together with", "governed_case": "dative", "notes": ""},
        "-shi": {"meaning": "in, to", "governed_case": "dative", "notes": "Drops dative case suffix -s"},
        "shoris": {"meaning": "among", "governed_case": "dative", "notes": ""},
        "shua": {"meaning": "between", "governed_case": "dative", "notes": ""},
        # instrumental
        "-dan": {"meaning": "from (a place)", "governed_case": "instrumental", "notes": "Drops instrumental case suffix -t"},
        # genitive
        "-gan": {"meaning": "from (a person, a thing)", "governed_case": "genitive", "notes": ""},
        "gamo": {"meaning": "because of", "governed_case": "genitive", "notes": ""},
        "garda": {"meaning": "except", "governed_case": "genitive", "notes": ""},
        "gareshe": {"meaning": "without", "governed_case": "genitive", "notes": ""},
        "-tvis": {"meaning": "for", "governed_case": "genitive", "notes": ""},
        "mier": {"meaning": "by", "governed_case": "genitive", "notes": ""},
        "magivrad": {"meaning": "instead of", "governed_case": "genitive", "notes": ""},
        "miuxedavad": {"meaning": "in spite of", "governed_case": "genitive", "notes": ""},
        "shesaxeb": {"meaning": "about, concerning", "governed_case": "genitive", "notes": ""},
        "-tsin": {"meaning": "before, in front of", "governed_case": "genitive", "notes": ""},
        # adverbial
        "-mde": {"meaning": "up to, as far as", "governed_case": "adverbial", "notes": "Drops adverbial case suffix -d"}
    }

    # --- 2. ADJECTIVE DECLENSION RULES ---
    # Consonant-final vs Vowel-final stem rules when modifying nouns
    ADJECTIVE_DECLENSION = {
        "consonant_stem": {
            # Example stem: did- (big)
            "nominative": "-i",    # did-i
            "ergative": "-ma",    # did-ma
            "dative": "",         # did
            "genitive": "-i",     # did-i
            "instrumental": "-i", # did-i
            "adverbial": "",      # did
            "vocative": "-o"      # did-o
        },
        "vowel_stem": {
            # Example stem: ch'aghara- (grey-haired)
            # Vowel-final stem adjectives are identical in all cases (do not decline)
            "nominative": "",
            "ergative": "",
            "dative": "",
            "genitive": "",
            "instrumental": "",
            "adverbial": "",
            "vocative": ""
        }
    }

    # --- 3. POSSESSIVE ADJECTIVES ---
    # Full case matrices for possessive adjectives
    POSSESSIVE_ADJECTIVES = {
        "first_person_singular": { # chem-i (my)
            "nominative": "chem-i", "ergative": "chem-ma", "dative": "chem-s", 
            "genitive": "chem-i", "instrumental": "chem-i(s)", "adverbial": "chem-s", "vocative": "chem-o"
        },
        "second_person_singular": { # shen-i (your)
            "nominative": "shen-i", "ergative": "shen-ma", "dative": "shen-s", 
            "genitive": "shen-i", "instrumental": "shen-i(s)", "adverbial": "shen-s", "vocative": None
        },
        "third_person_singular_proximal": { # amis-i (this one's)
            "nominative": "amis-i", "ergative": "amis-(ma)", "dative": "amis", 
            "genitive": "amis-(i)", "instrumental": "amis-(i)", "adverbial": "amis", "vocative": None
        },
        "third_person_singular_medial": { # magis-i (that one's)
            "nominative": "magis-i", "ergative": "magis-(ma)", "dative": "magis", 
            "genitive": "magis-(i)", "instrumental": "magis-(i)", "adverbial": "magis", "vocative": None
        },
        "third_person_singular_distal": { # (i)mis-i (that one's yonder)
            "nominative": "(i)mis-i", "ergative": "(i)mis-(ma)", "dative": "(i)mis", 
            "genitive": "(i)mis-(i)", "instrumental": "(i)mis-(i)", "adverbial": "(i)mis", "vocative": None
        },
        "first_person_plural": { # chven-i (our)
            "nominative": "chven-i", "ergative": "chven-ma", "dative": "chven-s", 
            "genitive": "chven-i", "instrumental": "chven-i(s)", "adverbial": "chven-s", "vocative": "chven-o"
        },
        "second_person_plural": { # tkven-i (your pl.)
            "nominative": "tkven-i", "ergative": "tkven-ma", "dative": "tkven-s", 
            "genitive": "tkven-i", "instrumental": "tkven-i(s)", "adverbial": "tkven-s", "vocative": None
        },
        "third_person_plural_proximal": { # amat-i (these ones')
            "nominative": "amat-i", "ergative": "amat-(ma)", "dative": "amat", 
            "genitive": "amat-i", "instrumental": "amat-(i)", "adverbial": "amat", "vocative": None
        },
        "third_person_plural_medial": { # magat-i (those ones')
            "nominative": "magat-i", "ergative": "magat-(ma)", "dative": "magat", 
            "genitive": "magat-i", "instrumental": "magat-(i)", "adverbial": "magat", "vocative": None
        },
        "third_person_plural_distal": { # (i)mat-i (those ones' yonder)
            "nominative": "(i)mat-i", "ergative": "(i)mat-(ma)", "dative": "(i)mat", 
            "genitive": "(i)mat-i", "instrumental": "(i)mat-(i)", "adverbial": "(i)mat", "vocative": None
        }
    }

    @classmethod
    def validate_postposition_case(cls, postposition: str, actual_case: str) -> bool:
        """Checks if a postposition matches its required governed case."""
        if postposition in cls.POSTPOSITIONS:
            return cls.POSTPOSITIONS[postposition]["governed_case"] == actual_case.lower()
        return False

    @classmethod
    def check_suffix_dropping_rule(cls, case_suffix: str, postposition: str) -> bool:
        """
        Enforces morphotactic truncation constraints:
        - -shi drops dative case suffix -s
        - -dan drops instrumental case suffix -t
        - -mde drops adverbial case suffix -d
        """
        if postposition == "-shi" and case_suffix == "-s":
            return False  # Violation: -s must be dropped
        if postposition == "-dan" and case_suffix == "-t":
            return False  # Violation: -t must be dropped
        if postposition == "-mde" and case_suffix == "-d":
            return False  # Violation: -d must be dropped
        return True
