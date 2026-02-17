# TQS Enhancement: File Upload Integration Guide

## Overview

This document describes the new TQS (Test Question Specification) generation feature that allows users to upload external TOS files in addition to using internally generated TOS.

### What's New?

✅ **Radio selection**: Choose between "Use Generated TOS" or "Upload TOS from File"
✅ **File upload support**: JSON, PDF, DOCX formats
✅ **Automatic parsing**: Extract TOS structure from uploaded files
✅ **Flexible test types**: Select question type (MCQ, Essay, Problem Solving, Mixed)
✅ **Seamless integration**: Uploaded TOS works with existing TQS generator
✅ **No breaking changes**: Existing workflow fully preserved

---

## Architecture Overview

### Data Flow

```
┌─────────────────┐
│  User selects   │
│  TOS source     │
└────────┬────────┘
         │
    ┌────▼──────────────────┐
    │                       │
┌───▼──────────────┐   ┌────▼─────────────────┐
│ Use Generated    │   │ Upload TOS from File  │
│ TOS (existing)   │   │                       │
└───┬──────────────┘   └────┬─────────────────┘
    │                        │
    │ Has assigned_slots     │ File upload
    │ from TOS dialog        │ → Parse
    │                         │ → Validate
    │                         │ → Convert to slots
    │                         │
    └────────┬────────────────┘
             │
        ┌────▼──────────────────────────────────┐
        │ Both paths produce assigned_slots      │
        │ - Same data structure                  │
        │ - Same pipeline to TQS generator       │
        └────┬─────────────────────────────────┘
             │
        ┌────▼──────────────────┐
        │  Select test type     │
        │  (MCQ, Essay, etc)    │
        └────┬─────────────────┘
             │
        ┌────▼──────────────────┐
        │ Generate Test          │
        │ Questions with AI      │
        └────────────────────────┘
```

### Session State Management

New session state variables:

```python
st.session_state.tqs_tos_source
    # "generated" or "uploaded"
    
st.session_state.uploaded_tos_data
    # Dict with parsed TOS structure
    # None if not uploaded
    
st.session_state.uploaded_tqs_assigned_slots
    # List of slots converted from uploaded TOS
    # None if not created yet
```

---

## User Workflow

### Path 1: Using Generated TOS (Existing)

```
1. Course/Syllabus tab → Input course info
2. Learning Outcomes tab → Add outcomes with hours
3. Assessment Profile tab → Configure Bloom distribution
4. Generate TOS tab → Create TOS matrix
5. Generate TQS tab:
   a. Select "Use Generated TOS"
   b. Click "Generate Test Questions"
   c. Review and export
```

### Path 2: Uploading TOS File (New)

```
1. Course/Syllabus tab → Input course info (optional)
2. Generate TQS tab:
   a. Select "Upload TOS from File"
   b. Upload JSON/PDF/DOCX file
   c. System parses and validates
   d. Select test type (MCQ, Essay, etc)
   e. Set points per item
   f. Click "Confirm TOS Source"
   g. Click "Generate Test Questions"
   h. Review and export
```

---

## Component Details

### 1. TOS Source Selection

**Location**: TQS tab, Step 1

```python
tos_source = st.radio(
    "Choose TOS source:",
    ["Use Generated TOS (from system)", "Upload TOS from File"]
)
```

**Behavior**:
- Shows radio buttons for clear selection
- Updates session state: `tqs_tos_source`
- Subsequent UI changes based on selection

### 2. File Upload Handler

**Location**: TQS tab, Step 1 (if "Upload TOS from File" selected)

```python
uploaded_file = st.file_uploader(
    "Choose TOS file",
    type=["json", "pdf", "docx"]
)
```

**Process**:
1. Accepts file in supported format
2. Reads file bytes
3. Calls `parse_tos_file()` from `tos_file_parser.py`
4. Stores parsed data in session state if valid
5. Shows validation summary

### 3. TOS Validation

**Module**: `services/tos_file_parser.py`

```python
def validate_tos_for_tqs_generation(tos_data):
    """
    Checks:
    - learning_outcomes not empty
    - tos_matrix not empty
    - Bloom distribution complete
    - total_items > 0
    """
    return (is_valid, message)
```

**Validation Checks**:
✅ All required fields present
✅ Non-empty outcomes list
✅ Non-empty TOS matrix
✅ All Bloom levels in distribution
✅ Item count > 0

