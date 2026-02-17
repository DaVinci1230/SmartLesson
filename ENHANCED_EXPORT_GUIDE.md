# Enhanced Export Features - Complete Guide

## 🎯 New Features Implemented

### ✅ **1. Answer Key Automatically Included**
Every DOCX and PDF export now includes a comprehensive answer key on a separate page.

**Format:**
```
ANSWER KEY

Question 1: B - Paris  [Bloom: Remember | 1 pts]

Question 2: A - Python  [Bloom: Understand | 2 pts]

Question 3: Recursion is when a function calls itself...  [Bloom: Apply | 3 pts]
```

**Features:**
- ✅ Separate page break before answer key
- ✅ Full answer text for MCQ (not just letter)
- ✅ Bloom level displayed beside each answer
- ✅ Point value shown for reference
- ✅ Sample answers for essay/short answer questions

---

### ✅ **2. Shuffle MCQ Choices**
Randomize the order of A, B, C, D choices while maintaining correct answer integrity.

**How It Works:**
1. Enable "🔀 Shuffle MCQ Choices" checkbox
2. Export to DOCX or PDF
3. Choices are randomized (e.g., B becomes C)
4. Correct answer letter automatically updated
5. **Original data remains unchanged**

**Example:**
```
Original:
A. London
B. Paris ✓
C. Berlin  
D. Madrid

After Shuffle:
A. Berlin
B. Madrid
C. Paris ✓  (was B, now C)
D. London
```

**Use Cases:**
- Prevent cheating by reordering choices
- Create practice versions with different layouts
- Test question validity by changing choice positions

---

### ✅ **3. Generate Version A & Version B**
Create multiple exam versions with different question order and shuffled choices.

**Features:**
- **Same questions** - content preserved
- **Different order** - questions shuffled
- **Shuffled choices** - MCQ options randomized
- **Separate answer keys** - one for each version
- **Single file export** - both versions in one document

**Structure:**
```
┌─────────────────────────────────────┐
│  MIDTERM EXAM - Version A           │
│  Questions 1-10                     │
│  (original order)                   │
├─────────────────────────────────────┤
│  ANSWER KEY - Version A             │
│  Q1: B [Bloom: Remember | 2 pts]    │
│  Q2: A [Bloom: Apply | 3 pts]       │
├─────────────────────────────────────┤
│  MIDTERM EXAM - Version B           │
│  Questions 1-10                     │
│  (different order)                  │
├─────────────────────────────────────┤
│  ANSWER KEY - Version B             │
│  Q1: C [Bloom: Analyze | 5 pts]     │
│  Q2: D [Bloom: Remember | 1 pt]     │
└─────────────────────────────────────┘
```

**Use Cases:**
- Prevent cheating in proctored exams
- Multiple testing sessions (morning/afternoon)
- Makeup exams with different question order
- A/B testing of question difficulty

---

## 🎨 How to Use in Streamlit

### **Step 1: Generate Your Questions**
Complete Steps 1-4 to generate TQS questions as usual.

### **Step 2: Configure Export Options**

Navigate to "📥 Export Test Questions" section:

```
Export Options
├─ ☐ 🔀 Shuffle MCQ Choices
│  Randomize A, B, C, D order
│  Correct answer updated automatically
│
└─ ☐ 📋 Generate Multiple Versions (A & B)
   Create Version A and B with:
   - Different question order
   - Shuffled MCQ choices
   - Separate answer keys
```

**Option Combinations:**

| Shuffle Choices | Generate Versions | Result |
|----------------|-------------------|---------|
| ☐ | ☐ | Standard export (original order) |
| ☑ | ☐ | Single version with shuffled choices |
| ☐ | ☑ | Version A & B with different question order |
| ☑ | ☑ | Version A & B with shuffled choices AND order |

### **Step 3: Export to Desired Format**

Click any export button:
- **📄 Export to DOCX** - Word document with versions
- **📕 Export to PDF** - PDF document with versions
- **📊 Export to CSV** - Spreadsheet (no versions)
- **📋 Export to JSON** - Raw data (no shuffle/versions)

### **Step 4: Download**

Success message appears:
- Single version: "✅ DOCX file ready!"
- Multiple versions: "✅ DOCX file with Version A & B ready!"

Click "📥 Download" button to save file.

---

## 💻 Programmatic Usage

### **Shuffle Choices Only**

