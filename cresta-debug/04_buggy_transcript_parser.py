"""
CRESTA DEBUG - Challenge 4: Conversation Transcript Parser
==========================================================
A colleague wrote a transcript parser. It works fine for clean input but
has ONE bug involving how it handles the colon separator in message text.

Consider a line like:
    AGENT: Sure, the time is 10:45, let me check.

The message text contains a colon. The bug silently truncates message text
whenever the message itself contains a colon.

Your job is to:
  1. Find the bug.
  2. Write a one-line comment above the broken line explaining what is wrong.
  3. Fix it.

Run this file to see which tests fail:
    python3 04_buggy_transcript_parser.py
"""


def parse_transcript(raw: str) -> list[dict]:
    turns = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        # BUG IS ON THE NEXT LINE
        parts = line.split(":")  # <-- what happens when message has a ":"?
        if len(parts) != 2:
            continue
        speaker, text = parts[0].strip(), parts[1].strip()
        if speaker not in ("AGENT", "CUSTOMER"):
            continue
        turns.append({"speaker": speaker, "text": text})
    return turns


def conversation_stats(turns: list[dict]) -> dict:
    if not turns:
        return {
            "total_turns": 0,
            "agent_turns": 0,
            "customer_turns": 0,
            "avg_agent_words": 0.0,
            "avg_customer_words": 0.0,
            "first_speaker": None,
            "longest_turn": None,
        }

    agent_texts = [t["text"] for t in turns if t["speaker"] == "AGENT"]
    customer_texts = [t["text"] for t in turns if t["speaker"] == "CUSTOMER"]

    def avg_words(texts):
        if not texts:
            return 0.0
        return sum(len(t.split()) for t in texts) / len(texts)

    longest = max(turns, key=lambda t: len(t["text"].split()))["text"]

    return {
        "total_turns": len(turns),
        "agent_turns": len(agent_texts),
        "customer_turns": len(customer_texts),
        "avg_agent_words": avg_words(agent_texts),
        "avg_customer_words": avg_words(customer_texts),
        "first_speaker": turns[0]["speaker"],
        "longest_turn": longest,
    }


# ------------------------------------------------------------------
# Tests
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

    # ---- basic parse (no colons in messages — passes even with bug) ----
    raw1 = "AGENT: Hello there.\nCUSTOMER: Hi!\n"
    t1 = parse_transcript(raw1)
    check("basic: turn count", len(t1), 2)
    check("basic: first speaker", t1[0]["speaker"], "AGENT")
    check("basic: first text", t1[0]["text"], "Hello there.")

    # ---- THE FAILING CASE: colon inside the message body ----
    raw2 = (
        "AGENT: Sure, the time is 10:45, let me check.\n"
        "CUSTOMER: Great, my ref is ID:9921.\n"
        "AGENT: Got it.\n"
    )
    t2 = parse_transcript(raw2)
    check("colon-in-msg: turn count", len(t2), 3)
    # guard access so we see all FAIL labels rather than an IndexError crash
    check(
        "colon-in-msg: agent text 1",
        t2[0]["text"] if len(t2) > 0 else None,
        "Sure, the time is 10:45, let me check.",
    )
    check(
        "colon-in-msg: customer text",
        t2[1]["text"] if len(t2) > 1 else None,
        "Great, my ref is ID:9921.",
    )
    check(
        "colon-in-msg: agent text 2", t2[2]["text"] if len(t2) > 2 else None, "Got it."
    )

    # ---- empty transcript ----
    check("empty", parse_transcript(""), [])

    # ---- malformed lines still skipped ----
    raw3 = "AGENT: Valid.\nnot valid\nCUSTOMER: Also valid.\n"
    t3 = parse_transcript(raw3)
    check("malformed skipped: count", len(t3), 2)

    passed = sum(results)
    print(f"\n{passed}/{len(results)} tests passed")