### 4. Test Type Selection

**Location**: TQS tab, Step 2 (if file uploaded)

```python
test_type = st.selectbox(
    "Question Type for Generated Questions:",
    ["Multiple Choice", "Essay", "Problem Solving", "Mixed"]
)

points_per_item = st.number_input(
    "Points per Item:",
    min_value=0.5,
    value=1.0,
    step=0.5
)
```

**Purpose**:
- Define how questions will be generated
- Set point value per question
- Used in `convert_tos_to_assigned_slots()`

### 5. TOS to Slots Conversion

**Module**: `services/tos_file_parser.py`, function `convert_tos_to_assigned_slots()`

```python
def convert_tos_to_assigned_slots(
    tos_data,
    question_type,
    points_per_item
):
    """
    Converts:
    TOS matrix (Bloom × Outcome → count)
    →
    Assigned slots (list of {outcome, bloom, type, points})
    
    Creates one slot per item in TOS matrix
    """
    return (success, assigned_slots or error_message)
```

**Output Format**:
```python
[
    {
        "outcome_id": 0,
        "outcome": "Identify photosynthesis components",
        "outcome_text": "...",  # Same as outcome, for compatibility
        "bloom": "Remember",
        "type": "Multiple Choice",  # Mapped from selection
        "points": 1.0
    },
    ...
]
```

### 6. TQS Generation

**Module**: `services/tqs_service.py`, function `generate_tqs()`

```python
tqs = generate_tqs(
    assigned_slots=assigned_slots,
    api_key=os.environ.get("GEMINI_API_KEY"),
    shuffle=True
)
```

**Compatible with**:
- Slots from generated TOS
- Slots from uploaded TOS
- Same AI generation logic
- Same output format

---

## File Parsing Details

### JSON Parser

**Format**: Direct JSON structure (see TOS_FILE_UPLOAD_GUIDE.md for examples)

```python
def _parse_json(self, file_content, file_name):
    """
    1. Decode UTF-8
    2. Parse JSON
    3. Validate structure
    4. Return normalized data
    """
```

**Validation**: Strict - all fields must be properly formatted

### PDF Parser

**Format**: Extracted text from tables

```python
def _parse_pdf(self, file_content, file_name):
    """
    1. Read PDF with PyPDF2
    2. Extract text from all pages
    3. Parse tables from text
    4. Map to TOS structure
    5. Return normalized data
    """
```

**Requirements**:
- Selectable text (not image-based)
- Well-structured table
- Clear Bloom level headers
- Numeric item counts

**Limitations**:
- Basic text extraction (not guaranteed accurate)
- Recommended: use JSON format instead

### DOCX Parser

**Format**: Tables in Word document

```python
def _parse_docx(self, file_content, file_name):
    """
    1. Open DOCX with python-docx
    2. Find tables
    3. Extract headers and data
    4. Map to TOS structure
    5. Return normalized data
    """
```

**Expected Structure**:
```
| Learning Outcome | Remember | Understand | Apply | ... |
|-----|-----|-----|-----|---|
| Outcome A | 2 | 2 | 1 | ... |
| Outcome B | 1 | 2 | 1 | ... |
```

---

## Error Handling

### File Upload Errors

**Invalid Format**:
```
❌ Failed to parse TOS file: 
[specific error message]
```

**Solutions**:
1. Check file extension (.json, .pdf, .docx)
2. For JSON: validate with jsonlint.com
3. For PDF/DOCX: verify table structure matches expected format

### Validation Errors

**Missing Required Fields**:
```
❌ TOS validation failed: 
No learning outcomes found in TOS
```

**Solutions**:
1. Ensure outcomes list is not empty
2. Check field names: "text" or "description"
3. Verify TOS matrix is not empty

**Item Count Issues**:
```
❌ TOS contains no items (total_items = 0)
```

**Solutions**:
1. Check TOS matrix values are > 0
2. Verify Bloom distribution is not all zeros
3. Ensure all outcome rows have at least one item

### Conversion Errors

**No Slots Generated**:
```
❌ No slots generated from TOS
```

**Solutions**:
1. Verify TOS has items (total_items > 0)
2. Check outcome mappings in matrix
3. Ensure Bloom levels are present

---

## Code Integration Points

### Services Modified/Created

| File | Purpose | Changes |
|------|---------|---------|
| `services/tos_file_parser.py` | TOS parsing & validation | **NEW** |
| `services/tos_validation.py` | Advanced validation | **NEW** |
| `app.py` | UI integration | **MODIFIED** |

