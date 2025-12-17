#!/usr/bin/env python3
"""
Utility functions with security vulnerabilities
"""

import os
import random
import tempfile
import yaml

# VULNERABILITY: Use of assert for security checks
def check_admin(user_role):
    assert user_role == "admin", "Not an admin"  # BUG: assert can be disabled with -O flag
    return True

# VULNERABILITY: Weak random number generation for security
def generate_token():
    # Using weak random for security token
    token = ''.join([str(random.randint(0, 9)) for _ in range(6)])  # BUG: predictable random
    return token

def generate_session_id():
    # Weak session ID generation
    return random.random()  # BUG: Not cryptographically secure

# VULNERABILITY: Insecure temporary file creation
def create_temp_file(content):
    # Race condition vulnerability
    filename = f"/tmp/myapp_{random.randint(1000, 9999)}.txt"  # BUG: predictable filename
    with open(filename, 'w') as f:
        f.write(content)
    return filename

# VULNERABILITY: YAML deserialization
def load_config(config_string):
    # Vulnerable to YAML deserialization attacks
    config = yaml.load(config_string)  # BUG: Should use yaml.safe_load()
    return config

# VULNERABILITY: Eval usage
def calculate(expression):
    # Arbitrary code execution
    result = eval(expression)  # BUG: eval on user input
    return result

# VULNERABILITY: Timing attack
def compare_tokens(token1, token2):
    # Vulnerable to timing attacks
    if token1 == token2:  # BUG: Non-constant time comparison
        return True
    return False

# VULNERABILITY: Insecure file permissions
def save_sensitive_data(data, filename):
    # Creates file with insecure permissions
    with open(filename, 'w') as f:
        f.write(data)
    # No permission setting - defaults to 644 (world-readable)

# VULNERABILITY: Directory traversal in file operations
def read_user_file(username, filename):
    # No path validation
    path = f"/var/data/{username}/{filename}"  # BUG: Can use ../../../etc/passwd
    with open(path, 'r') as f:
        return f.read()

# VULNERABILITY: Integer overflow
def calculate_price(quantity, price_per_item):
    # No overflow check
    total = quantity * price_per_item  # BUG: Can overflow
    return total

# VULNERABILITY: Regex DoS (ReDoS)
import re

def validate_email(email):
    # Vulnerable regex pattern
    pattern = r'^([a-zA-Z0-9]+)+@[a-zA-Z0-9]+\.[a-zA-Z]{2,}$'  # BUG: Catastrophic backtracking
    return re.match(pattern, email)

# VULNERABILITY: Logging sensitive data
import logging

def process_payment(card_number, cvv, amount):
    logging.info(f"Processing payment: Card={card_number}, CVV={cvv}, Amount={amount}")  # BUG: Logging PII
    return True

# VULNERABILITY: HTTP instead of HTTPS
def fetch_user_data(user_id):
    import requests
    url = f"http://api.example.com/users/{user_id}"  # BUG: Unencrypted HTTP
    response = requests.get(url)
    return response.json()

# VULNERABILITY: No input validation
def set_user_age(age):
    # No validation
    user_age = age  # BUG: Could be negative, string, etc.
    return user_age

# VULNERABILITY: Buffer overflow equivalent (unbounded string operations)
def create_username(first_name, last_name):
    # No length limits
    username = first_name + last_name  # BUG: No max length check
    return username

# VULNERABILITY: Unvalidated redirects
def redirect_after_login(next_url):
    # No URL validation
    return f"Redirecting to {next_url}"  # BUG: Open redirect vulnerability

# VULNERABILITY: Missing rate limiting
def send_email(recipient, message):
    # No rate limiting
    print(f"Sending email to {recipient}: {message}")
    return True

# VULNERABILITY: Sensitive data in comments
def connect_to_database():
    # Production credentials: admin / P@ssw0rd123
    # Server: db.prod.internal.com:5432
    pass

# VULNERABILITY: Old cryptographic algorithm
def encrypt_data(data):
    from Crypto.Cipher import DES  # BUG: DES is deprecated
    key = b'8bytekey'
    cipher = DES.new(key, DES.MODE_ECB)
    return cipher.encrypt(data)

# VULNERABILITY: No CSRF protection
def update_user_email(new_email):
    # No CSRF token validation
    return f"Email updated to {new_email}"

# VULNERABILITY: Unprotected API endpoints
def delete_all_users():
    # No authorization check
    return "All users deleted"