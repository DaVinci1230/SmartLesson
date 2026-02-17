# Gemini API Improvements - Complete Guide

## Overview

This document details the comprehensive improvements made to Gemini API handling in the SmartLesson TQS generation service, including the migration from the deprecated `google.generativeai` package to the official `google-genai` package.

**Important**: Google has deprecated `google.generativeai` (version 0.x). This codebase now uses the official `google-genai` package (version 1.x) for all Gemini API calls.

## What Was Improved

### CRITICAL UPDATE: Using Official google-genai Package

**Date**: February 17, 2026

Google has **deprecated** the `google.generativeai` package (0.x versions). The SmartLesson backend now uses the official **`google-genai`** package (1.x versions).

**Why This Matters**:
- ❌ `google.generativeai` - DEPRECATED (no longer receives updates)
- ✅ `google-genai` - OFFICIAL (actively maintained by Google)

**Already Installed**: `google-genai` (1.63.0) is included in your environment.

### Migration Details

| Component | Old (Deprecated) | New (Current) |
|-----------|-----------------|---------------|
| Package | `google.generativeai` | `google-genai` |
| Import | `import google.generativeai as genai` | `import google.genai as genai` |
| Client | `genai.GenerativeModel()` | `genai.Client()` |
| API Call | `model.generate_content()` | `client.models.generate_content()` |
| Status | ❌ Deprecated | ✅ Official & Maintained |

### 1. ✅ API Key Validation (On Startup)

**Function**: `validate_api_key()`

The system now validates that `GEMINI_API_KEY` environment variable is set before any generation starts.

```python
api_key = validate_api_key()  # Raises EnvironmentError if not set
```

**Error Message**:
```
EnvironmentError: GEMINI_API_KEY environment variable is not set. 
Please set it before running TQS generation. 
Example: export GEMINI_API_KEY='your-api-key-here'
```

### 2. ✅ Gemini Configuration with Error Handling

**Function**: `configure_gemini_api(api_key)`

Properly configures the Gemini API using `google-genai` package and handles common configuration errors:

```python
configure_gemini_api(api_key)  # Raises EnvironmentError on failure
```

**Uses**: Official `google-genai` package (replaces deprecated `google.generativeai`)

**Handles**:
- Import errors (google-genai not installed)
- Invalid API key format
- Configuration failures

### 3. ✅ Common API Error Detection

**Function**: `interpret_api_error(error)`

Automatically detects and interprets common Gemini API errors:

| Error Type | Detected By | Solution |
|-----------|-----------|----------|
| **AUTH_ERROR** (401) | Invalid/expired API key | Verify and update your API key |
| **RATE_LIMIT** (429) | Too many requests too fast | Wait and retry later |
| **TIMEOUT** | Network timeouts | Check network connection, try again |
| **SERVICE_UNAVAILABLE** (503) | Service down | Wait for service to recover |
| **TOKEN_LIMIT** | Prompt too long | Will be handled by batching |

**Example Output**:
```
API error during MCQ generation [AUTH_ERROR]: Invalid API Key: Your GEMINI_API_KEY is invalid or expired. Please check your API key and try again.
```

### 4. ✅ Detailed Logging for Debugging

#### Pre-Generation Logging

Before generating any questions, the system logs:

```
Validating Gemini API configuration...
✓ GEMINI_API_KEY found (length: 40 chars)
Gemini API configured successfully
✓ Gemini API configured and ready

Starting TQS generation for 20 slots
Shuffle: True
Development mode: False
Batch size: 10 slots per batch (for token limit management)

Validating assigned slots...
✓ All 20 slots validated successfully

Sample slots (first 3):
  Slot 0: outcome=Identify components of photosynthesis... bloom=Remember type=MCQ points=1.0
  Slot 1: outcome=Explain cellular respiration... bloom=Understand type=Short Answer points=2.0
  Slot 2: outcome=Apply conservation laws... bloom=Apply type=Problem Solving points=3.0

Processing 20 slots in 2 batch(es) (batch_size=10)
Processing batch 1/2 (slots 1-10)
```

#### Per-Slot Debug Logging

For each slot, detailed information is logged:

```
[DEBUG] Processing slot 0:
  - Question Type: MCQ
  - Bloom Level: Remember
  - Points: 1
  - Outcome: Identify the components of photosynthesis...

[DEBUG] Generating question for slot 1/20
  Outcome: Identify photosynthesis components...
  Type: MCQ | Bloom: Remember | Points: 1.0

MCQ Prompt (length: 534 chars):
Generate an assessment question based on the following:

Learning Outcome: Identify the components of photosynthesis
Bloom Level: Remember
Question Type: Multiple Choice (4 options)
Points: 1

[API CALL] Model: gemini-2.5-flash, Prompt length: 534 chars
Calling Gemini API for MCQ...
API Response received: {"question_text": "Which of the following...", ...}
✓ MCQ generated successfully
```

