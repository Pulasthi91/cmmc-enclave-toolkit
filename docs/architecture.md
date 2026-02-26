# CUI Enclave Architecture

## Overview

This document describes the architecture of the CMMC Enclave Toolkit's Docker-based CUI enclave. The design implements a cost-effective, open-source approach to CUI environment isolation that enables small and medium-sized DoD contractors to achieve CMMC Level 2 scope reduction without commercial managed enclave services.

---

## Design Principles

The enclave architecture is built on five core principles derived from NIST SP 800-171 Rev 3 and CMMC Level 2 requirements:

**1. Least Privilege:** Every container runs with only the capabilities required for its function. Unnecessary Linux capabilities are dropped at the container level.

**2. Defense in Depth:** Multiple overlapping controls (network isolation, VPN encryption, host hardening, audit logging) ensure that no single failure creates a CUI exposure.

**3. Scope Minimization:** By isolating all CUI processing to the enclave, the CMMC assessment boundary is limited to enclave components only. Systems outside the enclave do not require CMMC controls.

**4. Auditability:** Every action within the enclave is logged to an immutable audit container. Logs cannot be deleted or modified by enclave users.

**5. Affordability:** The entire stack runs on commodity x86_64 Linux hardware. A system with 8GB RAM and a 4-core CPU is sufficient for a small contractor deployment.

---

## Network Architecture

