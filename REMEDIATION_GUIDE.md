# Security Remediation Guide for Developers

This guide provides step-by-step instructions to fix common security vulnerabilities found by the scanner.

---

## 🔴 CRITICAL Severity

### 1. SQL Injection

**Risk**: Attacker can manipulate database queries to steal, modify, or delete data.

**Vulnerable Code**:
```python
query = f"SELECT * FROM users WHERE id={user_id}"
cursor.execute(query)
```

**Fix**:
```python
# Use parameterized queries
query = "SELECT * FROM users WHERE id=?"
cursor.execute(query, (user_id,))
```

**Testing**:
```python
# Test that this fails safely
def test_sql_injection():
    malicious_input = "1 OR 1=1"
    # Should NOT return all users
    result = get_user(malicious_input)
    assert result is None or len(result) == 1
```

---

### 2. Command Injection

**Risk**: Attacker can execute arbitrary system commands on the server.

**Vulnerable Code**:
```python
result = subprocess.check_output(f"ping {host}", shell=True)
```

**Fix**:
```python
# Use list arguments without shell=True
result = subprocess.run(
    ["ping", "-c", "1", host],
    capture_output=True,
    timeout=5,
    check=False
)
```

**Additional Protection**:
```python
# Validate input format
import re
if not re.match(r'^[a-zA-Z0-9.-]+$', host):
    raise ValueError("Invalid host format")
```

---

### 3. Insecure Deserialization (Pickle)

**Risk**: Attacker can execute arbitrary code by crafting malicious pickle data.

**Vulnerable Code**:
```python
import pickle
data = pickle.loads(user_input)
```

**Fix**:
```python
# Use JSON instead of pickle
import json
data = json.loads(user_input)

# If you MUST use pickle, use HMAC to verify integrity
import hmac
import hashlib

def safe_pickle_loads(data, secret_key):
    signature, pickled = data.split(b':', 1)
    expected = hmac.new(secret_key, pickled, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature.decode(), expected):
        raise ValueError("Invalid signature")
    return pickle.loads(pickled)
```

---

## 🟠 HIGH Severity

### 4. Cross-Site Scripting (XSS)

**Risk**: Attacker can inject JavaScript to steal user sessions or deface pages.

**Vulnerable Code**:
```python
from flask import render_template_string
output = f"<h1>Results for: {user_query}</h1>"
return render_template_string(output)
```

**Fix**:
```python
# Use proper templating with auto-escaping
from flask import render_template
return render_template('results.html', query=user_query)

# In results.html (Jinja2 auto-escapes by default):
# <h1>Results for: {{ query }}</h1>
```

**If templating not possible**:
```python
from html import escape
output = f"<h1>Results for: {escape(user_query)}</h1>"
```

---

### 5. Hardcoded Secrets

**Risk**: Credentials exposed in source control, accessible to anyone with repo access.

**Vulnerable Code**:
```python
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "admin123"
```

**Fix**:
```python
# Use environment variables
import os

API_KEY = os.environ.get('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY not set")

# Or use a secrets manager
from dotenv import load_dotenv
load_dotenv()  # Loads from .env file
API_KEY = os.getenv('API_KEY')
```

**Setup**:
```bash
# Create .env file (add to .gitignore!)
echo "API_KEY=sk-1234567890abcdef" >> .env
echo ".env" >> .gitignore
```

---

### 6. Path Traversal

**Risk**: Attacker can read arbitrary files on the system (e.g., /etc/passwd).

**Vulnerable Code**:
```python
file_path = f"/var/www/uploads/{filename}"
with open(file_path, 'r') as f:
    return f.read()
```

**Fix**:
```python
import os
from pathlib import Path

UPLOAD_DIR = "/var/www/uploads"

# Method 1: Validate filename
def safe_read_file(filename):
    # Only allow alphanumeric and safe chars
    if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
        raise ValueError("Invalid filename")
    
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Ensure path is still within upload directory
    if not os.path.realpath(file_path).startswith(UPLOAD_DIR):
        raise ValueError("Path traversal detected")
    
    with open(file_path, 'r') as f:
        return f.read()
```

---

## 🟡 MEDIUM Severity

### 7. Weak Cryptography (MD5/SHA1)

**Risk**: Easy to crack with modern hardware; vulnerable to collision attacks.

**Vulnerable Code**:
```python
import hashlib
password_hash = hashlib.md5(password.encode()).hexdigest()
```

**Fix**:
```python
# For password hashing, use bcrypt or Argon2
import bcrypt

# Hashing
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# Verification
if bcrypt.checkpw(password.encode(), stored_hash):
    print("Password correct")
```

**Alternative (for data integrity, not passwords)**:
```python
# Use SHA-256 or SHA-512
import hashlib
digest = hashlib.sha256(data.encode()).hexdigest()
```

