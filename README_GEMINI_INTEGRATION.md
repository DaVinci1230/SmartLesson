# Google Gemini API Integration - SmartLesson

## 📋 Quick Start

### 1. Get Your API Key
- Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
- Click "Get API Key"
- Copy your key

### 2. Configure Environment
Create or update `.env` file in project root:
```env
GEMINI_API_KEY=your_api_key_here
```

### 3. Verify Installation
```bash
python test_ai_service.py
```

All tests should pass ✓

### 4. Use in Your Streamlit App
See code snippets in `GEMINI_CODE_SNIPPETS.py`

---

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `services/ai_service.py` | Core AI service module with Gemini integration |
| `core/config.py` | Configuration (updated with GEMINI_API_KEY) |
| `requirements.txt` | Dependencies (updated with google-generativeai) |
| `GEMINI_INTEGRATION_EXAMPLES.md` | Complete integration guide with examples |
| `GEMINI_CODE_SNIPPETS.py` | Ready-to-use code snippets |
| `test_ai_service.py` | Automated test suite |

---

## 🤖 What Gemini Does

```
INPUT → Gemini API → Structured JSON → Validation → Your System → Display
```

### Gemini Capabilities:
✓ Classify competencies to Bloom's levels  
✓ Justify classifications  
✓ Generate multiple-choice questions  
✓ Return structured JSON  
✓ Follow strict format requirements  

### System Controls:
✓ Validates all JSON responses  
✓ Enforces Bloom percentages  
✓ Calculates TOS totals  
✓ Adjusts question counts if needed  
✓ Controls final display format  

---

## 🚀 Main Functions

### 1. Classify Competencies to Bloom Levels

```python
from services.ai_service import classify_competencies_bloom
from core.config import GEMINI_API_KEY

result = classify_competencies_bloom(
    competencies=[
        "Identify cell parts",
        "Explain photosynthesis",
        "Design an experiment"
    ],
    api_key=GEMINI_API_KEY
)

# Output:
# {
#   "competencies": [
#     {
#       "text": "Identify cell parts",
#       "bloom_level": "Remember",
#       "justification": "..."
#     },
#     ...
#   ]
# }
```

### 2. Generate Test Questions

```python
from services.ai_service import generate_test_questions
from core.config import GEMINI_API_KEY

result = generate_test_questions(
    competency="Explain photosynthesis",
    bloom_level="Understand",
    num_items=5,
    api_key=GEMINI_API_KEY,
    subject="Science",
    context="Grade 8"
)

# Output:
# {
#   "questions": [
#     {
#       "type": "MCQ",
#       "question": "What is photosynthesis?",
#       "choices": ["...", "...", "...", "..."],
#       "answer": "A",
#       "difficulty": "Easy"
#     },
#     ...
#   ]
# }
```

### 3. Batch Process (Classify + Generate All)

```python
from services.ai_service import batch_classify_and_generate
from core.config import GEMINI_API_KEY

result = batch_classify_and_generate(
    competencies=["Identify...", "Analyze...", "Create..."],
    bloom_weights={
        "Remember": 20,
        "Understand": 25,
        "Apply": 20,
        "Analyze": 20,
        "Evaluate": 10,
        "Create": 5
    },
    total_items=50,
    api_key=GEMINI_API_KEY
)

# Output includes classifications and questions for all competencies
# Total questions = 50, distributed across bloom levels
```

---

## ✅ JSON Validation

All responses are validated before returning:

### Bloom Classification Schema
Required fields:
- `competencies[].text` - Original competency (unchanged)
- `competencies[].bloom_level` - One of 6 Bloom levels
- `competencies[].justification` - Reason for classification

### Test Question Schema  
Required fields:
- `questions[].type` - MCQ (or other types)
- `questions[].question` - Question text
- `questions[].choices` - Exactly 4 choices
- `questions[].answer` - A, B, C, or D
- `questions[].difficulty` - Easy, Medium, or Hard

---

## 🔒 System Controls

Your system enforces:

```
Bloom Distribution Control
└─ System sets percentages (20% Remember, 25% Understand, etc.)
└─ System allocates total_items across Bloom levels
└─ Gemini generates questions for each level
└─ System validates count matches requested

Question Count Control
└─ You request N questions
└─ Gemini generates questions
└─ System validates count matches N (truncates if needed)
└─ Displays only validated questions

TOS Calculation Control
└─ TOS service (not Gemini) calculates all totals
└─ TOS service allocates items to outcomes
└─ Gemini only suggests question content
└─ Display shows system-calculated values

Format Control
└─ Your UI controls how content is displayed
└─ System validates before rendering
└─ Gemini cannot change formatting
└─ User sees formatted system output
```

---

## 📊 Error Handling

All functions include try-catch and validation:

```python
try:
    result = classify_competencies_bloom(competencies, GEMINI_API_KEY)
    # JSON was validated, safe to use
    
except ValueError as e:
    # JSON parsing or validation failed
    print(f"Validation error: {e}")
    
except Exception as e:
    # API error, network error, etc.
    print(f"Error: {e}")
```

