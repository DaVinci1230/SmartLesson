# TQS Export - Quick Reference

## 📥 Export Buttons (Streamlit UI)

Navigate to "Generate TQS" → Scroll to "📥 Export Test Questions"

```
┌──────────────────────────────────────────────────────┐
│  📄 Export to DOCX  │  📕 Export to PDF              │
│  Professional Word  │  Print-ready PDF               │
│  document with      │  document with                 │
│  answer key         │  answer key                    │
├─────────────────────┼────────────────────────────────┤
│  📊 Export to CSV   │  📋 Export to JSON             │
│  Spreadsheet format │  Raw data format               │
│  for LMS import     │  for backup                    │
└──────────────────────────────────────────────────────┘
```

---

## 🎯 API Endpoints

### Export to DOCX
```bash
GET /api/export/docx?course_name=CS101&exam_title=Midterm&exam_term=Fall%202026&instructor_name=Dr.%20Smith
```

### Export to PDF
```bash
GET /api/export/pdf?course_name=CS101&exam_title=Final&exam_term=Spring%202026
```

### Export to CSV
```bash
GET /api/export/csv
```

---

## 📄 File Formats

### DOCX Output
```
✓ Header with course info
✓ Instructions section
✓ Formatted questions
✓ MCQ choices (A, B, C, D)
✓ Answer spaces
✓ Separate answer key page
✓ Bloom levels & points
```

### PDF Output
```
✓ Same as DOCX
✓ Professional typography
✓ Page breaks
✓ Print-ready
✓ Universal compatibility
```

### CSV Output
```
Columns:
- Question Number
- Question Text
- Question Type
- Option A, B, C, D
- Correct Answer
- Answer Key/Sample Answer
- Bloom Level
- Points
- Learning Outcome
```

---

## 🧪 Test Exports

```powershell
# Run test suite
python test_tqs_export.py

# Expected output:
✅ DOCX Export - PASSED
✅ PDF Export - PASSED
✅ CSV Export - PASSED
✅ Metadata Extraction - PASSED
```

---

## 📦 Dependencies

```
python-docx==0.8.11    ✅ Installed
reportlab==4.0.9       ✅ Installed
csv (built-in)         ✅ Available
```

---

## 💡 Quick Tips

1. **Generate questions first** before exporting
2. **DOCX** for editing and customization
3. **PDF** for printing and distribution
4. **CSV** for importing to LMS or databases
5. **JSON** for backup and programmatic access

---

## 🔧 File Locations

- **Service**: [services/tqs_export_service.py](services/tqs_export_service.py)
- **API Routes**: [api_server.py](api_server.py#L529-L706)
- **Frontend**: [app.py](app.py#L1549-L1690)
- **Tests**: [test_tqs_export.py](test_tqs_export.py)

---

## ⚡ Common Commands

```powershell
# Start Streamlit
streamlit run app.py

# Start API Server
python api_server.py

# Test exports
python test_tqs_export.py

# Install dependencies
pip install python-docx reportlab
```

---

## 📖 Full Documentation

See [TQS_EXPORT_GUIDE.md](TQS_EXPORT_GUIDE.md) for complete details!

---

**Status**: ✅ All features implemented and tested!
