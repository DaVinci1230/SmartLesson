# Google Gemini AI Service Integration Guide

## Overview

This guide shows how to use the `ai_service.py` module with your SmartLesson Streamlit application. The AI service is an **augmentation layer only** — it classifies competencies and generates questions, but your system controls validation, totals, and formatting.

## Architecture Principle

```
┌─────────────────┐
│  Streamlit UI   │
│  (Unchanged)    │
└────────┬────────┘
         │
         ├─→ AI Service (Gemini)
         │   ├── Bloom Classification
         │   └── Question Generation
         │
         ├─→ Validation Layer (Your System)
         │   ├── JSON Schema Validation
         │   ├── Bloom Distribution Check
         │   └── Question Count Verification
         │
         └─→ TOS Service (Unchanged)
             ├── Compute Totals
             └── Allocate Items
```

## Quick Setup

### 1. Environment Configuration

Add to your `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

### 2. Install Dependencies

```bash
pip install google-generativeai>=0.3.2
pip install jsonschema>=4.26.0
```

These are already in `requirements.txt`.

## Usage Examples

### Example 1: Classify a Single Competency List

```python
from services.ai_service import classify_competencies_bloom
from core.config import GEMINI_API_KEY

# Your learning competencies
competencies = [
    "Identify the parts of a plant cell",
    "Explain the difference between mitosis and meiosis",
    "Design an experiment to test photosynthesis",
    "Evaluate the effectiveness of different fertilizers"
]

# Classify using Gemini
result = classify_competencies_bloom(
    competencies=competencies,
    api_key=GEMINI_API_KEY
)

# Result structure:
# {
#     "competencies": [
#         {
#             "text": "Identify the parts of a plant cell",
#             "bloom_level": "Remember",
#             "justification": "..."
#         },
#         ...
#     ]
# }

# Use classifications
for item in result["competencies"]:
    print(f"{item['text']} → {item['bloom_level']}")
```

### Example 2: Generate Test Questions

```python
from services.ai_service import generate_test_questions
from core.config import GEMINI_API_KEY

competency = "Describe the water cycle"
bloom_level = "Understand"
num_items = 5

result = generate_test_questions(
    competency=competency,
    bloom_level=bloom_level,
    num_items=num_items,
    api_key=GEMINI_API_KEY,
    subject="Science",
    context="Grade 10"
)

# Result structure:
# {
#     "questions": [
#         {
#             "type": "MCQ",
#             "question": "What is the first step of the water cycle?",
#             "choices": ["Evaporation", "Condensation", "Precipitation", "Infiltration"],
#             "answer": "A",
#             "difficulty": "Easy"
#         },
#         ...
#     ]
# }

# Use generated questions
for q in result["questions"]:
    print(f"Q: {q['question']}")
    print(f"Choices: {q['choices']}")
    print(f"Answer: {q['answer']}")
    print()
```

### Example 3: Batch Processing with Distribution Control

```python
from services.ai_service import batch_classify_and_generate
from core.config import GEMINI_API_KEY

competencies = [
    "Define key biology terms",
    "Analyze enzyme function",
    "Create experimental design"
]

# Your system controls the Bloom distribution
bloom_weights = {
    "Remember": 20,
    "Understand": 25,
    "Apply": 20,
    "Analyze": 20,
    "Evaluate": 10,
    "Create": 5
}

total_items = 50

result = batch_classify_and_generate(
    competencies=competencies,
    bloom_weights=bloom_weights,
    total_items=total_items,
    api_key=GEMINI_API_KEY,
    subject="Biology",
    context="College Level"
)

# Result includes:
# - classifications: Competencies mapped to Bloom levels
# - questions_by_competency: Generated questions for each
# - total_questions: Total questions generated

