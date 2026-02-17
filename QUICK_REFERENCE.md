# SmartLesson - Quick Reference Guide (Updated)

## Key Features at a Glance

### 📘 Main Tabs
1. **Lesson Planner** - Create lesson plans and learning objectives
2. **Assessment Generator** - Create TOS (Table of Specifications)

### 📊 Assessment Generator Tabs

| Tab | Purpose | Key Feature |
|-----|---------|-------------|
| **Course/Syllabus** | Upload PDF & course info | Auto-extracts Section IV learning outcomes |
| **Learning Outcomes** | Set learning goals & hours | Import from PDF, manage hours per outcome |
| **Assessment Profile** | Configure Bloom's distribution | Board/Non-Board/Custom templates |
| **Generate TOS** | Create test specifications | Imports from PDF section IV outcomes |
| **Generate TQS** | AI test generation | Coming soon |
| **Export** | Download TOS as Excel | Includes Midterm/Final in filename |

---

## Workflow: From PDF to TOS

### 1️⃣ Course/Syllabus Tab
```
Upload PDF
    ↓
Auto-extract from Section IV:
  • Course Code
  • Course Title
  • Semester
  • Academic Year
  • Instructor
  • Learning Outcomes (5-15 items)
    ↓
Select Exam Term: Midterm or Final
    ↓
Review & edit manually if needed
```

### 2️⃣ Learning Outcomes Tab
```
Click "Use PDF Learning Outcomes"
    ↓
Outcomes imported from Section IV
    ↓
Assign hours to each outcome
(Teacher controls hours allocation)
    ↓
View coverage %
    ↓
Add custom outcomes as needed
```

### 3️⃣ Assessment Profile
```
Select Program Type
    ↓
Adjust Bloom's Taxonomy %
  - Remember
  - Understand
  - Apply
  - Analyze
  - Evaluate
  - Create
    ↓
Total must equal 100%
```

### 4️⃣ Generate TOS
```
Set total test items
    ↓
Click "Generate TOS"
    ↓
View matrix of outcomes × Bloom's levels
    ↓
See item distribution
```

### 5️⃣ Export
```
Click "Export TOS as Excel"
    ↓
Download file:
  TOS_CS101_Midterm.xlsx
  or
  TOS_CS101_Final.xlsx
```

---

## PDF Syllabus Format

### ✅ Correct Format
```
SECTION IV: LEARNING PLAN

| Week | Learning Outcomes | Resources | Assessment |
|------|-------------------|-----------|------------|
| 1-2  | Explain fundamental HCI concepts | Textbook Ch 1-2 | Quiz |
| 3-4  | Analyze user behavior patterns | Case studies | Assignment |
| 5-6  | Design user interfaces | Tools & templates | Project |
```

### ❌ Will Not Extract Well
- Learning outcomes mixed throughout document
- No clear Section IV header
- Scanned/image-based PDF
- Outcomes not clearly separated

---

## Key Fields & Options

### Course Details
| Field | Options | Required | Notes |
|-------|---------|----------|-------|
| Course Code | Text (CS101, MATH-201) | Yes | Auto-extracted |
| Course Title | Text | Yes | Auto-extracted |
| Semester | 1st / 2nd / Summer | Yes | Auto-extracted |
| Academic Year | YYYY–YYYY format | Yes | Auto-extracted |
| Instructor | Text | No | Auto-extracted |
| Total Hours | Number | Yes | Manual entry |
| **Exam Term** | **Midterm / Final** | **Yes** | **NEW!** |

### Hours Management
- Each learning outcome gets assigned hours
- Hours shown in real-time total
- Coverage % calculated automatically
- Warning if hours > total course hours

### Bloom's Levels
- Remember (knowledge)
- Understand (comprehension)
- Apply (application)
- Analyze (analysis)
- Evaluate (evaluation)
- Create (synthesis)

All must total **100%**

---

## Tips & Best Practices

### For PDF Upload:
1. ✓ Ensure PDF has clear "Section IV" header
2. ✓ Use bullet points or numbers for outcomes
3. ✓ Keep outcomes in dedicated column/section
4. ✓ Use text-based PDF (not scanned)
5. ✓ Each outcome on separate line

### For Hour Allocation:
1. ✓ Distribute total hours across all outcomes
2. ✓ Match teaching time to outcome importance
3. ✓ Aim for ~80-100% coverage of total hours
4. ✓ Allow flexibility for reviews/exams

### For TOS Generation:
1. ✓ Define all learning outcomes first
2. ✓ Configure Bloom's distribution
3. ✓ Set realistic test item count
4. ✓ Generate TOS before changing settings

### For Export:
1. ✓ Verify Midterm/Final selection
2. ✓ Check all course details filled
3. ✓ Use descriptive file names
4. ✓ Store TOS files organized by term

