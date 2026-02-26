"""
Module 2: CUI/FCI Data Flow Analysis
======================================
The most critical module — determines whether CUI or FCI is actually
present in the environment and traces how it flows through systems.

This is the core of scope determination: if CUI/FCI doesn't flow through
a system, that system is likely out of scope.

NIST SP 800-171 Controls addressed:
  AC.1.001 — Limit system access to authorized users
  AC.2.006 — Limit use of portable storage devices
  MP.2.119 — Protect system media containing CUI
  SC.3.177 — Employ cryptographic mechanisms to protect CUI
"""

from scoping_tool.utils.question_engine import QuestionEngine, Question, QuestionType


# ── CUI Category definitions (from 32 CFR 2002 / CUI Registry) ────────────────
CUI_CATEGORIES = [
    "Acquisition & Procurement (e.g., contract data, bid information)",
    "Defense & Military (e.g., technical specs, weapons system data)",
    "Export Controlled (ITAR / EAR controlled technical data)",
    "Financial (e.g., cost/pricing data, budget information)",
    "Intelligence (e.g., threat assessments, SIGINT products)",
    "Law Enforcement Sensitive",
    "Privacy / Personally Identifiable Information (PII)",
    "Proprietary Business Information",
    "Research & Development (pre-decisional R&D data)",
    "Other CUI (specify in report)",
    "I am not sure — need help identifying",
]

DATA_FLOW_QUESTIONS = [
    # ── CUI presence ──────────────────────────────────────────────────────────
    Question(
        id="df_01",
        text=(
            "Does your organization receive, create, process, store, or transmit\n"
            "  any information on behalf of the U.S. federal government?"
        ),
        qtype=QuestionType.YES_NO,
        help_text=(
            "Answer YES if you perform work under any federal contract, "
            "grant, or cooperative agreement that involves government information."
        ),
        nist_controls=["AC.1.001"],
        is_critical=True,
    ),
    Question(
        id="df_02",
        text=(
            "Have you received a DD Form 254 (Contract Security Classification\n"
            "  Specification) or any contract clause referencing DFARS 252.204-7012\n"
            "  (Safeguarding Covered Defense Information)?"
        ),
        qtype=QuestionType.YES_NO,
        help_text=(
            "DFARS 252.204-7012 is the primary clause triggering CMMC requirements. "
            "A DD Form 254 indicates classified or sensitive work."
        ),
        nist_controls=["AC.1.001"],
        is_critical=True,
        depends_on=("df_01", True),
    ),
    Question(
        id="df_03",
        text="What type(s) of government information does your organization handle? (Select all that apply)",
        qtype=QuestionType.MULTI_CHOICE,
        choices=CUI_CATEGORIES,
        help_text=(
            "Select every category that applies. If unsure, select the last option.\n"
            "  The CUI Registry (archives.gov/cui) has the full category list."
        ),
        nist_controls=["MP.2.119"],
        depends_on=("df_01", True),
    ),
    # ── How CUI is received ───────────────────────────────────────────────────
    Question(
        id="df_04",
        text="How does CUI/FCI enter your organization? (Select all that apply)",
        qtype=QuestionType.MULTI_CHOICE,
        choices=[
            "Email (e.g., attachments from contracting officers)",
            "DoD portals / web applications (e.g., PIEE, EDA, SAFE)",
            "Removable media (USB drives, CDs)",
            "Shared network drives / file shares with the government",
            "Video conferencing (e.g., DoD-provided meeting links with shared docs)",
            "Physical documents / mail",
            "We generate CUI ourselves based on contract work",
            "Not sure",
        ],
        depends_on=("df_01", True),
        nist_controls=["AC.2.006", "MP.2.119"],
    ),
    # ── Where CUI is stored ───────────────────────────────────────────────────
    Question(
        id="df_05",
        text="Where is CUI/FCI stored in your environment? (Select all that apply)",
        qtype=QuestionType.MULTI_CHOICE,
        choices=[
            "Employee workstations / laptops (local storage)",
            "On-premises file server / NAS",
            "Microsoft SharePoint / OneDrive for Business",
            "Microsoft Teams (chats, files)",
            "Google Drive",
            "Other cloud storage (Box, Dropbox, etc.)",
            "Email server / cloud email (Exchange, Gmail)",
            "Database (SQL, Oracle, etc.)",
            "Removable media (USB, external drives)",
            "Mobile devices (phones, tablets)",
            "We do not store CUI — process only",
        ],
        depends_on=("df_01", True),
        nist_controls=["MP.2.119", "SC.3.177"],
        is_critical=True,
    ),
    # ── Encryption ────────────────────────────────────────────────────────────
    Question(
        id="df_06",
        text="Is CUI encrypted at rest (when stored)?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — all CUI storage locations use encryption",
            "Yes — some storage locations use encryption",
            "No — CUI is stored without encryption",
            "I am not sure",
        ],
        depends_on=("df_01", True),
        nist_controls=["SC.3.177"],
        gap_flag=True,
    ),
    Question(
        id="df_07",
        text="Is CUI encrypted in transit (when sent over networks or email)?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — TLS/HTTPS/S/MIME used consistently",
            "Yes — some transmissions are encrypted",
            "No — CUI is sent in plaintext",
            "I am not sure",
        ],
        depends_on=("df_01", True),
        nist_controls=["SC.3.177"],
        gap_flag=True,
    ),
    # ── CUI leaving the organization ──────────────────────────────────────────
    Question(
        id="df_08",
        text="Does your organization share or transmit CUI with subcontractors or other third parties?",
        qtype=QuestionType.YES_NO,
        depends_on=("df_01", True),
        help_text="This would extend your CMMC boundary to include those subcontractors.",
        nist_controls=["AC.2.006"],
    ),
    Question(
        id="df_08a",
        text="Do your subcontractors who receive CUI have CMMC certification or documented security controls?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — CMMC certified",
            "Yes — documented controls (SOC 2, ISO 27001, etc.)",
            "No — no known certification",
            "I am not sure",
        ],
        depends_on=("df_08", True),
        nist_controls=["AC.2.006"],
        gap_flag=True,
    ),
    # ── FCI-only check ────────────────────────────────────────────────────────
    Question(
        id="df_09",
        text=(
            "If your organization does NOT handle CUI, do you still handle Federal\n"
            "  Contract Information (FCI) — information provided by or generated for\n"
            "  the government under a contract, not intended for public release?"
        ),
        qtype=QuestionType.YES_NO,
        help_text=(
            "FCI requires CMMC Level 1 at minimum. "
            "Example: a contractor who only receives Statements of Work (non-CUI) still handles FCI."
        ),
        nist_controls=["AC.1.001"],
    ),
]


class DataFlowModule:
    """
    Runs the CUI/FCI Data Flow Analysis module.
    This is the most critical module for determining CMMC scope.
    """

    def run(self) -> dict:
        engine = QuestionEngine(DATA_FLOW_QUESTIONS)
        print(
            "  This module traces how CUI and FCI flows through your environment.\n"
            "  It is the most important section for determining your CMMC scope.\n"
            "\n"
            "  CUI = Controlled Unclassified Information (triggers CMMC Level 2)\n"
            "  FCI = Federal Contract Information (triggers CMMC Level 1 minimum)\n"
        )
        return engine.run()
