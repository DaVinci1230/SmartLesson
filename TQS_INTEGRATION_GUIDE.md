# TQS Integration Guide - How to Use in app.py

**Status:** ✅ Ready for Integration  
**Date:** February 15, 2026  

---

## 🎯 Quick Integration

### Step 1: Import the Functions

```python
from services.tqs_service import generate_tqs, get_tqs_statistics, export_tqs_to_json
from services.tos_slot_assignment_service import assign_question_types_to_bloom_slots
import os
```

### Step 2: Add Generation Button in Streamlit

```python
# In Generate TOS section of app.py
if st.button("🚀 Generate Test Questions (TQS)"):
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            st.error("❌ GEMINI_API_KEY not set in environment")
        else:
            st.info("Generating test questions from exam blueprint...")
            
            # Generate TQS
            tqs = generate_tqs(
                st.session_state.assigned_slots,  # From soft-mapping
                api_key,
                shuffle=True
            )
            
            # Store in session
            st.session_state.tqs = tqs
            
            # Show statistics
            stats = get_tqs_statistics(tqs)
            st.success(f"✅ Generated {stats['total_questions']} questions worth {stats['total_points']} points")
            
            # Display breakdown
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("By Question Type")
                for qtype in sorted(stats['questions_by_type'].keys()):
                    count = stats['questions_by_type'][qtype]
                    points = stats['points_by_type'].get(qtype, 0)
                    st.write(f"• {qtype}: {count} questions ({points} pts)")
            
            with col2:
                st.subheader("By Bloom Level")
                for bloom in sorted(stats['questions_by_bloom'].keys()):
                    count = stats['questions_by_bloom'][bloom]
                    points = stats['points_by_bloom'].get(bloom, 0)
                    st.write(f"• {bloom}: {count} questions ({points} pts)")
            
            # Show preview
            if st.checkbox("Preview first 3 questions"):
                for q in tqs[:3]:
                    st.markdown(f"### Q{q['question_number']}: {q['type']} ({q['points']} pts)")
                    st.write(f"**Outcome:** {q['outcome']}")
                    st.write(f"**Question:** {q['question_text']}")
                    
                    if q['type'] == 'MCQ':
                        st.write("**Choices:**")
                        for i, choice in enumerate(q['choices']):
                            st.write(f"• {chr(65+i)}) {choice}")
                        st.write(f"**Answer:** {q['correct_answer']}")
                    
                    elif q['type'] == 'Short Answer':
                        st.write(f"**Answer Key:** {q['answer_key'][:150]}...")
                    
                    else:  # Essay, Problem Solving, Drawing
                        st.write(f"**Sample Answer:** {q['sample_answer'][:150]}...")
                        st.write(f"**Rubric:** {len(q['rubric']['criteria'])} criteria, {q['rubric']['total_points']} points")
    
    except Exception as e:
        st.error(f"❌ Failed to generate TQS: {str(e)}")
        logger.error(f"TQS generation error: {e}", exc_info=True)
```

### Step 3: Add Export to Excel (in Export Section)

```python
if st.button("📥 Export TQS to JSON"):
    if "tqs" in st.session_state:
        filename = f"tqs_{st.session_state.exam_term.lower()}_{st.session_state.year}.json"
        export_tqs_to_json(st.session_state.tqs, filename)
        st.success(f"✅ TQS exported to {filename}")
    else:
        st.warning("⚠️ No TQS generated yet. Click 'Generate Test Questions' first.")
```

---

## 🔄 Integration Points

### Where in the Workflow?

```
Course/Syllabus Tab
    ↓
Learning Outcomes Tab
    ↓
Assessment Profile Tab
    ↓
Generate TOS Tab
    ├─→ [NEW] Generate Test Questions ← ADD HERE
    ├─→ [NEW] Preview TQS
    └─→ [NEW] Export TQS
    ↓
Export Tab
```

### Required Session State Variables

```python
# Must exist before calling generate_tqs():
st.session_state.assigned_slots  # From soft-mapping (already generated)
st.session_state.exam_term       # "Midterm" or "Final" (already set)
st.session_state.year            # Academic year (already set)
```

### Optional Session State Variables

```python
# Created by TQS generation:
st.session_state.tqs             # Generated test question sheet
st.session_state.tqs_stats       # Statistics from get_tqs_statistics()
```

---

## 📋 Complete Integration Example

### Full Code Block for app.py

