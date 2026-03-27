"""
bank_detector.py — Detect bank name from sender email and email subject
"""

from __future__ import annotations

# Each entry: (bank_label, [sender_fragments], [subject_keywords])
_BANK_RULES = [
    ("HDFC",     ["hdfcbank", "hdfc"],          ["hdfc"]),
    ("SBI",      ["sbi", "onlinesbi"],           ["sbi", "state bank"]),
    ("ICICI",    ["icicibank", "icici"],          ["icici"]),
    ("AXIS",     ["axisbank", "axis"],            ["axis"]),
    ("KOTAK",    ["kotak"],                       ["kotak"]),
    ("YES",      ["yesbank"],                     ["yes bank"]),
    ("PNB",      ["pnb", "punjabnational"],       ["pnb", "punjab national"]),
    ("BOB",      ["bankofbaroda", "bob"],         ["bank of baroda"]),
    ("IPPB",     ["ippbonline", "ippb"],          ["ippb", "india post payment"]),
    ("CANARA",   ["canarabank", "canara"],        ["canara bank"]),
    ("UNION",    ["unionbankofindia", "unionbank"],["union bank"]),
    ("INDIAN",   ["indianbank"],                  ["indian bank"]),
    ("INDUSIND", ["indusind"],                    ["indusind"]),
    ("FEDERAL",  ["federalbank"],                 ["federal bank"]),
    ("RBL",      ["rblbank", "rbl"],              ["rbl bank"]),
]

# Minimum keywords for email to be considered a bank statement
STATEMENT_KEYWORDS = [
    "statement", "account statement", "bank statement",
    "e-statement", "eStatement", "account summary",
]


def detect_bank(sender: str, subject: str) -> str:
    """Return bank label (e.g. 'HDFC') or 'UNKNOWN'."""
    s = (sender + " " + subject).lower()
    for label, sender_frags, subj_kws in _BANK_RULES:
        for frag in sender_frags:
            if frag in s:
                return label
        for kw in subj_kws:
            if kw in s:
                return label
    return "UNKNOWN"


def is_statement_email(subject: str) -> bool:
    """Return True if subject suggests a bank statement."""
    subj_lower = subject.lower()
    return any(kw.lower() in subj_lower for kw in STATEMENT_KEYWORDS)
