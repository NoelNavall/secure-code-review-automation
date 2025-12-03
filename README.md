# Assignment 18 - Secure Code Review Automation

Automated security scanning pipeline with LLM-powered triage and remediation suggestions.

## Overview

This tool automatically:
1. Scans code with Semgrep and Bandit
2. Normalizes findings into JSON
3. Uses LLM to prioritize and suggest fixes
4. Generates developer-friendly reports

## Quick Start

### 1. Installation

```bash
# Install security scanners
pip install semgrep bandit

# Install Python dependencies
pip install openai anthropic requests
```

### 2. API Key Setup (For Group Sharing)

**Option A: OpenAI (Recommended for groups)**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**Option B: Anthropic Claude**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Option C: LM Studio (FREE - Easy GUI, any model)**
```bash
# 1. Download from https://lmstudio.ai/
# 2. Load model (gpt-oss-20b, llama-3.1-8b, etc)
# 3. Click "Start Server"
export LLM_PROVIDER="lmstudio"
```
📖 **See [LMSTUDIO_GUIDE.md](LMSTUDIO_GUIDE.md) for detailed instructions**

**Option D: Ollama (FREE - CLI for local models)**
```bash
# Install from https://ollama.ai/download
ollama pull llama2
ollama serve  # Keep running
export LLM_PROVIDER="ollama"
```

**For Group Collaboration:**
- Create a shared OpenAI account and split costs ($2-3/person)
- OR use LM Studio - one person hosts, team connects remotely
- OR everyone runs LM Studio locally (free but needs good hardware)

### 3. Run the Scanner

```bash
# Scan a sample vulnerable app
python scanner.py --target ./sample_app

# Or scan any GitHub repo
python scanner.py --target https://github.com/user/repo
```

## Project Structure

```
.
├── README.md                          # This file
├── scanner.py                         # Main orchestration script
├── sample_app/                        # Vulnerable test application
│   ├── app.py                         # Flask app with vulnerabilities
│   └── utils.py                       # Helper functions with issues
├── .github/workflows/                 # CI/CD integration
│   └── security_scan.yml              # GitHub Actions workflow
├── reports/                           # Generated reports
│   ├── normalized_findings.json       # Raw scanner output
│   └── security_report.html           # Final developer report
└── prompts/                           # LLM prompt documentation
    └── llm_prompts.txt                # Prompts used for triage
```

## Configuration

Edit these variables in `scanner.py`:

```python
# Choose LLM provider
LLM_PROVIDER = "openai"  # Options: "openai", "anthropic", "ollama"

# Severity thresholds
CRITICAL_KEYWORDS = ["sql injection", "command injection", "xxe"]
```

## CI/CD Integration

The pipeline runs automatically on every push:
1. Code is committed to GitHub
2. GitHub Actions triggers `security_scan.yml`
3. Scanners run (Semgrep + Bandit)
4. LLM analyzes findings
5. Report is uploaded as artifact

## Cost Estimates (LLM Usage)

- **OpenAI GPT-4**: ~$0.10-0.50 per scan
- **Anthropic Claude**: ~$0.08-0.40 per scan
- **Ollama (local)**: Free (needs 8GB+ RAM)

For a group project: Expect <$5 total for all testing.

## Output Example

```
=== SECURITY SCAN REPORT ===

CRITICAL (Fix Immediately):
  1. SQL Injection in login.py:45
     - Risk: Attacker can dump entire database
     - Fix: Use parameterized queries
     - Code: cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))

MEDIUM (Fix This Sprint):
  2. Hardcoded secret in config.py:12
     - Risk: Credentials exposed in source control
     - Fix: Use environment variables
     - Code: SECRET_KEY = os.environ.get('SECRET_KEY')
```

## Limitations

- LLM may hallucinate fixes (always review manually)
- False positives possible (especially from Semgrep)
- Requires API key or local LLM setup
- Best for Python/JavaScript projects


## Troubleshooting

**"No API key found"**
- Set environment variable: `export OPENAI_API_KEY="..."`
- Or use local Ollama: `export LLM_PROVIDER="ollama"`

**"Semgrep not found"**
- Install: `pip install semgrep`
- Verify: `semgrep --version`

**"Too many findings"**
- Increase severity filter in scanner.py
- Focus on CRITICAL and HIGH only

## Team Collaboration Tips

1. **Share API costs**: Create one OpenAI account, split $10 credit
2. **Rotate keys**: Each member uses key for their testing phase
3. **Use local LLM**: One person runs Ollama, shares reports
4. **Cache results**: Save LLM responses to avoid duplicate API calls
