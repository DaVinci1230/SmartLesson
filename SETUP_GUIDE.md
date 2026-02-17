# SmartLesson PDF Syllabus Upload - Configuration Guide

## Features Implemented

### 1. **PDF Syllabus Upload & Auto-Population**
   - Located in the **"Course / Syllabus"** tab of the Assessment Generator
   - Users can upload a PDF syllabus file
   - The system automatically extracts:
     - ✅ Course Code (e.g., CS101, MATH1001)
     - ✅ Course Title
     - ✅ Semester (1st, 2nd, or Summer)
     - ✅ Academic Year
     - ✅ Instructor Name
     - ✅ Learning Outcomes

### 2. **Learning Outcomes Management** 
   - Located in the **"Learning Outcomes"** tab
   - Three ways to populate learning outcomes:
     1. **📄 From PDF**: Click "Use PDF Learning Outcomes" to import extracted outcomes
     2. **📥 From Lesson Planner**: Import objectives from the Lesson Planner tab
     3. **➕ Manual Entry**: Add custom outcomes

### 3. **Hour Control for Teachers**
   - Each learning outcome has an **editable hours field**
   - Teachers can control:
     - Hours taught for each outcome
     - Total hours allocation
   - **Hours Summary Dashboard** shows:
     - Total Hours Assigned
     - Total Course Hours
     - Coverage Percentage (%)
   - **Validation Warning**: Alerts if assigned hours exceed total course hours

---

## How to Use

### Step 1: Upload Syllabus PDF
1. Go to **"Assessment Generator"** → **"Course / Syllabus"** tab
2. Click **"Upload Syllabus (PDF)"**
3. Select your syllabus PDF file
4. The system will automatically extract all available information
5. Extracted details appear in a collapsible panel for review

### Step 2: Review & Edit Course Details
- All extracted fields can be manually edited:
  - Course Code
  - Course Title  
  - Semester
  - Academic Year
  - Instructor
  - Total Course Hours

### Step 3: Set Learning Outcomes & Hours
1. Go to **"Learning Outcomes"** tab
2. Click **"Use PDF Learning Outcomes"** to import from the uploaded syllabus
3. For each outcome, enter the **"Hours"** taught
4. The system tracks:
   - Total hours assigned
   - Coverage % of total course hours
5. Add custom outcomes as needed with the **"Add Outcome"** button

### Step 4: Monitor Hours Balance
- Check the **"📊 Hours Summary"** section
- Ensures no over-allocation of course hours
- Helps balance learning time across all outcomes

---

## New Files & Modules

### 1. **services/pdf_service.py**
   - Contains `extract_syllabus_details(pdf_file)` function
   - Parses PDF text using regex patterns
   - Extracts:
     - Course metadata
     - Learning outcomes (up to 5 from the PDF)
   - Returns structured data for app use

### 2. **Updated app.py**
   - Enhanced **"Course / Syllabus"** tab with PDF upload
   - Enhanced **"Learning Outcomes"** tab with hour management
   - Session state management for persistent data
   - Hours validation and summary metrics

### 3. **Updated requirements.txt**
   - Added `PyPDF2==4.0.1` for PDF text extraction

---

## Technical Details

### PDF Extraction Patterns
The system uses regex patterns to find:
- **Course Code**: `CS101`, `MATH-1001`, `ENG101`
- **Title**: After "Course Title" or "Subject" labels
- **Semester**: `1st`, `2nd`, `Summer` keywords
- **Academic Year**: `2025–2026` format
- **Instructor**: After "Instructor" or "Professor" labels
- **Learning Outcomes**: Section after "Learning Outcomes" header

### Session State Management
- `st.session_state.course_details`: Stores course metadata  
- `st.session_state.assessment_outcomes`: Stores outcomes with hours
- `st.session_state.extracted_learning_outcomes`: Temporary storage for PDF outcomes

---

## Troubleshooting

### PDF Extraction Not Working?
- Ensure PDF has clear headers (e.g., "Course Code:", "Course Title:")
- PDF must have readable text (not image-based)
- Check the expanded "Extracted Details" panel to see what was found

### Hours Not Saving?
- Streamlit requires explicit session state updates
- Hours are saved when you interact with the number input
- Use the "Hours Summary" to verify allocation

### Import from PDF Button Not Showing?
- Make sure you've uploaded a PDF in the "Course / Syllabus" tab
- The button only appears after successful PDF extraction
- Check for error messages in the Extracted Details panel

---

## Future Enhancements
- [ ] OCR support for image-based PDFs
- [ ] Learning outcomes extraction from more PDF sections
- [ ] AI-powered outcome parsing (using OpenAI API)
- [ ] Custom regex pattern configuration
- [ ] Bulk upload of multiple syllabi
- [ ] Database persistence of course & outcome data
