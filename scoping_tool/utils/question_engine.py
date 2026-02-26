"""
Question Engine
================
Core CLI engine for presenting questions, collecting answers,
handling dependencies, and storing responses.
"""

import sys
import textwrap
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Any


class QuestionType(Enum):
    YES_NO       = auto()
    CHOICE       = auto()
    MULTI_CHOICE = auto()
    TEXT         = auto()
    NUMBER       = auto()


@dataclass
class Question:
    id:           str
    text:         str
    qtype:        QuestionType
    choices:      List[str]       = field(default_factory=list)
    help_text:    Optional[str]   = None
    nist_controls: List[str]      = field(default_factory=list)
    depends_on:   Optional[Tuple] = None   # (question_id, expected_value)
    is_critical:  bool            = False  # Highlighted in report
    gap_flag:     bool            = False  # Flag as gap if answer indicates weakness


# ── Terminal helpers ───────────────────────────────────────────────────────────
def _tty() -> bool:
    return sys.stdout.isatty()

def _c(text: str, code: str) -> str:
    return f"{code}{text}\033[0m" if _tty() else text

BOLD   = "\033[1m"
CYAN   = "\033[96m"
YELLOW = "\033[93m"
GREEN  = "\033[92m"
RED    = "\033[91m"
DIM    = "\033[2m"
RESET  = "\033[0m"


class QuestionEngine:
    """
    Presents a list of Question objects interactively, handles
    conditional logic (depends_on), and returns a dict of answers.
    """

    def __init__(self, questions: List[Question]):
        self.questions = questions
        self.answers: dict = {}

    def run(self) -> dict:
        total = len(self.questions)
        shown = 0

        for q in self.questions:
            # Check dependency
            if q.depends_on:
                dep_id, expected = q.depends_on
                dep_answer = self.answers.get(dep_id)
                # Normalize comparison
                if isinstance(expected, bool):
                    actual = self._to_bool(dep_answer)
                    if actual != expected:
                        continue
                else:
                    if dep_answer != expected:
                        continue

            shown += 1
            self._print_question(q, shown)
            answer = self._collect_answer(q)
            self.answers[q.id] = answer
            print()

        return self.answers

    # ── Question display ───────────────────────────────────────────────────────
    def _print_question(self, q: Question, num: int):
        # Question number + critical flag
        critical_tag = _c(" [CRITICAL]", BOLD + RED) if q.is_critical else ""
        print(_c(f"  Q{num}:{critical_tag}", BOLD + CYAN))

        # Question text (wrapped)
        for line in q.text.split("\n"):
            print("  " + line.strip())

        # Help text
        if q.help_text:
            print()
            for line in q.help_text.split("\n"):
                print(_c(f"    ℹ  {line.strip()}", DIM))

        # NIST controls
        if q.nist_controls:
            controls = ", ".join(q.nist_controls)
            print(_c(f"    📋 NIST Controls: {controls}", DIM))

        print()

    # ── Answer collection ──────────────────────────────────────────────────────
    def _collect_answer(self, q: Question) -> Any:
        if q.qtype == QuestionType.YES_NO:
            return self._ask_yes_no()

        elif q.qtype == QuestionType.CHOICE:
            return self._ask_choice(q.choices)

        elif q.qtype == QuestionType.MULTI_CHOICE:
            return self._ask_multi_choice(q.choices)

        elif q.qtype == QuestionType.TEXT:
            val = input("  Your answer: ").strip()
            return val if val else None

        elif q.qtype == QuestionType.NUMBER:
            while True:
                val = input("  Enter a number: ").strip()
                try:
                    return int(val)
                except ValueError:
                    print(_c("  Please enter a valid number.", RED))

    def _ask_yes_no(self) -> bool:
        while True:
            ans = input(_c("  Answer [Y/N]: ", BOLD)).strip().lower()
            if ans in ("y", "yes"):
                return True
            if ans in ("n", "no"):
                return False
            print(_c("  Please enter Y or N.", RED))

    def _ask_choice(self, choices: List[str]) -> str:
        for i, choice in enumerate(choices, 1):
            print(f"  {_c(str(i), CYAN + BOLD)}) {choice}")
        print()
        while True:
            ans = input(_c("  Enter number: ", BOLD)).strip()
            try:
                idx = int(ans) - 1
                if 0 <= idx < len(choices):
                    selected = choices[idx]
                    print(_c(f"  ✓ Selected: {selected}", GREEN))
                    return selected
            except ValueError:
                pass
            print(_c(f"  Please enter a number between 1 and {len(choices)}.", RED))

    def _ask_multi_choice(self, choices: List[str]) -> List[str]:
        for i, choice in enumerate(choices, 1):
            print(f"  {_c(str(i), CYAN + BOLD)}) {choice}")
        print()
        print(_c("  Enter numbers separated by commas (e.g., 1,3,5) or 'all':", DIM))
        while True:
            ans = input(_c("  Your selection: ", BOLD)).strip()
            if ans.lower() == "all":
                print(_c(f"  ✓ Selected all options", GREEN))
                return choices[:]
            try:
                indices = [int(x.strip()) - 1 for x in ans.split(",")]
                selected = [choices[i] for i in indices if 0 <= i < len(choices)]
                if selected:
                    print(_c(f"  ✓ Selected: {', '.join(selected)}", GREEN))
                    return selected
            except (ValueError, IndexError):
                pass
            print(_c(f"  Please enter valid numbers between 1 and {len(choices)}.", RED))

    # ── Helpers ────────────────────────────────────────────────────────────────
    @staticmethod
    def _to_bool(value: Any) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("y", "yes", "true", "1")
        return None