```python
# ========================================================================
# SECTION: TQS Generation (Add to Generate TOS tab)
# ========================================================================

st.markdown("---")
st.subheader("📝 Step 3: Generate Test Questions (TQS)")

st.write("Based on the assigned question types, generate actual test questions using AI.")

if st.button("🚀 Generate Test Questions", key="generate_tqs_button"):
    try:
        # Verify prerequisites
        if "assigned_slots" not in st.session_state or not st.session_state.assigned_slots:
            st.error("❌ No assigned slots. Please generate TOS and assign question types first.")
        else:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                st.error("❌ GEMINI_API_KEY environment variable not set.")
            else:
                # Show progress
                progress_placeholder = st.empty()
                progress_placeholder.info("⏳ Generating test questions from exam blueprint...")
                
                try:
                    # Generate TQS
                    from services.tqs_service import generate_tqs, get_tqs_statistics
                    
                    tqs = generate_tqs(
                        assigned_slots=st.session_state.assigned_slots,
                        api_key=api_key,
                        shuffle=True
                    )
                    
                    # Store in session
                    st.session_state.tqs = tqs
                    st.session_state.tqs_stats = get_tqs_statistics(tqs)
                    
                    # Update progress
                    progress_placeholder.success(
                        f"✅ Generated {len(tqs)} test questions"
                    )
                    
                    # Display statistics
                    st.markdown("### TQS Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric(
                            "Total Questions",
                            st.session_state.tqs_stats["total_questions"]
                        )
                    with col2:
                        st.metric(
                            "Total Points",
                            f"{st.session_state.tqs_stats['total_points']:.0f}"
                        )
                    with col3:
                        st.metric(
                            "Question Types",
                            len(st.session_state.tqs_stats["questions_by_type"])
                        )
                    with col4:
                        st.metric(
                            "Bloom Levels",
                            len(st.session_state.tqs_stats["questions_by_bloom"])
                        )
                    
                    # Breakdown by type
                    st.markdown("### By Question Type")
                    type_df = pd.DataFrame([
                        {
                            "Type": qtype,
                            "Count": st.session_state.tqs_stats["questions_by_type"][qtype],
                            "Points": st.session_state.tqs_stats["points_by_type"].get(qtype, 0)
                        }
                        for qtype in sorted(st.session_state.tqs_stats["questions_by_type"].keys())
                    ])
                    st.dataframe(type_df, use_container_width=True)
                    
                    # Breakdown by Bloom
                    st.markdown("### By Bloom Level")
                    bloom_df = pd.DataFrame([
                        {
                            "Bloom Level": bloom,
                            "Count": st.session_state.tqs_stats["questions_by_bloom"][bloom],
                            "Points": st.session_state.tqs_stats["points_by_bloom"].get(bloom, 0)
                        }
                        for bloom in sorted(st.session_state.tqs_stats["questions_by_bloom"].keys())
                    ])
                    st.dataframe(bloom_df, use_container_width=True)
                    
                    # Preview
                    if st.checkbox("Preview sample questions", value=False, key="preview_tqs"):
                        st.markdown("### Sample Questions Preview")
                        
                        num_to_show = min(3, len(tqs))
                        for i, q in enumerate(tqs[:num_to_show]):
                            with st.expander(
                                f"Q{q['question_number']}: {q['type']} ({q['points']} pts) - "
                                f"{q['bloom']} - {q['outcome'][:40]}..."
                            ):
                                st.write(f"**Learning Outcome:** {q['outcome']}")
                                st.write(f"**Question Text:** {q['question_text']}")
                                
                                if q['type'] == 'MCQ':
                                    st.write("**Choices:**")
                                    for j, choice in enumerate(q['choices']):
                                        st.write(f"  {chr(65+j)}) {choice}")
                                    st.write(f"**Answer:** {q['correct_answer']}")
                                
                                elif q['type'] == 'Short Answer':
                                    st.write(f"**Answer Key:** {q['answer_key']}")
                                    if "rubric" in q and q["rubric"]:
                                        st.write("**Rubric:**")
                                        for criterion in q["rubric"]["criteria"]:
                                            st.write(
                                                f"• {criterion['descriptor']} "
                                                f"({criterion['points']} pts)"
                                            )
                                
                                else:  # Essay, Problem Solving, Drawing
                                    st.write(f"**Sample Answer:** {q['sample_answer'][:200]}...")
                                    st.write("**Rubric:**")
                                    for criterion in q["rubric"]["criteria"]:
                                        st.write(
                                            f"• {criterion['descriptor']} "
                                            f"({criterion['points']} pts)"
                                        )
                
                except Exception as e:
                    progress_placeholder.error(f"❌ Failed: {str(e)}")
                    logger.error(f"TQS generation error: {e}", exc_info=True)

st.markdown("---")

# ========================================================================
# SECTION: TQS Export (Add to Export tab)
# ========================================================================

if "tqs" in st.session_state:
    st.subheader("📤 Export Test Questions")
    
    if st.button("📥 Download TQS as JSON"):
        from services.tqs_service import export_tqs_to_json
        
        filename = f"tqs_{st.session_state.exam_term.lower()}_{st.session_state.year}.json"
        export_tqs_to_json(st.session_state.tqs, filename)
        
        st.success(f"✅ TQS exported to {filename}")
        st.json(st.session_state.tqs[:1])  # Show structure of first question
```

