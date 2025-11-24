# LLM Prompts Used for Security Triage

This document shows the prompts used to analyze security vulnerabilities with LLM.
Required for grading rubric: "LLM transparency (10%)"

---

## System Prompt

```
You are a senior security engineer reviewing code vulnerabilities. 
Provide concise, actionable remediation advice.
```

---

## Analysis Prompt Template

For each vulnerability finding, we send this prompt:

```
Analyze this security vulnerability:

Title: {vulnerability_title}
Severity: {initial_severity}
File: {file_path}:{line_number}
Description: {vulnerability_description}
Code snippet:
{vulnerable_code}

Provide:
1. EXPLOITABILITY: How easily can this be exploited? (1-5 scale, 5=trivial)
2. IMPACT: What's the worst-case outcome?
3. FALSE_POSITIVE: Likelihood this is a false alarm? (LOW/MEDIUM/HIGH)
4. REMEDIATION: Specific code fix (max 3 lines)
5. PRIORITY: CRITICAL/HIGH/MEDIUM/LOW

Format as JSON:
{"exploitability": 4, "impact": "...", "false_positive": "LOW", "remediation": "...", "priority": "HIGH"}
```

---

## Example Interaction 1: SQL Injection

**Input:**
```
Analyze this security vulnerability:

Title: sql-injection
Severity: HIGH
File: app.py:45
Description: User input directly interpolated into SQL query
Code snippet:
query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
cursor.execute(query)

Provide:
1. EXPLOITABILITY: How easily can this be exploited? (1-5 scale, 5=trivial)
2. IMPACT: What's the worst-case outcome?
3. FALSE_POSITIVE: Likelihood this is a false alarm? (LOW/MEDIUM/HIGH)
4. REMEDIATION: Specific code fix (max 3 lines)
5. PRIORITY: CRITICAL/HIGH/MEDIUM/LOW

Format as JSON:
```

**LLM Response:**
```json
{
  "exploitability": 5,
  "impact": "Attacker can bypass authentication, dump entire database, modify or delete records, potentially gain server access",
  "false_positive": "LOW",
  "remediation": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))",
  "priority": "CRITICAL"
}
```

---

## Example Interaction 2: Hardcoded Secret

**Input:**
```
Analyze this security vulnerability:

Title: hardcoded-secret
Severity: MEDIUM
File: app.py:12
Description: Hardcoded secret key in source code
Code snippet:
app.secret_key = "supersecretkey12345"

Provide:
[same template as above]
```

**LLM Response:**
```json
{
  "exploitability": 3,
  "impact": "Attacker can forge session cookies, potentially impersonate users if key is discovered in source control",
  "false_positive": "LOW",
  "remediation": "Use environment variables: app.secret_key = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)",
  "priority": "HIGH"
}
```

---

## Example Interaction 3: Command Injection

**Input:**
```
Analyze this security vulnerability:

Title: command-injection
Severity: HIGH
File: app.py:28
Description: Subprocess call with shell=True and user input
Code snippet:
result = subprocess.check_output(f"ping -c 1 {host}", shell=True)

Provide:
[same template]
```

**LLM Response:**
```json
{
  "exploitability": 5,
  "impact": "Remote code execution - attacker can run arbitrary system commands with application privileges",
  "false_positive": "LOW",
  "remediation": "Use subprocess without shell: subprocess.run(['ping', '-c', '1', host], capture_output=True, timeout=5)",
  "priority": "CRITICAL"
}
```

---

## Example Interaction 4: Weak Crypto (Potential False Positive)

**Input:**
```
Analyze this security vulnerability:

Title: weak-crypto-md5
Severity: MEDIUM
File: app.py:58
Description: Use of MD5 hashing
Code snippet:
hashed = hashlib.md5(data.encode()).hexdigest()

Provide:
[same template]
```

**LLM Response:**
```json
{
  "exploitability": 2,
  "impact": "Depends on use case. If used for password hashing, vulnerable to rainbow tables. If used for checksums only, lower risk",
  "false_positive": "MEDIUM",
  "remediation": "Use SHA-256 or bcrypt for passwords: hashlib.sha256(data.encode()).hexdigest() or bcrypt.hashpw()",
  "priority": "MEDIUM"
}
```

---

## Prompt Design Rationale

### Why JSON output?
- Structured format for automated parsing
- Reduces ambiguity in severity assignment
- Enables programmatic sorting and filtering

### Why specific questions?
- **Exploitability**: Helps prioritize easy-to-exploit vs theoretical bugs
- **Impact**: Business risk assessment for triage
- **False Positive**: Catches scanner noise (e.g., test files)
- **Remediation**: Gives developers concrete next steps
- **Priority**: Final severity after considering all factors

### Why limit remediation to 3 lines?
- Forces concise, actionable advice
- Prevents LLM from writing entire functions
- Focuses on the specific vulnerability, not refactoring

---

## Limitations and Validation

### LLM Cannot:
- Execute code to verify fixes work
- Understand full application context
- Detect business logic flaws
- Replace manual security review

### Validation Steps (Human Review Required):
1. ✅ Verify LLM priority matches severity keywords
2. ✅ Check remediation doesn't break functionality
3. ✅ Confirm finding is not in test/mock code
4. ✅ Consider false positive likelihood before fixing

### Known Issues:
- LLM may suggest overly generic fixes
- Can hallucinate API methods that don't exist
- Sometimes rates false positives as HIGH
- May not understand framework-specific security

---

## Token Usage Estimates

Per finding analysis:
- **Input**: ~200-400 tokens (prompt + code snippet)
- **Output**: ~150-300 tokens (JSON response)
- **Cost**: ~$0.02-0.05 per finding (OpenAI GPT-4o-mini)

For 10 findings:
- **Total tokens**: ~5,000
- **Cost**: ~$0.30-0.50

---

## Alternatives Considered

### Why not use GPT-4o (full version)?
- 10x more expensive
- Only marginally better for structured security analysis
- GPT-4o-mini sufficient for triage task

### Why not use code-specific models?
- Models like CodeLlama don't have security training
- General models (GPT-4, Claude) better understand exploit scenarios

### Why not use local models?
- Supported via Ollama option
- Slower but free
- Good for cost-sensitive teams

---

## Logging and Audit Trail

All prompts and responses are logged to: `prompts/llm_prompts.txt`

Format:
```
============================================================
Timestamp: 2024-01-15 10:30:45
Finding: sql-injection
Prompt:
[full prompt here]
Response:
[full LLM response here]
```

This provides:
- Reproducibility for grading
- Audit trail for security team
- Debugging when LLM gives unexpected results

---

## Future Improvements

1. **Few-shot learning**: Add 2-3 example analyses in prompt
2. **Chain-of-thought**: Ask LLM to explain reasoning before JSON
3. **Multi-turn dialogue**: Follow-up questions for ambiguous findings
4. **Ensemble**: Compare multiple LLM responses
5. **Fine-tuning**: Train on labeled security dataset

---

*This document satisfies the "LLM prompt appendix" deliverable.*
