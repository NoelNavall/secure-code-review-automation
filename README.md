# Security Scanner - Assignment 18

A Python tool that scans code for security vulnerabilities using Semgrep, Bandit, and LM Studio.

---

## What It Does

Scans Python files for security bugs like:
- SQL injection
- Command injection  
- Hardcoded passwords
- XSS vulnerabilities
- Weak cryptography

Then uses a local AI (LM Studio) to explain each bug and how to fix it.

---

## Project Structure

```
secure-code-review-automation/
│
├── src/                        # Scanner code
│   ├── scanner.py              # Main file - runs everything
│   ├── scanners.py             # Semgrep & Bandit integration
│   ├── config.py               # Settings
│   ├── llm_provider.py         # LM Studio connection
│   ├── triage.py               # AI bug analysis
│   └── report_generator.py     # Creates HTML report
│
├── sample/                     # Test files with bugs
│   ├── app.py                  # Vulnerable Flask app
│   └── utils.py                # More buggy code
│
├── reports/                    # Scan results (auto-generated)
│   └── [date]_[time]_[file]/
│       ├── report.html         # Open this in browser
│       ├── findings.json       # Raw data
│       └── llm_prompts.txt     # AI conversation log
│
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

---

## Setup

### 1. Install Python packages:
```bash
pip install -r requirements.txt
```

### 2. Make sure LM Studio is running:
- Open LM Studio
- Load a model (like ChatGPT or Llama)
- Start the server on port 1234

### 3. Run a scan:
```bash
python src/scanner.py --target sample/app.py
```

### 4. Open the report:
- Go to `reports/` folder
- Open the newest folder
- Open `report.html` in your browser

---

## Usage

### Scan a single file:
```bash
python src/scanner.py --target sample/app.py
```

### Scan a whole folder:
```bash
python src/scanner.py --target sample
```

### Skip AI analysis (faster):
```bash
python src/scanner.py --target sample/app.py --skip-llm
```

---

## How It Works

1. **Semgrep & Bandit** scan the code for security issues
2. **Scanner** combines the results
3. **LM Studio** analyzes each bug (how bad it is, how to fix it)
4. **Report** is generated as HTML

---

## Requirements

- Python 3.8 or newer
- Semgrep
- Bandit
- LM Studio (running locally)
- Other packages in requirements.txt

---

## Example Output

```
============================================================
SECURE CODE REVIEW AUTOMATION
============================================================
[1/4] Running static analysis tools...
Running Semgrep...
   Found 0 Semgrep findings
Running Bandit...
   Found 10 Bandit findings

[2/4] Normalizing findings...
Total unique findings: 10

[3/4] Preparing output directory...

[4/4] Analyzing with LLM...
Analyzing 10 findings with LLM (lmstudio)...
   Analyzing 1/10: hardcoded_sql_expressions
   Analyzing 2/10: hardcoded_password_string
   ...

============================================================
SCAN COMPLETE
============================================================
Summary:
   CRITICAL: 3
   HIGH:     5
   MEDIUM:   2
   LOW:      0

Reports saved to: reports/2025-12-31_15-30-00_app.py/
```

---

## Tools Used

- **Semgrep** - https://semgrep.dev/
- **Bandit** - https://github.com/PyCQA/bandit
- **LM Studio** - https://lmstudio.ai/