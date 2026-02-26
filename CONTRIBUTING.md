# Contributing to CMMC Enclave Toolkit

Thank you for your interest in contributing. This project exists to make CMMC compliance accessible to small and medium-sized DoD contractors who cannot afford commercial solutions. Every contribution helps protect the U.S. Defense Industrial Base.

## How to Contribute

### Reporting Issues
- Use the GitHub Issues tab to report bugs or request features
- For security vulnerabilities, see [SECURITY.md](SECURITY.md) — do not open a public issue

### Pull Requests
1. Fork the repository and create a feature branch (`git checkout -b feature/your-feature`)
2. Write clear, well-commented code
3. Add tests for new scoping questions or scoring logic
4. Update documentation if you change behavior
5. Submit a pull request with a clear description of the change

### Areas Most Needed
- **Additional scoping question modules** (e.g., cloud-specific, OT/ICS environments)
- **Windows Server enclave variant** using Docker Desktop or WSL2
- **Terraform deployment** for AWS GovCloud or Azure Government
- **Additional report formats** (PDF, DOCX)
- **Translations** of documentation

## Code Style
- Python: PEP 8, type hints encouraged, docstrings required for public functions
- Bash: `set -euo pipefail`, comments explaining NIST control rationale
- YAML: 2-space indentation, comments on all non-obvious settings

## Questions
Open a GitHub Discussion or contact the maintainer at pulasthibatuwita9@gmail.com.