---

### 8. Missing Input Validation

**Risk**: Unexpected input can cause crashes, logic errors, or security issues.

**Vulnerable Code**:
```python
def set_age(age):
    user.age = age  # No validation!
```

**Fix**:
```python
def set_age(age):
    # Validate type
    if not isinstance(age, int):
        raise TypeError("Age must be integer")
    
    # Validate range
    if age < 0 or age > 150:
        raise ValueError("Age must be between 0 and 150")
    
    user.age = age
```

**Use validation libraries**:
```python
from pydantic import BaseModel, validator

class User(BaseModel):
    age: int
    
    @validator('age')
    def age_must_be_reasonable(cls, v):
        if v < 0 or v > 150:
            raise ValueError('must be 0-150')
        return v
```

---

### 9. Insecure Random Number Generation

**Risk**: Predictable tokens allow session hijacking or authentication bypass.

**Vulnerable Code**:
```python
import random
session_token = str(random.randint(100000, 999999))
```

**Fix**:
```python
# Use secrets module for cryptographic randomness
import secrets

# Generate token
session_token = secrets.token_urlsafe(32)

# Generate random integer
otp = secrets.randbelow(1000000)  # 0-999999
```

---

## 🔵 LOW Severity

### 10. Debug Mode Enabled

**Risk**: Exposes stack traces and internal paths to attackers.

**Vulnerable Code**:
```python
app.run(debug=True)
```

**Fix**:
```python
# Use environment variable
import os
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
app.run(debug=DEBUG)

# Production: Never set DEBUG=True
```

---

### 11. Weak File Permissions

**Risk**: Sensitive files readable by other users on the system.

**Vulnerable Code**:
```python
with open('secrets.txt', 'w') as f:
    f.write(secret_data)
# File created with default permissions (0644 - world readable)
```

**Fix**:
```python
import os

# Set restrictive permissions
with open('secrets.txt', 'w') as f:
    f.write(secret_data)

os.chmod('secrets.txt', 0o600)  # Only owner can read/write
```

---

## Testing Your Fixes

### 1. Unit Tests for Security

```python
import pytest

def test_sql_injection_prevention():
    """Verify SQL injection is blocked"""
    malicious_input = "1' OR '1'='1"
    result = get_user_by_id(malicious_input)
    assert result is None

def test_xss_prevention():
    """Verify XSS is escaped"""
    malicious_script = "<script>alert('XSS')</script>"
    output = render_search_results(malicious_script)
    assert "<script>" not in output
    assert "&lt;script&gt;" in output

def test_path_traversal_prevention():
    """Verify path traversal is blocked"""
    with pytest.raises(ValueError):
        read_file("../../etc/passwd")
```

### 2. Integration Tests

```python
def test_authentication_required():
    """Verify protected endpoints require auth"""
    response = client.get('/admin/users')
    assert response.status_code == 401

def test_rate_limiting():
    """Verify rate limiting is enforced"""
    for _ in range(100):
        response = client.post('/login', data={'user': 'test'})
    
    # Should be rate limited
    assert response.status_code == 429
```

---

## Verification Checklist

Before marking a vulnerability as "fixed", verify:

- [ ] Code change implements the recommended fix
- [ ] Unit test added to prevent regression
- [ ] Manual testing confirms vulnerability is closed
- [ ] No new vulnerabilities introduced by fix
- [ ] Code review by another team member
- [ ] Update documentation if API changed

---

## Common Mistakes to Avoid

### ❌ DON'T: Blacklist-based validation
```python
# Bad: easy to bypass
if "script" not in user_input:
    return user_input
```

### ✅ DO: Whitelist-based validation
```python
# Good: only allow known-safe patterns
if re.match(r'^[a-zA-Z0-9]+$', user_input):
    return user_input
raise ValueError("Invalid input")
```

---

### ❌ DON'T: Client-side only validation
```javascript
// Bad: client can bypass
if (isValid(input)) {
    sendToServer(input);
}
```

### ✅ DO: Server-side validation (always)
```python
# Good: server validates everything
@app.route('/api/submit')
def submit():
    if not validate_input(request.form['data']):
        return "Invalid input", 400
```

---

## Additional Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CWE Database**: https://cwe.mitre.org/
- **Python Security**: https://github.com/pyupio/safety
- **SANS Secure Coding**: https://www.sans.org/secure-coding/

---

## Getting Help

If you're unsure about a fix:

1. **Check the scanner's LLM analysis** in `reports/security_report.html`
2. **Consult OWASP** for the specific vulnerability type
3. **Ask your security team** for guidance
4. **Test in a safe environment** before production

---

*This remediation guide is generated automatically. Always verify fixes with security experts.*