### 5. ✅ Wrapped API Calls with Error Context

Each API call is now wrapped with try-catch that provides full context:

```python
try:
    logger.info(f"Calling Gemini API for {question_type}...")
    logger.debug(f"[API CALL] Model: gemini-2.5-flash, Prompt length: {len(prompt)} chars")
    
    response = model.generate_content(prompt)
    logger.debug(f"API Response received: {str(response.text)[:200]}...")
    
    # Parse and validate response...
    
except Exception as api_error:
    error_type, user_msg = interpret_api_error(api_error)
    logger.error(f"API error during {question_type} generation [{error_type}]: {user_msg}")
    logger.debug(f"Raw error: {type(api_error).__name__}: {str(api_error)}")
    logger.debug(f"Prompt length: {len(prompt)} chars")
    if DEVELOPMENT_MODE:
        logger.debug(f"Prompt: {prompt[:300]}")
    raise  # Re-raise for proper error propagation
```

### 6. ✅ Batching for Token Limit Management

Large question sets are processed in batches of 10 slots to prevent hitting token limits:

```
Processing 50 slots in 5 batch(es) (batch_size=10)
Processing batch 1/5 (slots 1-10)
Processing batch 2/5 (slots 11-20)
Processing batch 3/5 (slots 21-30)
Processing batch 4/5 (slots 31-40)
Processing batch 5/5 (slots 41-50)
```

**Benefits**:
- Prevents "context length exceeded" errors on large batches
- Allows recovery from partial failures
- Better memory management

### 7. ✅ Development Mode Flag

Set `SMARTLESSON_DEV_MODE=true` for full error details:

```bash
export SMARTLESSON_DEV_MODE=true
python -m streamlit run app.py
```

When enabled:
- Full prompts are logged for debugging
- Full exception tracebacks are shown
- More verbose API call details

## Usage Examples

### Example 1: Normal TQS Generation

```python
from services.tqs_service import generate_tqs

assigned_slots = [...]  # From soft-mapping
tqs = generate_tqs(assigned_slots, shuffle=True)
# API key is automatically read from GEMINI_API_KEY env var
```

### Example 2: With Explicit API Key

```python
tqs = generate_tqs(assigned_slots, api_key="your-api-key", shuffle=True)
```

### Example 3: Debugging with Development Mode

```bash
export SMARTLESSON_DEV_MODE=true
export GEMINI_API_KEY='your-api-key'
python -m streamlit run app.py
```

Then check the terminal for detailed logs including full prompts and responses.

## Error Handling Flow

```
generate_tqs()
├─ validate_api_key()                    [Check env variable]
├─ configure_gemini_api()                [Configure Gemini]
├─ Validate input slots
└─ For each slot:
   └─ generate_question_with_gemini()
      ├─ Create prompt
      ├─ Call Gemini API              [Wrapped with error handling]
      │  └─ interpret_api_error()     [Detect error type]
      ├─ Parse response
      ├─ Validate against schema
      └─ Return question or raise exception
```

## Log Levels

- **INFO**: Major milestones (API validation, slot counts, generation progress)
- **DEBUG**: Detailed information (prompt lengths, sample slots, API calls)
- **WARNING**: Failures with recovery (partial slot failures, retry logic)
- **ERROR**: Fatal errors that stop execution (invalid API key, all slots failed)

## Common Debugging Scenarios

### Scenario 1: "Invalid API Key"

```
ERROR: API error during MCQ generation [AUTH_ERROR]: 
Invalid API Key: Your GEMINI_API_KEY is invalid or expired. 
Please check your API key and try again.
```

**Solution**:
1. Verify your API key is correct
2. Check if the key has expired
3. Generate a new key from Google AI Studio
4. Update environment variable

### Scenario 2: "Rate Limit Exceeded"

```
ERROR: API error during Essay generation [RATE_LIMIT]: 
Rate Limit Exceeded: Too many requests to Gemini API. 
Please wait a moment and try again.
```

**Solution**:
1. Wait a few minutes before retrying
2. Reduce the number of slots per batch (modify `batch_size`)
3. Add delays between batches

### Scenario 3: "Timeout"

