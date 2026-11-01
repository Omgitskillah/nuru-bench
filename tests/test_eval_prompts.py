"""Nuru's no-save phrase check (core.questions) against every prompt in the suite's cases."""
import json
from pathlib import Path

from core import questions

EVALS = Path(__file__).resolve().parents[1]


def eval_prompts():
    legacy = json.loads((EVALS / "decision_layer" / "cases.json").read_text())
    for case in legacy.values():
        yield from ([case["prompt"]] if "prompt" in case else [])
        yield from (turn["prompt"] for turn in case.get("turns", []))
    for case in json.loads((EVALS / "multi_turn" / "cases.json").read_text()).values():
        yield from (turn["prompt"] for turn in case["turns"])
    for case in json.loads((EVALS / "multi_turn" / "failure_pairs" / "cases.json").read_text())["cases"]:
        yield from (turn["prompt"] for turn in case["multi_turn"])


WRITE_REQUEST = ("save", "add ", "append", "create", "write a ", "update", "rename", "move", "record", "log ")


def test_no_eval_prompt_that_matches_also_asks_for_a_write():
    # The check withholds writes, so a match on a prompt that wants one would cost that test its write.
    # Each match must be a turn that only forbids writing: none of them may also ask for one.
    matched = [p for p in eval_prompts() if questions.no_save_phrase(p)]
    assert len(matched) >= 40
    for prompt in matched:
        rest = prompt.lower().replace(questions.no_save_phrase(prompt).lower(), "")
        asks = [w for w in WRITE_REQUEST if w in rest]
        assert not asks or any(prompt.startswith(start) for start in KNOWN_READ_ONLY), (prompt, asks)


# Matches whose other words only sound like a write request, each read and judged by hand (2026-10-09):
# "write ... here" is the reply, "recorded" and "status updates" describe notes, and the moved date is
# the conversation's ("Do not edit or schedule anything").
KNOWN_READ_ONLY = (
    "Write a three-bullet manager summary here",
    "From Berlin Admin Chaos Notes, give the recorded",
    "Move one of those dates back a week",
    "Locate every note that records the SARA-R510S",
    "Audit the project notes, their status updates",
    "Gather current project status and the relevant corrections for a short manager update",
    "Find and read my internet-contract note. Identify the recorded",
    "Using the current date supplied for this run, calculate calendar days to the recorded",
)
