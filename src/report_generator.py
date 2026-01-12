#!/usr/bin/env python3
"""
Report generation - creates HTML and JSON reports from scan results
"""

import json
from datetime import datetime
from typing import List, Dict


# Basic remediation guidance when LLM is not available
BASIC_REMEDIATION = {
    "sql": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id=?', (user_id,))",
    "command injection": "Use subprocess with list arguments instead of shell=True: subprocess.run(['ping', '-c', '1', host])",
    "hardcoded": "Store secrets in environment variables or a secrets manager, not in code",
    "xss": "Use proper HTML escaping: from markupsafe import escape; return escape(user_input)",
    "pickle": "Use JSON instead of pickle for untrusted data, or implement signature verification",
    "md5": "Use SHA-256 or stronger: hashlib.sha256(data.encode()).hexdigest()",
    "des": "Use AES encryption from cryptography library: from cryptography.fernet import Fernet",
    "yaml.load": "Use yaml.safe_load() instead of yaml.load() to prevent code execution",
    "eval": "Never use eval() on user input. Use ast.literal_eval() for safe evaluation",
    "assert": "Don't use assert for security checks. Use proper if/raise statements",
    "xxe": "Use defusedxml library or disable external entity processing",
    "timeout": "Add timeout parameter: requests.get(url, timeout=5)",
}

def get_basic_remediation(finding: Dict) -> str:
    """Get basic remediation advice based on vulnerability type"""
    message = finding.get('message', '').lower()
    title = finding.get('title', '').lower()
    
    for keyword, advice in BASIC_REMEDIATION.items():
        if keyword in message or keyword in title:
            return advice
    
    return "Review the code and apply security best practices for this vulnerability type"


