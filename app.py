import streamlit as st
from services.tos_service import generate_tos
from services.export_service import export_tos_exact_format
from services.pdf_service import extract_syllabus_details
from services.tqs_export_service import tqs_export_service

from services.question_type_service import (
    QuestionType,
    validate_question_type_distribution,
    compute_total_points,
    compute_question_type_totals,
    get_default_question_types,
    format_question_types_for_display
)
from services.tqs_service import (
    generate_tqs,
    get_tqs_statistics,
    export_tqs_to_json
)
from services.tos_file_parser import (
    TOSFileParser,
    validate_tos_for_tqs_generation,
    convert_tos_to_assigned_slots,
    parse_tos_file
)
from services.tos_slot_assignment_service import assign_question_types_to_bloom_slots
from services.question_api_service import QuestionAPIService

import pandas as pd
import os
import json
import uuid
import random
import logging
from typing import Dict, Tuple, Any

logger = logging.getLogger(__name__)

# ======================================================
# AUTH HELPERS
# ======================================================
AUTH_USERNAME = "admin"
AUTH_PASSWORD = "smart123"

def init_auth_state() -> None:
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "login_error" not in st.session_state:
        st.session_state.login_error = ""

def authenticate_user(username: str, password: str) -> bool:
    return username == AUTH_USERNAME and password == AUTH_PASSWORD

def render_login_page() -> None:
    st.title("SmartLesson Login")
    st.caption("Please sign in to continue.")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if authenticate_user(username, password):
            st.session_state.is_authenticated = True
            st.session_state.login_error = ""
            st.rerun()
        else:
            st.session_state.login_error = "Invalid username or password."

    if st.session_state.login_error:
        st.error(st.session_state.login_error)

# ======================================================
# SECRETS HELPERS
# ======================================================
def get_gemini_api_key() -> str | None:
    """Safely read GEMINI_API_KEY from Streamlit secrets or environment."""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]
    except Exception:
        # Streamlit raises when secrets.toml is missing
        pass

    return os.environ.get("GEMINI_API_KEY")

# ======================================================
# INITIALIZE QUESTION API SERVICE
# ======================================================
question_api = QuestionAPIService(storage_backend='session_state')

# ======================================================
# HELPER FUNCTIONS FOR EDITABLE TQS
# ======================================================

def update_question_in_tqs(question_index: int, updated_data: Dict[str, Any]):
    """Update a question in session state by index."""
    return question_api.update_question(question_index, updated_data, st.session_state)

def delete_question_from_tqs(question_index: int):
    """Delete a question from session state by index."""
    return question_api.delete_question(question_index, st.session_state)

def regenerate_single_question(question_index: int, api_key: str):
    """Regenerate a single question using Gemini API."""
    return question_api.regenerate_question(question_index, api_key, st.session_state)

@st.cache_data(ttl=3600)  # Cache for 1 hour
def cached_extract_syllabus(pdf_bytes, exam_term="Midterm"):
    """Cache PDF extraction to avoid repeated processing. Caches per exam_term."""
    import io
    pdf_file = io.BytesIO(pdf_bytes)
    return extract_syllabus_details(pdf_file, exam_term=exam_term)

st.set_page_config(
    page_title="SmartLesson",
    layout="wide"
)

init_auth_state()

if not st.session_state.is_authenticated:
    render_login_page()
    st.stop()

if st.sidebar.button("Logout"):
    st.session_state.is_authenticated = False
    st.session_state.login_error = ""
    st.rerun()

st.title("📘 SmartLesson")
st.caption("Lesson Planning | TOS & Test Question Generator")

# ======================================================
# MAJOR TABS
# ======================================================
main_tabs = st.tabs([
    "📘 Lesson Planner",
    "📊 Assessment Generator (TOS / TQS)"
])

# ======================================================
# TAB 1: LESSON PLANNER
# ======================================================
with main_tabs[0]:
    st.subheader("Lesson Planner")

    lesson_tabs = st.tabs([
        "Lesson Details",
        "Learning Objectives",
        "Teaching Plan"
    ])

    # --- Lesson Details ---
    with lesson_tabs[0]:
        st.markdown("### Lesson Information")

        subject = st.text_input("Subject")
        topic = st.text_input("Topic")
        grade_level = st.selectbox(
            "Grade / Year Level",
            ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "College"]
        )
        duration = st.number_input(
            "Duration (minutes)",
            min_value=10,
            max_value=240,
            step=10
        )

    # --- Learning Objectives ---
    with lesson_tabs[1]:
        st.markdown("### Learning Objectives")

        if "lesson_objectives" not in st.session_state:
            st.session_state.lesson_objectives = []

        obj_text = st.text_input("Objective")
        obj_bloom = st.selectbox(
            "Bloom’s Level",
            ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
        )

        if st.button("Add Objective"):
            if obj_text:
                st.session_state.lesson_objectives.append({
                    "objective": obj_text,
                    "bloom": obj_bloom
                })

        if st.session_state.lesson_objectives:
            st.table(st.session_state.lesson_objectives)

    # --- Teaching Plan ---
    with lesson_tabs[2]:
        st.markdown("### Teaching Plan")

        strategy = st.selectbox(
            "Teaching Strategy",
            ["Lecture", "Discussion", "Group Work", "Hands-on Activity"]
        )
        assessment = st.selectbox(
            "Assessment Method",
            ["Quiz", "Recitation", "Performance Task", "Written Exam"]
        )

        st.info("📌 Lesson planning logic will be extended here.")