---

## 🧪 Testing

Run the test suite:

```bash
python test_ai_service.py
```

Tests included:
1. ✓ Import verification
2. ✓ Bloom classification
3. ✓ Question generation
4. ✓ Batch processing
5. ✓ JSON validation

---

## 💡 Best Practices

### Do:
✓ Cache results to reduce API calls
✓ Show loading spinner during Gemini calls
✓ Validate before displaying
✓ Handle errors gracefully
✓ Log API usage
✓ Keep API key in .env (never commit)
✓ Use specific, detailed prompts
✓ Review Gemini output before using

### Don't:
✗ Don't let Gemini modify question counts
✗ Don't trust Gemini for calculations/totals
✗ Don't use Gemini for validation logic
✗ Don't expose API key in code
✗ Don't assume JSON format without validation
✗ Don't rely on Gemini for system-critical decisions

---

## 🔧 Integration Checklist

- [ ] Set GEMINI_API_KEY in .env
- [ ] Run `python test_ai_service.py` (all tests pass)
- [ ] Import ai_service functions in app.py
- [ ] Add UI elements for AI assistance (copy from GEMINI_CODE_SNIPPETS.py)
- [ ] Test with small examples first
- [ ] Display loading indicators during API calls
- [ ] Handle errors with user-friendly messages
- [ ] Cache results where appropriate
- [ ] Document any custom integrations

---

## 📈 Performance Tips

1. **Cache Results**
```python
@st.cache_data(ttl=3600)
def cached_classify(competencies_tuple):
    return classify_competencies_bloom(list(competencies_tuple), GEMINI_API_KEY)
```

2. **Batch Small Competencies**
- Instead of classifying 20 individually: do it once with all 20
- Saves API calls and time

3. **Show Progress**
```python
with st.spinner("🤖 Processing..."):
    result = classify_competencies_bloom(...)
```

4. **Lazy Load Questions**
- Don't generate all questions upfront
- Generate per-outcome as needed

---

## 🐛 Troubleshooting

### "GEMINI_API_KEY environment variable is not set"
→ Add to .env: `GEMINI_API_KEY=your_key`

### "Could not extract valid JSON"
→ Gemini response format unexpected. Try:
- Simpler prompt
- Different wording
- Smaller batch

### "JSON validation failed"
→ Gemini response missing required fields. Check:
- Are all 4 question choices present?
- Is answer one of A, B, C, D?
- Is bloom_level valid?

### "API rate limit exceeded"
→ Add delay between calls or reduce batch size

### Status: 429 Too Many Requests
→ Wait before making more API calls
→ Use caching to reduce calls

---

## 📚 Documentation Files

- **GEMINI_INTEGRATION_EXAMPLES.md** - Complete integration guide with code examples
- **GEMINI_CODE_SNIPPETS.py** - Copy-paste ready code
- **this file** - Quick reference and overview

---

## 🎯 Architecture Summary

```
┌──────────────────────────────────────────────┐
│         Streamlit UI (Unchanged)              │
├──────────────────────────────────────────────┤
│                                              │
│  Classroom:                                  │
│  - Upload PDF → Extract Syllabus             │
│  - Define Outcomes → Set Hours                │
│  - Set Bloom % → Set Total Items             │
│                                              │
│  Assessment:                                 │
│  - [NEW] AI Classify Competencies ← Gemini   │
│  - [NEW] AI Generate Questions ← Gemini     │
│  - Generate TOS (System Controlled)          │
│  - Export to Excel                           │
│                                              │
├──────────────────────────────────────────────┤
│      AI Service Layer (NEW)                  │
│  - Google Gemini Integration                 │
│  - JSON Validation                           │
│  - Error Handling                            │
├──────────────────────────────────────────────┤
│      System Service Layer (Unchanged)        │
│  - TOS Calculation                           │
│  - Export Service                            │
│  - PDF Service                               │
└──────────────────────────────────────────────┘
```

---

## ✨ What's New

### Added Files:
- `services/ai_service.py` - Gemini integration module
- `test_ai_service.py` - Test suite
- `GEMINI_INTEGRATION_EXAMPLES.md` - Full guide
- `GEMINI_CODE_SNIPPETS.py` - Code examples

### Updated Files:
- `core/config.py` - Added GEMINI_API_KEY
- `requirements.txt` - Added google-generativeai

### Unchanged:
- Your Streamlit UI layout
- Validation logic
- TOS service
- Export service
- PDF service
- All existing functionality

---

## 📞 Support

For issues:
1. Check error messages in logs
2. Run `test_ai_service.py` to diagnose
3. Verify API key is valid and active
4. Check internet connection
5. Review GEMINI_INTEGRATION_EXAMPLES.md

---

**Status**: ✓ Ready to use  
**Version**: 1.0  
**Last Updated**: February 14, 2026  
**Architecture**: System-Controlled with AI Augmentation