```python
from services.tqs_export_service import tqs_export_service

# Export with shuffled choices
docx_buffer = tqs_export_service.export_to_docx(
    questions=questions,
    course_name="CS101",
    exam_title="Midterm Exam",
    shuffle_choices=True,         # ← Enable shuffle
    generate_versions=False
)

# Save to file
with open("exam_shuffled.docx", "wb") as f:
    f.write(docx_buffer.getvalue())
```

### **Generate Version A & B**

```python
# Export with multiple versions
docx_buffer = tqs_export_service.export_to_docx(
    questions=questions,
    course_name="CS101",
    exam_title="Final Exam",
    shuffle_choices=False,
    generate_versions=True,       # ← Enable versions
    num_versions=2,               # A and B
    shuffle_question_order=True   # Different order
)

# File will contain both versions
with open("exam_versions_AB.docx", "wb") as f:
    f.write(docx_buffer.getvalue())
```

### **Manual Choice Shuffling**

```python
# Shuffle choices manually for inspection
shuffled_questions = tqs_export_service.shuffle_questions_choices(
    questions=original_questions,
    seed=42  # Optional: for reproducible shuffling
)

# Original questions remain unchanged
print(original_questions[0]['choices'])  # ['A', 'B', 'C', 'D']
print(shuffled_questions[0]['choices'])  # ['C', 'A', 'D', 'B']
```

### **Generate Multiple Versions Manually**

```python
# Generate 3 versions (A, B, C)
versions = tqs_export_service.generate_exam_versions(
    questions=questions,
    num_versions=3,
    shuffle_question_order=True,
    shuffle_choices=True
)

# Inspect versions
for version_label, version_questions in versions:
    print(f"{version_label}: {len(version_questions)} questions")
    print(f"First question: {version_questions[0]['question_text']}")
```

---

## 🔒 Data Safety

### **Original Data Protection**

✅ **All operations use deep copies**
- Original questions in database/session never modified
- Shuffle applies only to export copies
- Multiple exports won't affect each other

✅ **No persistent changes**
- Shuffling happens at export time
- No database writes or updates
- Session state remains unchanged

✅ **Reproducible with seeds**
- Optional seed parameter for testing
- Same seed = same shuffle order
- Useful for debugging and validation

**Verification:**
```python
original = st.session_state.generated_tqs
print(original[0]['choices'])  # ['London', 'Paris', 'Berlin', 'Madrid']

# Export with shuffle
export_to_docx(..., shuffle_choices=True)

print(original[0]['choices'])  # Still ['London', 'Paris', 'Berlin', 'Madrid'] ✅
```

---

## 📊 Answer Key Format

### **MCQ Questions**
```
Question 1: B - Paris  [Bloom: Remember | 1 pts]
```

**Components:**
- Question number
- Correct answer letter (B)
- Full answer text (Paris)
- Bloom taxonomy level
- Point value

### **Short Answer Questions**
```
Question 2: Recursion is when a function calls itself to solve a problem  [Bloom: Understand | 3 pts]
```

**Components:**
- Question number
- Sample answer or answer key
- Bloom level
- Points

### **Essay/Problem Solving Questions**
```
Question 3: Students should discuss temperature changes, rainfall patterns, crop yields...  [Bloom: Analyze | 10 pts]
```

**Components:**
- Question number
- Grading rubric or sample answer (truncated if > 100 chars)
- Bloom level
- Points

---

## 🎯 Best Practices

### **When to Use Shuffle Choices**

✅ **Good Use Cases:**
- In-person proctored exams (harder to cheat)
- Multiple testing sessions
- Practice exams with different layouts
- Question validity testing

❌ **Avoid When:**
- Choices have logical order (e.g., "All of the above")
- Sequential options (e.g., "1-5", "6-10", "11-15")
- Already randomized questions

### **When to Generate Versions**

✅ **Good Use Cases:**
- Large class sizes (>50 students)
- High-stakes exams (finals, certifications)
- Multiple exam rooms
- Morning and afternoon sessions
- Makeup exams

❌ **Avoid When:**
- Small class (<10 students)
- Low-stakes quizzes
- Open-book exams
- Take-home assignments

### **Combining Options**

| Scenario | Shuffle Choices | Generate Versions | Reason |
|----------|----------------|-------------------|---------|
| Final exam, 100 students | ☑ | ☑ | Maximum security |
| Midterm, 30 students | ☐ | ☑ | Different order sufficient |
| Practice quiz | ☑ | ☐ | Help students practice |
| Take-home exam | ☐ | ☐ | No need for randomization |

