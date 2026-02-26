#!/usr/bin/env python3
"""
CMMC Enclave Toolkit — CUI/FCI Scoping Assessment Tool
=======================================================
Author:  Pulasthi Batuwita
License: MIT
Purpose: Interactive CLI that guides DoD contractors through a structured
         questionnaire to accurately identify their CMMC assessment scope,
         determine CUI/FCI boundaries, and generate a scoping report.

Usage:
    python scope_assessment.py
    python scope_assessment.py --output reports/my_assessment.json
    python scope_assessment.py --resume reports/my_assessment.json
"""

import os
import sys
import json
import argparse
import textwrap
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoping_tool.questions.system_inventory import SystemInventoryModule
from scoping_tool.questions.data_flow import DataFlowModule
from scoping_tool.questions.boundary import BoundaryModule
from scoping_tool.questions.access_control import AccessControlModule
from scoping_tool.utils.scoring import ScopeScorer
from scoping_tool.reports.report_generator import ReportGenerator

# ── Terminal colors ────────────────────────────────────────────────────────────
class Colors:
    HEADER    = "\033[95m"
    BLUE      = "\033[94m"
    CYAN      = "\033[96m"
    GREEN     = "\033[92m"
    YELLOW    = "\033[93m"
    RED       = "\033[91m"
    BOLD      = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET     = "\033[0m"

def color(text: str, *codes: str) -> str:
    """Wrap text in ANSI color codes if stdout is a TTY."""
    if not sys.stdout.isatty():
        return text
    return "".join(codes) + text + Colors.RESET


# ── Banner ─────────────────────────────────────────────────────────────────────
BANNER = r"""
  ___  __  __ __  __  ___   _____           _   _ _   _  ___ _
 / __||  \/  |  \/  |/ __| | ____|_ __  ___| | | __ )| | ___| |__
| |   | |\/| | |\/| | |    |  _| | '_ \/ __| | | |_ \| |/ _ \ '_ \
| |__ | |  | | |  | | |__  | |___| | | \__ \ |_| |_) | |  __/ |_) |
 \___||_|  |_|_|  |_|\___| |_____|_| |_|___/\___/____/|_|\___|_.__/

         CUI / FCI Scoping Assessment Tool  v1.0.0
         CMMC Level 2  |  NIST SP 800-171 Rev 3
         github.com/yourusername/cmmc-enclave-toolkit
"""

INTRO = """
This tool guides you through a structured scoping assessment to determine:

  1. Which of your systems process, store, or transmit CUI or FCI
  2. The boundary of your CMMC assessment scope
  3. Which NIST SP 800-171 controls apply to your environment
  4. Recommended enclave architecture to reduce your scope

Definitions:
  CUI  — Controlled Unclassified Information (requires CMMC Level 2)
  FCI  — Federal Contract Information (requires CMMC Level 1 minimum)

Time required:  ~15–30 minutes
Output:         JSON data file + Markdown scoping report

Press ENTER to begin, or Ctrl+C to exit.
"""


