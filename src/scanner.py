#!/usr/bin/env python3
"""
Main Security Scanner - Assignment 18
Orchestrates the security scanning pipeline by coordinating all the different modules.

This is the main entry point. It:
1. Runs Semgrep and Bandit scanners
2. Sends findings to LLM for analysis
3. Generates HTML and JSON reports
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime

# Import our custom modules
from scanners import run_semgrep, run_bandit, normalize_findings
from triage import triage_findings
from report_generator import generate_json_report, generate_html_report


def ensure_directories():
    """
    Create the reports directory if it doesn't exist.
    This is where all scan results will be saved.
    """
    Path("reports").mkdir(exist_ok=True)


def main():
    """
    Main function that runs the entire scanning pipeline.
    Parses command line arguments and coordinates all the modules.
    """
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="Automated Secure Code Review")
    parser.add_argument("--target", default="./sample_app", 
                       help="Directory or file to scan")
    parser.add_argument("--skip-llm", action="store_true", 
                       help="Skip LLM analysis (faster, but less detailed)")
    args = parser.parse_args()
    
    # Print header
    print("=" * 60)
    print("SECURE CODE REVIEW AUTOMATION")
    print("=" * 60)
    
    # Make sure reports directory exists
    ensure_directories()
    
    # Check if the target path exists
    if not os.path.exists(args.target):
        print(f"ERROR: Target not found: {args.target}")
        print("   Please provide a valid file or directory path")
        sys.exit(1)
    
    # STEP 1: Run the scanners
    print("\n[1/4] Running static analysis tools...")
    semgrep_findings = run_semgrep(args.target)
    bandit_findings = run_bandit(args.target)
    
    # STEP 2: Combine and deduplicate findings
    print("\n[2/4] Normalizing findings...")
    findings = normalize_findings(semgrep_findings, bandit_findings)
    print(f"Total unique findings: {len(findings)}")
    
    # If no vulnerabilities found, we're done
    if not findings:
        print("\n✓ No security issues found!")
        return
    
    # STEP 3: Create output folder with timestamp
    # Format: reports/2025-12-31_14-30-00_app.py/
    print("\n[3/4] Preparing output directory...")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    target_name = os.path.basename(args.target.rstrip('/\\'))
    if not target_name:
        target_name = "root"
    
    scan_folder = f"reports/{timestamp}_{target_name}"
    os.makedirs(scan_folder, exist_ok=True)
    
    # File paths for outputs
    prompts_filename = f"{scan_folder}/llm_prompts.txt"
    json_filename = f"{scan_folder}/findings.json"
    html_filename = f"{scan_folder}/report.html"
    
    # STEP 4: LLM triage (optional)
    if not args.skip_llm:
        print("\n[4/4] Analyzing with LLM...")
        findings = triage_findings(findings, prompts_filename)
    else:
        print("\n[4/4] Skipping LLM analysis (--skip-llm flag)")
    
    # STEP 5: Generate reports
    print("\nGenerating reports...")
    generate_json_report(findings, json_filename)
    generate_html_report(findings, html_filename)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print(f"Summary:")
    print(f"   CRITICAL: {sum(1 for f in findings if f['severity'] == 'CRITICAL')}")
    print(f"   HIGH:     {sum(1 for f in findings if f['severity'] == 'HIGH')}")
    print(f"   MEDIUM:   {sum(1 for f in findings if f['severity'] == 'MEDIUM')}")
    print(f"   LOW:      {sum(1 for f in findings if f['severity'] == 'LOW')}")
    print(f"\nReports saved to: {scan_folder}/")
    print(f"   View report: {html_filename}")
    print(f"\nTo view the report, open it in your browser:")
    print(f"   Windows: start {html_filename}")
    print(f"   Mac:     open {html_filename}")
    print(f"   Linux:   xdg-open {html_filename}")


if __name__ == "__main__":
    main()