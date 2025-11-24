# Architecture & Flow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Repository                       │
│  (Your Code + .github/workflows/security_scan.yml)         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Git Push / Pull Request
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions CI/CD                     │
│  1. Checkout code                                           │
│  2. Install dependencies (semgrep, bandit, python libs)     │
│  3. Run security_scan.yml workflow                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Execute scanner.py
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                     scanner.py (Main)                       │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │ Step 1: Run Static Analysis                      │     │
│  │  - Semgrep (rules-based scanning)                │     │
│  │  - Bandit (Python security linting)              │     │
│  │  Output: Raw findings (JSON)                     │     │
│  └──────────────────────────────────────────────────┘     │
│                        │                                    │
│                        ↓                                    │
│  ┌──────────────────────────────────────────────────┐     │
│  │ Step 2: Normalize & Deduplicate                  │     │
│  │  - Combine Semgrep + Bandit results              │     │
│  │  - Remove duplicates                             │     │
│  │  - Standardize format                            │     │
│  │  Output: normalized_findings.json                │     │
│  └──────────────────────────────────────────────────┘     │
│                        │                                    │
│                        ↓                                    │
│  ┌──────────────────────────────────────────────────┐     │
│  │ Step 3: LLM-Powered Triage                       │     │
│  │  ┌────────────────────────────────────────┐     │     │
│  │  │ For each finding (top 10):             │     │     │
│  │  │  - Generate analysis prompt            │     │     │
│  │  │  - Call LLM API (OpenAI/Anthropic)     │     │     │
│  │  │  - Parse JSON response                 │     │     │
│  │  │  - Extract: exploitability, impact,    │     │     │
│  │  │    false_positive, remediation, priority│    │     │
│  │  └────────────────────────────────────────┘     │     │
│  │  Output: Enriched findings with LLM data        │     │
│  └──────────────────────────────────────────────────┘     │
│                        │                                    │
│                        ↓                                    │
│  ┌──────────────────────────────────────────────────┐     │
│  │ Step 4: Generate Reports                         │     │
│  │  - JSON: Machine-readable                        │     │
│  │  - HTML: Human-friendly with colors              │     │
│  │  - Prompts log: Transparency audit               │     │
│  └──────────────────────────────────────────────────┘     │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        │ Output artifacts
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                        Reports                              │
│  ├── reports/normalized_findings.json (raw data)           │
│  ├── reports/security_report.html (for devs)               │
│  └── prompts/llm_prompts.txt (transparency)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Example

### Input: Vulnerable Code
```python
# sample_app/app.py line 45
query = f"SELECT * FROM users WHERE username='{username}'"
cursor.execute(query)
```

### Step 1: Scanner Detection
```json
{
  "tool": "semgrep",
  "severity": "HIGH",
  "title": "sql-injection",
  "message": "User input in SQL query",
  "file": "app.py",
  "line": 45,
  "code": "query = f\"SELECT * FROM users..."
}
```

### Step 2: LLM Analysis
**Prompt sent to LLM:**
```
Analyze this security vulnerability:

Title: sql-injection
Severity: HIGH
File: app.py:45
Description: User input in SQL query
Code: query = f"SELECT * FROM users WHERE username='{username}'"

Provide:
1. EXPLOITABILITY: (1-5)
2. IMPACT: (worst case)
3. FALSE_POSITIVE: (LOW/MEDIUM/HIGH)
4. REMEDIATION: (specific fix)
5. PRIORITY: (CRITICAL/HIGH/MEDIUM/LOW)
```

**LLM Response:**
```json
{
  "exploitability": 5,
  "impact": "Attacker can dump entire database, modify records, bypass authentication",
  "false_positive": "LOW",
  "remediation": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE username=?', (username,))",
  "priority": "CRITICAL"
}
```

### Step 3: Final Output (HTML Report)
```html
<div class="finding CRITICAL">
  <h3>1. SQL Injection</h3>
  <span class="severity CRITICAL">CRITICAL</span>
  <p>File: app.py:45 | Tool: semgrep</p>
  
  <h4>Description</h4>
  <p>User input in SQL query</p>
  
  <h4>Vulnerable Code</h4>
  <code>query = f"SELECT * FROM users WHERE username='{username}'"</code>
  
  <h4>Impact</h4>
  <p>Attacker can dump entire database, modify records, bypass authentication</p>
  
  <h4>Exploitability</h4>
  <p>5/5 (Trivial to exploit)</p>
  
  <div class="remediation">
    <h4>✅ Remediation</h4>
    <p>Use parameterized queries: cursor.execute('SELECT * FROM users WHERE username=?', (username,))</p>
  </div>
</div>
```

---

## LLM Provider Flow

