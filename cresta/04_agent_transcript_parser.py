"""
CRESTA - Challenge 4: Conversation Transcript Parser
=====================================================
Context: Cresta ingests contact-centre transcripts. Given a raw multi-line
transcript string, parse it into a structured list of turns and compute some
simple statistics about the conversation.

The raw transcript has lines in the format:
    <SPEAKER>: <message text>

Where SPEAKER is "AGENT" or "CUSTOMER" (always uppercase).
Blank lines should be ignored.
Lines that do NOT match the pattern should be collected as "malformed".

Implement the two functions below:

    def parse_transcript(raw: str) -> list[dict]
    def conversation_stats(turns: list[dict]) -> dict

--- parse_transcript ---
Returns a list of turn dicts, one per valid line, in order:
    {"speaker": "AGENT" | "CUSTOMER", "text": "<message>"}

--- conversation_stats ---
Given the list of turns (output of parse_transcript), returns a dict:
    {
        "total_turns":      int,   # total number of valid turns
        "agent_turns":      int,   # turns by AGENT
        "customer_turns":   int,   # turns by CUSTOMER
        "avg_agent_words":  float, # mean word count across agent turns (0.0 if none)
        "avg_customer_words": float,
        "first_speaker":    str | None,  # "AGENT", "CUSTOMER", or None if no turns
        "longest_turn":     str | None,  # the full text of the longest turn (word count)
                                         # None if no turns; first longest if tie
    }

Examples:
    raw = \"\"\"
    AGENT: Hello, how can I help you today?
    CUSTOMER: Hi! I need help with my invoice.
    AGENT: Sure, I can help with that.
    CUSTOMER: Great thanks.
    \"\"\"

    parse_transcript(raw) →
    [
        {"speaker": "AGENT",    "text": "Hello, how can I help you today?"},
        {"speaker": "CUSTOMER", "text": "Hi! I need help with my invoice."},
        {"speaker": "AGENT",    "text": "Sure, I can help with that."},
        {"speaker": "CUSTOMER", "text": "Great thanks."},
    ]

    conversation_stats(turns) →
    {
        "total_turns":          4,
        "agent_turns":          2,
        "customer_turns":       2,
        "avg_agent_words":      6.0,   # (7 + 5) / 2 = 6.0 — count words by split()
        "avg_customer_words":   6.0,   # (7 + 2) / 2 ... wait let's count carefully:
                                       # "Hi! I need help with my invoice." → 7 words
                                       # "Great thanks." → 2 words → avg = 4.5
        "first_speaker":        "AGENT",
        "longest_turn":         "Hello, how can I help you today?",
    }

    NOTE: count words using str.split() (splits on any whitespace).
"""

import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel

EXPECTED_LINE_START = re.compile(r"^(AGENT|CUSTOMER):")


class SpeakerType(Enum):
    agent = "AGENT"
    customer = "CUSTOMER"


class TurnDict(BaseModel):
    speaker: SpeakerType
    text: str


class TurnStats(BaseModel):
    total_turns: int
    agent_turns: int
    customer_turns: int
    avg_agent_words: float
    avg_customer_words: float
    first_speaker: Optional[str] = None
    longest_turn: Optional[str] = None


def safe_average(total_txt: int, turns: int):
    if total_txt == 0 or turns == 0:
        return 0

    return total_txt / turns


def parse_transcript(raw: str) -> list[dict]:
    """
    Parse a raw transcript string into a list of turn dicts.
    Blank lines and malformed lines are silently skipped.
    """
    # YOUR CODE HERE
    valid_turns = []
    split_lines = raw.split("\n")
    for line in split_lines:
        matched = EXPECTED_LINE_START.match(line)
        if matched is None:
            continue
        _, end = matched.span()
        speaker, text = line[: end - 1].strip(), line[end + 1 :].strip()
        SpeakerType(speaker)
        valid_turns.append({"speaker": speaker, "text": text})
    return valid_turns