---

## 🧪 Testing & Validation

### **Run Enhanced Tests**

```powershell
python test_export_enhanced.py
```

**Expected Output:**
```
✅ Shuffle Choices - PASSED
✅ Version Generation - PASSED
✅ DOCX with Shuffle - PASSED
✅ DOCX with Versions A & B - PASSED
✅ PDF with Versions A & B - PASSED

Generated test files:
- test_shuffle.docx
- test_versions.docx
- test_versions.pdf
```

### **Manual Verification Checklist**

For **Shuffled Exports**:
- [ ] Open test_shuffle.docx
- [ ] Check MCQ choices are in different order
- [ ] Verify correct answer letter changed
- [ ] Confirm answer key matches shuffled choices
- [ ] Check non-MCQ questions unchanged

For **Version A & B**:
- [ ] Open test_versions.docx
- [ ] Find "Version A" header
- [ ] Check question order
- [ ] Find "ANSWER KEY - Version A"
- [ ] Verify answers match Version A questions
- [ ] Find "Version B" header (different order)
- [ ] Find "ANSWER KEY - Version B"
- [ ] Verify answers match Version B questions

---

## 🔧 Technical Details

### **Shuffle Algorithm**

```python
def _shuffle_mcq_choices(question, seed=None):
    """
    1. Extract choices: ['A', 'B', 'C', 'D']
    2. Note correct answer position: B (index 1)
    3. Create pairs: [(choice, is_correct), ...]
    4. Shuffle pairs randomly
    5. Rebuild choices array
    6. Find new correct answer position
    7. Update correct_answer letter
    """
```

**Properties:**
- Fisher-Yates shuffle algorithm
- O(n) time complexity
- Uniform distribution
- Seed-able for reproducibility

### **Version Generation Algorithm**

```python
def generate_exam_versions(questions, num_versions=2):
    """
    For each version:
    1. Deep copy questions
    2. Shuffle question order (optional)
    3. Renumber questions (1, 2, 3, ...)
    4. Shuffle MCQ choices (optional)
    5. Update correct_answer letters
    6. Return (version_label, questions)
    """
```

**Properties:**
- Independent versions (no cross-contamination)
- Maintains point totals
- Preserves question metadata
- Different random seed per version

### **File Structure**

**Single Version DOCX:**
```
Header (Title, Course, Instructor, Date)
Instructions
Total Points
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Questions (1, 2, 3, ...)
[PAGE BREAK]
ANSWER KEY
Answers with Bloom levels
```

**Multiple Versions DOCX:**
```
Version A Header
Version A Instructions
Version A Questions
[PAGE BREAK]
ANSWER KEY - Version A
[PAGE BREAK]
Version B Header
Version B Instructions
Version B Questions
[PAGE BREAK]
ANSWER KEY - Version B
```

---

## 📚 Related Documentation

- [TQS_EXPORT_GUIDE.md](TQS_EXPORT_GUIDE.md) - Basic export features
- [TQS_EXPORT_QUICKREF.md](TQS_EXPORT_QUICKREF.md) - Quick reference
- [REGENERATE_DELETE_GUIDE.md](REGENERATE_DELETE_GUIDE.md) - Edit features

---

## ✅ Summary

### **What's Included:**

1. **Answer Key** ✅
   - Automatically in all DOCX/PDF exports
   - Bloom levels beside each answer
   - Separate page for easy printing

2. **Shuffle Choices** ✅
   - Randomize MCQ options (A, B, C, D)
   - Correct answer updated automatically
   - Original data never modified

3. **Version A & B** ✅
   - Same questions, different order
   - Shuffled MCQ choices
   - Separate answer keys
   - Single file export

### **Implementation Status:**

| Feature | DOCX | PDF | CSV | JSON |
|---------|------|-----|-----|------|
| Answer Key | ✅ | ✅ | N/A | N/A |
| Shuffle Choices | ✅ | ✅ | ❌ | ❌ |
| Version A & B | ✅ | ✅ | ❌ | ❌ |
| Bloom Levels | ✅ | ✅ | ✅ | ✅ |

### **Frontend Integration:**
- ✅ Checkbox toggles in Streamlit UI
- ✅ Clear option descriptions
- ✅ Success messages with version info
- ✅ No code changes needed by users

**All features production-ready!** 🎉
