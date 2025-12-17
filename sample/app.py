#!/usr/bin/env python3
"""
Sample Vulnerable Web Application
DO NOT use in production - intentionally insecure for testing
"""

from flask import Flask, request, render_template_string
import sqlite3
import os
import subprocess
import pickle

app = Flask(__name__)

# VULNERABILITY: Hardcoded secret key
app.secret_key = "supersecretkey12345"

# VULNERABILITY: SQL Injection
@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # Vulnerable to SQL injection
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)  # BUG: Direct string interpolation
    user = cursor.fetchone()
    
    if user:
        return "Login successful!"
    return "Login failed"

# VULNERABILITY: Command Injection
@app.route('/ping', methods=['GET'])
def ping():
    host = request.args.get('host', 'localhost')
    
    # Vulnerable to command injection
    result = subprocess.check_output(f"ping -c 1 {host}", shell=True)  # BUG: shell=True with user input
    return result

# VULNERABILITY: Path Traversal
@app.route('/download', methods=['GET'])
def download():
    filename = request.args.get('filename')
    
    # Vulnerable to path traversal
    with open(f"/var/www/files/{filename}", 'r') as f:  # BUG: No path validation
        return f.read()

# VULNERABILITY: XSS (Cross-Site Scripting)
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    
    # Vulnerable to XSS
    template = f"<html><body><h1>Search results for: {query}</h1></body></html>"  # BUG: Unescaped user input
    return render_template_string(template)

# VULNERABILITY: Insecure Deserialization
@app.route('/load_data', methods=['POST'])
def load_data():
    data = request.data
    
    # Vulnerable to insecure deserialization
    obj = pickle.loads(data)  # BUG: Unpickling untrusted data
    return str(obj)

# VULNERABILITY: Weak Cryptography
@app.route('/encrypt', methods=['POST'])
def encrypt():
    import hashlib
    data = request.form['data']
    
    # Vulnerable: Using MD5 for security
    hashed = hashlib.md5(data.encode()).hexdigest()  # BUG: MD5 is cryptographically broken
    return hashed

# VULNERABILITY: Missing Authentication
@app.route('/admin/delete_user', methods=['POST'])
def delete_user():
    user_id = request.form['user_id']
    
    # No authentication check!
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE id={user_id}")
    conn.commit()
    
    return "User deleted"

# VULNERABILITY: SSRF (Server-Side Request Forgery)
@app.route('/fetch_url', methods=['GET'])
def fetch_url():
    import requests
    url = request.args.get('url')
    
    # Vulnerable to SSRF
    response = requests.get(url)  # BUG: No URL validation
    return response.text

# VULNERABILITY: Information Disclosure
@app.route('/debug')
def debug():
    # Exposing sensitive debug information
    return {
        "database_password": os.environ.get("DB_PASSWORD", "default_pass"),
        "api_keys": {
            "stripe": "sk_live_123456789",
            "aws": "AKIAIOSFODNN7EXAMPLE"
        },
        "internal_ips": ["10.0.0.1", "192.168.1.100"]
    }

# VULNERABILITY: Weak Password Requirements
def create_user(username, password):
    # No password strength validation
    if len(password) < 3:  # BUG: Too weak
        return "Password too short"
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # Storing password in plaintext
    cursor.execute(f"INSERT INTO users VALUES ('{username}', '{password}')")  # BUG: No hashing
    conn.commit()

# VULNERABILITY: Race Condition
user_balance = 1000

@app.route('/transfer', methods=['POST'])
def transfer():
    global user_balance
    amount = int(request.form['amount'])
    
    # Race condition vulnerability
    if user_balance >= amount:
        # No locking mechanism
        user_balance -= amount  # BUG: Race condition
        return f"Transferred {amount}"
    return "Insufficient funds"

# VULNERABILITY: XML External Entity (XXE)
@app.route('/parse_xml', methods=['POST'])
def parse_xml():
    import xml.etree.ElementTree as ET
    xml_data = request.data
    
    # Vulnerable to XXE
    tree = ET.fromstring(xml_data)  # BUG: No XXE protection
    return tree.text

if __name__ == '__main__':
    # VULNERABILITY: Debug mode in production
    app.run(debug=True, host='0.0.0.0')  # BUG: debug=True exposes stack traces