def get_code_context(filepath: str, line_number: int, context_lines: int = 5) -> str:
    """
    Get code around the vulnerable line so you can see what's happening
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Don't go below line 1 or above last line
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        # Build output with line numbers
        result = []
        for i in range(start, end):
            line_num = i + 1
            line_content = lines[i].rstrip()
            
            # Mark the vulnerable line
            if line_num == line_number:
                result.append(f">>> {line_num:4d}  {line_content}  ← BUG HERE")
            else:
                result.append(f"    {line_num:4d}  {line_content}")
        
        return '\n'.join(result)
    
    except Exception as e:
        return f"Couldn't read file: {str(e)}"


def generate_json_report(findings: List[Dict], output_path: str):
    """
    Save findings as JSON for processing later
    """
    report = {
        "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_findings": len(findings),
        "summary": {
            "CRITICAL": sum(1 for f in findings if f['severity'] == 'CRITICAL'),
            "HIGH": sum(1 for f in findings if f['severity'] == 'HIGH'),
            "MEDIUM": sum(1 for f in findings if f['severity'] == 'MEDIUM'),
            "LOW": sum(1 for f in findings if f['severity'] == 'LOW'),
        },
        "findings": findings
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nJSON report saved: {output_path}")


def generate_html_report(findings: List[Dict], output_path: str):
    """
    Generate simple HTML report that you can open in a browser
    """
    
    # Basic HTML with simple styling
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Security Scan Report</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #f0f0f0; 
        }
        .header { 
            background: #333; 
            color: white; 
            padding: 20px; 
            border-radius: 5px; 
        }
        .summary { 
            display: flex; 
            gap: 10px; 
            margin: 20px 0; 
        }
        .stat { 
            background: white; 
            padding: 15px; 
            border-radius: 5px; 
            flex: 1; 
            text-align: center;
            cursor: pointer;
        }
        .stat:hover { 
            background: #e0e0e0; 
        }
        .stat.active { 
            border: 2px solid #0066cc;
            background: #e6f2ff;
        }
        .stat.critical { border-left: 5px solid #d32f2f; }
        .stat.high { border-left: 5px solid #f57c00; }
        .stat.medium { border-left: 5px solid #fbc02d; }
        .stat.low { border-left: 5px solid #388e3c; }
        
        .finding { 
            background: white; 
            padding: 15px; 
            margin: 15px 0; 
            border-radius: 5px; 
        }
        .finding.hidden { 
            display: none; 
        }
        .finding.CRITICAL { border-left: 5px solid #d32f2f; }
        .finding.HIGH { border-left: 5px solid #f57c00; }
        .finding.MEDIUM { border-left: 5px solid #fbc02d; }
        .finding.LOW { border-left: 5px solid #388e3c; }
        
        .severity { 
            display: inline-block; 
            padding: 5px 10px; 
            border-radius: 3px; 
            color: white; 
            font-weight: bold;
        }
        .severity.CRITICAL { background: #d32f2f; }
        .severity.HIGH { background: #f57c00; }
        .severity.MEDIUM { background: #fbc02d; }
        .severity.LOW { background: #388e3c; }
        
        code { 
            background: #2b2b2b; 
            color: #f8f8f8; 
            padding: 10px; 
            display: block; 
            border-radius: 3px; 
            overflow-x: auto; 
            font-family: 'Courier New', monospace;
            font-size: 14px;
            white-space: pre;
        }
        
        .info { 
            background: #e8f5e9; 
            border: 1px solid #c8e6c9; 
            padding: 10px; 
            border-radius: 3px; 
            margin: 10px 0; 
        }
        
        .warning {
            background: #fff3e0;
            border: 1px solid #ffb74d;
            padding: 10px;
            border-radius: 3px;
            margin: 10px 0;
        }
        
        .location { 
            color: #666; 
            font-size: 0.9em; 
        }
        
        h3 { 
            margin-top: 0; 
        }
        
        .filter-info {
            text-align: center;
            color: #666;
            margin: 10px 0;
            font-style: italic;
        }
        
        .pagination {
            text-align: center;
            margin: 20px 0;
        }
        
        .page-btn {
            padding: 8px 12px;
            margin: 0 5px;
            border: 1px solid #ccc;
            background: white;
            cursor: pointer;
            border-radius: 3px;
        }
        
        .page-btn:hover {
            background: #e0e0e0;
        }
        
        .page-btn.active {
            background: #0066cc;
            color: white;
            border-color: #0066cc;
        }
    </style>
    <script>
        // Simple filtering and pagination
        let activeFilters = new Set();
        let currentPage = 1;
        const itemsPerPage = 20;
        
        function toggleFilter(severity) {
            if (activeFilters.has(severity)) {
                activeFilters.delete(severity);
            } else {
                activeFilters.add(severity);
            }
            
            // Update button styles
            document.querySelectorAll('.stat').forEach(btn => {
                btn.classList.remove('active');
            });
            activeFilters.forEach(sev => {
                document.querySelector('.stat.' + sev.toLowerCase()).classList.add('active');
            });
            
            currentPage = 1;
            applyFilters();
        }
        
        function applyFilters() {
            const findings = document.querySelectorAll('.finding');
            let visible = [];
            
            findings.forEach(finding => {
                const severity = finding.className.split(' ')[1];
                
                if (activeFilters.size === 0 || activeFilters.has(severity)) {
                    visible.push(finding);
                } else {
                    finding.classList.add('hidden');
                }
            });
            
            // Pagination
            const start = (currentPage - 1) * itemsPerPage;
            const end = start + itemsPerPage;
            
            visible.forEach((finding, idx) => {
                if (idx >= start && idx < end) {
                    finding.classList.remove('hidden');
                } else {
                    finding.classList.add('hidden');
                }
            });
            
            updatePagination(visible.length);
        }
        
        function updatePagination(totalVisible) {
            const totalPages = Math.ceil(totalVisible / itemsPerPage);
            const paginationDiv = document.getElementById('pagination');
            
            let html = '';
            
            if (currentPage > 1) {
                html += '<button class="page-btn" onclick="changePage(' + (currentPage - 1) + ')">Previous</button>';
            }
            
            for (let i = 1; i <= totalPages; i++) {
                if (i === currentPage) {
                    html += '<button class="page-btn active">' + i + '</button>';
                } else {
                    html += '<button class="page-btn" onclick="changePage(' + i + ')">' + i + '</button>';
                }
            }
            
            if (currentPage < totalPages) {
                html += '<button class="page-btn" onclick="changePage(' + (currentPage + 1) + ')">Next</button>';
            }
            
            paginationDiv.innerHTML = html;
        }
        
        function changePage(page) {
            currentPage = page;
            applyFilters();
        }
        
        // Run on page load
        window.onload = function() {
            applyFilters();
        };
    </script>
</head>
<body>
    <div class="header">
        <h1>Security Scan Report</h1>
        <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>
    
    <div class="summary">
        <div class="stat critical" onclick="toggleFilter('CRITICAL')">
            <h2>""" + str(sum(1 for f in findings if f['severity'] == 'CRITICAL')) + """</h2>
            <p>Critical</p>
        </div>
        <div class="stat high" onclick="toggleFilter('HIGH')">
            <h2>""" + str(sum(1 for f in findings if f['severity'] == 'HIGH')) + """</h2>
            <p>High</p>
        </div>
        <div class="stat medium" onclick="toggleFilter('MEDIUM')">
            <h2>""" + str(sum(1 for f in findings if f['severity'] == 'MEDIUM')) + """</h2>
            <p>Medium</p>
        </div>
        <div class="stat low" onclick="toggleFilter('LOW')">
            <h2>""" + str(sum(1 for f in findings if f['severity'] == 'LOW')) + """</h2>
            <p>Low</p>
        </div>
    </div>
    
    
    <div id="pagination" class="pagination"></div>
    
    <div id="findings">
"""
    
    # Add each finding
    for idx, finding in enumerate(findings, 1):
        llm = finding.get('llm_analysis', {})
        has_llm_data = llm and not llm.get('error') and not llm.get('raw_response')
        
        html += f"""
    <div class="finding {finding['severity']}">
        <h3>{idx}. {finding['title']}</h3>
        <span class="severity {finding['severity']}">{finding['severity']}</span>
        <p class="location">File: {finding['file']} (line {finding['line']}) | Found by: {finding['tool']}</p>
        
        <h4>What's wrong:</h4>
        <p>{finding['message']}</p>
        
        <h4>Code:</h4>
        <code>{get_code_context(finding['file'], finding['line'], context_lines=3)}</code>
"""
        
        # Add LLM analysis if available
        if has_llm_data:
            if llm.get('impact'):
                html += f"""
        <h4>Impact:</h4>
        <p>{llm.get('impact', 'Unknown')}</p>
"""
            
            if llm.get('exploitability'):
                html += f"""
        <h4>How easy to exploit:</h4>
        <p>{llm.get('exploitability', 'Unknown')}/5</p>
"""
            
            if llm.get('remediation'):
                html += f"""
        <div class="info">
            <h4>How to fix (AI-generated):</h4>
            <p>{llm.get('remediation', 'See documentation')}</p>
        </div>
"""
        else:
            # Fallback: show basic remediation when LLM not available
            basic_fix = get_basic_remediation(finding)
            html += f"""
        <div class="warning">
            <h4>How to fix (basic guidance):</h4>
            <p>{basic_fix}</p>
            <small><em>Note: LLM analysis not available. Run with --llm-top-k for detailed AI-powered remediation.</em></small>
        </div>
"""
        
        html += "    </div>\n"
    
    html += """
    </div>
    
    <div id="pagination-bottom" class="pagination"></div>

</body>
</html>
"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"HTML report saved: {output_path}")