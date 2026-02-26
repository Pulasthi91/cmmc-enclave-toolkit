"""
Module 1: System & Asset Inventory
====================================
Gathers information about all systems, hardware, and software
in the contractor's environment to build an initial asset inventory
for CMMC scoping purposes.

NIST SP 800-171 Controls addressed:
  CM.2.061 — Establish and maintain baseline configurations
  CM.2.062 — Establish and maintain a system component inventory
"""

from scoping_tool.utils.question_engine import QuestionEngine, Question, QuestionType


SYSTEM_INVENTORY_QUESTIONS = [
    Question(
        id="si_01",
        text="How many total computing devices (laptops, desktops, servers, VMs) does your organization operate?",
        qtype=QuestionType.CHOICE,
        choices=["1–10", "11–50", "51–200", "201–500", "500+"],
        help_text="Include all devices that employees use for work, regardless of whether they handle government data.",
        nist_controls=["CM.2.062"],
    ),
    Question(
        id="si_02",
        text="Do any of your systems run on cloud infrastructure (AWS, Azure, GCP, etc.)?",
        qtype=QuestionType.YES_NO,
        help_text="This includes SaaS tools (Microsoft 365, Google Workspace), IaaS, or PaaS environments.",
        nist_controls=["CM.2.061", "SC.3.177"],
    ),
    Question(
        id="si_02a",
        text="Which cloud platforms does your organization use? (Select all that apply)",
        qtype=QuestionType.MULTI_CHOICE,
        choices=[
            "Microsoft 365 / Azure",
            "Google Workspace / GCP",
            "Amazon Web Services (AWS)",
            "Other SaaS applications",
            "On-premises only",
        ],
        depends_on=("si_02", True),
        nist_controls=["CM.2.061"],
    ),
    Question(
        id="si_03",
        text="Do you use any Government Furnished Equipment (GFE) or Government Furnished Information (GFI)?",
        qtype=QuestionType.YES_NO,
        help_text="GFE/GFI provided by the DoD may already be covered under separate authorization.",
        nist_controls=["CM.2.062"],
    ),
    Question(
        id="si_04",
        text="Do employees use personal devices (BYOD) for any work-related activities, including email?",
        qtype=QuestionType.YES_NO,
        help_text="Personal devices that access company email or systems may bring CUI into scope.",
        nist_controls=["AC.2.006", "CM.2.061"],
    ),
    Question(
        id="si_05",
        text="Does your organization have a documented system/asset inventory?",
        qtype=QuestionType.YES_NO,
        help_text="NIST 800-171 CM.2.062 requires maintaining a current inventory of organizational systems.",
        nist_controls=["CM.2.062"],
    ),
    Question(
        id="si_06",
        text="How many active employees / users access your IT systems?",
        qtype=QuestionType.CHOICE,
        choices=["1–5", "6–25", "26–100", "101–500", "500+"],
        nist_controls=["AC.1.001"],
    ),
    Question(
        id="si_07",
        text="Do you use any Operational Technology (OT) or Industrial Control Systems (ICS) in your work?",
        qtype=QuestionType.YES_NO,
        help_text="Manufacturing equipment, sensors, or SCADA systems connected to your network may be in scope.",
        nist_controls=["CM.2.062", "SC.3.180"],
    ),
    Question(
        id="si_08",
        text="Do any third-party vendors, subcontractors, or managed service providers have access to your systems?",
        qtype=QuestionType.YES_NO,
        help_text=(
            "Third-party access can extend your CMMC assessment boundary. "
            "If they handle CUI/FCI, they may also need CMMC certification."
        ),
        nist_controls=["AC.2.006", "CM.2.062"],
    ),
    Question(
        id="si_08a",
        text="Do those third parties have their own CMMC certification or documented security controls?",
        qtype=QuestionType.CHOICE,
        choices=[
            "Yes — they are CMMC certified",
            "Yes — they have documented security controls (e.g., SOC 2, ISO 27001)",
            "No — unknown",
            "No — they have no formal certification",
        ],
        depends_on=("si_08", True),
        nist_controls=["AC.2.006"],
    ),
    Question(
        id="si_09",
        text="Do you have network diagrams or data flow diagrams for your environment?",
        qtype=QuestionType.YES_NO,
        help_text="These are required for a CMMC assessment and needed to define your System Security Plan (SSP).",
        nist_controls=["CM.2.061"],
        gap_flag=True,  # Flag as a potential gap if NO
    ),
]


class SystemInventoryModule:
    """
    Runs the System & Asset Inventory question module.
    Returns a dict of {question_id: answer} for all questions answered.
    """

    def run(self) -> dict:
        engine = QuestionEngine(SYSTEM_INVENTORY_QUESTIONS)
        print(
            "  This module helps identify all systems and assets that may fall\n"
            "  within your CMMC assessment boundary.\n"
        )
        return engine.run()
