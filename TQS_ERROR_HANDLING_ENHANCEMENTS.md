# TQS Generation Error Handling & Debugging Enhancements

## Overview

This document describes comprehensive enhancements to TQS (Test Question Sheet) generation to provide better error visibility, detailed logging, and graceful failure handling when generating large numbers of test questions (60+ slots).

## Problem Statement

**Original Issue**: TQS generation would fail silently with generic error messages:
- User sees: "Failed to generate questions. Please try again."
- No visibility into actual error (API failure, data validation, token limits, etc.)
- No debugging information about which slots failed or why
- 60 slots would cause either complete failure or hidden API errors

## Solutions Implemented

### 1. Comprehensive Input Validation (PHASE 0)

**File**: `services/tqs_service.py` - `generate_tqs()` function (lines ~700-780)

**What Changed**:
- Added validation before ANY question generation
- Checks for:
  - Non-empty list of assigned_slots
  - All required fields present: `outcome_id`, `outcome_text`, `bloom_level`, `question_type`, `points`
  - Valid bloom level values (Remember, Understand, Apply, Analyze, Evaluate, Create)
  - Positive numeric points value
  - Non-empty outcome_text

**Error Messages**:
```
Invalid assigned_slots: expected non-empty list, received dict
Slot 0 missing fields: ['bloom_level', 'question_type', 'points']
Slot 0: invalid bloom_level 'InvalidBloomLevel'
Slot 0: points must be positive number, got 0
Slot 0: outcome_text is empty
```

**Benefit**: Catches data problems before wasting API calls; provides actionable error messages

### 2. Batch Processing Architecture (PHASE 1)

**File**: `services/tqs_service.py` - `generate_tqs()` function (lines ~780-820)

**What Changed**:
- Process 60 slots in 6 batches of 10 slots each
- Each batch processed sequentially
- Individual try/except around each slot generation
- Partial failure tolerance: if 50/60 questions generate, returns partial TQS

**Example Log Output**:
```
Processing batch 1/6 (slots 1-10)
  ✓ Slot 1: MCQ generated successfully
  ✗ Slot 2: Exception during generation: RateLimitError: 429 Too Many Requests
Processing batch 2/6 (slots 11-20)
  ✓ Slot 11: Short Answer generated successfully
  ...

Generation Results:
  Total slots: 60
  Successfully generated: 58
  Failed: 2
  Continuing with 58 successfully generated questions
```

**Benefit**: 
- Prevents single failing slot from crashing entire generation
- Visible progress for user ("batch 1/6")
- Token limit not exceeded (10 slots at a time)

### 3. Detailed Logging Throughout

**File**: `services/tqs_service.py` 

**Logging Enhancements**:

#### Pre-Generation Logging
```python
logger.info(f"Sample slots (first 3):")
for idx, slot in enumerate(assigned_slots[:3]):
    logger.info(
        f"  Slot {idx}: outcome={str(slot.get('outcome_text', ''))[:40]}... "
        f"bloom={slot.get('bloom_level')} type={slot.get('question_type')} points={slot.get('points')}"
    )
```

#### Per-Batch Progress
```python
logger.info(f"Processing batch {batch_num + 1}/{total_batches} (slots {batch_start + 1}-{batch_end})")
```

#### Per-Slot Details
```python
logger.debug(f"  Outcome: {slot.get('outcome_text', '')[:60]}")
logger.debug(f"  Type: {slot.get('question_type')} | Bloom: {slot.get('bloom_level')} | Points: {slot.get('points')}")
```

#### Success/Failure Tracking
```python
logger.info(f"  ✓ Slot {slot_index}: {slot.get('question_type')} generated successfully")
logger.error(f"  ✗ Slot {slot_index}: Exception during generation: {error_msg}")
logger.exception(f"Full traceback for slot {slot_index}:")
```

#### Final Report
```
============================================================
TQS GENERATION COMPLETE
============================================================
Total questions: 58
Total points: 285
Failed slots: 2 (recovered with partial TQS)
============================================================
```

**Debugging Benefit**: User/developer can see exact flow and identify which slots fail

### 4. Enhanced API Error Handling

**File**: `services/tqs_service.py` - `generate_question_with_gemini()` function

**What Changed** (for each question type: MCQ, Short Answer, Essay, Problem Solving, Drawing):

**Before**:
```python
response = model.generate_content(prompt)
json_data = extract_json_from_response(response.text)
if not json_data:
    logger.error("Failed to parse MCQ JSON response")
    return None
```

**After**:
```python
logger.debug(f"MCQ Prompt:\n{prompt[:200]}...")

try:
    logger.info(f"Calling Gemini API for MCQ...")
    response = model.generate_content(prompt)
    logger.debug(f"API Response received: {str(response.text)[:200]}...")
    
    json_data = extract_json_from_response(response.text)
    
    if not json_data:
        logger.error("Failed to parse MCQ JSON response")
        logger.debug(f"Raw response: {response.text[:500]}")
        return None
    
    # Validation...
    
except Exception as api_error:
    logger.error(f"API error during MCQ generation: {type(api_error).__name__}: {str(api_error)}")
    logger.debug(f"Prompt was: {prompt[:300]}")
    raise  # Re-raise so generate_tqs can catch and log with slot context
```

**Captured Exceptions**:
- `RateLimitError`: 429 - Too Many Requests (Gemini API rate limit)
- `ResourceExhausted`: Token quota exceeded
- `InvalidArgument`: Malformed prompt or schema mismatch
- `PermissionDenied`: API key issues
- `DeadlineExceeded`: Network timeout
- Any other API exception with full traceback

