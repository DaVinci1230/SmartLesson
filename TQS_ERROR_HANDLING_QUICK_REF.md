# TQS Error Handling - Quick Reference Guide

## What Was Fixed

### Problem
- TQS generation failed silently with message "Failed to generate questions"
- No visibility into actual errors (API failures, token limits, data issues)
- 60 slots would all-or-nothing: either all succeed or all fail
- No debugging information available

### Solution
Enhanced error handling with:
1. Comprehensive input validation (PHASE 0)
2. Batch processing for 60 slots (PHASE 1)
3. Detailed logging throughout
4. API error handling with actual exception types
5. Graceful partial failure support
6. Field name consistency

---

## Key Files Modified

### `services/tqs_service.py`

#### `generate_tqs()` Function (Lines 665-900)
- **PHASE 0** (lines 705-755): Input validation
  - Check non-empty list of slots
  - Verify required fields present
  - Validate field values (bloom level, points, etc.)

- **PHASE 1** (lines 760-820): Batch processing
  - Split 60 slots into 6 batches of 10
  - Try/except around each slot generation
  - Collect failures but continue if some succeed

- **PHASE 4** (lines 840-880): Final reporting
  - Summary statistics
  - Detailed failure analysis
  - Clear success/partial success messages

#### `generate_question_with_gemini()` (Lines 250-661)
**For each question type** (MCQ, Short Answer, Essay, Problem Solving, Drawing):

```python
try:
    logger.info(f"Calling Gemini API for {question_type}...")
    response = model.generate_content(prompt)
    # ... parse and validate ...
except Exception as api_error:
    logger.error(f"API error during {question_type}: {type(api_error).__name__}")
    raise  # Re-raise so outer function logs with slot context
```

**Field names made consistent**:
```python
question = {
    "outcome_id": slot.get("outcome_id", 0),
    "outcome_text": outcome,  # ✅ Matches input "outcome_text"
    "bloom_level": bloom_level,  # ✅ Matches input "bloom_level"
    "question_type": question_type,  # ✅ Matches input "question_type"
    # ... other fields
}
```

---

## How to Use / Test

### Running the Validation Tests
```bash
cd d:\SOFTWARE ENGINEERING\SmartLesson
python test_tqs_error_handling.py
```

**Expected Output**:
```
============================================================
TEST 1: Input Validation
============================================================
1a. Testing empty assigned_slots...
✓ PASSED: Caught error as expected: Invalid assigned_slots...

1b. Testing non-list assigned_slots...
✓ PASSED: Caught error as expected...

... (more tests) ...

############################################################
# ✅ ALL TESTS COMPLETED
############################################################
```

### Using with Real Data

**Input Structure** (from soft-mapping):
```python
assigned_slots = [
    {
        "outcome_id": 1,
        "outcome_text": "Identify mitosis phases",  # Required, non-empty
        "bloom_level": "Remember",  # One of: Remember, Understand, Apply, Analyze, Evaluate, Create
        "question_type": "MCQ",  # One of: MCQ, Short Answer, Essay, Problem Solving, Drawing
        "points": 3  # Required, positive
    },
    # ... 59 more slots ...
]
```

**Call in app.py**:
```python
tqs = generate_tqs(
    assigned_slots=assigned_slots,
    api_key=os.getenv("GEMINI_API_KEY"),
    shuffle=True
)
```

**Output Structure** (same field names as input):
```python
tqs = [
    {
        "question_number": 1,
        "outcome_id": 1,
        "outcome_text": "Identify mitosis phases",  # From input
        "bloom_level": "Remember",  # From input
        "question_type": "MCQ",  # From input
        "points": 3,  # From input
        "question_text": "Which phase of mitosis is characterized by...",  # Generated
        "choices": ["A) Prophase", "B) Metaphase", "C) Anaphase", "D) Telophase"],
        "correct_answer": "B",
        "generated_at": "2024-01-15T10:30:00.123456"
    },
    # ... 59 more questions ...
]
```

---

## Error Messages You'll See

### Input Validation Errors
```
ValueError: Invalid assigned_slots: expected non-empty list, received dict
ValueError: Slot 0 missing fields: ['bloom_level', 'question_type', 'points']
ValueError: Slot 5: invalid bloom_level 'InvalidLevel'
ValueError: Slot 8: points must be positive number, got 0
ValueError: Slot 12: outcome_text is empty
```

### API Errors
```
RateLimitError: 429 Too Many Requests
ResourceExhausted: Token quota exceeded
InvalidArgument: Prompt validation failed
PermissionDenied: Invalid API key
DeadlineExceeded: Connection timeout
```

