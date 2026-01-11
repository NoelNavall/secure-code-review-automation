#!/usr/bin/env python3
import os

# You're using LM Studio
LLM_PROVIDER = "lmstudio"

# What makes a bug CRITICAL
CRITICAL_KEYWORDS = [
    "sql injection", "command injection", "code injection",
    "xxe", "deserialization", "path traversal", "rce"
]

# What makes a bug HIGH severity
HIGH_KEYWORDS = [
    "xss", "csrf", "authentication", "authorization",
    "hardcoded", "secret", "password", "crypto"
]

# Report customization
ITEMS_PER_PAGE = 20           # Vulnerabilities per page
CODE_CONTEXT_LINES = 1        # Lines of code to show
SCANNER_TIMEOUT =  60        # 5 minutes max