# ======================================================
# TAB 2: ASSESSMENT GENERATOR
# ======================================================
with main_tabs[1]:
    st.subheader("Assessment Generator")

    assess_tabs = st.tabs([
        "Course / Syllabus",
        "Learning Outcomes",
        "Assessment Profile",
        "Generate TOS",
        "Generate TQS",
        "Export"
    ])

    # --- Course / Syllabus ---
    with assess_tabs[0]:
        st.markdown("### Course / Syllabus Information")

        # Initialize session state for course details
        if "course_details" not in st.session_state:
            st.session_state.course_details = {
                "course_code": "",
                "course_title": "",
                "semester": "1st",
                "academic_year": "2025–2026",
                "instructor": "",
                "total_hours": 0,
                "exam_term": "Midterm"  # NEW: Exam term selection
            }

        # ===== EXAM TERM SELECTION (FIRST - before PDF upload) =====
        st.markdown("#### 🎯 Select Exam Term")
        exam_term = st.radio(
            "Which exam term do you want to create TOS for?",
            ["Midterm", "Final"],
            horizontal=True,
            index=["Midterm", "Final"].index(st.session_state.course_details["exam_term"]),
            key="exam_term_select_top"
        )
        st.session_state.course_details["exam_term"] = exam_term
        st.info(f"📌 Learning outcomes will be extracted for: **{exam_term}**")

        col1, col2 = st.columns(2)

        # PDF Upload Section
        st.markdown("#### 📄 Upload Syllabus (PDF)")
        syllabus_file = st.file_uploader(
            "Upload syllabus PDF to auto-populate course details",
            type=["pdf"],
            key="syllabus_uploader"
        )

        if syllabus_file is not None:
            # Read PDF bytes for caching
            pdf_bytes = syllabus_file.read()
            
            # Get the selected exam_term
            selected_exam_term = st.session_state.course_details.get("exam_term", "Midterm")
            
            # Check if exam_term has changed - if so, re-extract learning outcomes
            outcomes_need_refresh = (
                "extracted_exam_term" not in st.session_state or 
                st.session_state.extracted_exam_term != selected_exam_term
            )
            
            with st.spinner(f"📖 Extracting syllabus details for {selected_exam_term}... (Optimized)"):
                # Use cached extraction with exam_term parameter
                extracted = cached_extract_syllabus(pdf_bytes, exam_term=selected_exam_term)
                
                if "error" not in extracted:
                    # Check if already processed (don't reprocess) - BUT DO refresh if exam_term changed
                    if "pdf_processing_done" not in st.session_state or outcomes_need_refresh:
                        # Update session state with extracted data - ONLY ONCE (or when exam_term changes)
                        st.session_state.course_details["course_code"] = extracted.get("course_code", "")
                        st.session_state.course_details["course_title"] = extracted.get("course_title", "")
                        st.session_state.course_details["semester"] = extracted.get("semester", "1st") or "1st"
                        st.session_state.course_details["academic_year"] = extracted.get("academic_year", "2025–2026")
                        st.session_state.course_details["instructor"] = extracted.get("instructor", "")
                        
                        # Store learning outcomes for the next tab
                        st.session_state.extracted_learning_outcomes = extracted.get("learning_outcomes", [])
                        st.session_state.extracted_exam_term = selected_exam_term  # NEW: Track which exam_term these outcomes are for
                        st.session_state.pdf_processing_done = True
                    
                    st.success("✅ Syllabus details extracted successfully!")
                    
                    # Show extracted information
                    with st.expander("📋 Extracted Details", expanded=True):
                        st.write(f"**Course Code:** {extracted.get('course_code', 'Not found')}")
                        st.write(f"**Course Title:** {extracted.get('course_title', 'Not found')}")
                        st.write(f"**Semester:** {extracted.get('semester', 'Not found')}")
                        st.write(f"**Academic Year:** {extracted.get('academic_year', 'Not found')}")
                        st.write(f"**Instructor:** {extracted.get('instructor', 'Not found')}")
                        
                        if extracted.get("learning_outcomes"):
                            st.write("**Learning Outcomes Found:**")
                            for idx, outcome in enumerate(extracted.get("learning_outcomes", [])[:15], 1):
                                st.write(f"{idx}. {outcome}")
                            st.info(f"✅ Found {len(extracted.get('learning_outcomes', []))} learning outcomes. Go to the **Learning Outcomes** tab to import them!")
                        else:
                            st.warning("⚠️ No learning outcomes found in Section IV. Make sure your PDF has a 'Learning Outcomes' section in 'Section IV'.")
                else:
                    st.error(f"❌ Error extracting PDF: {extracted.get('error', 'Unknown error')}")

        # Manual Course Details Input
        st.markdown("#### ✏️ Course Details (Manual Entry / Edit)")

        with col1:
            course_code = st.text_input(
                "Course Code",
                value=st.session_state.course_details["course_code"],
                key="course_code_input"
            )
            st.session_state.course_details["course_code"] = course_code

            course_title = st.text_input(
                "Course Title",
                value=st.session_state.course_details["course_title"],
                key="course_title_input"
            )
            st.session_state.course_details["course_title"] = course_title

            semester = st.selectbox(
                "Semester",
                ["1st", "2nd", "Summer"],
                index=["1st", "2nd", "Summer"].index(st.session_state.course_details["semester"]),
                key="semester_select"
            )
            st.session_state.course_details["semester"] = semester

        with col2:
            academic_year = st.text_input(
                "Academic Year",
                value=st.session_state.course_details["academic_year"],
                key="academic_year_input"
            )
            st.session_state.course_details["academic_year"] = academic_year

            instructor = st.text_input(
                "Instructor (optional)",
                value=st.session_state.course_details["instructor"],
                key="instructor_input"
            )
            st.session_state.course_details["instructor"] = instructor

            total_hours = st.number_input(
                "Total Course Hours",
                min_value=1,
                value=int(st.session_state.course_details["total_hours"]) if st.session_state.course_details["total_hours"] else 1,
                key="total_hours_input"
            )
            st.session_state.course_details["total_hours"] = total_hours

        st.info("ℹ️ This information appears in the TOS header.")

    # TAB 2: LEARNING OUTCOMES
    # -----------------------------
