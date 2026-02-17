# Enhanced Export Features - Quick Reference

## ✅ What's New

### 1. **Answer Key** (Always Included)
```
ANSWER KEY

Question 1: B - Paris  [Bloom: Remember | 1 pts]
Question 2: A [Bloom: Understand | 3 pts]
Question 3: See rubric [Bloom: Analyze | 10 pts]
```

### 2. **Shuffle MCQ Choices**
```
Original: A, B✓, C, D
Shuffled: C, A, D✓, B  (B became D)
```

### 3. **Version A & B**
```
One file contains:
- Version A (questions 1-10)
- Answer Key A
- Version B (questions in different order)
- Answer Key B
```

---

## 🎯 Quick Usage

### **In Streamlit UI:**

1. Generate TQS questions
2. Scroll to "📥 Export Test Questions"
3. Check options:
   - `☐ 🔀 Shuffle MCQ Choices`
   - `☐ 📋 Generate Multiple Versions (A & B)`
4. Click export button (DOCX, PDF, CSV, or JSON)
5. Download file

### **Option Combinations:**

| Shuffle | Versions | Result |
|---------|----------|--------|
| ☐ | ☐ | Standard export |
| ☑ | ☐ | Shuffled choices |
| ☐ | ☑ | Version A & B |
| ☑ | ☑ | Version A & B with shuffle |

---

## 💻 Code Examples

### **Shuffle Choices:**
```python
docx_buffer = tqs_export_service.export_to_docx(
    questions=questions,
    shuffle_choices=True
)
```

### **Generate Versions:**
```python
docx_buffer = tqs_export_service.export_to_docx(
    questions=questions,
    generate_versions=True,
    num_versions=2
)
```

### **Both:**
```python
docx_buffer = tqs_export_service.export_to_docx(
    questions=questions,
    shuffle_choices=True,
    generate_versions=True
)
```

---

## 🔒 Safety Guarantees

✅ **Original data NEVER modified**
✅ **Shuffle applies only to exports**
✅ **Deep copies used internally**
✅ **Reproducible with seeds**

---

## 🧪 Test Features

```powershell
# Run enhanced tests
python test_export_enhanced.py

# Expected output:
✅ Shuffle Choices - PASSED
✅ Version Generation - PASSED
✅ DOCX with Versions A & B - PASSED
✅ PDF with Versions A & B - PASSED
```

**Generated Files:**
- `test_shuffle.docx` - Single version with shuffle
- `test_versions.docx` - Version A & B
- `test_versions.pdf` - Version A & B

---

## 📊 Answer Key Format

**MCQ:**
```
Question 1: B - Paris  [Bloom: Remember | 1 pts]
```

**Short Answer:**
```
Question 2: Recursion is when...  [Bloom: Understand | 3 pts]
```

**Essay:**
```
Question 3: See grading rubric  [Bloom: Evaluate | 10 pts]
```

---

## 🎯 When to Use

### **Shuffle Choices:**
- ✅ In-person proctored exams
- ✅ Multiple testing sessions
- ✅ Practice exams
- ❌ Sequential options (1-5, 6-10)
- ❌ "All of the above" questions

### **Version A & B:**
- ✅ Large classes (50+ students)
- ✅ High-stakes exams
- ✅ Multiple rooms/sessions
- ✅ Makeup exams
- ❌ Small classes (<10 students)
- ❌ Take-home assignments

---

## 📁 File Locations

- **Service:** [services/tqs_export_service.py](services/tqs_export_service.py)
- **Frontend:** [app.py](app.py#L1549-L1700)
- **Tests:** [test_export_enhanced.py](test_export_enhanced.py)
- **Full Guide:** [ENHANCED_EXPORT_GUIDE.md](ENHANCED_EXPORT_GUIDE.md)

---

## ✨ Key Features

| Feature | Status | DOCX | PDF | CSV |
|---------|--------|------|-----|-----|
| Answer Key | ✅ | ✅ | ✅ | - |
| Bloom Levels | ✅ | ✅ | ✅ | ✅ |
| Shuffle Choices | ✅ | ✅ | ✅ | - |
| Version A & B | ✅ | ✅ | ✅ | - |

---

**Status:** ✅ All features implemented and tested!

See [ENHANCED_EXPORT_GUIDE.md](ENHANCED_EXPORT_GUIDE.md) for complete documentation.
