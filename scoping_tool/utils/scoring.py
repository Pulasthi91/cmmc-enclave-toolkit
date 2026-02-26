"""
Scope Scoring Engine
=====================
Analyzes all module responses and produces a structured scope score:
  - CMMC level required
  - Whether CUI/FCI is confirmed in scope
  - Estimated number of in-scope systems
  - Whether an enclave is recommended
  - List of identified compliance gaps
  - NIST 800-171 control gap summary
"""

from typing import Any, Dict, List, Optional


class ScopeScorer:
    """
    Calculates a comprehensive CMMC scope score from assessment responses.
    """

    def __init__(self, responses: Dict[str, Dict]):
        self.r = responses  # All module responses
        # Flatten to a single dict for easy lookup
        self.flat: Dict[str, Any] = {}
        for module_data in responses.values():
            if isinstance(module_data, dict):
                self.flat.update(module_data)

    def calculate(self) -> Dict:
        cui_in_scope = self._cui_in_scope()
        fci_in_scope = self._fci_in_scope()
        cmmc_level   = self._cmmc_level(cui_in_scope, fci_in_scope)
        gaps         = self._identify_gaps()
        enclave_rec  = self._enclave_recommended()
        scope_sys    = self._estimate_systems_in_scope()

        return {
            "cui_in_scope":            cui_in_scope,
            "fci_in_scope":            fci_in_scope,
            "cmmc_level_required":     cmmc_level,
            "enclave_recommended":     enclave_rec,
            "systems_in_scope":        scope_sys,
            "compliance_gaps":         gaps,
            "gap_count":               len(gaps),
            "high_priority_gaps":      [g for g in gaps if g["priority"] == "HIGH"],
            "nist_control_gaps":       self._nist_control_gaps(gaps),
            "scope_reduction_possible": self._scope_reduction_possible(),
        }

    # ── CUI / FCI determination ────────────────────────────────────────────────
    def _cui_in_scope(self) -> bool:
        """CUI is in scope if the contractor confirmed handling government info
        AND either has DFARS clause OR identified CUI categories."""
        handles_gov   = self.flat.get("df_01") is True
        has_dfars     = self.flat.get("df_02") is True
        cui_cats      = self.flat.get("df_03", [])
        has_cui_cats  = bool(cui_cats) and "I am not sure" not in (cui_cats or [])

        return handles_gov and (has_dfars or has_cui_cats)

    def _fci_in_scope(self) -> bool:
        """FCI is in scope if they handle government info at all."""
        return (
            self.flat.get("df_01") is True or
            self.flat.get("df_09") is True
        )

    def _cmmc_level(self, cui: bool, fci: bool) -> str:
        if cui:
            return "Level 2"
        if fci:
            return "Level 1"
        return "Not Required (verify contract requirements)"

    # ── Gaps ──────────────────────────────────────────────────────────────────
    def _identify_gaps(self) -> List[Dict]:
        gaps = []

        def gap(control, title, detail, priority="MEDIUM"):
            gaps.append({
                "nist_control": control,
                "title":        title,
                "detail":       detail,
                "priority":     priority,
            })

        # MFA
        mfa = self.flat.get("ac_02", "")
        if "No — password" in str(mfa) or "Partial" in str(mfa):
            gap("IA.3.083", "Multi-Factor Authentication Not Fully Implemented",
                "MFA is required for all access to CUI systems under NIST 800-171 Rev 3 IA.3.083. "
                "Password-only authentication is not compliant.",
                priority="HIGH")

        # Remote access
        remote = self.flat.get("ac_05", "")
        if "no MFA" in str(remote) or "direct RDP" in str(remote):
            gap("AC.1.001 / IA.3.083",
                "Remote Access Lacks MFA or VPN Protection",
                "Remote access to CUI systems must use MFA and encrypted channels (VPN). "
                "Direct RDP/SSH without VPN is a critical exposure.",
                priority="HIGH")

        # Encryption at rest
        enc_rest = self.flat.get("df_06", "")
        if "No" in str(enc_rest) or "not sure" in str(enc_rest).lower():
            gap("SC.3.177", "CUI Not Encrypted at Rest",
                "NIST SC.3.177 requires CUI to be encrypted at rest using FIPS 140-2 validated "
                "cryptographic modules. Unencrypted CUI storage is a critical gap.",
                priority="HIGH")

        # Encryption in transit
        enc_transit = self.flat.get("df_07", "")
        if "plaintext" in str(enc_transit).lower() or "not sure" in str(enc_transit).lower():
            gap("SC.3.177", "CUI Not Encrypted in Transit",
                "CUI transmitted over networks must be encrypted (TLS 1.2+ or equivalent). "
                "Plaintext transmission is a critical compliance failure.",
                priority="HIGH")

        # Network separation
        boundary = self.flat.get("bd_02", "")
        if "No — all systems share" in str(boundary):
            gap("SC.3.180", "No Network Segmentation for CUI Systems",
                "CUI systems should be on an isolated network segment or enclave. "
                "Flat networks where all systems share the same segment expand CMMC scope significantly.",
                priority="HIGH")

        # Shared services
        if self.flat.get("bd_06") is True:
            shared = self.flat.get("bd_06a", [])
            if shared and "None" not in str(shared):
                gap("SC.3.180 / AC.1.001",
                    "Shared Services Span CUI and Non-CUI Environments",
                    f"Shared services ({', '.join(shared) if isinstance(shared, list) else shared}) "
                    "that span both CUI and non-CUI environments bring additional systems into CMMC scope.",
                    priority="HIGH")

        # SSP missing
        if self.flat.get("bd_07") is False:
            gap("CM.2.061", "No System Security Plan (SSP)",
                "A written SSP documenting your system boundary, security controls, and NIST 800-171 "
                "implementation is required for CMMC Level 2 assessment.",
                priority="HIGH")

        # SPRS not submitted
        if self.flat.get("bd_08") is False:
            gap("CM.2.061", "SPRS Score Not Submitted",
                "DoD contractors must submit a NIST SP 800-171 self-assessment score to SPRS. "
                "Failure to do so may violate contract requirements.",
                priority="MEDIUM")

        # Logging
        logging = self.flat.get("ac_07", "")
        if "No logging" in str(logging):
            gap("AU.2.041", "No Audit Logging on CUI Systems",
                "NIST AU.2.041 requires audit records for user activities on CUI systems. "
                "No logging means you cannot detect or investigate security incidents.",
                priority="HIGH")

        # MFA for privileged
        if self.flat.get("ac_03") is False:
            gap("AC.1.002", "No Separation of Privileged and Standard Accounts",
                "Admin/privileged accounts should be separate from standard user accounts "
                "to limit the blast radius of a compromised credential.",
                priority="MEDIUM")

        # USB control
        usb = self.flat.get("ac_08", "")
        if "unrestricted" in str(usb).lower() or "No —" in str(usb):
            gap("AC.2.006 / MP.2.119", "Removable Media Not Controlled",
                "USB and removable media use on CUI systems must be restricted and controlled. "
                "Unrestricted USB access is a common data exfiltration vector.",
                priority="MEDIUM")

        # BYOD
        if self.flat.get("si_04") is True:
            gap("AC.1.001 / MP.2.119",
                "Personal Devices (BYOD) Used for Work Activities",
                "Personal devices accessing company email or systems may bring CUI into an uncontrolled "
                "environment. BYOD policies and MDM controls are required.",
                priority="MEDIUM")

        # Awareness training
        training = self.flat.get("ac_09", "")
        if "No formal" in str(training):
            gap("AT.2.056", "No Formal Cybersecurity Awareness Training Program",
                "NIST AT.2.056 requires all users with access to CUI systems to receive "
                "periodic security awareness training.",
                priority="MEDIUM")

        # Subcontractors without CMMC
        sub = self.flat.get("df_08a", "")
        if sub and ("no known" in str(sub).lower() or "not sure" in str(sub).lower()):
            gap("AC.2.006", "Subcontractors Handling CUI Lack CMMC Certification",
                "Subcontractors who receive CUI may be required to obtain their own CMMC certification "
                "under the flow-down requirements of DFARS 252.204-7021.",
                priority="HIGH")

        return gaps

    # ── Enclave recommendation ─────────────────────────────────────────────────
    def _enclave_recommended(self) -> bool:
        """Recommend an enclave if:
        - CUI is in scope AND
        - No existing enclave AND
        - Not every system is a CUI system (i.e., scope reduction is possible)
        """
        cui        = self._cui_in_scope()
        no_enclave = self.flat.get("bd_03") is False or self.flat.get("bd_03") is None
        not_all    = self.flat.get("bd_01") is False
        willing    = self.flat.get("bd_04") is not False  # Default to recommend

        return cui and no_enclave and (not_all or willing)

    # ── Estimated systems in scope ─────────────────────────────────────────────
    def _estimate_systems_in_scope(self) -> str:
        """Rough estimate based on device count and separation answers."""
        total_map = {
            "1–10": 10, "11–50": 50, "51–200": 200, "201–500": 500, "500+": 999
        }
        total = total_map.get(self.flat.get("si_01", "1–10"), 10)

        # If entire environment is in scope
        if self.flat.get("bd_01") is True:
            return str(total)

        # If enclave or separation exists
        boundary = self.flat.get("bd_02", "")
        if "physically separate" in str(boundary) or "logically separated" in str(boundary):
            return f"~{max(1, total // 5)} (estimated enclave systems only)"

        if "Partially" in str(boundary):
            return f"~{max(1, total // 2)} (estimated)"

        return str(total)

    # ── Scope reduction possible ───────────────────────────────────────────────
    def _scope_reduction_possible(self) -> bool:
        return (
            self.flat.get("bd_01") is False and
            (
                self.flat.get("bd_01a") is True or
                self.flat.get("bd_04") is True
            )
        )

    # ── NIST control gap summary ───────────────────────────────────────────────
    def _nist_control_gaps(self, gaps: List[Dict]) -> List[str]:
        controls = set()
        for gap in gaps:
            for c in gap["nist_control"].split("/"):
                controls.add(c.strip())
        return sorted(controls)
