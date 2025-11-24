# 🖥️ LM Studio Setup Guide

Complete guide for using LM Studio with this security scanner (100% FREE!)

---

## Why LM Studio?

- ✅ **FREE** - No API costs
- ✅ **Private** - Data never leaves your machine
- ✅ **Fast** - Good hardware = fast responses
- ✅ **Easy** - GUI interface for model management
- ✅ **Compatible** - Works with any GGUF model

---

## Quick Setup (5 minutes)

### Step 1: Install LM Studio

**Download from:** https://lmstudio.ai/

Available for:
- 🪟 Windows
- 🍎 macOS (Apple Silicon & Intel)
- 🐧 Linux

### Step 2: Download a Model

Open LM Studio and search for models. **Recommended options:**

#### Option A: GPT-OSS-20B (Your choice - Good balance)
```
Search in LM Studio: "gpt-oss-20b"
Download: TheBloke/gpt-oss-20b-GGUF
File: gpt-oss-20b.Q4_K_M.gguf (12GB)
```

#### Option B: Llama 3.1 8B (Faster, smaller)
```
Search: "llama-3.1-8b"
Download: bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
File: Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf (4.9GB)
```

#### Option C: DeepSeek Coder (Best for code)
```
Search: "deepseek-coder-6.7b"
Download: TheBloke/deepseek-coder-6.7B-instruct-GGUF
File: deepseek-coder-6.7b-instruct.Q4_K_M.gguf (4GB)
```

**Quantization Guide:**
- `Q4_K_M` - Good balance (recommended)
- `Q5_K_M` - Better quality, larger size
- `Q8_0` - Best quality, largest size

### Step 3: Start the Server

1. In LM Studio, click **"Local Server"** tab (left sidebar)
2. Select your downloaded model
3. Click **"Start Server"**
4. Server will start on: `http://localhost:1234`

**Default settings are fine!** But you can adjust:
- **Context Length**: 4096 (good for code)
- **GPU Offload**: Max (for speed)
- **Temperature**: 0.3 (for consistent output)

### Step 4: Configure Scanner

```bash
# Set LM Studio as provider
export LM_STUDIO_URL="http://localhost:1234/v1/chat/completions"
export LLM_PROVIDER="lmstudio"

# Run scanner
python scanner.py --target ./sample_app
```

---

## Full Example with GPT-OSS-20B

```bash
# 1. Install dependencies (if not done)
pip install -r requirements.txt

# 2. Start LM Studio server
# (Click "Start Server" in LM Studio GUI with gpt-oss-20b loaded)

# 3. Configure environment
export LLM_PROVIDER="lmstudio"
export LM_STUDIO_URL="http://localhost:1234/v1/chat/completions"  # Optional, this is default

# 4. Test connection
python -c "
import requests
response = requests.post(
    'http://localhost:1234/v1/chat/completions',
    json={'messages': [{'role': 'user', 'content': 'Say OK'}], 'max_tokens': 10}
)
print(response.json()['choices'][0]['message']['content'])
"

# Should print: OK (or similar)

# 5. Run full scan
python scanner.py --target ./sample_app

# 6. View results
open reports/security_report.html
```

---

## Performance Expectations

### GPT-OSS-20B on Different Hardware

| Hardware | Speed per Finding | Total (10 findings) |
|----------|------------------|-------------------|
| RTX 4090 | ~10 sec | ~2 min |
| RTX 3080 | ~20 sec | ~3.5 min |
| M2 Max | ~15 sec | ~2.5 min |
| M1 Pro | ~25 sec | ~4 min |
| CPU only | ~60 sec | ~10 min |

**Compare to OpenAI API:** ~5 seconds total for all 10 findings

Trade-off: LM Studio is slower but FREE! ✅

---

## Troubleshooting

### "Connection refused" error

**Problem:** Scanner can't reach LM Studio server

**Fix:**
```bash
# 1. Check if server is running
curl http://localhost:1234/v1/models

# Should return JSON with model info

# 2. Make sure LM Studio server is started
# (Green "Running" indicator in LM Studio)

# 3. Check port isn't blocked
netstat -an | grep 1234
```

### "Model not loaded" error

**Fix:**
1. In LM Studio, go to "Local Server" tab
2. Select a model from dropdown
3. Click "Load Model"
4. Wait for "Model loaded" message

### Slow performance

**Fix:**
1. In LM Studio settings:
   - **GPU Offload**: Set to maximum layers
   - **Context Length**: Reduce to 2048 if memory issues
2. Use smaller quantization (Q4 instead of Q8)
3. Use smaller model (8B instead of 20B)

### Out of memory

**Fix:**
1. Close other applications
2. Use smaller model (Llama 3.1 8B instead of GPT-OSS-20B)
3. Use more aggressive quantization (Q4_0 instead of Q4_K_M)

**Memory Requirements:**
- GPT-OSS-20B Q4_K_M: ~12GB RAM
- Llama 3.1 8B Q4_K_M: ~5GB RAM
- DeepSeek Coder 6.7B: ~4GB RAM

---

## Advanced Configuration

### Custom Port

If port 1234 is already used:

**In LM Studio:**
1. Server Settings → Port → Change to 8080 (or any free port)
2. Click "Restart Server"

