#!/usr/bin/env python3
"""
Quick test script to verify your setup is working
Run this BEFORE the full scan to catch issues early
"""

import sys
import subprocess
import os

def test_command(cmd, name):
    """Test if a command works"""
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ {name}: WORKING")
            return True
        else:
            print(f"❌ {name}: FAILED")
            print(f"   Error: {result.stderr.decode()[:100]}")
            return False
    except FileNotFoundError:
        print(f"❌ {name}: NOT INSTALLED")
        return False
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        return False

def test_api_key(provider):
    """Test if API key is set and working"""
    if provider == "openai":
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            print("❌ OpenAI API Key: NOT SET")
            print("   Fix: export OPENAI_API_KEY='sk-proj-xxxxx'")
            return False
        
        try:
            import openai
            openai.api_key = key
            # Quick test call
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Respond with: OK"}],
                max_tokens=10
            )
            if response.choices[0].message.content:
                print("✅ OpenAI API Key: WORKING")
                return True
        except ImportError:
            print("❌ OpenAI library: NOT INSTALLED")
            print("   Fix: pip install openai")
            return False
        except Exception as e:
            print(f"❌ OpenAI API Key: INVALID")
            print(f"   Error: {str(e)[:100]}")
            return False
    
    elif provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            print("❌ Anthropic API Key: NOT SET")
            print("   Fix: export ANTHROPIC_API_KEY='sk-ant-xxxxx'")
            return False
        
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=10,
                messages=[{"role": "user", "content": "Respond with: OK"}]
            )
            if response.content:
                print("✅ Anthropic API Key: WORKING")
                return True
        except ImportError:
            print("❌ Anthropic library: NOT INSTALLED")
            print("   Fix: pip install anthropic")
            return False
        except Exception as e:
            print(f"❌ Anthropic API Key: INVALID")
            print(f"   Error: {str(e)[:100]}")
            return False
    
    elif provider == "ollama":
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                print("✅ Ollama: RUNNING")
                return True
            else:
                print("❌ Ollama: NOT RESPONDING")
                return False
        except:
            print("❌ Ollama: NOT RUNNING")
            print("   Fix: ollama serve")
            return False
    
    elif provider == "lmstudio":
        try:
            import requests
            lm_studio_url = os.environ.get("LM_STUDIO_URL", "http://localhost:1234/v1/models")
            response = requests.get(lm_studio_url, timeout=3)
            if response.status_code == 200:
                print("✅ LM Studio: RUNNING")
                # Try to show loaded model
                data = response.json()
                if data.get("data"):
                    model_name = data["data"][0].get("id", "unknown")
                    print(f"   Loaded model: {model_name}")
                return True
            else:
                print("❌ LM Studio: NOT RESPONDING")
                return False
        except Exception as e:
            print("❌ LM Studio: NOT RUNNING")
            print("   Fix: Start server in LM Studio GUI")
            print("   See: LMSTUDIO_GUIDE.md")
            return False
    
    return False

def main():
    print("=" * 60)
    print("🧪 TESTING YOUR SETUP")
    print("=" * 60)
    print()
    
    results = []
    
    # Test Python version
    print("Testing Python version...")
    version = sys.version_info
    if version >= (3, 8):
        print(f"✅ Python {version.major}.{version.minor}: OK")
        results.append(True)
    else:
        print(f"❌ Python {version.major}.{version.minor}: TOO OLD (need 3.8+)")
        results.append(False)
    print()
    
    # Test scanners
    print("Testing security scanners...")
    results.append(test_command(["semgrep", "--version"], "Semgrep"))
    results.append(test_command(["bandit", "--version"], "Bandit"))
    print()
    
    # Test Python libraries
    print("Testing Python libraries...")
    try:
        import openai
        print("✅ openai library: INSTALLED")
        results.append(True)
    except ImportError:
        print("⚠️  openai library: NOT INSTALLED (ok if using Ollama)")
        results.append(True)  # Not critical
    
    try:
        import anthropic
        print("✅ anthropic library: INSTALLED")
        results.append(True)
    except ImportError:
        print("⚠️  anthropic library: NOT INSTALLED (ok if using OpenAI)")
        results.append(True)  # Not critical
    
    try:
        import requests
        print("✅ requests library: INSTALLED")
        results.append(True)
    except ImportError:
        print("❌ requests library: NOT INSTALLED")
        print("   Fix: pip install requests")
        results.append(False)
    print()
    
    # Test LLM provider
    print("Testing LLM provider...")
    provider = os.environ.get("LLM_PROVIDER", "openai")
    print(f"Current provider: {provider}")
    results.append(test_api_key(provider))
    print()
    
    # Test file structure
    print("Testing file structure...")
    required_files = [
        "scanner.py",
        "sample_app/app.py",
        "sample_app/utils.py",
        "README.md"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}: EXISTS")
            results.append(True)
        else:
            print(f"❌ {file}: MISSING")
            results.append(False)
    print()
    
    # Summary
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ ALL TESTS PASSED ({passed}/{total})")
        print()
        print("🚀 You're ready to run the scanner!")
        print("   Next step: python scanner.py --target ./sample_app")
        return 0
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total} passed)")
        print()
        print("📝 Fix the issues above, then run this test again.")
        print("   Need help? Check SETUP_GUIDE.md")
        return 1

if __name__ == "__main__":
    sys.exit(main())
