import os

# What makes a bug CRITICAL (overrides tool output)
CRITICAL_KEYWORDS = [
    "sql injection", "command injection", "code injection",
    "xxe", "deserialization", "path traversal", "rce"
]

# What makes a bug HIGH severity (overrides tool output)
HIGH_KEYWORDS = [
    "xss", "csrf", "authentication", "authorization",
    "hardcoded", "secret", "password", "crypto"
]

# Report customization
ITEMS_PER_PAGE = 20           # Vulnerabilities per page
CODE_CONTEXT_LINES = 1        # Lines of code to show
SCANNER_TIMEOUT =  60         # 1 minute max
LLM_TIMEOUT = 120             # 2 minutes max