**In scanner:**
```bash
export LM_STUDIO_URL="http://localhost:8080/v1/chat/completions"
```

### Multiple Models

Switch models without restarting scanner:

```bash
# Scan with GPT-OSS-20B
# (Load in LM Studio first)
python scanner.py --target ./project1

# Switch to Llama 3.1 in LM Studio
# No environment changes needed!
python scanner.py --target ./project2
```

### Response Quality Tuning

Edit `scanner.py` line ~175:

```python
def call_lmstudio(prompt: str) -> str:
    # Adjust these parameters:
    response = requests.post(
        lm_studio_url,
        json={
            "messages": [...],
            "temperature": 0.3,    # 0.1-0.7 (lower = more consistent)
            "max_tokens": 2000,    # Increase for longer responses
            "top_p": 0.9,          # Add for more diverse output
            "repeat_penalty": 1.1  # Reduce repetition
        }
    )
```

---

## Comparing Outputs

### OpenAI GPT-4o-mini
- **Speed**: ⚡⚡⚡⚡⚡ (5 sec total)
- **Quality**: ⭐⭐⭐⭐⭐ (excellent)
- **Cost**: 💰 $0.20 per scan

### LM Studio GPT-OSS-20B
- **Speed**: ⚡⚡⚡ (2-4 min)
- **Quality**: ⭐⭐⭐⭐ (very good)
- **Cost**: 💰 FREE

### LM Studio Llama 3.1 8B
- **Speed**: ⚡⚡⚡⚡ (1-2 min)
- **Quality**: ⭐⭐⭐⭐ (good)
- **Cost**: 💰 FREE

**Recommendation:** Start with Llama 3.1 8B for speed, upgrade to GPT-OSS-20B if you need better analysis.

---

## Group Collaboration with LM Studio

### Strategy 1: One Person Hosts

**Host machine:**
```bash
# In LM Studio: Enable "Allow remote connections"
# Or bind to 0.0.0.0 in settings

# Share your local IP (e.g., 192.168.1.100)
```

**Team members:**
```bash
export LM_STUDIO_URL="http://192.168.1.100:1234/v1/chat/completions"
export LLM_PROVIDER="lmstudio"
python scanner.py --target ./sample_app
```

### Strategy 2: Each Person Runs Locally

**Pros:**
- No network issues
- Everyone has full control

**Cons:**
- Each person needs good hardware
- Each person downloads model (~5-12GB)

### Strategy 3: Shared Cloud VM

Run LM Studio on cloud GPU:
- **RunPod**: ~$0.30/hour for RTX 3090
- **Vast.ai**: ~$0.20/hour for RTX 3080

Still cheaper than OpenAI for heavy usage!

---

## Best Models for Security Analysis

Ranked by quality for this task:

1. **GPT-4o-mini (OpenAI API)** - Best overall (paid)
2. **Claude Sonnet (Anthropic API)** - Excellent (paid)
3. **GPT-OSS-20B (LM Studio)** - Very good (free)
4. **DeepSeek Coder 6.7B** - Good for code (free)
5. **Llama 3.1 8B** - Fast & decent (free)
6. **Mistral 7B** - Good general purpose (free)

**For this assignment, any of these work fine!**

---

## Testing LM Studio Connection

Run this before scanning:

```bash
# Test 1: Check server is up
curl http://localhost:1234/v1/models

# Test 2: Simple completion
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Say OK"}
    ],
    "max_tokens": 10
  }'

# Test 3: Python test
python -c "
import requests
resp = requests.post(
    'http://localhost:1234/v1/chat/completions',
    json={'messages': [{'role': 'user', 'content': 'What is 2+2?'}]}
)
print(resp.json()['choices'][0]['message']['content'])
"
```

All should return valid responses ✅

---

## Quick Reference Card

```bash
# Start LM Studio server (GUI)
# Load model → Click "Start Server"

# Set environment
export LLM_PROVIDER="lmstudio"

# Run scanner
python scanner.py --target ./sample_app

# View results
open reports/security_report.html
```

**That's it!** No API keys, no costs, no limits. 🎉

---

## FAQ

**Q: Which model should I download first?**
A: Llama 3.1 8B (4.9GB) - fastest download, good quality

**Q: How much RAM do I need?**
A: 8GB minimum, 16GB recommended for GPT-OSS-20B

**Q: Can I use GPU?**
A: Yes! LM Studio automatically uses GPU if available (CUDA/Metal)

**Q: Is it really as good as OpenAI?**
A: For this task, local models are 80-90% as good. Perfectly acceptable for assignment!

**Q: What if I have a slow computer?**
A: Use smaller model (Llama 3.1 8B) or just analyze top 3 findings instead of 10

**Q: Can I mix providers?**
A: Yes! Use LM Studio for development, switch to OpenAI for final run

**Q: Does this work on M1/M2 Macs?**
A: Yes! LM Studio has excellent Apple Silicon support

---

## Summary

LM Studio is **perfect for students** because:
- ✅ FREE (no API costs)
- ✅ No sign-up required
- ✅ Works offline
- ✅ Privacy-friendly
- ✅ Easy GUI
- ✅ Good enough quality for assignments

**Total cost:** $0 (just download model once)

---

For more help: Check SETUP_GUIDE.md or run `python test_setup.py`
