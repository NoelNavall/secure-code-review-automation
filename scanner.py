#!/usr/bin/env python3
"""
Secure Code Review Automation - Main Scanner
Orchestrates static analysis tools and LLM-powered triage
"""

import json
import subprocess
import sys
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import argparse

# ============================================================================
# CONFIGURATION
# ============================================================================

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")  # openai, anthropic, ollama, lmstudio
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Severity classification keywords
CRITICAL_KEYWORDS = [
    "sql injection", "command injection", "code injection",
    "xxe", "deserialization", "path traversal", "rce"
]

HIGH_KEYWORDS = [
    "xss", "csrf", "authentication", "authorization",
    "hardcoded", "secret", "password", "crypto"
]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def run_command(cmd: List[str], cwd: str = ".") -> Dict[str, Any]:
    """Execute shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }

def ensure_directories():
    """Create required directories"""
    Path("reports").mkdir(exist_ok=True)

# ============================================================================
# SCANNER INTEGRATION
# ============================================================================

def run_semgrep(target_dir: str) -> List[Dict]:
    """Run Semgrep static analysis"""
    print("Running Semgrep...")
    
    result = run_command([
        "semgrep",
        "--config=auto",
        "--json",
        "--quiet",
        target_dir
    ])
    
    if not result["success"]:
        print(f"WARNING - Semgrep: {result['stderr']}")
    
    try:
        data = json.loads(result["stdout"]) if result["stdout"] else {"results": []}
        findings = []
        
        for item in data.get("results", []):
            findings.append({
                "tool": "semgrep",
                "severity": item.get("extra", {}).get("severity", "MEDIUM").upper(),
                "title": item.get("check_id", "Unknown").split(".")[-1],
                "message": item.get("extra", {}).get("message", item.get("check_id", "")),
                "file": item.get("path", ""),
                "line": item.get("start", {}).get("line", 0),
                "code": item.get("extra", {}).get("lines", ""),
                "cwe": item.get("extra", {}).get("metadata", {}).get("cwe", [])
            })
        
        print(f"   Found {len(findings)} Semgrep findings")
        return findings
    
    except json.JSONDecodeError:
        print("   No Semgrep findings or invalid JSON")
        return []

def run_bandit(target_dir: str) -> List[Dict]:
    """Run Bandit security linter for Python"""
    print("Running Bandit...")
    
    result = run_command([
        "bandit",
        "-r", target_dir,
        "-f", "json",
        "-ll"  # Only report LOW and above
    ])
    
    try:
        data = json.loads(result["stdout"]) if result["stdout"] else {"results": []}
        findings = []
        
        for item in data.get("results", []):
            findings.append({
                "tool": "bandit",
                "severity": item.get("issue_severity", "MEDIUM").upper(),
                "title": item.get("test_name", "Unknown"),
                "message": item.get("issue_text", ""),
                "file": item.get("filename", ""),
                "line": item.get("line_number", 0),
                "code": item.get("code", ""),
                "cwe": [item.get("issue_cwe", {}).get("id", "")] if item.get("issue_cwe") else []
            })
        
        print(f"   Found {len(findings)} Bandit findings")
        return findings
    
    except json.JSONDecodeError:
        print("   No Bandit findings or invalid JSON")
        return []

def normalize_findings(semgrep_findings: List[Dict], bandit_findings: List[Dict]) -> List[Dict]:
    """Combine and deduplicate findings"""
    all_findings = semgrep_findings + bandit_findings
    
    # Simple deduplication by file + line
    seen = set()
    unique_findings = []
    
    for finding in all_findings:
        key = f"{finding['file']}:{finding['line']}:{finding['title']}"
        if key not in seen:
            seen.add(key)
            unique_findings.append(finding)
    
    return unique_findings

# ============================================================================
# LLM INTEGRATION
# ============================================================================

def call_openai(prompt: str) -> str:
    """Call OpenAI API"""
    try:
        import openai
        openai.api_key = OPENAI_API_KEY
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper and faster
            messages=[
                {"role": "system", "content": "You are a senior security engineer reviewing code vulnerabilities. Provide concise, actionable remediation advice."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error calling OpenAI: {e}"

def call_anthropic(prompt: str) -> str:
    """Call Anthropic Claude API"""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": f"You are a senior security engineer reviewing code vulnerabilities. Provide concise, actionable remediation advice.\n\n{prompt}"}
            ]
        )
        
        return response.content[0].text
    
    except Exception as e:
        return f"Error calling Anthropic: {e}"

def call_ollama(prompt: str) -> str:
    """Call local Ollama LLM"""
    try:
        import requests
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama2",
                "prompt": f"You are a senior security engineer. {prompt}",
                "stream": False
            },
            timeout=120
        )
        
        return response.json().get("response", "No response from Ollama")
    
    except Exception as e:
        return f"Error calling Ollama: {e}\nMake sure Ollama is running: ollama serve"

def call_lmstudio(prompt: str) -> str:
    """Call LM Studio local server (OpenAI-compatible API)"""
    try:
        import requests
        
        # LM Studio runs OpenAI-compatible server on port 1234 by default
        lm_studio_url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1/chat/completions")
        
        response = requests.post(
            lm_studio_url,
            json={
                "messages": [
                    {"role": "system", "content": "You are a senior security engineer reviewing code vulnerabilities. Provide concise, actionable remediation advice."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            },
            timeout=120
        )
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"Error calling LM Studio: {e}\nMake sure LM Studio server is running on port 1234"

def call_llm(prompt: str) -> str:
    """Route to appropriate LLM provider"""
    if LLM_PROVIDER == "openai":
        if not OPENAI_API_KEY:
            return "ERROR: OPENAI_API_KEY not set. Run: export OPENAI_API_KEY='sk-...'"
        return call_openai(prompt)
    
    elif LLM_PROVIDER == "anthropic":
        if not ANTHROPIC_API_KEY:
            return "ERROR: ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY='sk-ant-...'"
        return call_anthropic(prompt)
    
    elif LLM_PROVIDER == "ollama":
        return call_ollama(prompt)
    
    elif LLM_PROVIDER == "lmstudio":
        return call_lmstudio(prompt)
    
    else:
        return f"ERROR: Unknown LLM_PROVIDER '{LLM_PROVIDER}'. Use: openai, anthropic, ollama, or lmstudio"

def triage_findings(findings: List[Dict]) -> List[Dict]:
    """Use LLM to prioritize and enrich findings"""
    print(f"\nAnalyzing {len(findings)} findings with LLM ({LLM_PROVIDER})...")
    
    if not findings:
        return []
    
    # Batch findings by severity for efficient LLM calls
    critical_findings = [f for f in findings if any(kw in f['message'].lower() for kw in CRITICAL_KEYWORDS)]
    high_findings = [f for f in findings if f not in critical_findings and any(kw in f['message'].lower() for kw in HIGH_KEYWORDS)]
    other_findings = [f for f in findings if f not in critical_findings and f not in high_findings]
    
    # Override severity based on keywords
    for f in critical_findings:
        f['severity'] = 'CRITICAL'
    for f in high_findings:
        f['severity'] = 'HIGH'
    
    # Get LLM analysis for top 10 most severe findings
    top_findings = (critical_findings + high_findings + other_findings)[:10]
    
    # Will be set by main() before calling this function
    prompts_file = getattr(triage_findings, 'prompts_file', 'prompts_temp.txt')
    
    for idx, finding in enumerate(top_findings):
        print(f"   Analyzing {idx+1}/{len(top_findings)}: {finding['title']}")
        
        prompt = f"""Analyze this security vulnerability:

Title: {finding['title']}
Severity: {finding['severity']}
File: {finding['file']}:{finding['line']}
Description: {finding['message']}
Code snippet:
{finding['code'][:500]}

Provide:
1. EXPLOITABILITY: How easily can this be exploited? (1-5 scale, 5=trivial)
2. IMPACT: What's the worst-case outcome?
3. FALSE_POSITIVE: Likelihood this is a false alarm? (LOW/MEDIUM/HIGH)
4. REMEDIATION: Specific code fix (max 3 lines)
5. PRIORITY: CRITICAL/HIGH/MEDIUM/LOW

Format as JSON:
{{"exploitability": 4, "impact": "...", "false_positive": "LOW", "remediation": "...", "priority": "HIGH"}}"""
        
        # Save prompt for transparency
        with open(prompts_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Finding: {finding['title']}\n")
            f.write(f"Prompt:\n{prompt}\n")
        
        llm_response = call_llm(prompt)
        
        # Save response
        with open(prompts_file, "a", encoding="utf-8") as f:
            f.write(f"Response:\n{llm_response}\n")
        
        # Parse LLM response (handle potential JSON in markdown)
        try:
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                llm_data = json.loads(json_match.group())
                finding['llm_analysis'] = llm_data
                
                # Update priority if LLM suggests different severity
                if llm_data.get('false_positive', '').upper() == 'HIGH':
                    finding['severity'] = 'INFO'
                elif llm_data.get('priority'):
                    finding['severity'] = llm_data['priority'].upper()
            else:
                finding['llm_analysis'] = {"raw_response": llm_response}
        
        except json.JSONDecodeError:
            finding['llm_analysis'] = {"raw_response": llm_response}
    
    # Sort by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
    findings.sort(key=lambda x: severity_order.get(x['severity'], 99))
    
    return findings

# ============================================================================
# REPORT GENERATION
# ============================================================================

def get_code_context(filepath: str, line_number: int, context_lines: int = 5) -> str:
    """
    Extract code context around a specific line with line numbers.
    Shows context_lines before and after the vulnerable line.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Calculate range (don't go below 1 or above file length)
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        # Build formatted output with line numbers
        result = []
        for i in range(start, end):
            line_num = i + 1
            line_content = lines[i].rstrip()
            
            # Mark the vulnerable line
            if line_num == line_number:
                result.append(f"➤ {line_num:4d}  {line_content}  ← VULNERABLE LINE")
            else:
                result.append(f"  {line_num:4d}  {line_content}")
        
        return '\n'.join(result)
    
    except Exception as e:
        # Fallback to original snippet if file can't be read
        return f"Could not read file context: {str(e)}"

def generate_json_report(findings: List[Dict], output_path: str):
    """Generate normalized JSON report"""
    report = {
        "scan_id": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "timestamp": datetime.now().isoformat(),
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
    """Generate developer-friendly HTML report"""
    
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Security Scan Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .summary { display: flex; gap: 15px; margin: 20px 0; }
        .stat { 
            background: white; 
            padding: 15px; 
            border-radius: 5px; 
            flex: 1; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }
        .stat:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 4px 8px rgba(0,0,0,0.2); 
        }
        .stat.active { 
            box-shadow: 0 0 0 3px #3498db;
            transform: scale(1.05);
        }
        .stat.critical { border-left: 4px solid #e74c3c; }
        .stat.high { border-left: 4px solid #e67e22; }
        .stat.medium { border-left: 4px solid #f39c12; }
        .stat.low { border-left: 4px solid #3498db; }
        .stat.critical.active { border-left: 4px solid #e74c3c; background: #fee; }
        .stat.high.active { border-left: 4px solid #e67e22; background: #fef3e6; }
        .stat.medium.active { border-left: 4px solid #f39c12; background: #fef9e6; }
        .stat.low.active { border-left: 4px solid #3498db; background: #e6f3fe; }
        .finding { background: white; padding: 20px; margin: 15px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.3s ease; }
        .finding.hidden { display: none; }
        .finding.CRITICAL { border-left: 5px solid #e74c3c; }
        .finding.HIGH { border-left: 5px solid #e67e22; }
        .finding.MEDIUM { border-left: 5px solid #f39c12; }
        .finding.LOW { border-left: 5px solid #3498db; }
        .severity { display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; color: white; }
        .severity.CRITICAL { background: #e74c3c; }
        .severity.HIGH { background: #e67e22; }
        .severity.MEDIUM { background: #f39c12; }
        .severity.LOW { background: #3498db; }
        code { 
            background: #2d2d2d; 
            color: #f8f8f2; 
            padding: 15px; 
            display: block; 
            border-radius: 5px; 
            overflow-x: auto; 
            margin: 10px 0; 
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.6;
        }
        .remediation { background: #d4edda; border: 1px solid #c3e6cb; padding: 10px; border-radius: 3px; margin: 10px 0; }
        .location { color: #7f8c8d; font-size: 0.9em; }
        .filter-hint { 
            text-align: center; 
            color: #7f8c8d; 
            font-size: 0.9em; 
            margin-top: 10px;
            font-style: italic;
        }
        .results-count {
            text-align: center;
            padding: 15px;
            background: #3498db;
            color: white;
            border-radius: 5px;
            margin: 20px 0;
            font-size: 1.1em;
            font-weight: bold;
        }
        .pagination {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 30px 0;
            padding: 20px;
            background: white;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .pagination-info {
            font-size: 1.1em;
            color: #2c3e50;
            font-weight: bold;
        }
        .pagination-buttons {
            display: flex;
            gap: 5px;
            align-items: center;
        }
        .page-btn {
            padding: 8px 15px;
            border: 1px solid #3498db;
            background: white;
            color: #3498db;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .page-btn:hover {
            background: #3498db;
            color: white;
            transform: translateY(-2px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .page-btn.active {
            background: #3498db;
            color: white;
            font-weight: bold;
        }
        .page-ellipsis {
            padding: 0 5px;
            color: #7f8c8d;
        }
        .findings-container {
            margin-bottom: 30px;
        }
    </style>
    <script>
        let activeFilters = new Set();
        let currentPage = 1;
        const itemsPerPage = 20;
        
        function toggleFilter(severity) {
            const stat = document.querySelector('.stat.' + severity.toLowerCase());
            
            if (activeFilters.has(severity)) {
                // Remove filter
                activeFilters.delete(severity);
                stat.classList.remove('active');
            } else {
                // Add filter
                activeFilters.add(severity);
                stat.classList.add('active');
            }
            
            currentPage = 1; // Reset to page 1 when filter changes
            applyFilters();
        }
        
        function applyFilters() {
            const findings = document.querySelectorAll('.finding');
            let visibleFindings = [];
            
            // First pass: determine which findings match filters
            findings.forEach(finding => {
                if (activeFilters.size === 0) {
                    visibleFindings.push(finding);
                } else {
                    let shouldShow = false;
                    activeFilters.forEach(filter => {
                        if (finding.classList.contains(filter)) {
                            shouldShow = true;
                        }
                    });
                    if (shouldShow) {
                        visibleFindings.push(finding);
                    }
                }
            });
            
            // Second pass: apply pagination
            const totalPages = Math.ceil(visibleFindings.length / itemsPerPage);
            const startIndex = (currentPage - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            
            findings.forEach(finding => finding.classList.add('hidden'));
            
            visibleFindings.forEach((finding, index) => {
                if (index >= startIndex && index < endIndex) {
                    finding.classList.remove('hidden');
                } else {
                    finding.classList.add('hidden');
                }
            });
            
            updateResultsCount(visibleFindings.length, findings.length);
            updatePagination(visibleFindings.length, totalPages);
        }
        
        function changePage(newPage) {
            currentPage = newPage;
            applyFilters();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
        
        function updatePagination(totalVisible, totalPages) {
            let paginationDiv = document.getElementById('pagination');
            if (!paginationDiv) {
                paginationDiv = document.createElement('div');
                paginationDiv.id = 'pagination';
                paginationDiv.className = 'pagination';
                document.querySelector('.findings-container').appendChild(paginationDiv);
            }
            
            if (totalPages <= 1) {
                paginationDiv.style.display = 'none';
                return;
            }
            
            paginationDiv.style.display = 'flex';
            
            let html = '<div class="pagination-info">Page ' + currentPage + ' of ' + totalPages + '</div>';
            html += '<div class="pagination-buttons">';
            
            // Previous button
            if (currentPage > 1) {
                html += '<button onclick="changePage(' + (currentPage - 1) + ')" class="page-btn">← Previous</button>';
            }
            
            // Page numbers
            const maxButtons = 5;
            let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
            let endPage = Math.min(totalPages, startPage + maxButtons - 1);
            
            if (endPage - startPage < maxButtons - 1) {
                startPage = Math.max(1, endPage - maxButtons + 1);
            }
            
            if (startPage > 1) {
                html += '<button onclick="changePage(1)" class="page-btn">1</button>';
                if (startPage > 2) html += '<span class="page-ellipsis">...</span>';
            }
            
            for (let i = startPage; i <= endPage; i++) {
                if (i === currentPage) {
                    html += '<button class="page-btn active">' + i + '</button>';
                } else {
                    html += '<button onclick="changePage(' + i + ')" class="page-btn">' + i + '</button>';
                }
            }
            
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) html += '<span class="page-ellipsis">...</span>';
                html += '<button onclick="changePage(' + totalPages + ')" class="page-btn">' + totalPages + '</button>';
            }
            
            // Next button
            if (currentPage < totalPages) {
                html += '<button onclick="changePage(' + (currentPage + 1) + ')" class="page-btn">Next →</button>';
            }
            
            html += '</div>';
            paginationDiv.innerHTML = html;
        }
        
        function updateResultsCount(visible, total) {
            let resultsDiv = document.getElementById('results-count');
            if (!resultsDiv) {
                resultsDiv = document.createElement('div');
                resultsDiv.id = 'results-count';
                resultsDiv.className = 'results-count';
                document.querySelector('.summary').after(resultsDiv);
            }
            
            const totalPages = Math.ceil(visible / itemsPerPage);
            const startItem = (currentPage - 1) * itemsPerPage + 1;
            const endItem = Math.min(currentPage * itemsPerPage, visible);
            
            if (activeFilters.size === 0) {
                if (totalPages > 1) {
                    resultsDiv.textContent = `Showing ${startItem}-${endItem} of ${total} findings (Page ${currentPage}/${totalPages})`;
                } else {
                    resultsDiv.textContent = `Showing all ${total} findings`;
                }
                resultsDiv.style.background = '#3498db';
            } else {
                const filterNames = Array.from(activeFilters).join(' + ');
                if (totalPages > 1) {
                    resultsDiv.textContent = `Showing ${startItem}-${endItem} of ${visible} findings (${filterNames}) - Page ${currentPage}/${totalPages}`;
                } else {
                    resultsDiv.textContent = `Showing ${visible} of ${total} findings (${filterNames})`;
                }
                resultsDiv.style.background = '#2ecc71';
            }
        }
        
        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            applyFilters();
        });
    </script>
</head>
<body>
    <div class="header">
        <h1>Security Scan Report</h1>
        <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>
    
    <div class="summary">
        <div class="stat critical" onclick="toggleFilter('CRITICAL')">
            <h3>""" + str(sum(1 for f in findings if f['severity'] == 'CRITICAL')) + """</h3>
            <p>Critical</p>
        </div>
        <div class="stat high" onclick="toggleFilter('HIGH')">
            <h3>""" + str(sum(1 for f in findings if f['severity'] == 'HIGH')) + """</h3>
            <p>High</p>
        </div>
        <div class="stat medium" onclick="toggleFilter('MEDIUM')">
            <h3>""" + str(sum(1 for f in findings if f['severity'] == 'MEDIUM')) + """</h3>
            <p>Medium</p>
        </div>
        <div class="stat low" onclick="toggleFilter('LOW')">
            <h3>""" + str(sum(1 for f in findings if f['severity'] == 'LOW')) + """</h3>
            <p>Low</p>
        </div>
    </div>
    
    <div class="filter-hint">
        Click on severity boxes above to filter findings. Click multiple to combine filters. Click again to remove filter.
    </div>
    
    <div class="findings-container">
    <h2>Findings</h2>
"""
    
    # Show ALL findings (pagination in JavaScript)
    for idx, finding in enumerate(findings, 1):
        llm = finding.get('llm_analysis', {})
        
        html += f"""
    <div class="finding {finding['severity']}">
        <h3>{idx}. {finding['title']}</h3>
        <span class="severity {finding['severity']}">{finding['severity']}</span>
        <p class="location">File: {finding['file']}:{finding['line']} | Tool: {finding['tool']}</p>
        
        <h4>Description</h4>
        <p>{finding['message']}</p>
        
        <h4>Vulnerable Code</h4>
        <code style="white-space: pre; font-family: 'Courier New', monospace; line-height: 1.5;">{get_code_context(finding['file'], finding['line'], context_lines=4)}</code>
"""
        
        if llm:
            if llm.get('impact'):
                html += f"""
        <h4>Impact</h4>
        <p>{llm.get('impact', 'N/A')}</p>
        
        <h4>Exploitability</h4>
        <p>{llm.get('exploitability', 'N/A')}/5</p>
"""
            
            if llm.get('remediation'):
                html += f"""
        <div class="remediation">
            <h4>Remediation</h4>
            <p>{llm.get('remediation', 'See scanner documentation')}</p>
        </div>
"""
        
        html += "    </div>\n"
    
    html += """
    </div><!-- End findings-container -->
    
    <div style="margin-top: 30px; padding: 20px; background: #ecf0f1; border-radius: 5px;">
        <h3>Important Notes</h3>
        <ul>
            <li>LLM-generated suggestions should be reviewed by a human security expert</li>
            <li>False positives are possible - verify each finding in context</li>
            <li>Use pagination controls above to navigate through findings (20 per page)</li>
            <li>Always test remediation in a safe environment before production</li>
        </ul>
    </div>
</body>
</html>
"""
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"HTML report saved: {output_path}")

# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Automated Secure Code Review")
    parser.add_argument("--target", default="./sample_app", help="Directory to scan")
    parser.add_argument("--skip-llm", action="store_true", help="Skip LLM analysis")
    args = parser.parse_args()
    
    print("=" * 60)
    print("SECURE CODE REVIEW AUTOMATION")
    print("=" * 60)
    
    ensure_directories()
    
    # Check if target exists
    if not os.path.exists(args.target):
        print(f"ERROR: Target not found: {args.target}")
        print("   Please provide a valid file or directory path")
        sys.exit(1)
    
    # Run scanners
    semgrep_findings = run_semgrep(args.target)
    bandit_findings = run_bandit(args.target)
    
    # Normalize
    findings = normalize_findings(semgrep_findings, bandit_findings)
    print(f"\nTotal unique findings: {len(findings)}")
    
    if not findings:
        print("\nNo security issues found!")
        return
    
    # LLM triage
    if not args.skip_llm:
        findings = triage_findings(findings)
    else:
        print("\n⏭️  Skipping LLM analysis (--skip-llm flag)")
    
    # Generate scan folder with timestamp and target name
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    target_name = os.path.basename(args.target.rstrip('/\\'))
    if not target_name:
        target_name = "root"
    
    scan_folder = f"reports/{timestamp}_{target_name}"
    os.makedirs(scan_folder, exist_ok=True)
    
    # Set prompts file path for triage function to use
    prompts_filename = f"{scan_folder}/llm_prompts.txt"
    
    # LLM triage
    if not args.skip_llm:
        triage_findings.prompts_file = prompts_filename  # Set before calling
        findings = triage_findings(findings)
    else:
        print("\n⏭️  Skipping LLM analysis (--skip-llm flag)")
    
    # Generate report filenames
    json_filename = f"{scan_folder}/findings.json"
    html_filename = f"{scan_folder}/report.html"
    
    # Generate reports
    generate_json_report(findings, json_filename)
    generate_html_report(findings, html_filename)
    
    print("\n" + "=" * 60)
    print("\nSCAN COMPLETE")
    print("=" * 60)
    print(f"Summary:")
    print(f"   CRITICAL: {sum(1 for f in findings if f['severity'] == 'CRITICAL')}")
    print(f"   HIGH:     {sum(1 for f in findings if f['severity'] == 'HIGH')}")
    print(f"   MEDIUM:   {sum(1 for f in findings if f['severity'] == 'MEDIUM')}")
    print(f"   LOW:      {sum(1 for f in findings if f['severity'] == 'LOW')}")
    print(f"\nScan saved to: {scan_folder}/")
    print(f"   Open: {scan_folder}/report.html")

if __name__ == "__main__":
    main()