def conversation_stats(turns: list[dict]) -> dict:
    """
    Compute statistics over a parsed list of turn dicts.
    """  # YOUR CODE HERE
    meta = TurnStats(
        **{
            "total_turns": len(turns),
            "agent_turns": 0,
            "customer_turns": 0,
            "avg_agent_words": 0.0,
            "avg_customer_words": 0.0,
            "first_speaker": None,
            "longest_turn": None,
        }
    )

    if not turns:
        return meta.model_dump()

    meta.first_speaker = turns[0].get("speaker") or "UNKNOWN"
    customer_txt_count = 0
    agent_txt_count = 0

    for turn in turns:
        turn = TurnDict(**turn)
        speaker, text = turn.speaker, turn.text
        split_text = text.split(" ")

        if speaker is SpeakerType.agent:
            agent_txt_count += len(split_text)
            meta.agent_turns += 1
        else:
            customer_txt_count += len(split_text)
            meta.customer_turns += 1

        if meta.longest_turn is None or len(split_text) > len(meta.longest_turn):
            meta.longest_turn = text

    meta.avg_customer_words = safe_average(customer_txt_count, meta.customer_turns)
    meta.avg_agent_words = safe_average(agent_txt_count, meta.agent_turns)

    return meta.model_dump()


# ------------------------------------------------------------------
# Tests — run this file directly:  python 04_agent_transcript_parser.py
# ------------------------------------------------------------------
if __name__ == "__main__":
    results = []

    def check(label: str, got, expected):
        status = "PASS" if got == expected else "FAIL"
        results.append(status == "PASS")
        print(f"[{status}] {label}")
        if got != expected:
            print(f"       got:      {got!r}")
            print(f"       expected: {expected!r}")

    # ---- test 1: basic parse ----
    raw1 = """
AGENT: Hello, how can I help you today?
CUSTOMER: Hi! I need help with my invoice.
AGENT: Sure, I can help with that.
CUSTOMER: Great thanks.
"""
    turns1 = parse_transcript(raw1)
    check("turn count", len(turns1), 4)
    check("first turn speaker", turns1[0]["speaker"], "AGENT")
    check("first turn text", turns1[0]["text"], "Hello, how can I help you today?")
    check("last turn speaker", turns1[-1]["speaker"], "CUSTOMER")
    check("last turn text", turns1[-1]["text"], "Great thanks.")

    # ---- test 2: stats ----
    stats1 = conversation_stats(turns1)
    check("total_turns", stats1["total_turns"], 4)
    check("agent_turns", stats1["agent_turns"], 2)
    check("customer_turns", stats1["customer_turns"], 2)
    # "Hello, how can I help you today?" → 7 words
    # "Sure, I can help with that."      → 6 words  → avg = 6.5
    check("avg_agent_words", stats1["avg_agent_words"], 6.5)
    # "Hi! I need help with my invoice." → 7 words
    # "Great thanks."                    → 2 words  → avg = 4.5
    check("avg_customer_words", stats1["avg_customer_words"], 4.5)
    check("first_speaker", stats1["first_speaker"], "AGENT")
    check("longest_turn", stats1["longest_turn"], "Hello, how can I help you today?")

    # ---- test 3: malformed lines are skipped ----
    raw2 = """
AGENT: Valid line.
this is malformed
: also malformed
CUSTOMER: Another valid one.
"""
    turns2 = parse_transcript(raw2)
    check("malformed lines skipped: count", len(turns2), 2)
    check("malformed: first speaker", turns2[0]["speaker"], "AGENT")

    # ---- test 4: empty transcript ----
    turns_empty = parse_transcript("")
    check("empty transcript → empty list", turns_empty, [])
    stats_empty = conversation_stats(turns_empty)
    check("empty stats total_turns", stats_empty["total_turns"], 0)
    check("empty stats first_speaker", stats_empty["first_speaker"], None)
    check("empty stats longest_turn", stats_empty["longest_turn"], None)
    check("empty stats avg_agent_words", stats_empty["avg_agent_words"], 0.0)

    # # ---- test 5: only agent speaks ----
    raw3 = "AGENT: One.\nAGENT: Two words here.\n"
    turns3 = parse_transcript(raw3)
    stats3 = conversation_stats(turns3)
    check("only agent: customer_turns", stats3["customer_turns"], 0)
    check("only agent: avg_customer", stats3["avg_customer_words"], 0.0)
    # "One." → 1 word; "Two words here." → 3 words → avg = 2.0
    check("only agent: avg_agent", stats3["avg_agent_words"], 2.0)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} tests passed")
