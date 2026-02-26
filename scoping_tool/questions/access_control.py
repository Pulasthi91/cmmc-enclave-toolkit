"""
Module 4: Access Control & Authentication
==========================================
Evaluates who can access CUI systems and how authentication is implemented.
Access control is one of the most frequently assessed CMMC domains.

NIST SP 800-171 Controls addressed:
  AC.1.001 — Limit system access to authorized users
  AC.1.002 — Limit system access to the types of transactions and functions
  AC.2.005 — Provide privacy and security notices
  AC.2.006 — Limit use of portable storage
  IA.3.083 — Use multifactor authentication for local and network access
  IA.3.085 — Employ replay-resistant authentication mechanisms
"""

from scoping_tool.utils.question_engine import QuestionEngine, Question, QuestionType


ACCESS_CONTROL_QUESTIONS = [
    Question(
        id="ac_01",
        text="Does your organization maintain a formal list of authorized users for CUI systems?",
        qtype=QuestionType.YES_NO,
        help_text=(
            "NIST AC.1.001 requires that access to CUI systems be limited to\n"
            "  authorized users with a documented need to access that information."
        ),
        nist_controls=["AC.1.001"],
        gap_flag=True,
    ),
    Question(
        id="ac_02",
        text="Is Multi-Factor Authentication (MFA) enforced for all accounts that can access CUI?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — MFA enforced for all users (local and remote)",
            "Yes — MFA enforced for remote access only",
            "Yes — MFA enforced for privileged/admin accounts only",
            "No — password-only authentication is used",
            "Partially implemented",
        ],
        help_text=(
            "NIST IA.3.083 requires MFA for local and network access to CUI systems.\n"
            "  This is one of the most commonly failed CMMC controls for SMBs."
        ),
        nist_controls=["IA.3.083"],
        is_critical=True,
        gap_flag=True,
    ),
    Question(
        id="ac_03",
        text="Are privileged accounts (admins) separated from standard user accounts?",
        qtype=QuestionType.YES_NO,
        help_text=(
            "Admins should use a dedicated admin account for privileged tasks "
            "and a separate standard account for day-to-day work."
        ),
        nist_controls=["AC.1.002"],
        gap_flag=True,
    ),
    Question(
        id="ac_04",
        text="Does your organization enforce a password complexity and length policy?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — meets NIST 800-63B requirements (min 8 chars, complexity)",
            "Yes — but below NIST recommendations",
            "No formal policy — users choose their own passwords",
            "Not sure",
        ],
        nist_controls=["IA.3.083"],
        gap_flag=True,
    ),
    Question(
        id="ac_05",
        text="Is remote access to CUI systems (VPN, RDP, SSH) controlled and logged?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — VPN with MFA + full logging",
            "Yes — VPN but no MFA",
            "Yes — direct RDP/SSH (no VPN)",
            "No formal remote access controls",
            "No remote access allowed",
        ],
        nist_controls=["AC.1.001", "IA.3.085"],
        is_critical=True,
        gap_flag=True,
    ),
    Question(
        id="ac_06",
        text="Are user accounts reviewed and de-provisioned promptly when employees leave or change roles?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — formal offboarding process with immediate account termination",
            "Yes — accounts removed within 1–7 days",
            "No formal process — accounts may remain active",
            "Not sure",
        ],
        nist_controls=["AC.1.001"],
        gap_flag=True,
    ),
    Question(
        id="ac_07",
        text="Are user activities on CUI systems logged and monitored?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — comprehensive logging with alerting (SIEM)",
            "Yes — basic logging (event logs, auditd)",
            "Partial — some systems are logged",
            "No logging in place",
        ],
        help_text=(
            "CMMC Level 2 requires audit logging (AU controls). "
            "Logs must be protected from unauthorized access or modification."
        ),
        nist_controls=["AU.2.041", "AU.2.042"],
        gap_flag=True,
    ),
    Question(
        id="ac_08",
        text="Is the use of removable media (USB drives, external hard drives) controlled on CUI systems?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — USB ports are disabled or blocked by policy + technical control",
            "Yes — policy exists but not technically enforced",
            "No — unrestricted USB usage",
            "Not sure",
        ],
        nist_controls=["AC.2.006", "MP.2.119"],
        gap_flag=True,
    ),
    Question(
        id="ac_09",
        text="Do personnel with access to CUI receive regular cybersecurity awareness training?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — annual formal training with documentation",
            "Yes — informal training (ad hoc)",
            "No formal training program",
        ],
        help_text="NIST AT.2.056 requires security awareness training for all users.",
        nist_controls=["AT.2.056"],
        gap_flag=True,
    ),
    Question(
        id="ac_10",
        text="Does your organization have a written acceptable use policy (AUP) for CUI systems?",
        qtype=QuestionType.YES_NO,
        nist_controls=["AC.2.005"],
        gap_flag=True,
    ),
]


class AccessControlModule:
    """Runs the Access Control & Authentication module."""

    def run(self) -> dict:
        engine = QuestionEngine(ACCESS_CONTROL_QUESTIONS)
        print(
            "  This module evaluates your access control and authentication\n"
            "  posture — one of the most frequently assessed CMMC domains.\n"
        )
        return engine.run()