print(f"Classifications: {result['classifications']}")
print(f"Total Questions Generated: {result['total_questions']}")
```

## Integration into Streamlit App

### Step 1: Import the AI Service

At the top of your `app.py`:

```python
from services.ai_service import (
    classify_competencies_bloom,
    generate_test_questions
)
from core.config import GEMINI_API_KEY
```

### Step 2: Add AI-Assisted Competency Classification

Add this in the Learning Objectives tab:

```python
# --- Learning Objectives (WITH AI ASSISTANCE) ---
with lesson_tabs[1]:
    st.markdown("### Learning Objectives")

    # Initialize session state
    if "lesson_objectives" not in st.session_state:
        st.session_state.lesson_objectives = []

    # Add objective manually
    obj_text = st.text_input("Objective")
    obj_bloom = st.selectbox(
        "Bloom's Level",
        ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        add_manual = st.button("Add Objective Manually")
    with col2:
        use_ai = st.button("🤖 Suggest Bloom Level")

    # Manual addition
    if add_manual:
        if obj_text:
            st.session_state.lesson_objectives.append({
                "objective": obj_text,
                "bloom": obj_bloom
            })
            st.success("Objective added!")

    # AI-assisted classification
    if use_ai:
        if obj_text:
            try:
                with st.spinner("🤖 Analyzing with Gemini..."):
                    result = classify_competencies_bloom(
                        competencies=[obj_text],
                        api_key=GEMINI_API_KEY
                    )
                    
                    ai_bloom = result["competencies"][0]["bloom_level"]
                    ai_justification = result["competencies"][0]["justification"]
                    
                    st.info(f"**AI Suggestion:** {ai_bloom}")
                    st.caption(ai_justification)
                    
                    # User still controls final choice
                    confirm = st.button("✓ Use This Classification")
                    if confirm:
                        st.session_state.lesson_objectives.append({
                            "objective": obj_text,
                            "bloom": ai_bloom
                        })
                        st.success("Objective added with AI assistance!")
            except Exception as e:
                st.error(f"❌ AI Classification Error: {str(e)}")
                st.caption("Fall back to manual selection")

    # Display objectives
    if st.session_state.lesson_objectives:
        st.dataframe(st.session_state.lesson_objectives)
```

### Step 3: Add AI-Assisted Question Generation

Replace the TQS placeholder section:

```python
# --- Generate TQS (WITH AI ASSISTANCE) ---
with assess_tabs[4]:
    st.markdown("### Generate Test Questions (AI-Assisted)")

    st.info("""
    🤖 **How it works:**
    1. Select a learning outcome
    2. Specify Bloom level and number of items
    3. Gemini generates questions
    4. System validates and displays
    5. You can download question bank
    """)

    # Show available outcomes
    if "assessment_outcomes" in st.session_state and st.session_state.assessment_outcomes:
        outcomes = st.session_state.assessment_outcomes
        selected_outcome = st.selectbox(
            "Select Learning Outcome",
            [o["outcome"] for o in outcomes]
        )

        # Find selected outcome details
        selected = next((o for o in outcomes if o["outcome"] == selected_outcome), None)

        if selected:
            col1, col2, col3 = st.columns(3)
            with col1:
                bloom_level = st.selectbox(
                    "Bloom Level",
                    ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
                )
            with col2:
                num_questions = st.number_input(
                    "Number of Questions",
                    min_value=1,
                    max_value=20,
                    value=5
                )
            with col3:
                generate_btn = st.button("🤖 Generate with Gemini")

            if generate_btn:
                try:
                    with st.spinner("🤖 Generating questions..."):
                        result = generate_test_questions(
                            competency=selected_outcome,
                            bloom_level=bloom_level,
                            num_items=num_questions,
                            api_key=GEMINI_API_KEY,
                            subject=st.session_state.course_details.get("subject", ""),
                            context=st.session_state.course_details.get("grade_level", "")
                        )

                        # Store in session state
                        st.session_state.generated_questions = result["questions"]
                        st.success(f"✓ Generated {len(result['questions'])} questions!")

                        # Display questions
                        for i, q in enumerate(result["questions"], 1):
                            with st.expander(f"Question {i} [{q['difficulty']}]"):
                                st.write(f"**Q:** {q['question']}")
                                st.write(f"**A)** {q['choices'][0]}")
                                st.write(f"**B)** {q['choices'][1]}")
                                st.write(f"**C)** {q['choices'][2]}")
                                st.write(f"**D)** {q['choices'][3]}")
                                
                                # Show answer (system controls revelation)
                                if st.checkbox(f"Show Answer - Q{i}"):
                                    st.success(f"**Answer: {q['answer']}")

                        # Export questions
                        if st.button("📥 Download Question Bank"):
                            import json
                            questions_json = json.dumps(result["questions"], indent=2)
                            st.download_button(
                                label="Download JSON",
                                data=questions_json,
                                file_name="questions.json",
                                mime="application/json"
                            )

                except Exception as e:
                    st.error(f"❌ Generation Error: {str(e)}")
                    st.caption("Please try again or report to developer")
    else:
        st.warning("Please define learning outcomes in the Assessment section first.")
```

## Error Handling Pattern

```python
from services.ai_service import classify_competencies_bloom
from core.config import GEMINI_API_KEY

try:
    # Call AI service
    result = classify_competencies_bloom(
        competencies=["Your competency here"],
        api_key=GEMINI_API_KEY
    )
    
    # If we get here, JSON was validated successfully
    # Use the result
    st.success("✓ Classification successful!")
    st.json(result)
    
except ValueError as e:
    # JSON parsing or validation error
    st.error(f"❌ Invalid response format: {str(e)}")
    st.caption("Gemini response didn't match expected format")
    
except Exception as e:
    # Other errors (API, network, etc.)
    st.error(f"❌ Error: {str(e)}")
    st.caption("Check GEMINI_API_KEY and internet connection")
```

## JSON Validation Details

All responses are validated against strict schemas:

### Bloom Classification Schema
```json
{
  "type": "object",
  "properties": {
    "competencies": {
      "type": "array",
      "items": {
        "properties": {
          "text": "string (unchanged from input)",
          "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create",
          "justification": "string"
        }
      }
    }
  }
}
```

### Test Question Schema
```json
{
  "type": "object",
  "properties": {
    "questions": {
      "type": "array",
      "items": {
        "properties": {
          "type": "MCQ",
          "question": "string",
          "choices": ["array of 4 strings"],
          "answer": "A|B|C|D",
          "difficulty": "Easy|Medium|Hard"
        }
      }
    }
  }
}
```

## System Controls (NOT Gemini-Controlled)

Your application controls:

1. **Question Count**: If Gemini returns wrong count, system adjusts
2. **Validation**: All JSON validated before use
3. **Bloom Distribution**: System allocates items, not Gemini
4. **Totals**: TOS service calculates, Gemini just suggests questions
5. **Final Formatting**: Your UI controls what's displayed

## Troubleshooting

### Issue: "GEMINI_API_KEY environment variable is not set"

**Solution**: Add to `.env` file:
```
GEMINI_API_KEY=your_key_here
```

### Issue: "Could not extract valid JSON from Gemini response"

**Solution**: Gemini response format was unexpected. The module tries multiple extraction methods:
- Code block markers (```json)
- Raw JSON objects
- Custom JSON parsing

