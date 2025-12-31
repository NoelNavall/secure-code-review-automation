#!/usr/bin/env python3
"""
LLM provider integrations.
This module handles calling different AI services (OpenAI, Anthropic, local models).
Makes it easy to switch between providers without changing other code.
"""

# Import config settings at the top level
import config


def call_openai(prompt: str) -> str:
    """
    Call OpenAI's GPT API.
    Using gpt-4o-mini because it's cheaper and faster than GPT-4.
    """
    try:
        import openai
        openai.api_key = config.OPENAI_API_KEY
        
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
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
    """
    Call Anthropic's Claude API.
    Claude is good at detailed analysis and following instructions.
    """
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        
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
    """
    Call local Ollama LLM.
    Ollama runs models locally on your computer - free but slower.
    """
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
    """
    Call local LM Studio LLM.
    LM Studio provides an OpenAI-compatible API for local models.
    """
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
    """
    Main function that routes to the correct LLM provider.
    Checks LLM_PROVIDER setting and calls the right function.
    """
    # Get the provider setting
    provider = config.LLM_PROVIDER.lower()
    
    # Map provider names to their functions
    providers = {
        "openai": call_openai,
        "anthropic": call_anthropic,
        "ollama": call_ollama,
        "lmstudio": call_lmstudio
    }
    
    provider_func = providers.get(provider)
    
    if not provider_func:
        return f"Unknown LLM provider: {config.LLM_PROVIDER}"
    
    return provider_func(prompt)