**Benefit**: Actual error type and message visible to developer

### 5. Field Name Consistency

**File**: `services/tqs_service.py` - `generate_question_with_gemini()` function

**What Changed** (in all question type handlers):

**Before**:
```python
question = {
    "outcome": outcome,           # ❌ Wrong field name
    "bloom": bloom_level,         # ❌ Wrong field name
    "type": question_type,        # ❌ Wrong field name
}
```

**After**:
```python
question = {
    "outcome_id": slot.get("outcome_id", 0),
    "outcome_text": outcome,      # ✅ Consistent with slot field names
    "bloom_level": bloom_level,   # ✅ Consistent with slot field names
    "question_type": question_type,  # ✅ Consistent with slot field names
    "points": points,
}
```

**Updated in**:
- MCQ questions (line ~311)
- Short Answer questions (line ~395)
- Essay questions (line ~463)
- Problem Solving questions (line ~551)
- Drawing questions (line ~639)

**Benefit**: No field name mismatches when passing questions between functions

### 6. Graceful Failure Handling

**File**: `services/tqs_service.py` - `generate_tqs()` function (lines ~810-850)

**What Changed**:
```python
if len(generated_questions) == 0:
    # Only fail completely if NO questions were generated
    error_msg = f"Failed to generate any questions. First error: {failed_slots[0][2]}"
    logger.error(error_msg)
    raise RuntimeError(error_msg)
else:
    # Allow partial success (55/60 acceptable)
    logger.warning(f"Continuing with {len(generated_questions)} successfully generated questions")
```

**Scenarios**:
- 60/60 questions generated → Success
- 55/60 questions generated → Partial success (returns 55 questions)
- 0/60 questions generated → Complete failure (raises RuntimeError with first error)

**User Experience**:
- Shows warning if some slots fail
- Displays actual error messages
- Still provides usable test sheet even with partial failures

## Field Name Summary

### Input (assigned_slots from soft-mapping):
```python
{
    "outcome_id": 1,           # int
    "outcome_text": "...",     # str (required, non-empty)
    "bloom_level": "Remember", # str (one of 6 valid values)
    "question_type": "MCQ",    # str
    "points": 5                # int/float (required, positive)
}
```

### Output (generated_questions):
```python
{
    "question_number": 1,      # int (assigned sequentially)
    "outcome_id": 1,           # int (from input)
    "outcome_text": "...",     # str (from input)
    "bloom_level": "Remember", # str (from input)
    "question_type": "MCQ",    # str (from input)
    "points": 5,               # int/float (from input)
    "question_text": "...",    # str (from Gemini)
    "choices": ["A) ...", ...],  # list (MCQ only)
    "correct_answer": "A",     # str (MCQ only)
    "answer_key": "...",         # str (Short Answer only)
    "sample_answer": "...",      # str (Essay/Problem Solving/Drawing)
    "rubric": {...},             # dict (Essay/Problem Solving/Drawing)
    "generated_at": "2024-01-15T10:30:00.123456"  # ISO timestamp
}
```

## Error Handling in app.py

**File**: `app.py` (lines 908-935)

**Current Implementation**:
```python
try:
    with st.spinner("⏳ Generating test questions..."):
        tqs = generate_tqs(
            assigned_slots=assigned_slots_to_use,
            api_key=api_key,
            shuffle=True
        )
    
    if tqs:
        st.session_state.generated_tqs = tqs
        st.success(f"✅ Generated {len(tqs)} test questions")
    else:
        st.error("❌ Failed to generate questions.")

except Exception as e:
    st.error(f"❌ Error generating questions: {str(e)}")
    import traceback
    st.error(traceback.format_exc())  # Display full error details
```

**User Sees**:
- Actual error message: "Error generating questions: RateLimitError: 429 Too Many Requests"
- Full traceback for debugging if needed

## Testing & Validation

**Test File**: `test_tqs_error_handling.py`

**Test Results** ✅:
- Input validation catches all invalid inputs with clear messages
- Field names consistent throughout pipeline
- Batch processing correctly segments 60 slots into 6 batches of 10
- Error messages are clear and actionable
- Logging provides visibility into generation flow

## Deployment Checklist

- ✅ Input validation PHASE 0 implemented
- ✅ Batch processing PHASE 1 implemented  
- ✅ Comprehensive logging throughout
- ✅ API error handling with try/except
- ✅ Field name consistency verified
- ✅ Graceful failure handling for partial results
- ✅ Error messages clear and actionable
- ✅ Tests pass and validate all changes
- ✅ Documentation complete

## Next Steps / Future Enhancements

1. **Token Management**: Monitor token usage per batch, reduce batch size if needed
2. **Retry Logic**: Implement exponential backoff for failed slots
3. **Progress UI**: Real-time progress bar showing "Batch 2/6: 8/10 complete"
4. **Questions Cache**: Cache similar questions to reduce API calls
5. **Performance Optimization**: Parallel batch processing if API limits allow

## Summary of Benefits

| Problem | Solution | Benefit |
|---------|----------|---------|
| Generic errors | Actual exception messages | Know what went wrong |
| Silent failures | Comprehensive logging | Understand what happened |
| 60 slots crashes | Batch processing | Avoid token limits |
| Wrong field names | Consistent naming | Prevent data corruption |
| Partial failures halt everything | Graceful degradation | Get partial results when possible |
| No debugging info | Detailed per-batch logs | Trace execution flow |
| 0/60 questions mystifies user | Clear error reports | Understand root cause |

