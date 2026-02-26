#!/usr/bin/env bash
# =============================================================================
# CMMC Enclave Toolkit — Linux Host Hardening Script
# =============================================================================
# Hardens a Linux host (Ubuntu 22.04 / RHEL 8+) running the CUI enclave to
# align with NIST SP 800-171 Rev 3 requirements.
#
# Usage (run as root on the Docker host):
#   sudo bash host_harden.sh
#   sudo bash host_harden.sh --check-only    # Audit without making changes
#
# NIST Controls addressed:
#   CM.2.061 — Establish baseline configurations
#   CM.3.068 — Restrict, disable, or prevent the use of nonessential programs
#   SI.1.210 — Identify, report, and correct information and system flaws
#   AC.1.001 — Limit system access to authorized users
#   AU.2.041 — Create and retain system audit logs
#   IA.3.083 — Use multifactor authentication
#
# Author:  Pulasthi Batuwita
# License: MIT
# =============================================================================

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

CHECK_ONLY=false
PASS=0; FAIL=0; WARN=0

# ── Parse args ────────────────────────────────────────────────────────────────
for arg in "$@"; do
  [[ "$arg" == "--check-only" ]] && CHECK_ONLY=true
done

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
ok()      { echo -e "${GREEN}[PASS]${RESET}  $*"; ((PASS++)); }
fail()    { echo -e "${RED}[FAIL]${RESET}  $*"; ((FAIL++)); }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; ((WARN++)); }
section() { echo -e "\n${BOLD}${CYAN}── $* ${RESET}"; }

apply() {
  # apply <description> <command...>
  local desc="$1"; shift
  if $CHECK_ONLY; then
    warn "CHECK ONLY: Would apply: $desc"
  else
    info "Applying: $desc"
    eval "$@" && ok "$desc" || fail "Failed: $desc"
  fi
}

require_root() {
  [[ $EUID -eq 0 ]] || { echo -e "${RED}This script must be run as root.${RESET}"; exit 1; }
}

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "  CMMC Enclave Toolkit — Linux Host Hardening"
echo "  NIST SP 800-171 Rev 3 | CMMC Level 2"
echo -e "  Mode: $([ "$CHECK_ONLY" = true ] && echo 'AUDIT ONLY' || echo 'APPLY CHANGES')${RESET}"
echo ""

require_root

# ─────────────────────────────────────────────────────────────────────────────
section "1. System Updates (SI.1.210)"
# ─────────────────────────────────────────────────────────────────────────────

if command -v apt-get &>/dev/null; then
  apply "Update package lists" "apt-get update -qq"
  apply "Apply security updates" "DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -qq"
  apply "Install security utilities" \
    "apt-get install -y -qq auditd audispd-plugins ufw fail2ban aide libpam-pwquality"
elif command -v dnf &>/dev/null; then
  apply "Apply security updates (DNF)" "dnf update --security -y -q"
  apply "Install security utilities (DNF)" \
    "dnf install -y audit aide fail2ban"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "2. Kernel Hardening via sysctl (SC.3.183, SC.3.180)"
# ─────────────────────────────────────────────────────────────────────────────

SYSCTL_FILE="/etc/sysctl.d/99-cmmc-hardening.conf"

if ! $CHECK_ONLY; then
cat > "$SYSCTL_FILE" << 'EOF'
# CMMC Enclave Toolkit — Kernel Hardening
# NIST SP 800-171: SC.3.183, SC.3.180, SC.3.187

# ── Network hardening ──────────────────────────────────────────────────────
# Disable IP source routing (prevent spoofing)
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Disable ICMP redirects (prevent MITM via redirect attacks)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Enable reverse path filtering (prevent IP spoofing)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore bogus ICMP error responses
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Enable SYN cookies (prevent SYN flood attacks)
net.ipv4.tcp_syncookies = 1

# Disable IPv6 if not needed (reduce attack surface)
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# ── Process hardening ──────────────────────────────────────────────────────
# Restrict ptrace (prevent process injection)
kernel.yama.ptrace_scope = 1

# Restrict kernel log access (prevent info disclosure)
kernel.dmesg_restrict = 1

# Restrict kernel pointer exposure
kernel.kptr_restrict = 2

# Disable magic SysRq key
kernel.sysrq = 0

# ── File system hardening ──────────────────────────────────────────────────
# Prevent hard links to files user doesn't own
fs.protected_hardlinks = 1
fs.protected_symlinks = 1

# Restrict core dumps (prevent sensitive data in dumps)
fs.suid_dumpable = 0
EOF
  apply "Apply kernel hardening parameters" "sysctl --system -q"
  ok "Kernel hardening configuration written to $SYSCTL_FILE"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "3. SSH Hardening (AC.1.001, IA.3.083)"
# ─────────────────────────────────────────────────────────────────────────────

SSH_CONFIG="/etc/ssh/sshd_config.d/99-cmmc.conf"

if ! $CHECK_ONLY; then
cat > "$SSH_CONFIG" << 'EOF'
# CMMC Enclave Toolkit — SSH Hardening
# NIST SP 800-171: AC.1.001, IA.3.083, IA.3.085

# Disable root login
PermitRootLogin no

# Disable password authentication (key-based only)
PasswordAuthentication no
ChallengeResponseAuthentication no
PermitEmptyPasswords no

# Disable X11 forwarding
X11Forwarding no

# Disable TCP forwarding (unless needed for VPN)
AllowTcpForwarding no
AllowAgentForwarding no

# Use strong ciphers and MACs
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512

# Connection limits
MaxAuthTries 4
MaxSessions 3
LoginGraceTime 30

