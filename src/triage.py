#!/usr/bin/env python3
"""
LLM-powered triage and prioritization of security findings
"""

import json
import re
from datetime import datetime
from typing import List, Dict

from config import CRITICAL_KEYWORDS, HIGH_KEYWORDS, LLM_PROVIDER
from llm_provider import call_llm


def triage_findings(findings: List[Dict], prompts_file: str = 'prompts_temp.txt') -> List[Dict]:
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
    findings.sort(key=lambda f: (severity_order.get(f['severity'], 5), f['file']))
    
    return findings