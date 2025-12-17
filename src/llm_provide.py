#!/usr/bin/env python3
"""
LLM provider integrations (OpenAI, Anthropic, Ollama, LM Studio)
"""

from config import OPENAI_API_KEY, ANTHROPIC_API_KEY, LLM_PROVIDER


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
        return f"Error calling Ollama: {e}"


def call_lmstudio(prompt: str) -> str:
    """Call local LM Studio LLM"""
    try:
        import requests
        
        response = requests.post(
            "http://localhost:1234/v1/chat/completions",
            json={
                "model": "local-model",
                "messages": [
                    {"role": "system", "content": "You are a senior security engineer."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            },
            timeout=120
        )
        
        return response.json()["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"Error calling LM Studio: {e}"


def call_llm(prompt: str) -> str:
    """Route to appropriate LLM provider"""
    providers = {
        "openai": call_openai,
        "anthropic": call_anthropic,
        "ollama": call_ollama,
        "lmstudio": call_lmstudio
    }
    
    provider_func = providers.get(LLM_PROVIDER.lower())
    
    if not provider_func:
        return f"Unknown LLM provider: {LLM_PROVIDER}"
    
    return provider_func(prompt)