# Log level for audit compliance
LogLevel VERBOSE

# Disconnect idle sessions
ClientAliveInterval 300
ClientAliveCountMax 3
EOF
  apply "Restart SSH to apply hardening" "systemctl restart sshd || systemctl restart ssh"
  ok "SSH configuration hardened: $SSH_CONFIG"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "4. Audit Logging (AU.2.041, AU.2.042, AU.3.045)"
# ─────────────────────────────────────────────────────────────────────────────

AUDIT_RULES="/etc/audit/rules.d/99-cmmc.rules"

if ! $CHECK_ONLY; then
cat > "$AUDIT_RULES" << 'EOF'
# CMMC Enclave Toolkit — Audit Rules
# NIST SP 800-171: AU.2.041, AU.2.042, AU.3.045

# Remove all existing rules and set buffer size
-D
-b 8192

# Ensure log immutability — rules cannot be changed at runtime
-e 2

# ── Privileged command execution ───────────────────────────────────────────
-a always,exit -F path=/usr/bin/sudo -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/su -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/passwd -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged

# ── Authentication events ──────────────────────────────────────────────────
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k identity
-w /etc/sudoers.d/ -p wa -k identity

# ── Login/logout events ────────────────────────────────────────────────────
-w /var/log/lastlog -p wa -k logins
-w /var/run/faillock/ -p wa -k logins
-w /var/log/faillog -p wa -k logins

# ── File access (CUI directory) ────────────────────────────────────────────
-w /home/cuiuser/ -p rwxa -k cui-access
-w /opt/cui-data/ -p rwxa -k cui-access

# ── Network configuration changes ─────────────────────────────────────────
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k network-modification
-w /etc/hosts -p wa -k network-modification
-w /etc/network/ -p wa -k network-modification

# ── System call monitoring ─────────────────────────────────────────────────
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm-mod
-a always,exit -F arch=b64 -S chown -S fchown -S lchown -F auid>=1000 -F auid!=4294967295 -k perm-mod
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -F exit=-EACCES -F auid>=1000 -k access
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -F exit=-EPERM -F auid>=1000 -k access

# ── Module loading ─────────────────────────────────────────────────────────
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k modules

# ── Docker events ──────────────────────────────────────────────────────────
-w /usr/bin/docker -p x -k docker
-w /var/lib/docker/ -p wa -k docker
-w /etc/docker/ -p wa -k docker
EOF
  apply "Load audit rules" "augenrules --load 2>/dev/null || auditctl -R $AUDIT_RULES"
  apply "Enable auditd service" "systemctl enable --now auditd"
  ok "Audit logging configured: $AUDIT_RULES"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "5. Firewall Configuration (SC.3.183)"
# ─────────────────────────────────────────────────────────────────────────────

if command -v ufw &>/dev/null && ! $CHECK_ONLY; then
  apply "Enable UFW firewall" "ufw --force enable"
  apply "Default deny incoming" "ufw default deny incoming"
  apply "Default allow outgoing" "ufw default allow outgoing"
  apply "Allow SSH" "ufw allow ssh"
  apply "Allow WireGuard VPN port" "ufw allow ${VPN_PORT:-51820}/udp"
  apply "Reload UFW" "ufw reload"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "6. Password Policy (IA.3.083)"
# ─────────────────────────────────────────────────────────────────────────────

if ! $CHECK_ONLY; then
cat > /etc/security/pwquality.conf << 'EOF'
# NIST 800-63B / CMMC IA.3.083 password requirements
minlen = 15
minclass = 3
maxrepeat = 3
maxclasserepeat = 4
dcredit = -1
ucredit = -1
lcredit = -1
ocredit = -1
EOF
  ok "Password policy configured (/etc/security/pwquality.conf)"
fi

# ─────────────────────────────────────────────────────────────────────────────
section "7. Disable Unnecessary Services (CM.3.068)"
# ─────────────────────────────────────────────────────────────────────────────

DISABLE_SERVICES=(
  "telnet" "rsh" "rlogin" "rexec" "nis" "tftp"
  "cups" "avahi-daemon" "bluetooth"
)

for svc in "${DISABLE_SERVICES[@]}"; do
  if systemctl is-active --quiet "$svc" 2>/dev/null; then
    apply "Disable $svc" "systemctl disable --now $svc 2>/dev/null || true"
  fi
done

# ─────────────────────────────────────────────────────────────────────────────
section "8. File Integrity Monitoring (SI.1.210)"
# ─────────────────────────────────────────────────────────────────────────────

if command -v aide &>/dev/null && ! $CHECK_ONLY; then
  apply "Initialize AIDE database (first run)" "aide --init 2>/dev/null && mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db || true"

  # Schedule daily AIDE check
  cat > /etc/cron.daily/aide-check << 'EOF'
#!/bin/bash
/usr/bin/aide --check 2>&1 | logger -t aide-cmmc
EOF
  chmod +x /etc/cron.daily/aide-check
  ok "AIDE file integrity monitoring initialized"
fi

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${CYAN}── Hardening Summary ──────────────────────────────────────${RESET}"
echo -e "  ${GREEN}PASS: $PASS${RESET}  ${RED}FAIL: $FAIL${RESET}  ${YELLOW}WARN: $WARN${RESET}"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo -e "${RED}  ⚠ Some hardening steps failed. Review output above.${RESET}"
  exit 1
else
  echo -e "${GREEN}  ✓ Host hardening complete.${RESET}"
  echo -e "  Next step: Run ${CYAN}verify_controls.sh${RESET} to validate NIST control implementation."
  echo ""
fi
