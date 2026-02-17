# GEMINI API - QUICK REFERENCE CARD

## 🚀 5-Minute Setup

```bash
# 1. Get key from https://makersuite.google.com/app/apikey
# 2. Add to .env file
GEMINI_API_KEY=your_api_key_here

# 3. Test installation
python test_ai_service.py

# All tests passing? You're done! ✅
```

---

## 📝 Most Common Code Patterns

### Pattern 1: Classify Competencies
```python
from services.ai_service import classify_competencies_bloom
from core.config import GEMINI_API_KEY

result = classify_competencies_bloom(
    competencies=["Identify cell parts", "Design experiment"],
    api_key=GEMINI_API_KEY
)
```

### Pattern 2: Generate Questions
```python
from services.ai_service import generate_test_questions
from core.config import GEMINI_API_KEY

result = generate_test_questions(
    competency="Explain photosynthesis",
    bloom_level="Understand",
    num_items=5,
    api_key=GEMINI_API_KEY
)
```

### Pattern 3: Add to Streamlit
```python
if st.button("🤖 AI Suggest"):
    with st.spinner("Analyzing..."):
        result = classify_competencies_bloom([obj_text], GEMINI_API_KEY)
        st.info(result["competencies"][0]["bloom_level"])
```

### Pattern 4: Error Handling
```python
try:
    result = classify_competencies_bloom(competencies, GEMINI_API_KEY)
except Exception as e:
    st.error(f"Error: {e}")
```

---

## 🔑 Three Core Functions

| Function | Does | Returns |
|----------|------|---------|
| `classify_competencies_bloom(competencies, api_key)` | Assigns Bloom levels | JSON with levels |
| `generate_test_questions(competency, bloom_level, num_items, api_key)` | Creates MCQs | JSON with questions |
| `batch_classify_and_generate(...)` | Does both together | Combined results |

---

## ✅ System-Controlled (NOT Gemini)

- Bloom percentage distribution
- Total number of items
- Question count validation
- TOS calculations
- JSON validation
- Display formatting
- Original text preservation

---

## ❌ Common Errors & Fixes

| Error | Fix |
|-------|-----|
| "not set" | `export GEMINI_API_KEY=key` |
| "ImportError" | `pip install google-generativeai` |
| "Could not extract JSON" | Try again or check API key |
| "validation failed" | Check response format in logs |
| "429 Rate Limit" | Weight and use caching |

---

## 📄 JSON Output Examples

### Bloom Classification
```json
{
  "competencies": [{
    "text": "Identify cell parts",
    "bloom_level": "Remember",
    "justification": "Requires recalling knowledge..."
  }]
}
```

### Question Generation
```json
{
  "questions": [{
    "type": "MCQ",
    "question": "What organelle produces energy?",
    "choices": ["Mitochondria", "Nucleus", "Ribosome", "Vacuole"],
    "answer": "A",
    "difficulty": "Easy"
  }]
}
```

---

## 🧪 Quick Test

Run directly in Python:
```python
from services.ai_service import classify_competencies_bloom
from core.config import GEMINI_API_KEY

result = classify_competencies_bloom(["Test"], GEMINI_API_KEY)
print("✓ Working!" if result else "✗ Failed")
```

Or in terminal:
```bash
python test_ai_service.py
```

---

## 📚 Documentation Map

**Start here** → `README_GEMINI_INTEGRATION.md` (5 min)  
**Learn how** → `GEMINI_IMPLEMENTATION_GUIDE.md` (10 min)  
**See examples** → `GEMINI_INTEGRATION_EXAMPLES.md` (15 min)  
**Copy code** → `GEMINI_CODE_SNIPPETS.py` (5 min)  
**Full info** → `INTEGRATION_SUMMARY.md` (10 min)  

---

## ⏱️ Time to Production

| Step | Time |
|------|------|
| Setup API key | 5 min |
| Run test | 2 min |
| Add code to app | 15 min |
| Test in Streamlit | 10 min |
| Deploy | 5 min |
| **Total** | **37 min** |

---

## 💡 Pro Tips

1. **Use caching**:
   ```python
   @st.cache_data(ttl=3600)
   def get_classes(comp_tuple):
       return classify_competencies_bloom(list(comp_tuple), GEMINI_API_KEY)
   ```

2. **Show spinners**:
   ```python
   with st.spinner("🤖 Processing..."):
       result = function_call()
   ```

3. **Batch requests** (faster than individual)

4. **Monitor usage** in Google AI Studio

---

## 🆘 Troubleshooting Flowchart

```
Something not working?
  ↓
  → Check .env has GEMINI_API_KEY
  → Run: python test_ai_service.py
  → Check logs for errors
  → Is API key valid? (check Google AI Studio)
  → Internet connected?
  → Try running test again
  → Check documentation
  → Search error message
```

---

## 🔐 Security Checklist

- [ ] API key in `.env`
- [ ] `.env` in `.gitignore`
- [ ] Never hardcode API key
- [ ] Never log API key
- [ ] Use env vars in production

---

## 📊 Performance

| Operation | Time |
|-----------|------|
| Classify 1 competency | ~5-10 sec |
| Generate 5 questions | ~10-15 sec |
| Batch 10 competencies | ~60-90 sec |
| Validate JSON | < 100ms |

---

## 🎯 Implementation Checklist

- [ ] API key obtained
- [ ] .env configured
- [ ] `test_ai_service.py` passes
- [ ] Code copied to app.py
- [ ] Streamlit runs without errors
- [ ] Features tested
- [ ] Deployed to production

---

## 📞 Support Resources

- Google AI Docs: https://ai.google.dev/
- Get API Key: https://makersuite.google.com/app/apikey
- Streamlit Docs: https://docs.streamlit.io/
- JSON Schema: https://json-schema.org/

---

## ✨ What You Get

✅ Bloom classification (with AI assistance)  
✅ Question generation (with AI assistance)  
✅ Full JSON validation  
✅ Error handling  
✅ Complete documentation  
✅ Test suite  
✅ Code examples  
✅ Production ready  

---

**Status**: ✅ Ready to Use  
**Setup Time**: ~5 minutes  
**Integration Time**: ~30 minutes  
**Difficulty**: Easy  

Get started now! → Read `README_GEMINI_INTEGRATION.md`
