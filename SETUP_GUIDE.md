# Setup and Usage Guide

## Quick Setup (5 minutes)

### 1. Install Tools

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installations
semgrep --version
bandit --version
```

### 2. Configure API Key (Choose ONE option)

#### Option A: OpenAI (Best for groups - $5 should cover entire project)
```bash
# Get key from: https://platform.openai.com/api-keys
export OPENAI_API_KEY="sk-proj-xxxxxxxxxxxx"
export LLM_PROVIDER="openai"
```

#### Option B: Anthropic Claude (Similar pricing to OpenAI)
```bash
# Get key from: https://console.anthropic.com/
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxx"
export LLM_PROVIDER="anthropic"
```

#### Option C: Local LLM (FREE - but slower)
```bash
# Install Ollama: https://ollama.ai/download
ollama pull llama2
ollama serve  # Keep running in separate terminal
export LLM_PROVIDER="ollama"
```

### 3. Run the Scanner

```bash
# Scan the sample vulnerable app
python scanner.py --target ./sample_app

# View results
open reports/security_report.html  # macOS
xdg-open reports/security_report.html  # Linux
start reports/security_report.html  # Windows
```

---

## Group Collaboration Strategies

### Strategy 1: Shared OpenAI Account (Recommended)
1. One person creates OpenAI account
2. Add $10 credit (plenty for project)
3. Share API key with team via secure channel (Signal, 1Password)
4. Track usage at: https://platform.openai.com/usage
5. Split costs at end (likely <$5 total)

### Strategy 2: Key Rotation
```bash
# Team rotates who provides key each week
# Week 1: Alice's key
# Week 2: Bob's key
# Week 3: Charlie's key
```

### Strategy 3: Local LLM (No cost, but slower)
```bash
# One person runs Ollama locally
ollama serve
python scanner.py --target ./sample_app

# Share generated reports with team
# No API costs, but takes 5-10x longer
```

### Strategy 4: CI/CD with Secrets
```bash
# Store API key in GitHub Secrets
# Settings → Secrets → Actions → New secret
# Name: OPENAI_API_KEY
# Value: sk-proj-xxxxxxxxxxxx

# Pipeline will use it automatically
```

---

## Testing Your Setup

### Step 1: Test Scanners (No LLM needed)
```bash
# Test Semgrep
semgrep --config=auto sample_app/

# Test Bandit  
bandit -r sample_app/

# If both work, scanners are installed correctly
```

### Step 2: Test LLM Connection
```bash
# Quick test with minimal token usage
python -c "
import os
from scanner import call_llm
print(call_llm('Respond with: API connection successful'))
"
```

### Step 3: Full Scan with LLM
```bash
# Run complete pipeline
python scanner.py --target ./sample_app

# Should generate:
# - reports/normalized_findings.json
# - reports/security_report.html  
# - prompts/llm_prompts.txt
```

---

## Understanding the Output

### normalized_findings.json
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_findings": 25,
  "summary": {
    "CRITICAL": 5,
    "HIGH": 8,
    "MEDIUM": 10,
    "LOW": 2
  },
  "findings": [...]
}
```

### security_report.html
- Color-coded severity levels
- Top 20 most critical issues
- LLM-generated remediation advice
- Code snippets showing vulnerable lines

### prompts/llm_prompts.txt
- Exact prompts sent to LLM
- LLM responses for each finding
- Timestamp for each interaction
- Useful for grading rubric (LLM transparency)

---

## Customization

### Adjust Severity Thresholds
Edit `scanner.py`:
```python
CRITICAL_KEYWORDS = [
    "sql injection", "command injection",
    "xxe", "deserialization"
]

HIGH_KEYWORDS = [
    "xss", "csrf", "hardcoded secret"
]
```

### Change LLM Model
```python
# In scanner.py, call_openai() function
model="gpt-4o-mini"  # Cheaper, faster
model="gpt-4o"       # Smarter, but 10x cost
```

### Limit API Costs
```python
# In scanner.py, triage_findings()
top_findings = findings[:5]  # Only analyze top 5 (not 10)
```

---

## Troubleshooting

### "Semgrep not found"
```bash
# Fix: Install semgrep
pip install semgrep

# Verify
which semgrep
```

### "OpenAI API key not set"
```bash
# Fix: Export key
export OPENAI_API_KEY="sk-proj-xxxx"

# Verify
echo $OPENAI_API_KEY
```

### "Rate limit exceeded"
```bash
# Fix 1: Wait 1 minute and retry
# Fix 2: Reduce findings analyzed
python scanner.py --target ./sample_app

# In scanner.py, change:
top_findings = findings[:3]  # Analyze fewer findings
```

### "Connection refused (Ollama)"
```bash
# Fix: Start Ollama server
ollama serve

# In another terminal:
python scanner.py --target ./sample_app
```

### "No findings detected"
```bash
# Check if target has Python files
ls sample_app/*.py

# Try scanning a different directory
python scanner.py --target /path/to/your/code
```

---

## Cost Estimation

### OpenAI Pricing (gpt-4o-mini)
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- **Typical scan**: $0.10 - $0.30
- **Project total**: <$5 for all testing

### Anthropic Pricing (Claude Sonnet)
- Similar to OpenAI
- Slightly faster for code analysis

### Ollama (Local)
- **Cost**: $0 (100% free)
- **Trade-off**: 5-10x slower than API
- **Requirements**: 8GB+ RAM

---

## Adding to Existing Projects

### Scan Your Own Code
```bash
# Scan any directory
python scanner.py --target /path/to/your/project

# Scan specific files
python scanner.py --target ./src/api/
```

### Integrate with Git Hooks
```bash
# .git/hooks/pre-commit
#!/bin/bash
python scanner.py --target . --skip-llm
if [ $? -ne 0 ]; then
    echo "Security issues found! Review reports/"
    exit 1
fi
```

### Add to Makefile
```makefile
.PHONY: security-scan
security-scan:
	python scanner.py --target .
	@echo "Report: reports/security_report.html"
```

---

## Grading Rubric Checklist

- [ ] **CI Integration (25%)**: GitHub Actions workflow present and working
- [ ] **Triage Accuracy (30%)**: LLM correctly prioritizes findings
- [ ] **Developer Guidance (25%)**: HTML report has clear remediation steps
- [ ] **Documentation (10%)**: README explains setup and usage
- [ ] **LLM Transparency (10%)**: prompts/llm_prompts.txt shows all LLM interactions

---

## FAQ

**Q: Can multiple people use the same API key?**  
A: Yes! OpenAI keys work from multiple IPs simultaneously.

**Q: Will the key expire?**  
A: No, but you can rotate it for security. Check usage at platform.openai.com.

**Q: What if we run out of credits?**  
A: Add more ($5-10 is plenty). Scan costs ~$0.20 each.

**Q: Can we use free LLM APIs?**  
A: Yes! Try Ollama (local) or Hugging Face (free tier). Edit `call_llm()` function.

**Q: How do we submit the API key with assignment?**  
A: DON'T submit the key! Use .gitignore or environment variables. Submit only the code.

**Q: What if scanners find 100+ issues?**  
A: LLM will prioritize top 10. HTML report shows top 20. Focus on CRITICAL/HIGH.

---

## Next Steps

1. ✅ Run scanner on sample_app to verify setup
2. ✅ Check all 3 report files are generated
3. ✅ Review HTML report in browser
4. ✅ Scan your own project code
5. ✅ Commit to GitHub and verify CI pipeline runs
6. ✅ Document any customizations in README

Good luck! 🚀
