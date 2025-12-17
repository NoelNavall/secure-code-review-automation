# Security Scanner - Assignment 18

## Project Name and Brief Purpose

**Project:** Automated Secure Code Review with LLM Integration

**Purpose:** This system combines static analysis tools (Semgrep and Bandit) with Large Language Models (LLM) to automatically identify, prioritize, and provide remediation guidance for security vulnerabilities in Python applications.

## Scope - What the Project Covers

The project implements a complete security scanning pipeline that:
- Scans Python code for security vulnerabilities
- Analyzes criticality using AI-powered assessment
- Generates interactive HTML reports with filtering and pagination
- Integrates with CI/CD pipelines (GitHub Actions)
- Provides concrete remediation suggestions for identified vulnerabilities

## Legal/Ethical Warning

**IMPORTANT:** This project contains intentionally vulnerable code examples for testing purposes only.

- Use ONLY in isolated testing environments
- NEVER run vulnerable example files in production
- Source code in `sample/` contains deliberately insecure patterns
- Project is designed for educational purposes in security testing
- Follow responsible security practices during all testing

## Quick Start

### Basic Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure LMStudio
export LLM_PROVIDER="lmstudio"

# Run scan
python scanner.py --target ./sample_app
```

### View Results

```bash
# Open HTML report
open reports/YYYY-MM-DD_HH-MM-SS_sample_app/report.html

# List all scans
python view_reports.py --list

# View latest scan
python view_reports.py --latest
```

## Brief Description of File Structure

```
secure-code-review/
├── scanner.py                 # Main security scanning script
├── view_reports.py           # Report viewing and filtering tool
├── requirements.txt          # Python dependencies
│
├── sample/               # Vulnerable test files
│   ├── app.py               # Flask app with vulnerabilities
│   └── utils.py             # Utility functions with vulnerabilities
│
├── reports/                  # Generated scan results
│   └── YYYY-MM-DD_HH-MM-SS_target/
│       ├── report.html      # Interactive HTML report
│       ├── findings.json    # Raw JSON data
│       └── llm_prompts.txt  # LLM interaction log
│
├── .github/workflows/
│   └── security_scan.yml    # CI/CD pipeline configuration
│
├── docs/                    # Documentation
│   ├── writeup.md          # Lab report (background, methodology, results)
│   ├── SETUP_GUIDE.md      # Detailed installation guide
│   ├── REMEDIATION_GUIDE.md # Vulnerability remediation guidance
│   └── ...                 # Additional technical documentation
│
└── README.md               # This file
```

### Key Components

**Code/**
- `scanner.py` - Orchestrates Semgrep, Bandit, and LLM analysis
- `view_reports.py` - Command-line tool for report management

**Docs/**
- `writeup.md` - Complete lab report with background, theory, methodology, and results
- `SETUP_GUIDE.md` - Installation instructions
- `REMEDIATION_GUIDE.md` - Fix patterns for common vulnerabilities

**Prompts/**
- Generated automatically during execution
- Contains all LLM prompts and responses for transparency

## Software/License Information

### Dependencies

**Core Tools:**
- Python 3.8+
- Semgrep (Apache 2.0 License)
- Bandit (Apache 2.0 License)

**Python Libraries:**
- requests (Apache 2.0) - HTTP requests
- Flask (BSD License) - Web framework for test app

**LLM Provider:**
- LM Studio

### Project License

This project is created for educational purposes as part of Ethical Hackin DI6005.

**Usage Rights:**
- Free use for academic purposes
- Modification and distribution permitted for education
- Commercial use requires separate agreement

**Disclaimer:**
- Software provided "as is" without warranties
- Developer not responsible for damages from use
- User responsible for safe handling of vulnerable test files

### Third-Party Licenses

See respective tool documentation for complete license terms:
- Semgrep: https://github.com/returntocorp/semgrep/blob/develop/LICENSE
- Bandit: https://github.com/PyCQA/bandit/blob/main/LICENSE

## Functionality

### Core Features

**1. Automatic Vulnerability Detection**
- Combines Semgrep and Bandit for comprehensive analysis
- Identifies SQL injection, command injection, XSS, etc.
- Normalizes results from both tools

**2. LLM-Driven Prioritization**
- Analyzes exploitability (scale 1-5)
- Assesses impact and consequences
- Identifies false positives
- Generates specific remediation suggestions

**3. Interactive Reports**
- Clickable filtering by severity
- Pagination (20 findings per page)
- Code context with line numbers
- Highlighted vulnerable lines

**4. CI/CD Integration**
- GitHub Actions workflow
- Automatic scanning on push/pull request
- Weekly scheduled scans
- Fails on critical vulnerabilities

### Supported Vulnerability Types

- SQL Injection
- Command Injection
- Cross-Site Scripting (XSS)
- Hardcoded Secrets
- Weak Cryptography
- Insecure Deserialization
- Path Traversal
- CSRF

## Usage Examples

### Basic Scanning

```bash
# Scan an application
python scanner.py --target ./sample_app

# Skip LLM analysis (faster)
python scanner.py --target ./sample_app --skip-llm
```

### Report Management

```bash
# List all scans
python view_reports.py --list

# Filter by severity
python view_reports.py --filter-severity critical

# Filter by target
python view_reports.py --filter-target sample_app

# Compare two scans
python view_reports.py --compare SCAN1_ID SCAN2_ID
```

### CI/CD Usage

GitHub Actions workflow included for automatic scanning:

```yaml
# .github/workflows/security_scan.yml already included
# Configuration via repository secrets
```



## Troubleshooting

**Problem: Semgrep not found (Windows)**
- Solution: Use WSL2 for better compatibility
- Alternative: `pipx install semgrep`

**Problem: LM Studio connection failed**
- Verify server is running (green indicator)
- Check URL: `curl http://localhost:1234/v1/models`

**Problem: No findings**
- Verify scanning vulnerable example files
- Confirm Semgrep/Bandit are installed

## Support and Documentation

**Complete documentation:**
- See `docs/writeup.md` for lab report
- See `SETUP_GUIDE.md` for detailed installation
- See `REMEDIATION_GUIDE.md` for fix guidance

**If issues arise:**
1. Run `python test_setup.py` for diagnostics
2. Check `llm_prompts.txt` for LLM interactions
3. Review error messages in terminal

## Author

Developed as part of Assignment 18 - Secure Code Review with LLM Integration

Course: Ethical Hacking DI6005
Institution: Halmstad University
Date: November 2025