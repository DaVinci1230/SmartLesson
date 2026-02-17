# SmartLesson PDF Upload Feature - Quick Start

## Overview
The PDF Syllabus Upload feature automatically extracts key course information and learning outcomes from your PDF files, streamlining the TOS (Table of Specifications) creation process.

---

## Installation & Setup

### 1. Install Required Package
```bash
pip install PyPDF2==4.0.1
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
streamlit run app.py
```

---

## Workflow

### Tab 1: Course / Syllabus
1. **Upload PDF**: Click "Upload Syllabus (PDF)"
2. **Auto-Extraction**: System extracts:
   - Course Code
   - Course Title
   - Semester
   - Academic Year
   - Instructor Name
   - Learning Outcomes (up to 5)

3. **Review & Edit**: All fields are editable for corrections:
   ```
   Course Code:    [CS101 or MATH-201]
   Course Title:   [Advanced Programming]
   Semester:       [1st / 2nd / Summer]
   Academic Year:  [2025–2026]
   Instructor:     [Dr. John Smith]
   Total Hours:    [45 hours]
   ```

### Tab 2: Learning Outcomes  
1. **Import from PDF**: Click "📄 Use PDF Learning Outcomes"
2. **Assign Hours**: Enter hours taught for each outcome
3. **Monitor Balance**: Check the Summary:
   - Total Hours Assigned
   - Total Course Hours
   - Coverage %

Example:
```
├─ Learning Outcome 1: Understand different programming paradigms
│  └─ Hours: 8
├─ Learning Outcome 2: Apply design patterns
│  └─ Hours: 12
├─ Learning Outcome 3: Develop object-oriented applications  
│  └─ Hours: 15
└─ Learning Outcome 4: Evaluate algorithm efficiency
   └─ Hours: 10

Hours Summary:
  Assigned: 45 hours
  Total: 45 hours
  Coverage: 100%
```

---

## PDF Requirements

For best results, your PDF should include:

1. **Clear Headers** (any of these):
   - "Course Code:" or "Code:"
   - "Course Title:" or "Subject:"
   - "Semester:" or "Term:"
   - "Academic Year:" or "AY:"
   - "Instructor:" or "Professor:"
   - "Learning Outcomes:" or "Course Objectives:"

2. **Readable Text**:
   - PDF must be text-based (not scanned images)
   - Text should be clearly formatted
   - Use standard formatting for dates (YYYY–YYYY)

3. **Example Syllabus Format**:
   ```
   COURSE INFORMATION
   Course Code: CS101
   Course Title: Introduction to Computer Science
   
   COURSE DETAILS
   Semester: 1st
   Academic Year: 2025–2026
   Instructor: Dr. Sarah Johnson
   Total Hours: 45
   
   LEARNING OUTCOMES
   By the end of this course, students will be able to:
   1. Understand fundamental programming concepts
   2. Apply problem-solving techniques
   3. Develop simple applications
   4. Analyze code efficiency
   5. Create project solutions
   ```

---

## Feature Details

### Automatic Extraction Patterns

The system uses intelligent pattern matching to find:

| Field | Patterns Searched |
|-------|-------------------|
| **Course Code** | CS101, MATH-201, ENG101, BIO-305 |
| **Title** | "Course Title: ...", "Subject: ..." |
| **Semester** | "1st", "2nd", "Summer", "First", "Second" |
| **Year** | "2025–2026", "2024-2025" |
| **Instructor** | "Instructor:", "Professor:", "Facilitator:" |
| **Outcomes** | Section after "Learning Outcomes" header |

### Hours Management

- **Edit Anytime**: Change hours for any outcome individually
- **Real-time Validation**: System warns if hours exceed total
- **Coverage Tracking**: See what % of course time is allocated
- **Add Custom Outcomes**: Manually add outcomes not in the PDF

---

## Session State

Data is stored in Streamlit's session state and persists while the app is running:

```python
st.session_state.course_details = {
    "course_code": "",
    "course_title": "",
    "semester": "1st",
    "academic_year": "2025–2026",
    "instructor": "",
    "total_hours": 0
}

st.session_state.assessment_outcomes = [
    {
        "outcome": "Understand programming concepts",
        "hours": 10
    },
    ...
]
```

---

## Troubleshooting

### Issue: PDF upload shows "Error extracting PDF"
**Solution**: 
- Ensure the PDF is not scanned/image-based
- Try re-saving the PDF in a different format
- Check if headers are clearly labeled

### Issue: Missing course details after upload
**Solution**:
- The system may not find all fields - that's OK!
- You can still manually enter missing information
- Check "Extracted Details" to see what was found

### Issue: Learning Outcomes button not appearing
**Solution**:
- First upload a PDF successfully
- The button only appears if outcomes were extracted
- If no outcomes found in PDF, manually add them

### Issue: Hours not persisting
**Solution**:
- Streamlit apps reset when code changes (hot reload)
- Upload PDF again to restore extracted data
- Your manual hour entries should persist during the session

---

## Next Steps in Workflow

After configuring course details and learning outcomes:

1. **Assessment Profile** (Tab 3)
   - Set Bloom's Taxonomy distribution
   - Choose program type (Board/Non-Board/Custom)

2. **Generate TOS** (Tab 4)
   - Create Table of Specifications
   - Distribute test items across outcomes and Bloom's levels

3. **Generate TQS** (Tab 5)
   - AI-assisted test question generation
   - Coming soon!

4. **Export** (Tab 6)
   - Download TOS as Excel file
   - Ready to use in assessments

---

## Code Structure

```
SmartLesson/
├── app.py                  # Main Streamlit app
├── services/
│   ├── pdf_service.py      # PDF extraction logic ← NEW
│   ├── tos_service.py      # TOS generation
│   ├── export_service.py   # Excel export
│   ├── ai_service.py       # AI integration
│   └── lesson_service.py   # Lesson planning
├── models/
│   ├── lesson.py
│   ├── question.py
│   └── tos.py
├── requirements.txt        # Dependencies (with PyPDF2)
└── SETUP_GUIDE.md         # Complete documentation
```

---

## Tips for Best Results

1. **Use Standard Formatting**: Clearly label sections in your PDF
2. **Check Extracted Data**: Review the expanded "Extracted Details" panel
3. **Adjust as Needed**: Don't hesitate to manually edit auto-populated fields
4. **Hour Allocation**: Distribute hours to match your teaching plan
5. **Cross-Check**: Verify coverage % matches your course design

Enjoy streamlined syllabus processing! 📘