### Imports Added to app.py

```python
from services.tos_file_parser import (
    TOSFileParser,
    validate_tos_for_tqs_generation,
    convert_tos_to_assigned_slots,
    parse_tos_file
)
```

### No Breaking Changes

✅ Existing TOS generation workflow unchanged
✅ Existing TQS generation from internal TOS unchanged
✅ Database/session state compatible
✅ Backward compatible with saved sessions

---

## Data Structure Reference

### Parsed TOS Structure (Output of parse_tos_file)

```python
{
    "learning_outcomes": [
        {
            "id": 0,
            "text": "str",
            "hours": float  # optional
        }
    ],
    "bloom_distribution": {
        "Remember": int,      # percentage or count
        "Understand": int,
        "Apply": int,
        "Analyze": int,
        "Evaluate": int,
        "Create": int
    },
    "tos_matrix": {
        "Remember": {
            "0": int,   # outcome_id: item_count
            "1": int,
            ...
        },
        "Understand": {...},
        ...
    },
    "total_items": int,
    "total_points": int,  # optional
    "metadata": {
        "course_code": str,  # optional
        "course_title": str,
        "file_name": str,    # auto-populated
        "parsed_at": str,    # ISO timestamp
        "parsing_method": str  # "json" / "docx_table" / "text_extraction_basic"
    }
}
```

### Assigned Slots Structure (Output of convert_tos_to_assigned_slots)

```python
[
    {
        "outcome_id": int,
        "outcome": str,           # Learning outcome text
        "outcome_text": str,      # Same, for compatibility
        "bloom": str,             # "Remember", "Understand", etc
        "type": str,              # "Multiple Choice", "Essay", etc
        "points": float           # Points per item
    },
    ...
]
```

---

## Testing Checklist

- [ ] User can select "Use Generated TOS" and generate TQS from system
- [ ] User can select "Upload TOS from File"
- [ ] JSON file upload works and validates
- [ ] PDF file upload works (if PyPDF2 installed)
- [ ] DOCX file upload works (if python-docx installed)
- [ ] Uploaded TOS shows correct summary (outcomes, items, bloom %)
- [ ] Test type selection appears after file upload
- [ ] "Confirm TOS Source" button converts to slots correctly
- [ ] Generated TQS from uploaded TOS has correct count and format
- [ ] Exported TQS JSON includes correct metadata
- [ ] Error messages are clear and actionable
- [ ] Both paths (generated and uploaded) produce identical TQS output format

---

## Performance Considerations

### Parsing Performance

| Format | Speed | Reliability |
|--------|-------|-------------|
| JSON | Fast | Very High |
| PDF | Slow | Medium |
| DOCX | Medium | High |

**Recommendation**: JSON format for large datasets (>50 outcomes)

### Session State

- Uploaded TOS cached in `st.session_state.uploaded_tos_data`
- Re-uploading same file doesn't cause re-parsing
- Clear session state if switching between sources

---

## Dependencies

### Required (for JSON support)
- Python 3.8+
- Streamlit
- (No additional dependencies for JSON)

### Optional (for PDF/DOCX)
```bash
pip install PyPDF2          # For PDF parsing
pip install python-docx     # For DOCX parsing
```

### Installation

```bash
# In your project directory
pip install -r requirements.txt
# Or individually:
pip install PyPDF2
pip install python-docx
```

---

## Future Enhancements

Potential improvements:
1. Excel (.xlsx) format support
2. CSV format support
3. Direct database TOS import
4. Batch file processing
5. TOS template creation/download
6. Advanced table detection (OpenCV for PDF)
7. OCR for image-based PDFs
8. Merge multiple TOS files

---

## Support & Troubleshooting

### Common Issues

**"PDF parsing not available"**
- Solution: `pip install PyPDF2`

**"DOCX parsing not available"**
- Solution: `pip install python-docx`

**"Cannot detect file type"**
- Solution: Use correct extension (.json, .pdf, .docx)

**"Invalid JSON file"**
- Solution: Validate at jsonlint.com, check UTF-8 encoding

**"Could not find Bloom levels in table headers"**
- Solution: Use exact spelling: Remember, Understand, Apply, Analyze, Evaluate, Create

For more details, see **TOS_FILE_UPLOAD_GUIDE.md**