# ── Core assessment orchestrator ───────────────────────────────────────────────
class ScopingAssessment:
    """
    Orchestrates the full CUI/FCI scoping assessment across all question modules.
    Collects responses, scores them, and triggers report generation.
    """

    MODULES = [
        ("system_inventory",  "Module 1: System & Asset Inventory",      SystemInventoryModule),
        ("data_flow",         "Module 2: CUI/FCI Data Flow Analysis",    DataFlowModule),
        ("boundary",          "Module 3: System Boundary Definition",    BoundaryModule),
        ("access_control",    "Module 4: Access Control & Authentication", AccessControlModule),
    ]

    def __init__(self, output_path: str = None, resume_path: str = None):
        self.output_path  = output_path or f"reports/scoping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.resume_path  = resume_path
        self.responses    = {}
        self.metadata     = {
            "tool_version":    "1.0.0",
            "assessment_date": datetime.now().isoformat(),
            "organization":    None,
            "assessor":        None,
        }

    # ── Public entry point ─────────────────────────────────────────────────────
    def run(self):
        self._print_banner()

        if self.resume_path:
            self._load_resume()

        input()  # Wait for ENTER after intro
        self._collect_metadata()

        for module_key, module_title, ModuleClass in self.MODULES:
            if module_key in self.responses:
                print(color(f"\n  ✓ Skipping {module_title} (already completed)\n", Colors.GREEN))
                continue
            module = ModuleClass()
            print(color(f"\n{'─' * 60}", Colors.CYAN))
            print(color(f"  {module_title}", Colors.BOLD + Colors.CYAN))
            print(color(f"{'─' * 60}\n", Colors.CYAN))
            self.responses[module_key] = module.run()
            self._autosave()

        self._finalize()

    # ── Metadata collection ────────────────────────────────────────────────────
    def _collect_metadata(self):
        print(color("\n  ORGANIZATION INFORMATION\n", Colors.BOLD))
        self.metadata["organization"] = self._ask("  Company / Organization name: ")
        self.metadata["cage_code"]    = self._ask("  CAGE Code (if known, or press ENTER to skip): ", required=False)
        self.metadata["assessor"]     = self._ask("  Person completing this assessment: ")
        self.metadata["contract_ref"] = self._ask("  Primary DoD contract number (or press ENTER): ", required=False)
        print()

    # ── Finalize & report ──────────────────────────────────────────────────────
    def _finalize(self):
        print(color(f"\n{'─' * 60}", Colors.CYAN))
        print(color("  ASSESSMENT COMPLETE — Generating Report", Colors.BOLD + Colors.GREEN))
        print(color(f"{'─' * 60}\n", Colors.CYAN))

        scorer    = ScopeScorer(self.responses)
        score     = scorer.calculate()
        generator = ReportGenerator(self.metadata, self.responses, score)

        # Save JSON data
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w") as f:
            json.dump({
                "metadata":  self.metadata,
                "responses": self.responses,
                "score":     score,
            }, f, indent=2)

        # Generate Markdown report
        report_path = self.output_path.replace(".json", "_report.md")
        generator.save_markdown(report_path)

        # Print summary to terminal
        self._print_summary(score, report_path)

    # ── Print summary ──────────────────────────────────────────────────────────
    def _print_summary(self, score: dict, report_path: str):
        cmmc_level = score.get("cmmc_level_required", "Unknown")
        cui_scope  = score.get("cui_in_scope", False)
        fci_scope  = score.get("fci_in_scope", False)
        system_ct  = score.get("systems_in_scope", 0)
        enclave    = score.get("enclave_recommended", False)

        level_color = Colors.RED if cmmc_level == "Level 2" else Colors.YELLOW

        print(color("  ┌─────────────────────────────────────────┐", Colors.CYAN))
        print(color("  │         SCOPING ASSESSMENT RESULTS      │", Colors.CYAN + Colors.BOLD))
        print(color("  ├─────────────────────────────────────────┤", Colors.CYAN))
        print(color(f"  │  CUI Present in Environment:  ", Colors.CYAN) +
              color("YES" if cui_scope else "NO", Colors.RED if cui_scope else Colors.GREEN) +
              color(" " * (10 - (3 if cui_scope else 2)) + "│", Colors.CYAN))
        print(color(f"  │  FCI Present in Environment:  ", Colors.CYAN) +
              color("YES" if fci_scope else "NO", Colors.RED if fci_scope else Colors.GREEN) +
              color(" " * (10 - (3 if fci_scope else 2)) + "│", Colors.CYAN))
        print(color(f"  │  Systems In Scope:            {system_ct:<10}│", Colors.CYAN))
        print(color(f"  │  CMMC Level Required:         ", Colors.CYAN) +
              color(f"{cmmc_level:<10}", level_color) +
              color("│", Colors.CYAN))
        print(color(f"  │  Enclave Recommended:         ", Colors.CYAN) +
              color("YES" if enclave else "NO", Colors.YELLOW if enclave else Colors.GREEN) +
              color(" " * (10 - (3 if enclave else 2)) + "│", Colors.CYAN))
        print(color("  └─────────────────────────────────────────┘\n", Colors.CYAN))

        print(color(f"  📄 Scoping report saved to: {report_path}", Colors.GREEN))
        print(color(f"  💾 Raw data saved to:       {self.output_path}\n", Colors.GREEN))

        if enclave:
            print(color(
                "  ⚠️  An enclave is recommended to reduce your CMMC scope.\n"
                "     See docs/deployment-guide.md to deploy the Docker CUI enclave.\n",
                Colors.YELLOW
            ))

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _ask(self, prompt: str, required: bool = True) -> str:
        while True:
            val = input(prompt).strip()
            if val or not required:
                return val
            print(color("  This field is required.", Colors.RED))

    def _autosave(self):
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w") as f:
            json.dump({"metadata": self.metadata, "responses": self.responses}, f, indent=2)

    def _load_resume(self):
        with open(self.resume_path) as f:
            data = json.load(f)
        self.metadata  = data.get("metadata", self.metadata)
        self.responses = data.get("responses", {})
        print(color(f"\n  Resuming assessment from: {self.resume_path}", Colors.YELLOW))

    def _print_banner(self):
        print(color(BANNER, Colors.CYAN + Colors.BOLD))
        print(color(INTRO, Colors.RESET))


# ── CLI entry point ────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="CMMC CUI/FCI Scoping Assessment Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python scope_assessment.py
              python scope_assessment.py --output reports/acme_corp_2025.json
              python scope_assessment.py --resume reports/acme_corp_2025.json
        """)
    )
    parser.add_argument("--output", metavar="PATH",  help="Output file path for assessment data (JSON)")
    parser.add_argument("--resume", metavar="PATH",  help="Resume a previously saved assessment")
    parser.add_argument("--version", action="version", version="cmmc-scope-tool 1.0.0")
    args = parser.parse_args()

    try:
        assessment = ScopingAssessment(output_path=args.output, resume_path=args.resume)
        assessment.run()
    except KeyboardInterrupt:
        print(color("\n\n  Assessment interrupted. Progress has been auto-saved.\n", Colors.YELLOW))
        sys.exit(0)


if __name__ == "__main__":
    main()
