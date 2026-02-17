"""
GEMINI INTEGRATION EXAMPLE - Complete Code Snippets

This file contains ready-to-use code snippets for integrating Gemini AI into your Streamlit app.
Copy and paste these directly into your app.py where needed.

KEY PRINCIPLE: AI is an AUGMENTATION LAYER. Your system still controls:
- Validation logic
- Bloom distribution percentages  
- Total number of items
- Final formatting and display
"""

# ============================================================================
# SECTION 1: IMPORTS (Add to top of app.py)
# ============================================================================

"""
from services.ai_service import (
    classify_competencies_bloom,
    generate_test_questions
)
from core.config import GEMINI_API_KEY
"""

# ============================================================================
# SECTION 2: AI-ASSISTED BLOOM CLASSIFICATION IN UI
# ============================================================================

"""
# --- Learning Objectives with AI Assistance ---
with lesson_tabs[1]:
    st.markdown("### Learning Objectives")

    # Initialize session state
    if "lesson_objectives" not in st.session_state:
        st.session_state.lesson_objectives = []

    # Input fields
    col1, col2 = st.columns([2, 1])
    with col1:
        obj_text = st.text_input("Objective", key="obj_input")
    with col2:
        objective_method = st.radio("Method", ["Manual", "AI"], horizontal=True)

    if objective_method == "Manual":
        # Manual Bloom selection
        obj_bloom = st.selectbox(
            "Bloom's Level",
            ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
        )
        
        if st.button("Add Objective", key="add_obj_manual"):
            if obj_text:
                st.session_state.lesson_objectives.append({
                    "objective": obj_text,
                    "bloom": obj_bloom
                })
                st.success("✓ Objective added!")
                st.rerun()

    else:  # AI method
        if st.button("🤖 Get AI Suggestion", key="ai_bloom_suggest"):
            if obj_text:
                try:
                    with st.spinner("Analyzing with Gemini..."):
                        result = classify_competencies_bloom(
                            competencies=[obj_text],
                            api_key=GEMINI_API_KEY
                        )
                        
                        item = result["competencies"][0]
                        st.success(f"✓ Suggested Bloom Level: **{item['bloom_level']}**")
                        st.caption(f"Why: {item['justification']}")
                        
                        # Store AI suggestion in session
                        st.session_state.ai_suggestion = item["bloom_level"]
                        
                except Exception as e:
                    st.error(f"AI Error: {str(e)}")

        # Use suggested level
        if "ai_suggestion" in st.session_state:
            use_suggestion = st.checkbox("Use AI suggestion")
            if use_suggestion:
                bloom_to_use = st.session_state.ai_suggestion
            else:
                bloom_to_use = st.selectbox(
                    "Choose Bloom Level",
                    ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
                )
            
            if st.button("Add Objective", key="add_obj_ai"):
                if obj_text:
                    st.session_state.lesson_objectives.append({
                        "objective": obj_text,
                        "bloom": bloom_to_use
                    })
                    st.success("✓ Objective added!")
                    st.rerun()

    # Display objectives
    if st.session_state.lesson_objectives:
        st.dataframe(st.session_state.lesson_objectives, use_container_width=True)
        if st.button("Clear All", key="clear_obj"):
            st.session_state.lesson_objectives = []
            st.rerun()
"""

# ============================================================================
# SECTION 3: AI-ASSISTED TEST QUESTION GENERATION
# ============================================================================

