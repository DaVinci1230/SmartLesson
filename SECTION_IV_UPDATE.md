# SmartLesson PDF Update - Section IV Learning Outcomes

## What's New

### 1. **Focused PDF Extraction from Section IV**
The PDF extraction now specifically targets **Section IV (Learning Plan)** from your syllabus PDF instead of searching the entire document randomly.

**Key improvements:**
- Looks specifically for "Section IV" or "LEARNING PLAN" headers
- Extracts only from the **Learning Outcomes column** of the learning plan table
- More accurate extraction of outcome statements like:
  - "Explain the fundamental concepts and scope of Human Computer Interaction (HCI)"
  - "Apply design principles in user interface development"
  - etc.

### 2. **Exam Term Selection (Midterm vs Final)**
Added a new feature to select which term to create the TOS for:

**Where it appears:**
- Course/Syllabus tab → "Exam Term (Which TOS?)" dropdown
- Options: **Midterm** or **Final**

**How it's used:**
- Displayed in TOS generation ("Creating TOS for: **Midterm Exam**")
- Included in exported Excel filename: `TOS_CS101_Midterm.xlsx` or `TOS_CS101_Final.xlsx`
- Stored in metadata for TOS reference

---

## Updated Features

### Course/Syllabus Tab
```
Column 1:                          Column 2:
- Course Code                      - Academic Year
- Course Title                     - Instructor
- Semester                         - Total Course Hours
                                   - 📚 Exam Term (NEW!)
```

### Learning Outcomes Section IV Extraction
The new extraction logic:
1. Finds "Section IV" or "Learning Plan" in the PDF
2. Locates the "Learning Outcomes" column
3. Extracts each learning outcome as a separate item
4. Filters out non-substantive text (week numbers, etc.)
5. Imports up to 15 outcomes

**Example extraction:**
```
Extracted Learning Outcomes:
  ✓ Explain the fundamental concepts and scope of HCI
  ✓ Analyze user behavior and interaction patterns
  ✓ Design effective user interfaces
  ✓ Evaluate usability in software applications
  ✓ Create interactive prototypes
```

### Generate TOS Tab
Now displays which exam you're creating:
```
📋 Creating TOS for: Midterm Exam
```

### Export Features
- File name now includes exam term: `TOS_CS101_Midterm.xlsx`
- Exam term included in Excel metadata
- Course information preview before export

---

## PDF Format Requirements

Your syllabus should have this structure for best results:

```
=== SECTION I: Course Information ===
Course Code: CS102
Course Title: Human Computer Interaction
Semester: 1st
Academic Year: 2025–2026
Instructor: Dr. Jane Smith
Total Hours: 45

=== SECTION IV: Learning Plan ===
(or Learning Outcomes, Learning Objectives, etc.)

| Week | Topic | Learning Outcomes | Resources | Assessment |
|------|-------|-------------------|-----------|------------|
| 1-2  | HCI Basics | Explain the fundamental concepts and scope of HCI; Understand the evolution of HCI discipline | Readings | Quiz |
| 3-4  | User Research | Analyze user behavior and interaction patterns; Design effective user research methods | Case studies | Assignment |
...
```

### Key Format Notes:
- **Section IV** must be clearly labeled as:
  - "Section IV" or "SECTION IV"
  - "Learning Plan" or "LEARNING PLAN"
  - "Learning Outcomes" or "LEARNING OUTCOMES"

- **Learning Outcomes column** should:
  - Be clearly separated (table column or indented section)
  - Start with action verbs (Explain, Understand, Analyze, Design, Create, etc.)
  - Be separated by semicolons or line breaks

---

## Code Changes Summary

### `services/pdf_service.py` - Updated
- New regex pattern specifically targeting Section IV
- Learning outcomes now extracted from column text
- Cleaner filtering of non-outcome text
- Supports multi-line outcomes

### `app.py` - Updated
- Added `exam_term` field to course_details
- New exam term selector in Course/Syllabus tab
- TOS generation now displays which exam term
- Export includes exam term in filename and metadata

---

## Usage Workflow

### Step 1: Upload PDF
1. Go to **Course/Syllabus** tab
2. Upload your syllabus PDF
3. System automatically extracts from Section IV

### Step 2: Select Exam Term
1. Choose **Midterm** or **Final** from the dropdown
2. This determines which exam you're creating TOS for

### Step 3: Review Learning Outcomes
1. Go to **Learning Outcomes** tab
2. Click **"Use PDF Learning Outcomes"** to import Section IV outcomes
3. Assign hours to each outcome

### Step 4: Generate & Export
1. Configure Bloom's taxonomy
2. Set test item count
3. Click **"Generate TOS"**
4. Download as Excel (file will be named with exam term)

---

## Troubleshooting

### No learning outcomes extracted?
- ✓ Verify "Section IV" header exists in PDF
- ✓ Check that outcomes are in a distinct column/section
- ✓ Outcomes should be 10+ characters long
- ✓ Look at "Extracted Details" panel for what was found

### Outcomes not being Read correctly?
- ✓ Ensure outcomes are separated by line breaks
- ✓ Check PDF is not image-based/scanned
- ✓ Try cleaner formatting with bullet points or numbers

### Exam term not saving?
- ✓ Make sure to select from dropdown
- ✓ Verify it appears in the "Generate TOS" tab info message
- ✓ Check Excel filename contains the exam term

---

## Example: Before vs After

### BEFORE Update:
```
Extracted Learning Outcomes:
❌ Course Information
  - HCI Basics
  - Lecture format with examples
  - Assessment: Quiz and assignment
(Mixing all text from entire document)
```

### AFTER Update:
```
Extracted Learning Outcomes:
✅ Explain the fundamental concepts and scope of HCI
✅ Analyze user behavior and interaction patterns
✅ Design effective user interfaces
✅ Evaluate usability in software applications
(Only from Section IV Learning Plan)
```

---

## Technical Details

### Section IV Detection Pattern
```python
r'(?:Section\s+IV|IV\.)\s*(?:Learning\s+Plan|LEARNING\s+PLAN)'
```

### Learning Outcomes Column Pattern
```python
r'(?:Learning\s+Outcomes?)[:\s\n]+((?:[\s\S]*?)(?=\n\s*(?:Assessment|Resources|$)))'
```

### Cleanup Process
1. Split by line breaks and bullets
2. Remove numbers/symbols at start
3. Keep only items > 10 characters
4. Filter out non-outcome text

---

## Next Steps

The TOS system now:
- ✅ Extracts Section IV learning outcomes accurately
- ✅ Allows Midterm/Final exam selection
- ✅ Includes exam term in all exports
- ✅ Better organized for different exam preparations

You can now create separate TOS for:
- **Midterm Exam**: First half of semester coverage
- **Final Exam**: Comprehensive coverage

Enjoy the enhanced PDF extraction! 📚