```
┌──────────────────────┐
│  scanner.py          │
│  call_llm(prompt)    │
└──────────┬───────────┘
           │
           ├─────────────┐
           │             │
    if openai     if anthropic     if ollama
           │             │             │
           ↓             ↓             ↓
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ OpenAI   │  │Anthropic │  │  Local   │
    │ API      │  │ API      │  │  Ollama  │
    │ GPT-4o   │  │ Claude   │  │  Llama2  │
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │             │
         └─────────────┴─────────────┘
                       │
                       ↓
              JSON response with
              analysis & remediation
```

---

## CI/CD Pipeline Flow

```
Developer pushes code
         ↓
GitHub triggers workflow
         ↓
┌─────────────────────┐
│ 1. Setup            │
│  - Checkout code    │
│  - Install Python   │
│  - Install deps     │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 2. Scan             │
│  - Run Semgrep      │
│  - Run Bandit       │
│  - Save raw results │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 3. LLM Analysis     │
│  - Load API key     │
│    from GitHub      │
│    Secrets          │
│  - Run scanner.py   │
│  - Generate reports │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 4. Upload Artifacts │
│  - JSON report      │
│  - HTML report      │
│  - Prompts log      │
│  (Retained 90 days) │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 5. PR Comment       │
│  Post summary:      │
│  🔴 CRITICAL: 5     │
│  🟠 HIGH: 8         │
│  🟡 MEDIUM: 10      │
│  🔵 LOW: 2          │
└─────────┬───────────┘
          ↓
┌─────────────────────┐
│ 6. Build Status     │
│  ✅ Pass (no crit)  │
│  ❌ Fail (has crit) │
└─────────────────────┘
```

---

## Cost Flow (OpenAI Example)

```
Per Finding Analysis:
┌──────────────────────────────┐
│ Prompt (input)               │
│  ~ 300 tokens                │
│  × $0.15 / 1M tokens         │
│  = $0.000045                 │
└───────────┬──────────────────┘
            │
            ↓
┌──────────────────────────────┐
│ Response (output)            │
│  ~ 200 tokens                │
│  × $0.60 / 1M tokens         │
│  = $0.000120                 │
└───────────┬──────────────────┘
            │
            ↓
Total per finding: ~$0.02

For 10 findings: ~$0.20
For 50 findings: ~$1.00
```

---

## Security Severity Classification

```
Keywords → Scanner Severity → LLM Confirmation → Final Priority

Example 1: SQL Injection
"sql injection" in message
        ↓
   CRITICAL (keyword match)
        ↓
   LLM confirms: exploitability=5
        ↓
   CRITICAL (final)

Example 2: Weak Crypto
"md5" in message
        ↓
   MEDIUM (scanner default)
        ↓
   LLM: depends on use case, false_positive=MEDIUM
        ↓
   MEDIUM (but flagged for review)

Example 3: False Positive
"eval" in test file
        ↓
   HIGH (scanner)
        ↓
   LLM: false_positive=HIGH, in test code
        ↓
   INFO (downgraded)
```

---

## Time & Resource Estimates

```
┌─────────────────────────┬──────────┬──────────┬────────────┐
│ Activity                │ Duration │ API Cost │ Human Time │
├─────────────────────────┼──────────┼──────────┼────────────┤
│ Setup (first time)      │ 5 min    │ $0       │ 5 min      │
│ Run scan (10 findings)  │ 2 min    │ $0.20    │ 0 min      │
│ Review HTML report      │ 10 min   │ $0       │ 10 min     │
│ Fix vulnerabilities     │ 2 hours  │ $0       │ 2 hours    │
│ CI/CD setup             │ 10 min   │ $0       │ 10 min     │
├─────────────────────────┼──────────┼──────────┼────────────┤
│ Total (per project)     │ ~3 hours │ $2-5     │ ~3 hours   │
└─────────────────────────┴──────────┴──────────┴────────────┘

ROI: Catches 10+ critical bugs automatically = saves days of manual review
```

---

## File Dependencies

```
scanner.py
├── Requires: semgrep, bandit (external)
├── Requires: openai OR anthropic OR requests (LLM)
├── Reads: sample_app/*.py (target code)
├── Writes: reports/*.json, reports/*.html
└── Logs: prompts/llm_prompts.txt

.github/workflows/security_scan.yml
├── Uses: scanner.py
├── Reads: GitHub Secrets (API keys)
└── Uploads: reports/ as artifacts

test_setup.py
├── Checks: Python version
├── Checks: Installed packages
├── Validates: API keys
└── Tests: LLM connectivity
```

---

This architecture achieves:
✅ Automation (CI/CD)
✅ Intelligence (LLM triage)
✅ Actionability (specific fixes)
✅ Transparency (logged prompts)
✅ Scalability (configurable)
✅ Cost-effectiveness (<$5 per project)