"""
# --- Generate Test Questions (AI-Assisted) ---
with assess_tabs[4]:
    st.markdown("### Generate Test Questions")
    
    st.info(
        "🤖 **Gemini-Assisted Question Generation**\\n"
        "1. Select learning outcome\\n"
        "2. Specify Bloom level and number of items\\n"
        "3. Gemini generates questions\\n"
        "4. System validates before display\\n"
        "5. Download or use for TOS"
    )

    if "assessment_outcomes" not in st.session_state or not st.session_state.assessment_outcomes:
        st.warning("Define learning outcomes in Assessment section first.")
    else:
        outcomes = st.session_state.assessment_outcomes
        
        # Select outcome
        outcome_texts = [o["outcome"] for o in outcomes]
        selected_text = st.selectbox("Learning Outcome", outcome_texts)
        selected_outcome = next(o for o in outcomes if o["outcome"] == selected_text)
        
        # Question parameters
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            bloom_level = st.selectbox(
                "Bloom Level",
                ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
            )
        with col2:
            num_questions = st.number_input(
                "Num Questions",
                min_value=1,
                max_value=20,
                value=5
            )
        with col3:
            st.write("")  # Align button
            generate = st.button("🤖 Generate", use_container_width=True)

        if generate:
            try:
                with st.spinner("🤖 Generating with Gemini..."):
                    result = generate_test_questions(
                        competency=selected_outcome["outcome"],
                        bloom_level=bloom_level,
                        num_items=num_questions,
                        api_key=GEMINI_API_KEY,
                        subject=st.session_state.course_details.get("subject", ""),
                        context=st.session_state.course_details.get("grade_level", "")
                    )
                
                # Store in session
                st.session_state.current_questions = result["questions"]
                st.session_state.current_outcome = selected_outcome["outcome"]
                st.success(f"✓ Generated {len(result['questions'])} questions!")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.caption("Ensure GEMINI_API_KEY is set in .env file")

        # Display generated questions
        if "current_questions" in st.session_state:
            st.markdown("#### Generated Questions")
            
            questions = st.session_state.current_questions
            for i, q in enumerate(questions, 1):
                with st.expander(f"Q{i} - {q['difficulty']} | Type: {q['type']}"):
                    st.write(f"**Question:** {q['question']}")
                    
                    # Display choices
                    st.write("**Choices:**")
                    for j, choice in enumerate(q['choices']):
                        st.write(f"  {chr(65+j)}) {choice}")
                    
                    # Show/Hide answer
                    if st.checkbox(f"Show Answer", key=f"show_ans_{i}"):
                        correct_idx = ord(q['answer']) - ord('A')
                        st.success(f"✓ Correct Answer: **{q['answer']}) {q['choices'][correct_idx]}")
            
            # Export options
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Download as JSON"):
                    import json
                    json_data = json.dumps(questions, indent=2)
                    st.download_button(
                        label="Save JSON",
                        data=json_data,
                        file_name=f"questions_{st.session_state.current_outcome[:20]}.json",
                        mime="application/json"
                    )
            
            with col2:
                if st.button("📥 Download as CSV"):
                    import csv
                    import io
                    csv_buffer = io.StringIO()
                    writer = csv.DictWriter(
                        csv_buffer,
                        fieldnames=["Type", "Question", "Choice A", "Choice B", "Choice C", "Choice D", "Answer", "Difficulty"]
                    )
                    writer.writeheader()
                    for q in questions:
                        writer.writerow({
                            "Type": q["type"],
                            "Question": q["question"],
                            "Choice A": q["choices"][0],
                            "Choice B": q["choices"][1],
                            "Choice C": q["choices"][2],
                            "Choice D": q["choices"][3],
                            "Answer": q["answer"],
                            "Difficulty": q["difficulty"]
                        })
                    
                    st.download_button(
                        label="Save CSV",
                        data=csv_buffer.getvalue(),
                        file_name=f"questions_{st.session_state.current_outcome[:20]}.csv",
                        mime="text/csv"
                    )
"""

# ============================================================================
# SECTION 4: BATCH PROCESSING (CLASSIFY ALL + GENERATE)
# ============================================================================