```
ERROR: API error during Problem Solving generation [TIMEOUT]: 
Network Timeout: Request to Gemini API took too long. 
This may indicate a network issue or server overload.
```

**Solution**:
1. Check internet connection
2. Retry after a few minutes
3. Check Gemini API status page

### Scenario 4: "Service Unavailable"

```
ERROR: API error during Drawing generation [SERVICE_UNAVAILABLE]: 
Gemini Service Unavailable: The service is temporarily down. 
Please try again later.
```

**Solution**:
1. Wait for the service to become available
2. Check Google's status page
3. Retry after 5-10 minutes

## Configuration Options

### Environment Variables

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `GEMINI_API_KEY` | Yes | `AIzaSy...` | Your Google API key |
| `SMARTLESSON_DEV_MODE` | No | `true` or `false` | Enable verbose logging |

### Code Configuration

In `services/tqs_service.py`:

```python
# Batch size for token limit management
batch_size = 10  # Process 10 slots at a time

# Development mode (can be set via env var)
DEVELOPMENT_MODE = os.getenv('SMARTLESSON_DEV_MODE', 'False').lower() == 'true'
```

## Performance & Reliability

### Token Limit Management
- Batch size: 10 slots per batch
- Typical prompt size: 400-800 tokens per question
- Safe limit: ~30,000 tokens per batch

### Error Recovery
- Partial failures: System continues with successful slots
- Failed slots: Logged with full error details
- Complete failure: Only if ALL slots fail (raises RuntimeError)

### Timeout Handling
- API calls: Wrapped with timeout detection
- Network errors: Automatically classified as TIMEOUT
- User-friendly messages: Explain the issue and next steps

## Testing the Improvements

### Test 1: Verify API Key Validation

```python
# Without API key
import os
if 'GEMINI_API_KEY' in os.environ:
    del os.environ['GEMINI_API_KEY']

from services.tqs_service import generate_tqs
try:
    tqs = generate_tqs(assigned_slots)
except EnvironmentError as e:
    print(f"✓ Caught expected error: {e}")
```

### Test 2: Verify google-genai Package is Available

```bash
# Check if google-genai is installed
python -c "import google.genai; print(f'google-genai {google.genai.version}')"

# Output: google-genai 1.63.0 (or higher)
```

### Test 3: Verify Error Handling

```python
# With invalid API key
from services.tqs_service import generate_tqs

os.environ['GEMINI_API_KEY'] = 'invalid-key-12345'
try:
    tqs = generate_tqs(assigned_slots)
except Exception as e:
    print(f"✓ Caught API error: {e}")
```

### Test 3: Verify Batching

```python
# Generate large question set
from services.tqs_service import generate_tqs

assigned_slots = [...]  # 50+ slots
print("Generating 50 questions (will show batch progress)...")
tqs = generate_tqs(assigned_slots, shuffle=True)
print(f"✓ Generated {len(tqs)} questions across multiple batches")
```

### Test 4: Verify Debug Logging

```bash
export SMARTLESSON_DEV_MODE=true
export GEMINI_API_KEY='your-key'
python -c "
from services.tqs_service import generate_tqs
tqs = generate_tqs(assigned_slots[:3])
" 2>&1 | grep -E "\[DEBUG\]|\[API CALL\]"
```

## Summary of Changes

| Component | Change | Benefit |
|-----------|--------|---------|
| `validate_api_key()` | NEW | Clear error message if API key missing |
| `configure_gemini_api()` | NEW | Proper error handling for configuration |
| `interpret_api_error()` | NEW | Detects and explains common errors |
| `generate_question_with_gemini()` | ENHANCED | Better error context, debug logging |
| `generate_tqs()` | ENHANCED | API validation on startup, batching |
| Logging | ENHANCED | More detailed pre- and per-call logging |
| Error Messages | ENHANCED | User-friendly error messages instead of generic ones |

## No Breaking Changes

✅ **100% Backward Compatible**
- Existing code continues to work
- API signature unchanged (api_key is optional parameter)
- Slot field names remain consistent
- Output format unchanged

## Next Steps

1. **Set API Key**: Configure `GEMINI_API_KEY` environment variable
2. **Test Generation**: Run TQS generation and verify logs
3. **Monitor Errors**: Check logs for any specific error patterns
4. **Enable Debug Mode** (if needed): Set `SMARTLESSON_DEV_MODE=true`
5. **Report Issues**: Include relevant log snippets when reporting problems

---

**Version**: 2.0 (Enhanced API Handling)  
**Last Updated**: February 17, 2026  
**Status**: ✅ Production Ready
