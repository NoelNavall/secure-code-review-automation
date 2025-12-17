#!/usr/bin/env python3
"""
Static analysis scanner integrations (Semgrep, Bandit)
"""

import json
import subprocess
from typing import List, Dict, Any


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