"""
# Example: Generate question bank for entire course
from services.ai_service import batch_classify_and_generate

def generate_full_question_bank():
    '''
    Generates questions for all outcomes according to Bloom distribution.
    Returns structured data for review and export.
    '''
    if "assessment_outcomes" not in st.session_state:
        st.error("No outcomes defined")
        return None
    
    try:
        with st.spinner("🤖 Processing all outcomes..."):
            competencies = [o["outcome"] for o in st.session_state.assessment_outcomes]
            bloom_weights = st.session_state.get("bloom_weights", {})
            total_items = st.session_state.get("total_items", 50)
            
            result = batch_classify_and_generate(
                competencies=competencies,
                bloom_weights=bloom_weights,
                total_items=total_items,
                api_key=GEMINI_API_KEY,
                subject=st.session_state.course_details.get("subject", ""),
                context=st.session_state.course_details.get("grade_level", "")
            )
            
            st.session_state.question_bank = result
            st.success(f"✓ Generated question bank: {result['total_questions']} items")
            return result
            
    except Exception as e:
        st.error(f"Failed: {str(e)}")
        return None

# Use in Streamlit:
# if st.button("Generate Full Question Bank"):
#     result = generate_full_question_bank()
"""

# ============================================================================
# SECTION 5: ERROR HANDLING PATTERN
# ============================================================================

"""
# Recommended error handling pattern:

from services.ai_service import classify_competencies_bloom
from core.config import GEMINI_API_KEY

if st.button("Test AI Service"):
    try:
        # Attempt to call AI service
        with st.spinner("Processing..."):
            result = classify_competencies_bloom(
                competencies=["Test competency"],
                api_key=GEMINI_API_KEY
            )
        
        # If successful (JSON was validated)
        st.success("✓ AI service working correctly!")
        st.json(result)
        
    except ValueError as ve:
        # JSON parsing or validation error
        st.error(f"❌ Response validation error: {str(ve)}")
        st.caption("Gemini response format incorrect. Try again.")
        
    except KeyError:
        # Configuration error
        st.error("❌ Configuration Error")
        st.caption("Check GEMINI_API_KEY in .env file")
        
    except Exception as e:
        # Generic error (API, network, etc.)
        st.error(f"❌ Error: {type(e).__name__}")
        st.caption(f"Details: {str(e)}")
        
        # Options for user
        if st.button("Retry"):
            st.rerun()
"""

# ============================================================================
# SECTION 6: CACHING FOR PERFORMANCE
# ============================================================================

"""
# Add caching to avoid repeated Gemini calls:

import streamlit as st
from services.ai_service import classify_competencies_bloom
from core.config import GEMINI_API_KEY

@st.cache_data(ttl=3600)  # Cache for 1 hour
def cached_classify(competencies_tuple):
    '''Cache Bloom classification results.'''
    return classify_competencies_bloom(
        competencies=list(competencies_tuple),
        api_key=GEMINI_API_KEY
    )

# Usage:
# competencies = ["Identify...", "Analyze...", "Create..."]
# result = cached_classify(tuple(competencies))
"""

# ============================================================================
# SECTION 7: COMPLETE MINIMAL EXAMPLE
# ============================================================================

"""
# Minimal working example - add this to your app.py

import streamlit as st
from services.ai_service import classify_competencies_bloom
from core.config import GEMINI_API_KEY

st.set_page_config(page_title="SmartLesson AI Test")

st.title("Gemini AI Service Test")

# Input
competencies = st.text_area("Enter competencies (one per line)")

if st.button("Classify with Gemini"):
    if competencies:
        try:
            comp_list = [c.strip() for c in competencies.split("\\n") if c.strip()]
            
            with st.spinner("🤖 Classifying..."):
                result = classify_competencies_bloom(
                    competencies=comp_list,
                    api_key=GEMINI_API_KEY
                )
            
            st.success("✓ Classification complete!")
            st.json(result)
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Enter at least one competency")
"""

# ============================================================================
# KEY REMINDERS
# ============================================================================

"""
✓ GEMINI HANDLES:
  - Bloom classification
  - Question generation
  - JSON response structure
  - Suggesting phrasing

✗ GEMINI DOES NOT HANDLE:
  - Changing question count (system adjusts)
  - Overriding validation (system validates all JSON)
  - Setting Bloom percentages (system allocates)
  - Changing final format (system controls display)
  - Calculating TOS totals (TOS service does this)

WORKFLOW:
1. UI captures user input
2. AI Service (Gemini) processes
3. Validation Layer checks JSON
4. System Service (TOS) calculates
5. UI displays validated results

Never import Gemini directly in app.py!
Always use: from services.ai_service import ...
"""
