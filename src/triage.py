"""
LLM-powered triage and prioritization of security findings
"""

import json
import re
from datetime import datetime
from typing import List, Dict

from config import CRITICAL_KEYWORDS, HIGH_KEYWORDS, LLM_TIMEOUT


def call_llm(prompt: str) -> str:
    """
    Call local LM Studio LLM.
    LM Studio supports OpenAI-compatible API but may need model parameter.
    """
    try:
        import requests
        
        # Try to get the loaded model name from LM Studio
        # First, try without model parameter (works if model is already loaded)
        request_body = {
            "messages": [
                {"role": "system", "content": "You are a senior security engineer analyzing code vulnerabilities. Always respond with valid JSON only, no preamble or explanations."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            json=request_body,
            timeout=LLM_TIMEOUT
        )
        
        # Check if request was successful
        if response.status_code != 200:
            # If failed, try adding a generic model parameter
            request_body["model"] = "local-model"
            response = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json=request_body,
                timeout=LLM_TIMEOUT
            )
        
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Debug: print response structure on first call
        if not hasattr(call_llm, '_debug_printed'):
            print(f"\n   [DEBUG] LM Studio response keys: {list(data.keys())}")
            call_llm._debug_printed = True
        
        # LM Studio uses OpenAI-compatible format with "choices"
        if "choices" in data and len(data["choices"]) > 0:
            choice = data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"]
            elif "text" in choice:
                return choice["text"]
        
        # Fallback: check for other common response formats
        elif "response" in data:
            return data["response"]
        elif "content" in data:
            return data["content"]
        elif "text" in data:
            return data["text"]
        elif "message" in data:
            if isinstance(data["message"], dict) and "content" in data["message"]:
                return data["message"]["content"]
            return str(data["message"])
        else:
            # Last resort: return the whole response as string for debugging
            return f"Error: Unexpected response format. Keys: {list(data.keys())}. Full response: {json.dumps(data, indent=2)}"
    
    except requests.exceptions.ConnectionError as e:
        return f"Error: Cannot connect to LM Studio. Make sure LM Studio is running on localhost:1234 with a model loaded."
    except requests.exceptions.Timeout as e:
        return f"Error: LM Studio request timed out after {LLM_TIMEOUT} seconds."
    except requests.exceptions.RequestException as e:
        return f"Error calling LM Studio (HTTP {response.status_code if 'response' in locals() else 'unknown'}): {e}"
    except json.JSONDecodeError as e:
        return f"Error: LM Studio returned invalid JSON: {e}. Response text: {response.text[:200] if 'response' in locals() else 'N/A'}"
    except KeyError as e:
        return f"Error parsing LM Studio response (missing key {e}). Response: {json.dumps(data, indent=2) if 'data' in locals() else 'N/A'}"
    except Exception as e:
        return f"Error calling LM Studio: {type(e).__name__}: {e}"

def triage_findings(findings: List[Dict], prompts_file: str = 'prompts_temp.txt', llm_top_k: int = 10) -> List[Dict]:
    """Use LLM to prioritize and enrich findings"""
    
    if not findings:
        return []
    
    print(f"Analyzing findings with LLM (lmstudio)...")
    
    # Batch findings by severity for efficient LLM calls
    critical_findings = [f for f in findings if any(kw in f['message'].lower() for kw in CRITICAL_KEYWORDS)]
    high_findings = [f for f in findings if f not in critical_findings and any(kw in f['message'].lower() for kw in HIGH_KEYWORDS)]
    other_findings = [f for f in findings if f not in critical_findings and f not in high_findings]
    
    # Override severity based on keywords
    for f in critical_findings:
        f['severity'] = 'CRITICAL'
    for f in high_findings:
        f['severity'] = 'HIGH'
    
    # Get LLM analysis for top most severe findings
    top_findings = (critical_findings + high_findings + other_findings)[:llm_top_k] if llm_top_k != -1 else findings
    
    print(f"Analyzing {len(top_findings)} findings with LLM (lmstudio)...")
    
    for idx, finding in enumerate(top_findings, 1):
        print(f"   Analyzing {idx}/{len(top_findings)}: {finding['title']}")
        
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
        
        # Check if response is an error message
        if llm_response.startswith("Error:"):
            print(f"      Warning: {llm_response[:100]}")
            finding['llm_analysis'] = {"error": llm_response}
            continue
        
        # Parse LLM response (handle potential JSON in markdown or with preamble)
        try:
            # Try to find JSON in the response (handle cases where LLM adds text before/after)
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                llm_data = json.loads(json_str)
                finding['llm_analysis'] = llm_data
                
                # Update priority if LLM suggests different severity
                if llm_data.get('false_positive', '').upper() == 'HIGH':
                    finding['severity'] = 'INFO'
                elif llm_data.get('priority'):
                    finding['severity'] = llm_data['priority'].upper()
            else:
                # No JSON found - store raw response
                finding['llm_analysis'] = {"raw_response": llm_response}
                print(f"      Warning: Could not extract JSON from LLM response")
        
        except json.JSONDecodeError as e:
            finding['llm_analysis'] = {"raw_response": llm_response, "parse_error": str(e)}
            print(f"      Warning: JSON parse error: {e}")
    
    # Sort by severity
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
    findings.sort(key=lambda f: (severity_order.get(f['severity'], 5), f['file']))
    
    return findings