---

## Common Issues & Solutions

### PDF Won't Extract?
- ✓ Check for "Section IV" header
- ✓ Verify PDF is text-based, not scanned
- ✓ Check outcomes start with action verbs
- ✓ Look at "Extracted Details" panel

### Learning Outcomes Missing?
- ✓ Click "Use PDF Learning Outcomes" button
- ✓ Button only appears after successful PDF upload
- ✓ Manually add if not extracted

### Hours Not Saving?
- ✓ Click on the number input to update
- ✓ Hours persist during session
- ✓ Re-upload PDF if session resets

### Exam Term Not Showing?
- ✓ Select from dropdown in Course/Syllabus
- ✓ Verify it appears in "Generate TOS" tab
- ✓ Check filename includes exam term

### Bloom's Not at 100%?
- ✓ Adjust sliders until total = 100%
- ✓ Green checkmark appears when valid
- ✓ Can't generate TOS until valid

---

## File Naming Convention

### Exported TOS Files
```
TOS_[CourseCode]_[ExamTerm].xlsx

Examples:
- TOS_CS101_Midterm.xlsx
- TOS_CS101_Final.xlsx
- TOS_MATH201_Midterm.xlsx
- TOS_ENG301_Final.xlsx
```

---

## Keyboard Shortcuts
(Standard Streamlit:)
- **R** = Rerun app
- **C** = Clear cache
- **Ctrl+Enter** = Submit forms

---

## Data Storage

### Session State (Persists during session)
- `course_details` - All course info including exam_term
- `assessment_outcomes` - Learning outcomes with hours
- `assessment_outcomes` - Total items & weights
- `bloom_weights` - Bloom's taxonomy distribution
- `generated_tos` - Final TOS matrix

### Lost When:
- App is restarted
- Browser tab closed
- Page refreshed (F5)

### Solution:
- Re-upload PDF or re-enter data
- Use Excel export to save results

---

## Version Info

**Current Version:** 2.1 (With Section IV Update)

**Latest Changes:**
- ✨ Section IV learning outcomes extraction
- ✨ Midterm/Final exam term selection
- ✨ Improved PDF pattern matching
- ✨ Enhanced export with exam term
- ✨ Better hours tracking & validation
- ✨ **[NEW] Weighted TOS Matrix Generation**
  - Items and Points now independent
  - Proper support for weighted question types
  - See: WEIGHTED_TOS_INTEGRATION.md

---

## 🆕 Weighted TOS Matrix Fix (Feb 14, 2026)

### What Changed?

**Problem Fixed:** TOS matrix now supports weighted question type scoring (e.g., Essay=5pts, MCQ=1pt)

**Result:**
- ✅ Items and Points are independent values
- ✅ Proper aggregation from question type assignments
- ✅ No "1 item = 1 point" assumption
- ✅ Weighted scoring preserved in export

### Example

```
Before: 12 items = 12 points (incorrect if items have different weights)
After:  12 items = 28 points (5 MCQ@1pt + 7 Essay@5pts = 40pts ... math)
        ↑ Independent values ✓
```

### New Functions

Two new functions in `services/tos_service.py`:

```python
# Get weighted matrices from assigned slots
items_mx, _, points_mx = generate_tos_from_assigned_slots(
    st.session_state.exam_blueprint
)

# Compute totals
total_items, total_points, _, _ = compute_tos_totals(items_mx, points_mx)
```

### For Developers

1. **Integration Guide:** See [WEIGHTED_TOS_INTEGRATION.md](WEIGHTED_TOS_INTEGRATION.md)
2. **Before/After:** See [BEFORE_AFTER_COMPARISON.md](BEFORE_AFTER_COMPARISON.md)
3. **Test It:** Run `python test_weighted_tos_matrix.py`

### For Teachers

The TOS now shows accurate point distribution based on question types you assign:
- Different question types can have different point values
- Total points reflect your exact configuration
- No hidden automatic conversions

---

## Support & Documentation

- **SETUP_GUIDE.md** - Complete feature documentation
- **PDF_UPLOAD_GUIDE.md** - PDF requirements & examples
- **SECTION_IV_UPDATE.md** - New update details
- **WEIGHTED_TOS_INTEGRATION.md** - How to use weighted TOS [NEW]
- **BEFORE_AFTER_COMPARISON.md** - Visual explanation [NEW]
- **WEIGHTED_TOS_MATRIX_FIX.md** - Technical details [NEW]

---

## Need Help?

Check these files for detailed info:
1. Review extracted details panel in app
2. Check PDF format against examples
3. Read documentation guides
4. Verify all required fields are entered
5. Try with a different PDF file

Happy TOS Creating! 📊✨