### Partial Failure (Acceptable)
```
Generation Results:
  Total slots: 60
  Successfully generated: 58
  Failed: 2
  Continuing with 58 successfully generated questions
```

### Complete Failure (Unrecoverable)
```
RuntimeError: Failed to generate any questions. First error: RateLimitError: 429 Too Many Requests
```

---

## Logging Levels

### INFO Level (Always Visible)
- TQS generation starting/ending
- Input validation results
- Batch processing progress
- Slot generation success/failure
- Final statistics

### DEBUG Level (Visible if logging.DEBUG)
- Detailed prompt content (first 200 chars)
- API response received (first 200 chars)
- Per-slot details (outcome, bloom, type, points)
- Raw API responses on error

### ERROR Level (Always Visible)
- Validation failures with details
- API errors with exception type and message
- Failed slots count and reasons

---

## Performance Notes

### Processing Time
- **Validation**: <100ms for 60 slots
- **Generation**: ~10-30 seconds per batch (depends on API response time)
- **Total**: ~1-3 minutes for 60 questions

### Batch Size Tuning
Default: 10 slots per batch
```python
batch_size = 10  # Change this in services/tqs_service.py line 768
```

**Token Estimation**:
- Per slot: 200-300 tokens
- Per batch: 2000-3000 tokens
- Safe margin from 1M token limit: yes

**If hitting token limits**: Reduce `batch_size` to 5

### API Call Pattern
- **Parallel**: No (batches processed sequentially)
- **Retry**: Manual re-run if partial failure
- **Cache**: None (every slot generates new question)

---

## Troubleshooting

### Symptom: All 60 slots fail with same error

**Check 1**: API key valid?
```python
api_key = os.getenv("GEMINI_API_KEY")
print(f"API key starts with: {api_key[:10]}...")  # Should not be None
```

**Check 2**: Slot structure correct?
```python
print(f"Sample slot: {assigned_slots[0]}")
# Should have: outcome_id, outcome_text, bloom_level, question_type, points
```

**Check 3**: API rate limit?
- Check Google Cloud Console for quota
- Reduce batch_size from 10 to 5
- Wait a few minutes before retrying

### Symptom: First 3 batch slots work, then all fail

**Cause**: Likely token limit exceeded
**Fix**: Reduce batch_size from 10 to 5 in tqs_service.py line 768

### Symptom: Specific slot always fails

**Debug**:
```python
# Check that specific slot
failed_slot = assigned_slots[X]
print(json.dumps(failed_slot, indent=2))

# Verify bloom level is valid
valid_blooms = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']
assert failed_slot['bloom_level'] in valid_blooms

# Verify points is positive
assert failed_slot['points'] > 0
```

---

## Field Name Reference

### Input (from `tos_slot_assignment_service.py`)
```python
slot = {
    "outcome_id": int,           # Database ID
    "outcome_text": str,         # Learning outcome description (required, non-empty)
    "bloom_level": str,          # Remember | Understand | Apply | Analyze | Evaluate | Create
    "question_type": str,        # MCQ | Short Answer | Essay | Problem Solving | Drawing
    "points": int or float,      # Positive number
}
```

### Output (from `tqs_service.py`)
```python
question = {
    # From input (preserved exactly)
    "outcome_id": int,
    "outcome_text": str,  # ✅ Same field name as input
    "bloom_level": str,   # ✅ Same field name as input
    "question_type": str, # ✅ Same field name as input
    "points": float,
    "question_number": int,  # Assigned sequentially after generation
    
    # Generated by AI
    "question_text": str,  # The actual question
    
    # Type-specific fields
    # MCQ only:
    "choices": [],         # List of 4 choices
    "correct_answer": "",  # Single correct choice
    
    # Short Answer only:
    "answer_key": "",      # Brief expected answer
    
    # Essay/Problem Solving/Drawing:
    "sample_answer": "",   # Detailed model answer
    "rubric": {},          # Scoring rubric with criteria
    
    # Metadata
    "generated_at": "",    # ISO timestamp
}
```

---

## Next Steps

1. **Test with real 60 slots**: Generate TOS, soft-map, then generate TQS
2. **Monitor API usage**: Watch logs for token consumption
3. **Adjust batch size if needed**: Reduce from 10 to 5 if hitting limits
4. **Enable retry logic**: Implement exponential backoff for rate limit errors
5. **Add progress UI**: Show real-time batch progress to user

---

## Documentation

- **Detailed Guide**: `TQS_ERROR_HANDLING_ENHANCEMENTS.md`
- **Complete Summary**: `PHASE_7_COMPLETION_SUMMARY.md`
- **Test Suite**: `test_tqs_error_handling.py`

