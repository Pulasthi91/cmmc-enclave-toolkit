"""
Module 3: System Boundary Definition
======================================
Helps the contractor define the precise boundary of their CMMC
assessment scope — which systems are in-scope vs. out-of-scope —
and evaluates whether an enclave approach would reduce scope.

NIST SP 800-171 Controls addressed:
  SC.3.180 — Implement subnetworks for publicly accessible system components
  SC.3.183 — Deny network communications traffic by default
  SC.3.187 — Implement cryptographic mechanisms to prevent unauthorized disclosure
"""

from scoping_tool.utils.question_engine import QuestionEngine, Question, QuestionType


BOUNDARY_QUESTIONS = [
    Question(
        id="bd_01",
        text="Is your entire IT environment (all systems) used for DoD contract work?",
        qtype=QuestionType.YES_NO,
        help_text=(
            "If YES, your entire environment is likely in scope.\n"
            "  If NO, you may be able to define a narrower assessment boundary."
        ),
        nist_controls=["SC.3.180"],
        is_critical=True,
    ),
    Question(
        id="bd_01a",
        text="Can you clearly identify which specific systems handle CUI/FCI vs. those that do not?",
        qtype=QuestionType.YES_NO,
        depends_on=("bd_01", False),
        help_text=(
            "If you can separate systems that touch CUI/FCI from those that don't, "
            "you can limit your CMMC scope to only the CUI-handling systems."
        ),
        nist_controls=["CM.2.062"],
    ),
    Question(
        id="bd_02",
        text="Are CUI-handling systems physically or logically separated from non-CUI systems?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — physically separate (different hardware, no network connection)",
            "Yes — logically separated (separate VLAN / network segment)",
            "Partially — some separation exists",
            "No — all systems share the same network",
            "Not applicable — entire environment handles CUI",
        ],
        nist_controls=["SC.3.180", "SC.3.183"],
        is_critical=True,
    ),
    Question(
        id="bd_03",
        text="Does your organization use a dedicated, isolated environment (enclave) for CUI processing?",
        qtype=QuestionType.YES_NO,
        help_text=(
            "An enclave is a dedicated, isolated environment where all CUI is processed.\n"
            "  Everything outside the enclave is out of CMMC scope."
        ),
        nist_controls=["SC.3.180"],
        is_critical=True,
    ),
    Question(
        id="bd_03a",
        text="How is your current CUI enclave implemented?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Dedicated physical machines (air-gapped)",
            "Virtual machines (VMware, Hyper-V, VirtualBox)",
            "Docker / containerized environment",
            "Cloud-hosted enclave (e.g., Microsoft GCC High, AWS GovCloud)",
            "Commercial managed enclave service",
            "Other",
        ],
        depends_on=("bd_03", True),
        nist_controls=["SC.3.180"],
    ),
    Question(
        id="bd_04",
        text="Would your organization be willing to implement a dedicated CUI enclave to reduce CMMC scope?",
        qtype=QuestionType.YES_NO,
        depends_on=("bd_03", False),
        help_text=(
            "An enclave limits which systems need CMMC controls — reducing cost and complexity.\n"
            "  This toolkit provides a free Docker-based enclave you can deploy on existing hardware."
        ),
        nist_controls=["SC.3.180"],
    ),
    Question(
        id="bd_05",
        text="Does your network have a defined perimeter with firewall(s) controlling ingress/egress traffic?",
        qtype=QuestionType.YES_NO,
        nist_controls=["SC.3.183"],
        gap_flag=True,
    ),
    Question(
        id="bd_06",
        text="Are there any systems that provide shared services (DNS, DHCP, Active Directory, file sharing) to BOTH CUI and non-CUI systems?",
        qtype=QuestionType.YES_NO,
        help_text=(
            "Shared services that touch both CUI and non-CUI systems may bring the\n"
            "  entire shared infrastructure into CMMC scope."
        ),
        nist_controls=["SC.3.180", "AC.1.001"],
        is_critical=True,
        gap_flag=True,
    ),
    Question(
        id="bd_06a",
        text="Which shared services span your CUI and non-CUI environments? (Select all that apply)",
        qtype=QuestionType.MULTI_CHOICE,
        choices=[
            "Active Directory / LDAP (identity/authentication)",
            "DNS servers",
            "DHCP servers",
            "File servers / NAS (shared drives)",
            "Email server",
            "Backup / DR systems",
            "Monitoring / SIEM",
            "IT management tools (RMM, patch management)",
            "None — shared services are separated",
        ],
        depends_on=("bd_06", True),
        nist_controls=["SC.3.180", "AC.1.001"],
    ),
    Question(
        id="bd_07",
        text="Does your organization have a written System Security Plan (SSP)?",
        qtype=QuestionType.YES_NO,
        help_text=(
            "An SSP is required for CMMC Level 2 assessment. It documents your system boundary,\n"
            "  security controls, and how you meet each NIST 800-171 requirement."
        ),
        nist_controls=["CM.2.061"],
        gap_flag=True,
    ),
    Question(
        id="bd_08",
        text="Have you previously completed a NIST SP 800-171 self-assessment (SPRS score submission)?",
        qtype=QuestionType.YES_NO,
        help_text=(
            "DoD contractors are required to submit a NIST SP 800-171 self-assessment score\n"
            "  to the Supplier Performance Risk System (SPRS)."
        ),
        nist_controls=["CM.2.061"],
        gap_flag=True,
    ),
    Question(
        id="bd_08a",
        text="What is your current SPRS score (if known)?",
        qtype=QuestionType.TEXT,
        depends_on=("bd_08", True),
        help_text="SPRS scores range from -203 (all controls failed) to 110 (all controls met). Enter your score.",
        nist_controls=["CM.2.061"],
    ),
]


class BoundaryModule:
    """Runs the System Boundary Definition module."""

    def run(self) -> dict:
        engine = QuestionEngine(BOUNDARY_QUESTIONS)
        print(
            "  This module defines the boundary of your CMMC assessment scope.\n"
            "  A well-defined boundary limits which systems require CMMC controls,\n"
            "  reducing the cost and complexity of compliance.\n"
        )
        return engine.run()