If all fail, an error is raised. This forces Gemini to be more precise.

### Issue: "JSON validation failed"

**Solution**: Gemini response didn't match schema. Check:
- Are all required fields present?
- Is `answer` one of A, B, C, D?
- Is `bloom_level` valid?
- Are there exactly 4 choices?

### Issue: "Generated X questions, but Y were requested"

**Solution**: System automatically truncates to requested number. If consistent issue, check prompt in `ai_service.py`.

## Performance Tips

1. **Cache Results**: Use Streamlit's `@st.cache_data` decorator
```python
@st.cache_data(ttl=3600)
def get_classifications(competencies_tuple):
    return classify_competencies_bloom(list(competencies_tuple), GEMINI_API_KEY)
```

2. **Batch Processing**: Classify multiple competencies in one call rather than individually

3. **Show Progress**: Use `st.spinner()` during Gemini calls for better UX

## Security Notes

- **Never commit GEMINI_API_KEY to version control**
- Add `.env` to `.gitignore`
- Use environment variables in production
- The API key is read-only to Gemini configuration, never logged or cached

## Next Steps

1. Set `GEMINI_API_KEY` in your `.env` file
2. Test with simple examples first
3. Integrate into your Streamlit UI incrementally
4. Validate responses in development before deploying
5. Monitor API usage to stay within free tier limits

## Contact & Support

For issues:
1. Check logs: Look for logging output from `ai_service.py`
2. Verify API key is correct
3. Ensure jsonschema is installed: `pip install jsonschema`
4. Test directly in Python before integrating into Streamlit