---

## 🔧 Configuration Checklist

- [ ] `GEMINI_API_KEY` environment variable set
- [ ] `services/tqs_service.py` in place
- [ ] `test_tqs_generation.py` available for testing
- [ ] Import statements added to app.py
- [ ] Button and UI code added to Generate TOS tab
- [ ] Export code added to Export tab
- [ ] Session state variables handled

---

## 📊 Data Flow in app.py

```
1. User uploads syllabus
   ↓
2. Extracts course info and outcomes
   ↓
3. User defines Bloom distribution
   ↓
4. Click "Generate TOS"
   ├─ Generates exam blueprint (TOS matrix)
   ├─ Soft-maps question types to Bloom slots
   └─ Stores assigned_slots in session
   ↓
5. Click "Generate Test Questions" [NEW]
   ├─ Takes assigned_slots as input
   ├─ Calls generate_tqs(assigned_slots, api_key)
   ├─ Generates actual test questions via Gemini
   └─ Stores tqs in session
   ↓
6. User previews questions
   ↓
7. Click "Export"
   ├─ Exports to JSON or Excel
   └─ Ready for printing/delivery
```

---

## 🧪 Testing Integration

### Manual Test in Streamlit

```python
# Add this to a test section in app.py
if st.checkbox("🧪 TEST MODE - TQS Functions"):
    st.markdown("### Test TQS Generation")
    
    if st.button("Run TQS Test with Sample Data"):
        # Sample data
        sample_slots = [
            {
                "outcome_id": 0,
                "outcome": "Identify components",
                "bloom": "Remember",
                "type": "MCQ",
                "points": 1
            },
            {
                "outcome_id": 0,
                "outcome": "Analyze processes",
                "bloom": "Analyze",
                "type": "Essay",
                "points": 5
            }
        ]
        
        # Generate
        from services.tqs_service import generate_tqs
        api_key = os.environ.get("GEMINI_API_KEY")
        
        try:
            tqs_test = generate_tqs(sample_slots, api_key)
            st.success(f"✅ Generated {len(tqs_test)} test questions")
            st.json(tqs_test)
        except Exception as e:
            st.error(f"❌ Test failed: {e}")
```

---

## ⚠️ Important Notes

### 1. API Key Required
```python
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY not set")
```

### 2. Session State Dependencies
```python
# assigned_slots MUST exist before calling generate_tqs
if "assigned_slots" not in st.session_state:
    st.error("Generate TOS first")
```

### 3. Generation Time
- Expect 20-60 seconds for 10-12 questions
- Show progress indicator to user
- Consider caching for same blueprint

### 4. Error Handling
```python
try:
    tqs = generate_tqs(...)
except ValueError as e:
    st.error(f"Generation failed: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    st.error("Unexpected error occurred")
```

---

## 🎓 Full Integration Example (Minimal)

```python
# Minimal integration - just the essentials

from services.tqs_service import generate_tqs, get_tqs_statistics

# In your Generate TOS section:
if st.button("Generate Test Questions"):
    try:
        tqs = generate_tqs(
            st.session_state.assigned_slots,
            os.environ.get("GEMINI_API_KEY"),
            shuffle=True
        )
        st.session_state.tqs = tqs
        
        stats = get_tqs_statistics(tqs)
        st.success(f"✅ Generated {stats['total_questions']} questions")
        
    except Exception as e:
        st.error(f"❌ Failed: {e}")
```

---

## 📞 Troubleshooting

### "No questions generated"
- Check GEMINI_API_KEY is set
- Verify assigned_slots has data
- Check internet connection

### "Rubric total doesn't match"
- Service auto-scales rubrics
- Check logs for scaling details
- Verify slot points values

### "JSON parsing error"
- Gemini response format changed
- Check Gemini API status
- Retry - may be transient

---

## ✅ Verification Steps

After integration:

1. [ ] Set GEMINI_API_KEY environment variable
2. [ ] Import TQS service in app.py
3. [ ] Add button and UI code
4. [ ] Test with sample slots
5. [ ] Verify questions generated
6. [ ] Check statistics display
7. [ ] Test export functionality
8. [ ] Verify rubrics are valid
9. [ ] Check point preservation
10. [ ] Deploy to production

---

## 🎉 You're Ready!

Once integrated, teachers can:
1. Create exam blueprint (TOS)
2. Assign question types intelligently
3. **Generate actual test questions automatically** ← NEW
4. Preview and edit questions
5. Export ready-to-use exam

The TQS module is production-ready and waiting to be integrated!

