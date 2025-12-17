#!/usr/bin/env python3
"""
Configuration management for the security scanner
"""

import os

# LLM Provider Configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")  # openai, anthropic, ollama, lmstudio
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

# Severity Classification Keywords
CRITICAL_KEYWORDS = [
    "sql injection", "command injection", "code injection",
    "xxe", "deserialization", "path traversal", "rce"
]

HIGH_KEYWORDS = [
    "xss", "csrf", "authentication", "authorization",
    "hardcoded", "secret", "password", "crypto"
]

# Report Settings
ITEMS_PER_PAGE = 20
CODE_CONTEXT_LINES = 4

# Scanner Settings
SCANNER_TIMEOUT = 300  # seconds