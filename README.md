# 🔒 CMMC Enclave Toolkit

**An open-source, affordable CUI enclave architecture and scoping toolkit for small and medium-sized DoD contractors pursuing CMMC Level 2 compliance.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![NIST SP 800-171](https://img.shields.io/badge/NIST%20SP%20800--171-Rev%203-green)](https://csrc.nist.gov/publications/detail/sp/800-171/rev-3/final)
[![CMMC Level 2](https://img.shields.io/badge/CMMC-Level%202-orange)](https://www.acq.osd.mil/cmmc/)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-yellow)](https://www.python.org/)

---

## 🎯 Problem Statement

The Department of Defense's Cybersecurity Maturity Model Certification (CMMC) program requires approximately **80,000–100,000 small and medium-sized businesses (SMBs)** in the Defense Industrial Base (DIB) to achieve verified cybersecurity compliance under NIST SP 800-171.

The primary challenge for SMBs:

- **Commercial CUI enclave solutions cost $50,000–$300,000+** per year — unaffordable for most small contractors
- **No standardized open-source methodology exists** for accurately scoping CUI/FCI environments
- Contractors either over-scope (wasting resources) or under-scope (creating security gaps)

**This toolkit solves both problems — for free.**

---

## 🛠️ What This Toolkit Provides

| Component | Description |
|-----------|-------------|
| 🗂️ **CUI/FCI Scoping Tool** | Python CLI that walks contractors through a structured questionnaire to accurately identify and document their CMMC assessment scope |
| 🐳 **Docker CUI Enclave** | Ready-to-deploy Docker Compose stack implementing an isolated CUI processing environment on commodity Linux hardware |
| 📋 **NIST 800-171 Control Mapping** | Enclave architecture mapped to all 110 NIST SP 800-171 Rev 3 controls |
| 📄 **Scoping Report Generator** | Auto-generates a formatted PDF/Markdown scoping report for CMMC assessment submission |
| 🔧 **Hardening Scripts** | Bash scripts for Linux host hardening aligned to CMMC Level 2 requirements |

---

## 🚀 Quick Start

### 1. Run the CUI/FCI Scoping Assessment

```bash
# Clone the repository
git clone https://github.com/Pulasthi91/cmmc-enclave-toolkit.git
cd cmmc-enclave-toolkit

# Install dependencies
pip install -r requirements.txt

# Run the interactive scoping questionnaire
python scoping_tool/scope_assessment.py
```

The tool will guide you through a structured questionnaire and generate a scoping report in `reports/`.

### 2. Deploy the CUI Enclave (Docker)

```bash
# Review and configure environment variables
cp enclave/.env.example enclave/.env
nano enclave/.env

# Build and launch the enclave stack
cd enclave
docker compose up -d

# Verify services are running
docker compose ps
```

---

## 📂 Repository Structure

```
cmmc-enclave-toolkit/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
├── requirements.txt
│
├── scoping_tool/                  # CUI/FCI Scoping Assessment CLI
│   ├── scope_assessment.py        # Main CLI entry point
│   ├── questions/
│   │   ├── system_inventory.py    # Asset & system questions
│   │   ├── data_flow.py           # CUI/FCI data flow questions
│   │   ├── boundary.py            # System boundary questions
│   │   └── access_control.py     # User access questions
│   ├── reports/
│   │   ├── report_generator.py    # Report generation engine
│   │   └── templates/             # Report templates
│   └── utils/
│       ├── scoring.py             # Scope scoring logic
│       └── nist_mapper.py         # NIST 800-171 control mapper
│
├── enclave/                       # Docker CUI Enclave Stack
│   ├── docker-compose.yml         # Main compose file
│   ├── .env.example               # Environment variable template
│   ├── docker/
│   │   ├── Dockerfile.cui-host    # Hardened CUI host image
│   │   ├── Dockerfile.audit       # Audit/logging container
│   │   └── Dockerfile.vpn         # VPN gateway container
│   ├── configs/
│   │   ├── auditd.rules           # Linux audit rules (NIST AC/AU controls)
│   │   ├── sysctl.conf            # Kernel hardening parameters
│   │   ├── pam.d/                 # PAM authentication config
│   │   └── rsyslog.conf           # Centralized logging config
│   └── scripts/
│       ├── host_harden.sh         # Linux host hardening script
│       ├── network_segmentation.sh # Network isolation setup
│       └── verify_controls.sh     # Post-deployment control verification
│
├── docs/
│   ├── architecture.md            # Enclave architecture overview
│   ├── nist-control-mapping.md    # Full NIST 800-171 control mapping
│   ├── deployment-guide.md        # Step-by-step deployment guide
│   ├── scoping-guide.md           # How to use the scoping tool
│   └── faq.md                     # Common questions
│
└── tests/
    ├── test_scoping.py            # Scoping tool unit tests
    └── test_controls.py           # Control verification tests
```

---

## 🏗️ Enclave Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  INTERNET / CORPORATE NETWORK        │
└──────────────────────────┬──────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  VPN Gateway │  (WireGuard)
                    │  Container  │
                    └──────┬──────┘
                           │  Encrypted tunnel only
              ┌────────────▼────────────┐
              │     CUI ENCLAVE         │  Docker network: cui-net
              │  (Isolated Subnet)      │  172.20.0.0/24
              │                         │
              │  ┌─────────────────┐   │
              │  │  CUI Workstation │   │  Hardened Ubuntu 22.04
              │  │  Container      │   │  No internet access
              │  └────────┬────────┘   │
              │           │            │
              │  ┌────────▼────────┐   │
              │  │  Audit & Log    │   │  auditd + rsyslog
              │  │  Container      │   │  Immutable log store
              │  └─────────────────┘   │
              └─────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   NON-CUI NETWORK       │  Docker network: std-net
              │   (Standard systems)    │  172.19.0.0/24
              └─────────────────────────┘
```

The enclave isolates CUI processing to a dedicated Docker network with no direct internet access, enforced through iptables rules and Docker network policies. All access is via encrypted VPN tunnel. Audit logs are shipped to an immutable syslog container.

---

## 📋 NIST SP 800-171 Control Coverage

This toolkit addresses controls across the following NIST SP 800-171 Rev 3 families:

| Control Family | Controls Addressed | Implementation |
|---------------|-------------------|----------------|
| Access Control (AC) | AC.1.001 – AC.2.006 | PAM config, Docker user namespaces |
| Audit & Accountability (AU) | AU.2.041 – AU.3.045 | auditd rules, centralized logging |
| Configuration Management (CM) | CM.2.061 – CM.3.068 | Dockerfile hardening, sysctl |
| Identification & Authentication (IA) | IA.3.083 – IA.3.086 | MFA enforcement, PAM |
| System & Comm. Protection (SC) | SC.3.177 – SC.3.187 | Network segmentation, TLS |
| System & Info. Integrity (SI) | SI.1.210 – SI.2.214 | File integrity, patch management |

See [docs/nist-control-mapping.md](docs/nist-control-mapping.md) for the full mapping.

---

## ⚠️ Disclaimer

This toolkit is provided as a **starting point and educational resource** for organizations pursuing CMMC compliance. It is **not a substitute for a formal CMMC assessment** by a Certified Third-Party Assessment Organization (C3PAO). Organizations must validate their implementation against CMMC requirements with qualified assessors.

---

## 🤝 Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests. Areas where help is most needed:

- Additional scoping question modules
- Windows Server enclave variant
- Terraform/cloud deployment option
- Translation of documentation

---

## 📜 License

MIT License — see [LICENSE](LICENSE). Free for use by any organization.

---

## 👤 Author

**Pulasthi Batuwita**
Cybersecurity Analyst | CMMC Practitioner | (ISC)² SSCP | RHCSA
- Website: [thevulnerabilitynews.com](https://thevulnerabilitynews.com)
- LinkedIn: [linkedin.com/in/pulasthibatuwita9](https://linkedin.com/in/pulasthibatuwita9)

---

## 📚 References

- [CMMC Program Overview — DoD](https://www.acq.osd.mil/cmmc/)
- [NIST SP 800-171 Rev 3](https://csrc.nist.gov/publications/detail/sp/800-171/rev-3/final)
- [CMMC Final Rule — 32 C.F.R. Part 170](https://www.federalregister.gov/documents/2024/10/15/2024-21517/cybersecurity-maturity-model-certification-cmmc-program)
- [CUI Registry — National Archives](https://www.archives.gov/cui)
- [CMMC Accreditation Body](https://cyberab.org)