```
INTERNET
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│  DOCKER HOST (Hardened Ubuntu 22.04 / RHEL 8)                │
│  host_harden.sh applied | auditd running | ufw enabled        │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  std-net: 172.19.0.0/24 (CORPORATE NETWORK SEGMENT)    │  │
│  │                                                         │  │
│  │  ┌──────────────────────┐                              │  │
│  │  │   VPN Gateway        │ ◄── UDP :51820 (WireGuard)  │  │
│  │  │   172.19.0.2         │     Encrypted tunnel only    │  │
│  │  │   172.20.0.2 ──────► │──┐                          │  │
│  │  └──────────────────────┘  │                          │  │
│  └─────────────────────────────│────────────────────────┘  │
│                                │                             │
│  ┌─────────────────────────────▼────────────────────────┐   │
│  │  cui-net: 172.20.0.0/24  (CUI ENCLAVE — ISOLATED)   │   │
│  │  internal: true  ◄── NO DIRECT INTERNET ACCESS       │   │
│  │                                                       │   │
│  │  ┌─────────────────┐   ┌───────────────────────┐    │   │
│  │  │ CUI Workstation │   │   Health Monitor       │    │   │
│  │  │ 172.20.0.10     │   │   172.20.0.5           │    │   │
│  │  │                 │   └────────────┬──────────┘    │   │
│  │  │ cui-documents   │                │               │   │
│  │  │ (encrypted vol) │                │               │   │
│  │  └────────┬────────┘                │               │   │
│  └───────────│────────────────────────│──────────────┘   │
│              │                         │                   │
│  ┌───────────▼─────────────────────────▼────────────────┐  │
│  │  mgmt-net: 172.18.0.0/24 (MANAGEMENT PLANE)         │  │
│  │  internal: true                                      │  │
│  │                                                      │  │
│  │  ┌────────────────────────────────┐                 │  │
│  │  │  Audit Logger (rsyslog)        │                 │  │
│  │  │  172.18.0.10                   │                 │  │
│  │  │  /var/log/cui-audit/ ◄── 90d  │                 │  │
│  │  │  Write-only from other ctrs    │                 │  │
│  │  └────────────────────────────────┘                 │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## Component Details

### VPN Gateway

**Image:** Custom WireGuard image (Dockerfile.vpn)
**Purpose:** Provides the sole encrypted entry point into the CUI enclave.

The VPN Gateway is the only container with connectivity to both the corporate network (`std-net`) and the CUI enclave (`cui-net`). All user access to CUI systems must traverse this gateway via WireGuard VPN. WireGuard was selected over OpenVPN because:
- Smaller attack surface (fewer lines of code)
- Better performance on commodity hardware
- Native Linux kernel integration
- FIPS-compatible cipher support (ChaCha20-Poly1305)

**NIST Controls Addressed:**
- SC.3.177 — Employ cryptographic mechanisms to protect CUI during transmission
- AC.1.001 — Limit system access to authorized users
- IA.3.083 — Use multifactor authentication (enforced at VPN credential level)

---

### CUI Workstation

**Image:** Hardened Ubuntu 22.04 (Dockerfile.cui-host)
**Purpose:** The only container where CUI documents are processed.

The workstation container has no direct internet access — all traffic is blocked at the Docker network level (`internal: true`). CUI documents are stored on an encrypted Docker volume (`cui-data`). The container runs as a non-root user (`cuiuser`) with all unnecessary Linux capabilities dropped.

Key security controls:
- `no-new-privileges:true` — prevents privilege escalation
- `cap_drop: ALL` — removes all capabilities, re-adds only required ones
- `security_opt: apparmor:docker-default` — AppArmor profile applied
- auditd rules loaded from `configs/auditd.rules` — all file access logged

**NIST Controls Addressed:**
- AC.1.001 — Limit access to authorized users
- AC.1.002 — Limit access by type of transaction
- CM.2.061 — Establish baseline configurations
- SC.3.180 — Implement subnetworks for system components
- AU.2.041 — Create and retain audit logs

---

### Audit Logger

**Image:** Custom rsyslog image (Dockerfile.audit)
**Purpose:** Immutable, centralized audit log store for all enclave events.

All enclave containers ship logs to the audit logger via syslog over the management network (`mgmt-net`). The audit logger stores logs to a persistent volume with 90-day retention by default. The container has no outbound connectivity — it only receives logs. This ensures that a compromised workstation container cannot delete audit evidence.

**NIST Controls Addressed:**
- AU.2.041 — Create and retain system audit logs
- AU.2.042 — Ensure audit log processes cannot be denied
- AU.3.045 — Review and update logged events

---

## CMMC Scope Reduction

The primary purpose of this enclave design is **CMMC scope reduction**.

Without an enclave, every system in a contractor's environment that can communicate with a CUI-handling system may be pulled into CMMC scope — including workstations, file servers, email servers, DNS, DHCP, and Active Directory. This dramatically increases the number of systems requiring NIST 800-171 controls and the cost of assessment.

With this enclave:

| Item | Without Enclave | With This Enclave |
|------|----------------|-------------------|
| Systems in CMMC scope | All systems on the network | Only enclave containers + Docker host |
| NIST controls to implement | Across entire environment | Scoped to enclave boundary |
| Estimated assessment effort | High (weeks) | Reduced (days) |
| Commercial enclave cost | $50,000–$300,000/year | $0 (open-source) |

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Storage | 100 GB SSD | 500 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Docker | 24.x+ | Latest stable |

A small contractor can run this entire stack on a dedicated mini-PC (e.g., Intel NUC, Dell OptiPlex Mini) costing $300–$800, versus $50,000+ for commercial managed enclave services.

---

## Security Limitations and Disclaimers

This toolkit provides a strong foundational security architecture, but users should be aware of the following limitations:

1. **Container escape risks:** Docker containers are not as isolated as VMs. If a critical Docker vulnerability enables a container escape, the Docker host could be compromised. Keeping the host OS and Docker Engine patched is essential.

2. **Host OS security is critical:** The security of the enclave depends heavily on the hardened host. Run `host_harden.sh` and keep the system patched.

3. **This is not a substitute for C3PAO assessment:** Official CMMC Level 2 certification requires assessment by a Certified Third-Party Assessment Organization (C3PAO). This toolkit helps you prepare and reduce scope — it does not certify compliance.

4. **WireGuard is not FIPS-validated by default:** Organizations subject to FIPS 140-2 requirements should verify their WireGuard implementation uses FIPS-validated modules or substitute an approved VPN solution.

---

## References

- [NIST SP 800-171 Rev 3](https://csrc.nist.gov/publications/detail/sp/800-171/rev-3/final)
- [CMMC Final Rule — 32 C.F.R. Part 170](https://www.federalregister.gov/documents/2024/10/15/2024-21517/cybersecurity-maturity-model-certification-cmmc-program)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [WireGuard Protocol](https://www.wireguard.com/papers/wireguard.pdf)
- [CMMC Accreditation Body](https://cyberab.org)