with assess_tabs[1]:
    st.markdown("### Learning Outcomes")

    # Initialize assessment outcomes
    if "assessment_outcomes" not in st.session_state:
        st.session_state.assessment_outcomes = []

    # ---------------------------------
    # NEW: SHOW THE EXAM TERM BEING USED
    # ---------------------------------
    current_exam_term = st.session_state.course_details.get("exam_term", "Midterm")
    extracted_exam_term = st.session_state.get("extracted_exam_term", None)
    
    if extracted_exam_term:
        if extracted_exam_term == current_exam_term:
            st.success(f"✅ Using learning outcomes from: **{current_exam_term}**")
        else:
            st.warning(
                f"⚠️ **Mismatch!** Learning outcomes are from **{extracted_exam_term}**, "
                f"but you selected **{current_exam_term}**. "
                f"Go back to Course/Syllabus tab, change back to {extracted_exam_term}, "
                f"and upload the PDF again to extract correct outcomes."
            )
    
    # ---------------------------------
    # AUTO-IMPORT FROM PDF (if available)
    # ---------------------------------
    st.markdown("#### 📥 Import Learning Outcomes")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if "extracted_learning_outcomes" in st.session_state and st.session_state.extracted_learning_outcomes:
            if st.button("📄 Use PDF Learning Outcomes", key="btn_pdf_outcomes"):
                st.session_state.assessment_outcomes = []
                for outcome_text in st.session_state.extracted_learning_outcomes:
                    st.session_state.assessment_outcomes.append({
                        "id": uuid.uuid4().hex,
                        "outcome": outcome_text,
                        "hours": 0  # teacher assigns hours
                    })
    
    with col2:
        if "lesson_objectives" in st.session_state and st.session_state.lesson_objectives:
            if st.button("📥 Use Lesson Objectives", key="btn_lesson_obj"):
                st.session_state.assessment_outcomes = []
                for obj in st.session_state.lesson_objectives:
                    st.session_state.assessment_outcomes.append({
                        "id": uuid.uuid4().hex,
                        "outcome": obj["objective"],
                        "hours": 0
                    })

    # Show status
    if st.session_state.assessment_outcomes:
        st.success(f"✅ {len(st.session_state.assessment_outcomes)} outcomes loaded")

    # ---------------------------------
    # MANUAL ADD OUTCOME
    # ---------------------------------
    st.markdown("#### ➕ Add Custom Learning Outcome")
    
    # Initialize session state for inputs BEFORE creating widgets
    if "lo_text_input" not in st.session_state:
        st.session_state.lo_text_input = ""
    if "lo_hours_input" not in st.session_state:
        st.session_state.lo_hours_input = 0
    
    # Callback to handle adding outcome and clearing inputs
    def add_outcome_callback():
        lo_text = st.session_state.lo_text_input
        lo_hours = st.session_state.lo_hours_input
        
        if lo_text and lo_text.strip():
            st.session_state.assessment_outcomes.append({
                "id": uuid.uuid4().hex,
                "outcome": lo_text.strip(),
                "hours": lo_hours
            })
            # Clear inputs BEFORE rerun (in callback)
            st.session_state.lo_text_input = ""
            st.session_state.lo_hours_input = 0
    
    col1, col2 = st.columns([4, 2])
    
    with col1:
        lo_text = st.text_input(
            "Learning Outcome",
            key="lo_text_input",
            value=st.session_state.lo_text_input
        )
    
    with col2:
        lo_hours = st.number_input(
            "Hours",
            min_value=0,
            value=st.session_state.lo_hours_input,
            key="lo_hours_input"
        )

    # Button with callback - this clears session state BEFORE widget re-registration
    st.button(
        "➕ Add Outcome",
        key="btn_add_outcome",
        on_click=add_outcome_callback
    )

    # ---------------------------------
    # DISPLAY + EDIT + DELETE
    # ---------------------------------
    if st.session_state.assessment_outcomes:
        st.markdown("#### 📋 Learning Outcomes & Hours Management")
        st.markdown("**Adjust the hours taught for each learning outcome:**")

        edited = False

        for outcome in st.session_state.assessment_outcomes:
            outcome_id = outcome.get('id', uuid.uuid4().hex)  # Add UUID if missing (legacy data)
            if 'id' not in outcome:
                outcome['id'] = outcome_id  # Store it for future use
            
            col1, col2, col3 = st.columns([5, 2, 1])

            with col1:
                st.write(f"**{st.session_state.assessment_outcomes.index(outcome) + 1}.** {outcome['outcome']}")

            with col2:
                new_hours = st.number_input(
                    "Hours",
                    min_value=0,
                    value=outcome["hours"],
                    key=f"hrs_{outcome_id}",
                    label_visibility="collapsed"
                )
                if new_hours != outcome["hours"]:
                    outcome["hours"] = new_hours
                    edited = True

            with col3:
                if st.button("❌", key=f"del_{outcome_id}", help="Delete this outcome"):
                    st.session_state.assessment_outcomes = [
                        o for o in st.session_state.assessment_outcomes 
                        if o.get('id', '') != outcome_id
                    ]

        # Show summary
        st.markdown("#### 📊 Hours Summary")
        total_assigned_hours = sum(o["hours"] for o in st.session_state.assessment_outcomes)
        total_course_hours = st.session_state.course_details.get("total_hours", 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Hours Assigned", total_assigned_hours)
        with col2:
            st.metric("Total Course Hours", total_course_hours)
        with col3:
            if total_course_hours > 0:
                percentage = (total_assigned_hours / total_course_hours) * 100
                st.metric("Coverage", f"{percentage:.1f}%")

        if total_assigned_hours > total_course_hours and total_course_hours > 0:
            st.warning(f"⚠️ Total hours assigned ({total_assigned_hours}) exceeds course hours ({total_course_hours})")
    else:
        st.info("No learning outcomes added yet. Import from PDF, lesson objectives, or add manually.")

    # --- Assessment Profile ---
# -----------------------------
# TAB 3: ASSESSMENT PROFILE
# -----------------------------
with assess_tabs[2]:
    st.markdown("### Bloom’s Taxonomy Profile")

    profile = st.radio(
        "Program Type",
        ["Board Course", "Non-Board Course (IT/CS)", "Custom"]
    )

    # -----------------------------
    # DEFAULT PROFILES
    # -----------------------------
    if profile == "Board Course":
        defaults = {
            "Remember": 30,
            "Understand": 30,
            "Apply": 20,
            "Analyze": 10,
            "Evaluate": 5,
            "Create": 5
        }
    elif profile == "Non-Board Course (IT/CS)":
        defaults = {
            "Remember": 10,
            "Understand": 15,
            "Apply": 30,
            "Analyze": 30,
            "Evaluate": 10,
            "Create": 5
        }
    else:  # Custom
        defaults = {
            "Remember": 0,
            "Understand": 0,
            "Apply": 0,
            "Analyze": 0,
            "Evaluate": 0,
            "Create": 0
        }

    st.markdown("#### Adjust Bloom’s Taxonomy Distribution (%)")

    bloom_weights = {}
    total_percent = 0

    for bloom, value in defaults.items():
        bloom_weights[bloom] = st.slider(
            bloom,
            min_value=0,
            max_value=100,
            value=value,
            step=5
        )
        total_percent += bloom_weights[bloom]

    # -----------------------------
    # VALIDATION
    # -----------------------------
    st.write(f"**Total Percentage:** {total_percent}%")

    if total_percent != 100:
        st.error("Bloom’s distribution must total 100%.")
    else:
        st.success("Bloom’s distribution is valid.")

    # -----------------------------
    # SAVE TO SESSION STATE
    # -----------------------------
    st.session_state.bloom_weights = bloom_weights


    # --- Generate TOS ---
with assess_tabs[3]:
    st.markdown("### Generate Table of Specifications")
    
    # Display which exam term we're creating TOS for
    exam_term = st.session_state.course_details.get("exam_term", "Midterm")
    st.info(f"📋 Creating TOS for: **{exam_term} Exam**")

    # ============================================================
    # SECTION 1: TOTAL TEST ITEMS
    # ============================================================
    st.markdown("#### 📝 Step 1: Define Total Test Items")
    
    total_items = st.number_input(
        "Total Number of Test Items",
        min_value=1,
        step=1,
        key="total_items_input"
    )
    
    # ============================================================
    # SECTION 2: QUESTION TYPE DISTRIBUTION
    # ============================================================
    st.markdown("#### 📊 Step 2: Question Type Distribution")
    st.markdown(
        "Define the distribution of question types and their point values. "
        "The sum of items must equal the total test items above."
    )
    
    # Initialize question types in session state if not present
    if "question_types" not in st.session_state:
        st.session_state.question_types = get_default_question_types()
    
    # Question Type Input UI
    st.markdown("**Question Types Configuration:**")
    
    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
    with col1:
        st.write("**Question Type**")
    with col2:
        st.write("**No. of Items**")
    with col3:
        st.write("**Points/Item**")
    with col4:
        st.write("**Action**")
    
    # Editor rows for question types
    updated_types = []
    for idx, qt in enumerate(st.session_state.question_types):
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        
        with col1:
            type_name = st.text_input(
                "Type",
                value=qt.type,
                key=f"qt_name_{qt.id}",
                label_visibility="collapsed"
            )
        
        with col2:
            num_items = st.number_input(
                "Items",
                value=qt.items,
                min_value=0,
                step=1,
                key=f"qt_items_{qt.id}",
                label_visibility="collapsed"
            )
        
        with col3:
            points_per = st.number_input(
                "Points",
                value=float(qt.points_per_item),
                min_value=0.0,
                step=0.5,
                key=f"qt_points_{qt.id}",
                label_visibility="collapsed"
            )
        
        with col4:
            if st.button("❌", key=f"del_qt_{qt.id}", help="Remove this question type"):
                # Filter out the deleted type by ID
                st.session_state.question_types = [
                    q for q in st.session_state.question_types if q.id != qt.id
                ]
                st.rerun()
            else:
                updated_types.append(
                    QuestionType(type_name, int(num_items), float(points_per), id=qt.id)
                )
    
    # Update session state with edited types
    if updated_types:
        st.session_state.question_types = updated_types
    
    # Add new question type button
    if st.button("➕ Add Question Type"):
        st.session_state.question_types.append(
            QuestionType("New Type", 0, 1)
        )
        st.rerun()
    
    # ========================================================================
    # SINGLE SOURCE OF TRUTH FOR TOTALS
    # ========================================================================
    # Compute total items and total points using a SINGLE function call.
    # This ensures perfect synchronization across all UI panels.
    # 
    # Why? Previously, totals were computed in multiple places:
    # - In summary table
    # - In validation metrics
    # - In export logic
    # 
    # This caused inconsistencies when items/points changed.
    # Now, compute_question_type_totals() is the ONLY place where totals
    # are calculated, and all UI panels use these values.
    # ========================================================================
    total_qt_items, total_qt_points = compute_question_type_totals(
        st.session_state.question_types
    )
    
    # Display summary table
    # NOTE: The summary includes a TOTAL row computed by format_question_types_for_display()
    # This TOTAL row must match the values from compute_question_type_totals() above.
    st.markdown("**Summary:**")
    summary_data = format_question_types_for_display(st.session_state.question_types)
    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
    
    # Validation and metrics
    # NOTE: All metrics use the totals computed above (total_qt_items, total_qt_points)
    # This ensures the top panel and bottom summary always show the same values.
    st.markdown("#### ✅ Validation & Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Items (Expected)", total_items)
    with col2:
        # This value comes from compute_question_type_totals() - SINGLE SOURCE OF TRUTH
        st.metric("Total Items (Configured)", total_qt_items)
    with col3:
        # This value comes from compute_question_type_totals() - SINGLE SOURCE OF TRUTH
        st.metric("Total Points (Computed)", f"{total_qt_points:.1f}")
    with col4:
        # Validation: configured items must equal expected items
        items_match = total_qt_items == total_items
        status = "✅ Match" if items_match else "❌ Mismatch"
        st.metric("Items Validation", status)
    
    # Validation errors
    is_valid, validation_errors = validate_question_type_distribution(
        st.session_state.question_types,
        total_items
    )
    
    if validation_errors:
        for error in validation_errors:
            st.error(f"❌ {error}")
    
    if is_valid and st.session_state.question_types:
        st.success("✅ Question type distribution is valid!")
    
    # ============================================================
    # SECTION 3: GENERATE TOS
    # ============================================================
    st.markdown("#### ⚙️️ Step 3: Generate TOS")

    
    generate = st.button("⚙ Generate TOS", disabled=not is_valid)

    if generate:
        # -------------------------------
        # VALIDATION
        # -------------------------------
        if "assessment_outcomes" not in st.session_state or not st.session_state.assessment_outcomes:
            st.error("Please define learning outcomes first.")
            st.stop()

        if total_items <= 0:
            st.error("Total test items must be greater than zero.")
            st.stop()

        # -------------------------------
        # PREPARE INPUTS FOR SERVICE
        # -------------------------------
        outcomes = []
        for idx, o in enumerate(st.session_state.assessment_outcomes):
            outcomes.append({
                "id": idx,
                "text": o["outcome"],
                "hours": o["hours"]
            })

        bloom_weights = st.session_state.get("bloom_weights")

        if not bloom_weights:
            st.error("Please configure Bloom’s Taxonomy profile.")
            st.stop()

        # -------------------------------
        # CALL TOS SERVICE
        # Bloom distribution logic NOT MODIFIED - still works as before
        # -------------------------------
        result = generate_tos(
            outcomes=outcomes,
            bloom_weights=bloom_weights,
            total_items=total_items
        )
        
        # Store extended TOS with question type distribution
        # NOTE: total_points is computed from compute_question_type_totals()
        # This uses the SINGLE SOURCE OF TRUTH, not a separate calculation
        st.session_state.generated_tos = {
            "outcomes": outcomes,
            "tos_matrix": result["tos_matrix"],
            "bloom_totals": result["bloom_totals"],
            # Question type distribution
            "question_types": st.session_state.question_types,
            "total_items": total_items,
            # Computed total points - derived from compute_question_type_totals()
            "total_points": total_qt_points
        }

        # Perform soft-mapping to assign question types to Bloom slots
        assigned_slots, _ = assign_question_types_to_bloom_slots(
            tos_matrix=result["tos_matrix"],
            outcomes=outcomes,
            question_types_list=st.session_state.question_types,
            shuffle=True
        )
        st.session_state.assigned_slots = assigned_slots

        # -------------------------------
        # DISPLAY RESULT
        # -------------------------------
        st.success("TOS generated successfully.")

        tos_matrix = result["tos_matrix"]

        # Convert to table
        table_data = []
        for o in outcomes:
            row = {"Learning Outcome": o["text"]}
            for bloom in tos_matrix:
                row[bloom] = tos_matrix[bloom].get(o["id"], 0)
            table_data.append(row)

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

        # Show Bloom totals
        st.markdown("### Bloom’s Level Totals")
        st.json(result["bloom_totals"])

    # Quick export after TOS generation
    if "generated_tos" in st.session_state:
        st.markdown("#### 📥 Export TOS")
        if st.button("⬇ Export TOS as Excel", key="btn_export_tos_generate_tab"):

            exam_term = st.session_state.course_details.get("exam_term", "Midterm")
            course_code = st.session_state.course_details.get("course_code", "")
            course_title = st.session_state.course_details.get("course_title", "")
            semester = st.session_state.course_details.get("semester", "")
            instructor = st.session_state.course_details.get("instructor", "")
            academic_year = st.session_state.course_details.get("academic_year", "")

            total_points = st.session_state.generated_tos.get("total_points", 0)

            excel = export_tos_exact_format(
                meta={
                    "name": instructor,
                    "subject_code": course_code,
                    "title": course_title,
                    "semester": semester,
                    "exam_term": exam_term,
                    "academic_year": academic_year,
                    "schedule": "",
                    "course": "",
                    "exam_date": "",
                    "course_content": ""
                },
                outcomes=st.session_state.generated_tos["outcomes"],
                tos_matrix=st.session_state.generated_tos["tos_matrix"],
                total_items=st.session_state.generated_tos.get("total_items", 0),
                total_points=int(total_points)
            )

            file_name = f"TOS_{course_code}_{exam_term}.xlsx"
            st.download_button(
                label="📥 Download TOS Excel",
                data=excel,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# --- Generate TQS ---
with assess_tabs[4]:
        st.markdown("### Generate Test Questions (TQS)")

        st.write("Generate actual test questions from your exam blueprint using AI.")
        st.write("Each question is tailored to the learning outcome and Bloom's level.")
        
        # ======================================================
        # HELPER FUNCTIONS FOR EDITABLE TOS
        # ======================================================
        
        def delete_outcome_from_tos(tos_data: Dict, outcome_id) -> Dict:
            """Remove an outcome from TOS and update the matrix."""
            if not tos_data:
                return tos_data
                
            # Remove from learning_outcomes
            tos_data["learning_outcomes"] = [
                o for o in tos_data.get("learning_outcomes", [])
                if o.get("id") != outcome_id
            ]
            
            # Remove from tos_matrix for each Bloom level
            tos_matrix = tos_data.get("tos_matrix", {})
            outcome_key = str(outcome_id)  # Handle both int and string keys
            
            for bloom_level in tos_matrix:
                if outcome_key in tos_matrix[bloom_level]:
                    del tos_matrix[bloom_level][outcome_key]
                # Also try numeric version
                if outcome_id in tos_matrix[bloom_level]:
                    del tos_matrix[bloom_level][outcome_id]
            
            # Recalculate total_items
            total = 0
            for bloom_level in tos_matrix:
                for item_count in tos_matrix[bloom_level].values():
                    total += item_count
            tos_data["total_items"] = total
            
            return tos_data
        
        def calculate_mixed_distribution_slots(
            tos_data: Dict,
            distribution: Dict[str, Dict[str, float]]
        ) -> Tuple[bool, Any]:
            """
            Convert mixed type distribution to assigned slots.
            
            distribution: {
                'MCQ': {'items': 30, 'points_per_item': 1.0},
                'Essay': {'items': 10, 'points_per_item': 5.0},
                ...
            }
            """
            try:
                total_slots_needed = tos_data.get("total_items", 0)
                total_slots_in_dist = sum(d.get("items", 0) for d in distribution.values())
                
                if total_slots_in_dist != total_slots_needed:
                    return False, f"Distribution items ({total_slots_in_dist}) must equal TOS total ({total_slots_needed})"
                
                outcomes = tos_data.get("learning_outcomes", [])
                if not outcomes:
                    # Support in-app generated TOS structure
                    outcomes = tos_data.get("outcomes", [])
                tos_matrix = tos_data.get("tos_matrix", {})
                
                # Create a list of all type slots based on distribution
                type_slots = []
                for q_type, config in distribution.items():
                    for _ in range(int(config.get("items", 0))):
                        type_slots.append({
                            "type": q_type,
                            "points": float(config.get("points_per_item", 1.0))
                        })
                
                # Shuffle type slots for randomness
                random.shuffle(type_slots)
                
                # Create assigned slots
                assigned_slots = []
                slot_index = 0
                
                for bloom in ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]:
                    bloom_row = tos_matrix.get(bloom, {})
                    for outcome in outcomes:
                        outcome_id = outcome.get("id", outcome.get("_id"))
                        outcome_text = outcome.get("text", outcome.get("description"))
                        
                        # Get count (handle both string and int keys)
                        count = bloom_row.get(outcome_id, bloom_row.get(str(outcome_id), 0))
                        
                        for _ in range(count):
                            if slot_index < len(type_slots):
                                slot = {
                                    "outcome_id": outcome_id,
                                    "outcome_text": outcome_text,
                                    "bloom_level": bloom,
                                    "question_type": type_slots[slot_index]["type"],
                                    "points": type_slots[slot_index]["points"]
                                }
                                assigned_slots.append(slot)
                                slot_index += 1
                
                return True, assigned_slots
                
            except Exception as e:
                logger.error(f"Error in mixed distribution: {str(e)}")
                return False, f"Distribution error: {str(e)}"

        # ======================================================
        # STEP 1: SELECT TOS SOURCE
        # ======================================================
        st.markdown("#### 📋 Step 1: Select TOS Source")
        
        # Initialize session state for editable TOS
        if "tqs_tos_source" not in st.session_state:
            st.session_state.tqs_tos_source = "generated"
        if "uploaded_tos_data" not in st.session_state:
            st.session_state.uploaded_tos_data = None
        if "edited_tos_data" not in st.session_state:
            st.session_state.edited_tos_data = None
        if "tqs_test_type_config" not in st.session_state:
            st.session_state.tqs_test_type_config = None
        
        tos_source = st.radio(
            "Choose TOS source:",
            ["Use Generated TOS (from system)", "Upload TOS from File"],
            key="tos_source_radio"
        )
        st.session_state.tqs_tos_source = tos_source
        
        # ======================================================
        # SECTION: FILE UPLOAD (if selected)
        # ======================================================
        if tos_source == "Upload TOS from File":
            st.markdown("#### 📤 Upload TOS File")
            st.write("Supported formats: JSON, XLSX, DOCX, PDF (experimental)")
            st.info("ℹ️ After upload, you can edit learning outcomes and configure test types")
            
            uploaded_file = st.file_uploader(
                "Choose TOS file",
                type=["json", "xlsx", "docx", "pdf"],
                key="tos_file_uploader"
            )
            
            if uploaded_file is not None:
                file_content = uploaded_file.read()
                file_name = uploaded_file.name
                
                # Parse TOS file
                success, tos_result = parse_tos_file(
                    file_content,
                    file_name
                )
                
                if success:
                    # Validate TOS
                    is_valid, validation_msg = validate_tos_for_tqs_generation(tos_result)
                    
                    if is_valid:
                        st.success(f"✅ {validation_msg}")
                        
                        # Store as edited data (working copy)
                        if st.session_state.edited_tos_data is None:
                            st.session_state.edited_tos_data = tos_result.copy()
                        st.session_state.uploaded_tos_data = tos_result.copy()
                        
                        # Show TOS summary
                        with st.expander("📊 TOS Details", expanded=False):
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Learning Outcomes", len(tos_result.get("learning_outcomes", [])))
                            with col2:
                                st.metric("Total Items", tos_result.get("total_items", 0))
                            with col3:
                                st.metric("File", tos_result.get("metadata", {}).get("file_name", "unknown"))
                            with col4:
                                st.metric("Format", tos_result.get("metadata", {}).get("parsing_method", "unknown"))
                            
                            # Show outcomes
                            st.write("**Learning Outcomes:**")
                            for outcome in tos_result.get("learning_outcomes", []):
                                st.write(f"- {outcome.get('text', outcome.get('description'))} (ID: {outcome.get('id')})")
                    else:
                        st.error(f"❌ TOS validation failed: {validation_msg}")
                        st.session_state.uploaded_tos_data = None
                        st.session_state.edited_tos_data = None
                
                else:
                    error_msg = tos_result.get("error", "Unknown error") if isinstance(tos_result, dict) else tos_result
                    st.error(f"❌ Failed to parse TOS file: {error_msg}")
                    st.session_state.uploaded_tos_data = None
                    st.session_state.edited_tos_data = None
        
        # ======================================================
        # CHECK: Do we have a valid TOS (generated or uploaded)?
        # ======================================================
        has_generated_tos = (
            "generated_tos" in st.session_state and 
            st.session_state.generated_tos is not None
        )
        has_uploaded_tos = st.session_state.edited_tos_data is not None
        
        if not has_generated_tos and not has_uploaded_tos:
            if tos_source == "Upload TOS from File":
                st.warning("⚠️ Please upload a TOS file to continue.")
            else:
                st.warning("⚠️ Please generate a TOS in the 'Generate TOS' tab first.")
            st.stop()
        
        # ======================================================
        # STEP 2: EDIT LEARNING OUTCOMES (only for uploaded TOS)
        # ======================================================
        if tos_source == "Upload TOS from File" and has_uploaded_tos:
            st.markdown("#### ✏️ Step 2: Edit Learning Outcomes")
            st.write("Review and edit your learning outcomes. Deleting an outcome will update the assessment matrix.")
            
            working_tos = st.session_state.edited_tos_data
            outcomes = working_tos.get("learning_outcomes", [])
            
            if outcomes:
                # Create editable outcomes table
                col1, col2, col3 = st.columns([3, 1, 0.5])
                with col1:
                    st.write("**Outcome Text**")
                with col2:
                    st.write("**Hours**")
                with col3:
                    st.write("**Delete**")
                
                st.divider()
                
                # Display outcomes with delete buttons
                outcomes_to_delete = []
                for idx, outcome in enumerate(outcomes):
                    outcome_id = outcome.get("id")
                    outcome_text = outcome.get("text", outcome.get("description", ""))
                    outcome_hours = outcome.get("hours", 0)
                    
                    col1, col2, col3 = st.columns([3, 1, 0.5])
                    
                    with col1:
                        st.text(outcome_text[:80])
                    with col2:
                        st.text(str(outcome_hours))
                    with col3:
                        if st.button("❌", key=f"del_outcome_{outcome_id}_{idx}", help="Delete this outcome"):
                            outcomes_to_delete.append(outcome_id)
                
                # Handle deletions
                if outcomes_to_delete:
                    for outcome_id in outcomes_to_delete:
                        st.session_state.edited_tos_data = delete_outcome_from_tos(
                            st.session_state.edited_tos_data,
                            outcome_id
                        )
                    st.success(f"✅ Deleted {len(outcomes_to_delete)} outcome(s). Matrix updated.")
                    st.rerun()
                
                # Show summary after edits
                st.markdown(f"**Total Learning Outcomes:** {len(st.session_state.edited_tos_data.get('learning_outcomes', []))}")
                st.markdown(f"**Total Items:** {st.session_state.edited_tos_data.get('total_items', 0)}")
            
            st.divider()
        
        # ======================================================
        # STEP 3: SELECT TEST TYPE CONFIGURATION
        # ======================================================
        st.markdown("#### 🎯 Step 3: Select Test Type Configuration")
        
        working_tos = st.session_state.edited_tos_data if has_uploaded_tos else st.session_state.generated_tos
        test_type_mode = st.radio(
            "Test Configuration:",
            ["Single Question Type", "Mixed Question Types"],
            key="test_type_mode_radio",
            horizontal=True
        )
        
        # ======================================================
        # SINGLE TYPE CONFIGURATION
        # ======================================================
        if test_type_mode == "Single Question Type":
            col1, col2 = st.columns(2)
            
            with col1:
                single_type = st.selectbox(
                    "Question Type:",
                    ["MCQ", "True or False", "Essay", "Short Answer", "Problem Solving"],
                    key="single_question_type"
                )
            
            with col2:
                points_per_item = st.number_input(
                    "Points per Item:",
                    min_value=0.5,
                    value=1.0,
                    step=0.5,
                    key="single_points_per_item"
                )
            
            # Store configuration
            st.session_state.tqs_test_type_config = {
                "mode": "single",
                "type": single_type,
                "points_per_item": points_per_item
            }
        
        # ======================================================
        # MIXED TYPE CONFIGURATION
        # ======================================================
        elif test_type_mode == "Mixed Question Types":
            st.write("Configure distribution of question types:")
            
            total_items = working_tos.get("total_items", 0)
            
            mixed_config = {}
            question_types = ["MCQ", "True or False", "Essay", "Short Answer", "Problem Solving"]
            
            col1, col2, col3 = st.columns(3)
            col_list = [col1, col2, col3, col1, col2]
            
            for idx, q_type in enumerate(question_types):
                with col_list[idx]:
                    st.write(f"**{q_type}**")
                    items = st.number_input(
                        f"Items ({q_type})",
                        min_value=0,
                        max_value=total_items,
                        value=0,
                        step=1,
                        key=f"mixed_items_{q_type}"
                    )
                    points = st.number_input(
                        f"Points per item ({q_type})",
                        min_value=0.5,
                        value=1.0,
                        step=0.5,
                        key=f"mixed_points_{q_type}"
                    )
                    
                    if items > 0:
                        mixed_config[q_type] = {
                            "items": items,
                            "points_per_item": points
                        }
            
            # Validate distribution
            total_in_dist = sum(config.get("items", 0) for config in mixed_config.values())
            
            if total_in_dist == 0:
                st.warning(f"⚠️ Assign at least some items to question types")
            elif total_in_dist != total_items:
                st.error(f"❌ Distribution total ({total_in_dist}) must equal TOS total ({total_items})")
            else:
                st.success(f"✅ Distribution valid: {total_in_dist} items across {len(mixed_config)} types")
            
            # Store configuration
            st.session_state.tqs_test_type_config = {
                "mode": "mixed",
                "distribution": mixed_config,
                "total_items": total_items
            }
        
        st.divider()
        
        # ======================================================
        # STEP 4: GENERATE TQS
        # ======================================================
        st.markdown("#### 🚀 Step 4: Generate Test Questions")
        
        # Prepare configuration summary
        config = st.session_state.tqs_test_type_config
        if config:
            if config.get("mode") == "single":
                st.info(f"📌 Configuration: {config['type']} ({config['points_per_item']} pts each)")
            else:
                total_pts = sum(
                    c.get("items", 0) * c.get("points_per_item", 1.0)
                    for c in config.get("distribution", {}).values()
                )
                st.info(f"📌 Mixed Configuration: {len(config.get('distribution', {}))} types, {config.get('total_items', 0)} items, {total_pts:.0f} pts total")
        
        if st.button("🚀 Generate Test Questions", key="btn_generate_tqs_enhanced"):
            # Validate configuration
            if not config:
                st.error("❌ Please configure test type settings first.")
                st.stop()
            
            # Get TOS to use
            if has_uploaded_tos:
                tos_to_use = st.session_state.edited_tos_data
                source_label = "Uploaded TOS"
            else:
                tos_to_use = st.session_state.generated_tos
                source_label = "Generated TOS"
            
            if not tos_to_use:
                st.error("❌ No TOS available. Please select or upload a TOS first.")
                st.stop()
            
            # Check API key (Streamlit secrets or environment variable)
            api_key = get_gemini_api_key()
            
            if not api_key:
                st.error("❌ GEMINI_API_KEY is not configured. Please add it to Streamlit secrets or environment variables.")
                st.info("💡 For Streamlit Cloud: Go to App Settings → Secrets and add: GEMINI_API_KEY = \"your-key-here\"")
                st.stop()
            
            try:
                with st.spinner("⏳ Generating test questions (this may take 1-2 minutes)..."):
                    # Convert TOS to assigned slots based on configuration
                    if config.get("mode") == "single":
                        success, assigned_slots = convert_tos_to_assigned_slots(
                            tos_to_use,
                            question_type=config["type"],
                            points_per_item=config["points_per_item"]
                        )
                    else:  # mixed mode
                        success, assigned_slots = calculate_mixed_distribution_slots(
                            tos_to_use,
                            config.get("distribution", {})
                        )
                    
                    if not success:
                        st.error(f"❌ {assigned_slots}")
                        st.stop()
                    
                    # Generate TQS
                    tqs = generate_tqs(
                        assigned_slots=assigned_slots,
                        api_key=api_key,
                        shuffle=True
                    )
                
                if tqs:
                    st.session_state.generated_tqs = tqs
                    stats = get_tqs_statistics(tqs)
                    st.session_state.tqs_stats = stats
                    
                    st.success(f"✅ Generated {len(tqs)} test questions from {source_label}")
                else:
                    st.error("❌ Failed to generate questions. Please try again.")
            
            except Exception as e:
                error_str = str(e)
                
                # Check for quota/rate limit errors
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str or "quota" in error_str.lower():
                    st.error("❌ **API Quota Limit Reached**")
                    st.warning("""
                    **The Gemini API free tier limit has been exceeded.**
                    
                    **Solutions:**
                    - ⏰ Wait for your daily quota to reset (midnight Pacific Time)
                    - 🔄 Try again in a few minutes if it's a rate limit
                    - 💳 Upgrade to a paid plan at [Google AI Studio](https://aistudio.google.com/)
                    - 🔑 Use a different API key with available quota
                    
                    **Note:** The app uses `gemini-2.0-flash` model.
                    """)
                else:
                    st.error(f"❌ Error generating questions: {error_str}")
                
                # Show full traceback in expander for debugging
                with st.expander("🔍 View Technical Details"):
                    import traceback
                    st.code(traceback.format_exc(), language="python")
        
        st.divider()
        
        # ======================================================
        # TQS STATISTICS & PREVIEW
        # ======================================================
        if "generated_tqs" in st.session_state and st.session_state.generated_tqs:
            st.markdown("#### 📊 Test Question Summary")
            
            tqs = st.session_state.generated_tqs
            stats = st.session_state.tqs_stats
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Questions", stats["total_questions"])
            with col2:
                st.metric("Total Points", f"{stats['total_points']:.0f}")
            with col3:
                st.metric("Question Types", len(stats["questions_by_type"]))
            with col4:
                st.metric("Bloom Levels", len(stats["questions_by_bloom"]))
            
            # Breakdown by type
            st.markdown("##### By Question Type")
            type_data = []
            for qtype in sorted(stats["questions_by_type"].keys()):
                type_data.append({
                    "Type": qtype,
                    "Count": stats["questions_by_type"][qtype],
                    "Points": stats["points_by_type"].get(qtype, 0)
                })
            df_types = pd.DataFrame(type_data)
            st.dataframe(df_types, use_container_width=True, hide_index=True)
            
            # Breakdown by Bloom
            st.markdown("##### By Bloom Level")
            bloom_data = []
            for bloom in sorted(stats["questions_by_bloom"].keys()):
                bloom_data.append({
                    "Bloom Level": bloom,
                    "Count": stats["questions_by_bloom"][bloom],
                    "Points": stats["points_by_bloom"].get(bloom, 0)
                })
            df_bloom = pd.DataFrame(bloom_data)
            st.dataframe(df_bloom, use_container_width=True, hide_index=True)
            
            # Preview/Edit questions
            st.markdown("##### ✏️ Edit Questions")
            st.caption("Click on any question to edit its content, regenerate, or delete it.")
            
            num_preview = min(3, len(tqs))
            
            # Check if we have only 1 question (avoid slider min_value == max_value error)
            total_questions = len(tqs)
            if total_questions <= 1:
                # Don't show slider for single question
                preview_choice = total_questions
                st.info("Displaying the 1 generated question.")
            else:
                preview_choice = st.slider(
                    "Number of questions to display",
                    min_value=1,
                    max_value=total_questions,
                    value=min(5, total_questions),
                    step=1,
                    key="preview_slider"
                )
            
            # Editable question cards
            for i, q in enumerate(tqs[:preview_choice]):
                question_idx = i  # Store index for callbacks
                
                with st.expander(
                    f"Q{q['question_number']}: {q.get('type', q.get('question_type', 'MCQ'))} ({q['points']} pts) - {q.get('outcome_text', q.get('learning_outcome', 'N/A'))[:40]}...",
                    expanded=(i == 0)
                ):
                    # Create a form for each question
                    with st.form(key=f"question_form_{q['question_number']}"):
                        st.markdown(f"**Question #{q['question_number']}**")
                        
                        # Outcome (read-only)
                        st.text_input(
                            "Learning Outcome",
                            value=q.get('outcome_text', q.get('learning_outcome', 'N/A')),
                            disabled=True,
                            key=f"outcome_{q['question_number']}"
                        )
                        
                        # Editable fields in columns
                        col1, col2 = st.columns(2)
                        with col1:
                            bloom_options = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
                            current_bloom = q.get('bloom', q.get('bloom_level', 'Remember'))
                            if current_bloom not in bloom_options:
                                bloom_options.append(current_bloom)
                            
                            new_bloom = st.selectbox(
                                "Bloom Level",
                                options=bloom_options,
                                index=bloom_options.index(current_bloom) if current_bloom in bloom_options else 0,
                                key=f"bloom_{q['question_number']}"
                            )
                        
                        with col2:
                            new_points = st.number_input(
                                "Points",
                                min_value=0.5,
                                max_value=100.0,
                                value=float(q.get('points', 1)),
                                step=0.5,
                                key=f"points_{q['question_number']}"
                            )
                        
                        # Question text (editable)
                        new_question_text = st.text_area(
                            "Question Text",
                            value=q.get('question_text', ''),
                            height=100,
                            key=f"qtext_{q['question_number']}"
                        )
                        
                        # Type-specific fields
                        if q.get('type', q.get('question_type')) == 'MCQ':
                            st.markdown("**Choices:**")
                            choices = q.get('choices', ['', '', '', ''])
                            new_choices = []
                            
                            for j in range(4):
                                choice_val = choices[j] if j < len(choices) else ''
                                new_choice = st.text_input(
                                    f"Choice {chr(65+j)}",
                                    value=choice_val,
                                    key=f"choice_{q['question_number']}_{j}"
                                )
                                new_choices.append(new_choice)
                            
                            # Correct answer dropdown
                            answer_options = ['A', 'B', 'C', 'D']
                            current_answer = q.get('correct_answer', 'A')
                            if current_answer not in answer_options:
                                current_answer = 'A'
                            
                            new_correct_answer = st.selectbox(
                                "Correct Answer",
                                options=answer_options,
                                index=answer_options.index(current_answer),
                                key=f"answer_{q['question_number']}"
                            )
                        
                        elif q.get('type', q.get('question_type')) == 'Short Answer':
                            new_answer_key = st.text_area(
                                "Expected Answer / Answer Key",
                                value=q.get('answer_key', ''),
                                height=80,
                                key=f"answer_key_{q['question_number']}"
                            )
                            
                            if q.get('rubric'):
                                with st.expander("📋 Rubric Details"):
                                    st.json(q['rubric'])
                        
                        else:  # Essay, Problem Solving, Drawing
                            new_sample_answer = st.text_area(
                                "Sample Answer",
                                value=q.get('sample_answer', ''),
                                height=80,
                                key=f"sample_{q['question_number']}"
                            )
                            
                            if q.get('rubric'):
                                with st.expander("📋 Rubric Details"):
                                    st.json(q['rubric'])
                        
                        # Action buttons
                        st.markdown("---")
                        col_save, col_regen, col_delete = st.columns(3)
                        
                        with col_save:
                            save_btn = st.form_submit_button("💾 Save Changes", use_container_width=True)
                        
                        with col_regen:
                            regen_btn = st.form_submit_button("🔄 Regenerate", use_container_width=True)
                        
                        with col_delete:
                            delete_btn = st.form_submit_button("🗑️ Delete", use_container_width=True, type="secondary")
                        
                        # Handle button actions
                        if save_btn:
                            # Prepare updated data
                            updated_data = {
                                'bloom': new_bloom,
                                'bloom_level': new_bloom,
                                'points': new_points,
                                'question_text': new_question_text
                            }
                            
                            # Add type-specific updates
                            if q.get('type', q.get('question_type')) == 'MCQ':
                                updated_data['choices'] = new_choices
                                updated_data['correct_answer'] = new_correct_answer
                            elif q.get('type', q.get('question_type')) == 'Short Answer':
                                updated_data['answer_key'] = new_answer_key
                            else:
                                updated_data['sample_answer'] = new_sample_answer
                            
                            # Update question
                            if update_question_in_tqs(question_idx, updated_data):
                                st.success(f"✅ Question {q['question_number']} updated!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to update question.")
                        
                        if regen_btn:
                            # Get API key (Streamlit secrets or environment variable)
                            api_key = get_gemini_api_key()
                            
                            if not api_key:
                                st.error("❌ GEMINI_API_KEY is not configured.")
                            else:
                                with st.spinner(f"Regenerating question {q['question_number']}..."):
                                    if regenerate_single_question(question_idx, api_key):
                                        st.success(f"✅ Question {q['question_number']} regenerated!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to regenerate question.")
                        
                        if delete_btn:
                            if delete_question_from_tqs(question_idx):
                                st.success(f"✅ Question {q['question_number']} deleted!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete question.")

# --- Export ---
with assess_tabs[5]:
        st.markdown("### Export")
        
        # Display current TOS settings
        if "generated_tos" in st.session_state:
            st.markdown("#### 📄 Course Configuration")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Course:** {st.session_state.course_details.get('course_code', '')} - {st.session_state.course_details.get('course_title', '')}")
                st.write(f"**Exam Term:** {st.session_state.course_details.get('exam_term', 'Midterm')}")
            with col2:
                st.write(f"**Instructor:** {st.session_state.course_details.get('instructor', 'N/A')}")
                st.write(f"**Academic Year:** {st.session_state.course_details.get('academic_year', '')}")

        # ======================================================
        # TOS EXPORT
        # ======================================================
        if "generated_tos" in st.session_state:
            # Display question type distribution summary
            if "question_types" in st.session_state.generated_tos:
                st.markdown("#### 📊 Question Type Distribution Summary")
                qt_summary = format_question_types_for_display(
                    st.session_state.generated_tos["question_types"]
                )
                df_qt = pd.DataFrame(qt_summary)
                st.dataframe(df_qt, use_container_width=True, hide_index=True)
            
            st.markdown("#### 📥 Export TOS")
            if st.button("⬇ Export TOS as Excel", key="btn_export_tos"):

                exam_term = st.session_state.course_details.get("exam_term", "Midterm")
                course_code = st.session_state.course_details.get("course_code", "")
                course_title = st.session_state.course_details.get("course_title", "")
                semester = st.session_state.course_details.get("semester", "")
                instructor = st.session_state.course_details.get("instructor", "")
                academic_year = st.session_state.course_details.get("academic_year", "")
                
                # Get total points from generated TOS
                # This comes from compute_question_type_totals() - the SINGLE SOURCE OF TRUTH
                total_points = st.session_state.generated_tos.get("total_points", 0)

                excel = export_tos_exact_format(
                    meta={
                        "name": instructor,
                        "subject_code": course_code,
                        "title": course_title,
                        "semester": semester,
                        "exam_term": exam_term,
                        "academic_year": academic_year,
                        "schedule": "",
                        "course": "",
                        "exam_date": "",
                        "course_content": ""
                    },
                    outcomes=st.session_state.generated_tos["outcomes"],
                    tos_matrix=st.session_state.generated_tos["tos_matrix"],
                    total_items=st.session_state.generated_tos.get("total_items", 0),
                    total_points=int(total_points)  # From SINGLE SOURCE OF TRUTH
                )

                file_name = f"TOS_{course_code}_{exam_term}.xlsx"
                st.download_button(
                    label="📥 Download TOS Excel",
                    data=excel,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("📊 Generate a TOS first to export it.")
        
        st.markdown("---")
        
        # ======================================================
        # TQS EXPORT
        # ======================================================
        if "generated_tqs" in st.session_state and st.session_state.generated_tqs:
            st.markdown("#### 📥 Export Test Questions")
            st.markdown("Export your finalized questions to various formats:")
            
            # Get course details for export
            exam_term = st.session_state.course_details.get("exam_term", "Midterm")
            course_code = st.session_state.course_details.get("course_code", "")
            course_name = st.session_state.course_details.get("course_name", "Course Name")
            instructor_name = st.session_state.course_details.get("instructor_name", "")
            
            # Export Options
            st.markdown("##### Export Options")
            col_opt1, col_opt2 = st.columns(2)
            
            with col_opt1:
                shuffle_choices = st.checkbox(
                    "🔀 Shuffle MCQ Choices", 
                    value=False,
                    help="Randomize the order of A, B, C, D choices for MCQ questions. Correct answer will be updated automatically.",
                    key="export_shuffle_choices"
                )
            
            with col_opt2:
                generate_versions = st.checkbox(
                    "📋 Generate Multiple Versions (A & B)", 
                    value=False,
                    help="Create Version A and Version B with different question order and shuffled choices. Both versions in one file.",
                    key="export_generate_versions"
                )
            
            if generate_versions:
                st.info("ℹ️ Multiple versions will include:\n- Different question order\n- Shuffled MCQ choices\n- Separate answer keys for each version")
            
            st.markdown("---")
            
            # Export buttons in columns
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # Export to DOCX
                if st.button("📄 Export to DOCX", use_container_width=True, key="btn_export_docx"):
                    try:
                        with st.spinner("Generating DOCX file..."):
                            docx_buffer = tqs_export_service.export_to_docx(
                                questions=st.session_state.generated_tqs,
                                course_name=course_name,
                                exam_title=f"{course_code} {exam_term} Exam",
                                exam_term=exam_term,
                                instructor_name=instructor_name,
                                shuffle_choices=shuffle_choices,
                                generate_versions=generate_versions,
                                num_versions=2,
                                shuffle_question_order=True
                            )
                            
                            file_name = f"TQS_{course_code}_{exam_term}.docx"
                            st.download_button(
                                label="📥 Download DOCX",
                                data=docx_buffer.getvalue(),
                                file_name=file_name,
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key="download_docx"
                            )
                            if generate_versions:
                                st.success("✅ DOCX file with Version A & B ready!")
                            else:
                                st.success("✅ DOCX file ready!")
                    except Exception as e:
                        st.error(f"❌ Error generating DOCX: {str(e)}")
            
            with col2:
                # Export to PDF
                if st.button("📕 Export to PDF", use_container_width=True, key="btn_export_pdf"):
                    try:
                        with st.spinner("Generating PDF file..."):
                            pdf_buffer = tqs_export_service.export_to_pdf(
                                questions=st.session_state.generated_tqs,
                                course_name=course_name,
                                exam_title=f"{course_code} {exam_term} Exam",
                                exam_term=exam_term,
                                instructor_name=instructor_name,
                                shuffle_choices=shuffle_choices,
                                generate_versions=generate_versions,
                                num_versions=2,
                                shuffle_question_order=True
                            )
                            
                            file_name = f"TQS_{course_code}_{exam_term}.pdf"
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_buffer.getvalue(),
                                file_name=file_name,
                                mime="application/pdf",
                                key="download_pdf"
                            )
                            if generate_versions:
                                st.success("✅ PDF file with Version A & B ready!")
                            else:
                                st.success("✅ PDF file ready!")
                    except Exception as e:
                        st.error(f"❌ Error generating PDF: {str(e)}")
            
            with col3:
                # Export to CSV
                if st.button("📊 Export to CSV", use_container_width=True, key="btn_export_csv"):
                    try:
                        with st.spinner("Generating CSV file..."):
                            csv_buffer = tqs_export_service.export_to_csv(
                                questions=st.session_state.generated_tqs
                            )
                            
                            file_name = f"TQS_{course_code}_{exam_term}.csv"
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv_buffer.getvalue(),
                                file_name=file_name,
                                mime="text/csv",
                                key="download_csv"
                            )
                            st.success("✅ CSV file ready!")
                    except Exception as e:
                        st.error(f"❌ Error generating CSV: {str(e)}")
            
            with col4:
                # Export to JSON (original functionality preserved)
                if st.button("📋 Export to JSON", use_container_width=True, key="btn_export_json"):
                    tqs_json = json.dumps(st.session_state.generated_tqs, indent=2)
                    
                    file_name = f"TQS_{course_code}_{exam_term}.json"
                    st.download_button(
                        label="📥 Download JSON",
                        data=tqs_json,
                        file_name=file_name,
                        mime="application/json",
                        key="download_json"
                    )
                    st.success("✅ JSON file ready!")
            
            # Export info
            with st.expander("ℹ️ Export Format Information"):
                st.markdown("""
                **DOCX**: Professional Word document with:
                - Formatted header with course info
                - Instructions section
                - All questions with proper formatting
                - Separate answer key page with metadata
                
                **PDF**: Printable PDF document with:
                - Same format as DOCX
                - Professional styling
                - Page breaks between sections
                - Ready for printing or digital distribution
                
                **CSV**: Spreadsheet format with columns:
                - Question Number, Question Text, Question Type
                - Options A-D, Correct Answer
                - Answer Key/Sample Answer
                - Bloom Level, Points, Learning Outcome
                - Great for importing into LMS or other systems
                
                **JSON**: Raw data format for:
                - Programmatic access
                - Backup and archival
                - Import into other applications
                """)
        else:
            st.info("📝 Generate test questions first to export them.")
