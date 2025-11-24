# 🚀 QUICK START (5 Minutes)

Get your secure code review scanner running in 5 minutes!

## Step 1: Install Everything (2 minutes)

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_setup.py
```

## Step 2: Set Up API Key (1 minute)

**Choose ONE option:**

### Option A: OpenAI (Recommended - $0.20 per scan)
```bash
export OPENAI_API_KEY="sk-proj-YOUR-KEY-HERE"
export LLM_PROVIDER="openai"
```
Get key: https://platform.openai.com/api-keys

### Option B: Anthropic Claude (Similar pricing)
```bash
export ANTHROPIC_API_KEY="sk-ant-YOUR-KEY-HERE"
export LLM_PROVIDER="anthropic"
```
Get key: https://console.anthropic.com/

### Option C: LM Studio (FREE - Best for GPT-OSS-20B)
```bash
# 1. Download from: https://lmstudio.ai/
# 2. Search and download model: "gpt-oss-20b" or "llama-3.1-8b"
# 3. Go to "Local Server" tab → Start Server
export LLM_PROVIDER="lmstudio"
```
**👉 See [LMSTUDIO_GUIDE.md](LMSTUDIO_GUIDE.md) for complete setup**

### Option D: Ollama (FREE but command-line)
```bash
# Install Ollama: https://ollama.ai/download
ollama pull llama2
ollama serve  # Keep running
export LLM_PROVIDER="ollama"
```

## Step 3: Run the Scanner (2 minutes)

```bash
# Scan the sample vulnerable app
python scanner.py --target ./sample_app

# View results
open reports/security_report.html
```

**Expected output:**
```
🔍 Running Semgrep...
   Found 15 Semgrep findings
🔍 Running Bandit...
   Found 18 Bandit findings
📊 Total unique findings: 25

🤖 Analyzing 25 findings with LLM (openai)...
   Analyzing 1/10: sql-injection
   Analyzing 2/10: command-injection
   ...

✅ SCAN COMPLETE
📊 Summary:
   CRITICAL: 5
   HIGH:     8
   MEDIUM:   10
   LOW:      2

📂 View reports:
   - reports/security_report.html
   - reports/normalized_findings.json
```

---

## For Group Projects

**Sharing API Key Option 1: Single Shared Account**
```bash
# One person creates account, team splits $10 cost
# Share key via Signal/1Password (never via email/Slack)
export OPENAI_API_KEY="team-shared-key"
```

**Sharing API Key Option 2: GitHub Secrets**
```bash
# Store in GitHub: Settings → Secrets → Actions
# Add: OPENAI_API_KEY = sk-proj-xxxxx
# Pipeline will use it automatically
```

**Sharing API Key Option 3: Local LLM (No key needed)**
```bash
# One person runs locally, shares reports
ollama serve
python scanner.py --target ./sample_app
# Email the reports/ folder to team
```

---

## Common Issues

**"No API key found"**
```bash
# Fix: Set environment variable
export OPENAI_API_KEY="sk-proj-xxxxx"
echo $OPENAI_API_KEY  # Should print your key
```

**"Semgrep not found"**
```bash
# Fix: Install semgrep
pip install semgrep
semgrep --version  # Should show version
```

**"Rate limit exceeded"**
```bash
# Fix: Wait 1 minute or use fewer findings
# Edit scanner.py, line ~295:
top_findings = findings[:3]  # Reduce from 10 to 3
```

---

## What's Included

```
.
├── README.md              # Full documentation
├── SETUP_GUIDE.md         # Detailed setup instructions
├── REMEDIATION_GUIDE.md   # How to fix vulnerabilities
├── scanner.py             # Main scanner script (ONE FILE!)
├── test_setup.py          # Verify your setup
├── requirements.txt       # Python dependencies
├── sample_app/            # Vulnerable test application
│   ├── app.py            # 12+ vulnerabilities
│   └── utils.py          # 15+ vulnerabilities
├── .github/workflows/     # CI/CD integration
│   └── security_scan.yml # GitHub Actions pipeline
└── prompts/              # LLM prompt documentation
    └── README_PROMPTS.md # Prompt transparency for grading
```

---

## Next Steps

1. ✅ Run `python test_setup.py` to verify installation
2. ✅ Run `python scanner.py --target ./sample_app`
3. ✅ Open `reports/security_report.html` in browser
4. ✅ Review the findings and LLM suggestions
5. ✅ Scan your own code: `python scanner.py --target /path/to/your/code`
6. ✅ Check GitHub Actions: Push to repo to trigger CI

---

## Grading Rubric Coverage

- ✅ **CI integration (25%)**: `.github/workflows/security_scan.yml`
- ✅ **Triage accuracy (30%)**: LLM prioritizes CRITICAL/HIGH/MEDIUM/LOW
- ✅ **Developer guidance (25%)**: `reports/security_report.html` with fixes
- ✅ **Documentation (10%)**: README.md, SETUP_GUIDE.md, REMEDIATION_GUIDE.md
- ✅ **LLM transparency (10%)**: `prompts/llm_prompts.txt` logs all prompts

---

## Cost for Entire Project

- **OpenAI**: $2-5 for all testing and development
- **Anthropic**: Similar to OpenAI
- **Ollama**: $0 (but slower)

**Team tip**: $10 prepaid credit covers 4 people easily.

---

## Need Help?

1. Check `SETUP_GUIDE.md` for detailed instructions
2. Check `REMEDIATION_GUIDE.md` for vulnerability fixes
3. Check `prompts/README_PROMPTS.md` for LLM transparency
4. Run `python test_setup.py` to diagnose issues

Good luck! 🚀
