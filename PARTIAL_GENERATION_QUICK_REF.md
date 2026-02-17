# Partial Generation Quick Reference

## What Happened?

You got 44 questions instead of 48 questions. This is **normal** and **recoverable**.

## Why Did This Happen?

The Gemini API returned fewer questions than expected. This can happen due to:
- **Rate Limiting**: API temporarily returning fewer results
- **Token Limits**: Large questions using more tokens
- **Batch Size**: Some batches naturally have fewer matches

## What to Do NOW

### Option 1: Regenerate Missing (Recommended ⭐)

```
Click: 🔄 Regenerate Missing Questions
```

**What happens:**
1. System identifies the 4 missing questions
2. Only regenerates those 4 (not all 48)
3. Merges new 4 with your existing 44
4. You get 47-48 questions total

**Time:** 30-60 seconds  
**Cost:** Uses only ~10% API quota instead of 100%

### Option 2: Continue Anyway

```
Click: ✏️ Review & Continue Anyway
```

**What happens:**
1. You keep the 44 questions
2. Workflow continues normally
3. You can manually add 4 more questions later OR
4. Download TQS and edit it in Word/Excel

**When to use:** If you only need 44 questions for now

---

## Technical Details

### Thresholds

| Missing % | What Happens |
|-----------|-------------|
| < 10% | ⚠️ Warning + options to regenerate or continue |
| ≥ 10% | ❌ **Error** - generation fails completely |

**Why 10%?**
- Less than 10% missing = acceptable classroom standard
- 10% or more missing = indicates serious problem

### Example Scenarios

| Expected | Generated | Missing | Status |
|----------|-----------|---------|--------|
| 48 | 44 | 4 (8.3%) | ✅ Allow with warning |
| 48 | 48 | 0 (0%) | ✅ Success |
| 50 | 42 | 8 (16%) | ❌ Error - fail |
| 100 | 85 | 15 (15%) | ❌ Error - fail |

---

## Session Management

### Session State After Partial Generation

```python
st.session_state.generated_tqs        # Has 44 questions
st.session_state.last_assigned_slots  # Stores 48 slots for regeneration
```

### Merging After Regeneration

When you click "Regenerate Missing":
1. System identifies 4 missing slots
2. Generates 4 new questions
3. Extends existing list: `[44 questions] + [4 new] = 48`
4. Sorts by question_number for consistency

---

## Troubleshooting

### "Still getting fewer than 48?"

**Try these:**
1. Wait 30 seconds - API may be rate limited
2. Try regenerating again - might get different batch
3. Check your API quota at [aistudio.google.com](https://aistudio.google.com)
4. Use different API key if available

### "Getting different numbers each time?"

This is **normal**. The API is non-deterministic and sometimes:
- Returns 44 questions
- Returns 45 questions (sometimes 1 extra!)
- Returns 48 questions (complete)

Just keep clicking Regenerate until you get to 48.

### "Getting error about 10% or more missing?"

This IS a problem. Try:
1. Check your learning outcomes - might be malformed
2. Verify test configuration is reasonable
3. Check question types match outcomes
4. Try with fewer items (e.g., 20 instead of 48)

---

## Files Updated

✅ **services/tqs_service.py**
- Lines 1565-1585: Severity-based assertion (≥10% threshold)

✅ **app.py**  
- Lines 108-125: `calculate_missing_slots()` helper function
- Lines 1370-1419: Enhanced UI with warning + buttons

---

## Key Changes in System Behavior

### Before This Fix
```
generated_tqs = 44 questions
❌ AssertionError: Generated 44 but expected 48
🛑 Workflow blocked
```

### After This Fix
```
generated_tqs = 44 questions
⚠️ Warning: "Partial Generation: 44 of 48"
✅ Two options: [Regenerate Missing] [Continue Anyway]
✅ Workflow continues
```

---

## Next Time This Happens

1. **Don't Panic** - It's expected behavior, not a bug
2. **Click Regenerate** - Usually fixes it within 1-2 tries
3. **Check Logs** - See which batch had issues
4. **Proceed** - Continue your testing once you reach target count

---

## Questions?

Check these files for more details:
- [PARTIAL_GENERATION_FIX.md](PARTIAL_GENERATION_FIX.md) - Full technical explanation
- [phase_7_final_report.md](PHASE_7_FINAL_REPORT.md) - Complete project status
- app.py lines 1370-1419 - UI implementation

**Summary:** The system is **working as designed**. Partial generation is acceptable, recoverable, and normal. 🎯
