# TOS Template Rendering Refactor - Complete Documentation

## Overview

The Table of Specifications (TOS) rendering system has been refactored to enforce a **strict institutional template format** instead of dynamically generating tables based on data length.

### Key Benefits
- ✅ **Consistent Layout**: Same structure regardless of data volume
- ✅ **Professional Appearance**: Matches institutional printed forms
- ✅ **Always Complete**: RBT, Items, Totals, and Roundings always rendered
- ✅ **Separation of Concerns**: AI logic stays in `ai_service.py`, rendering in `tos_template_renderer.py`
- ✅ **Maintainability**: Clear sections with explicit comments
- ✅ **Scalability**: Easy to modify template without touching AI code

---

## Architecture Overview

### Files Modified/Created

```
services/
├── tos_template_renderer.py       [NEW] Fixed template rendering logic
├── export_service.py               [UPDATED] Now delegates to renderer
└── ai_service.py                   [UNCHANGED] AI logic untouched
```

### Processing Pipeline

```
AI Generation (ai_service.py)
    ↓
    ↓ (supplies data: outcomes, tos_matrix)
    ↓
Fixed Template Renderer (tos_template_renderer.py)
    ├─ 1. Render Header Section
    ├─ 2. Create Fixed Table Headers
    ├─ 3. Inject Data into Fixed Cells
    ├─ 4. Compute Totals & Roundings
    ├─ 5. Render Footer Rows
    ├─ 6. Apply Formatting
    └─ Output: Excel File (BytesIO)
```

---

## Section 1: Header Rendering

### Function: `render_header_section(ws, meta)`

**Purpose**: Render institutional metadata above the table.

**Fixed Structure**:
- Row 1: "TABLE OF SPECIFICATIONS" (centered title)
- Rows 3-7: Left metadata (Name, Subject Code, Title, Total Items, Total Points)
- Rows 3-6: Right metadata (Semester, Class Schedule, Course, Exam Date)

**Example Output**:
```
┌─────────────────────────────────────────┐
│     TABLE OF SPECIFICATIONS             │
├─────────────────────────────────────────┤
│ Name: John Doe                           │
│ Subject Code: BIOL-101                   │
│ Descriptive Title: General Biology       │
│ Total Test Items: 50                     │
│ Total Points: 100                        │
│                                         │
│           (right side)                   │
│ Semester: 1st                            │
│ Class Schedule: M/W/F 10-11am            │
│ Course: Biology Laboratory               │
│ Exam Date: 2026-02-20                    │
```

**Data Source**: 
- Comes from `meta` dictionary passed to export function
- Keys: `name`, `subject_code`, `title`, `semester`, `schedule`, `course`, `exam_date`

**Key Implementation Details**:
- Uses `merge_cells()` to span metadata across columns
- Applies borders and font styling for professional appearance
- Left side uses columns A-B, right side uses columns T-U

---

## Section 2: Fixed Grid Construction

### Function: `create_fixed_table_headers(ws, start_row=9)`

**Purpose**: Create the fixed table header structure with ALL columns, regardless of data.

**Fixed Column Structure**:
```
Col 1: Course Content
Col 2: Learning Outcomes (from the Syllabus)
Col 3: RBT (Revised Bloom's Taxonomy)
Col 4: No. of Hours Taught

Cols 5-7:   REMEMBERING (Items | Pts | Item No.)
Cols 8-10:  UNDERSTANDING (Items | Pts | Item No.)
Cols 11-13: APPLYING (Items | Pts | Item No.)
Cols 14-16: ANALYZING (Items | Pts | Item No.)
Cols 17-19: EVALUATING (Items | Pts | Item No.)
Cols 20-22: CREATING (Items | Pts | Item No.)

Col 23: ITEMS (total)
Col 24: POINTS (total)
```

**Two-Row Header**:
- **Row 1** (start_row=9): Main category headers
  - "REMEMBERING", "UNDERSTANDING", etc. (spans 3 columns each)
- **Row 2** (start_row+1=10): Sub-headers
  - "No. of Items", "Pts", "Item No." (repeated for each Bloom level)

**Return Value**:
Dictionary mapping Bloom levels to starting columns:
```python
col_map = {
    "remembering": 5,
    "understanding": 8,
    "applying": 11,
    "analyzing": 14,
    "evaluating": 17,
    "creating": 20,
    "items_col": 23,
    "points_col": 24
}
```

**Styling**:
- Bold font, gray background (PatternFill)
- Center alignment, wrap text enabled
- Thin borders on all cells

---

## Section 3: Data Injection

### Function: `inject_outcome_data(ws, col_map, outcomes, tos_matrix, start_row=11)`

**Purpose**: Inject AI-generated data into the fixed grid cells.

**Key Feature**: **ALWAYS renders exactly `MIN_DATA_ROWS` rows** (default: 20)
- If outcomes < 20: remaining rows are empty but formatted
- If outcomes > 20: only first 20 are shown (configurable)
- Layout never collapses; structure always visible

**Data Injection Process**:

1. **Normalize TOS Matrix**:
   ```python
   normalized_tos = {
       k.strip().lower(): v
       for k, v in tos_matrix.items()
   }
   ```
   Ensures case-insensitive lookups

2. **For Each Row (0 to MIN_DATA_ROWS-1)**:
   - **Col A**: Course Content (usually blank, user fills)
   - **Col B**: Learning Outcome text
   - **Col C**: RBT (Bloom level)
   - **Col D**: No. of Hours Taught
   
   - **For Each Bloom Level**:
     - **Items**: Count from tos_matrix[bloom][row_idx]
     - **Pts**: Same as Items (default: 1 point per item)
     - **Item No.**: Empty (teacher fills manually)
   
   - **Row Total**: Sum of items across all Bloom levels
   - **Row Points**: Sum of points across all Bloom levels

3. **Apply Formatting**:
   - Thin borders on all cells
   - Center alignment
   - Row height: 20px (fixed)

**Return Values**:
```python
(last_filled_row, row_totals)

row_totals = {
    0: {"items": 5, "points": 5},
    1: {"items": 8, "points": 8},
    ...
}
```

**Example Data Flow**:
```
Input AI Data:
{
    "outcomes": [
        {"text": "Identify...", "hours": 2, "bloom_level": "Remember"},
        {"text": "Explain...", "hours": 3, "bloom_level": "Understand"}
    ],
    "tos_matrix": {
        "remember": {0: 3, 1: 0},
        "understand": {0: 0, 1: 4},
        ...
    }
}

↓ Injection ↓

Outcome 1: Outcome 1 | Identify... | Remember | 2 | [3] [3] [] | [0] [0] [] | ... | 3 | 3
Outcome 2: Outcome 2 | Explain... | Understand | 3 | [0] [0] [] | [4] [4] [] | ... | 4 | 4
Empty 3:  Empty 3 | | | | [] [] [] | [] [] [] | ... | 0 | 0
...
Empty 20: Empty 20 | | | | [] [] [] | [] [] [] | ... | 0 | 0
```

---

## Section 4: Totals & Roundings Computation

### Function: `compute_totals_and_roundings(col_map, outcomes, row_totals, tos_matrix)`

**Purpose**: Calculate column totals and rounding adjustments.

**Computation Logic**:

1. **For Each Bloom Level**:
   - Sum items across all outcomes
   - Sum points across all outcomes (typically equal to items)
   - Calculate rounded value: `round(items_sum)`

2. **Grand Totals**:
   - Sum all Bloom items → `grand_total_items`
   - Sum all Bloom points → `grand_total_points`
   - Round both to nearest integer

**Return Structure**:
```python
{
    "bloom_totals": {
        "remember": {"items": 10, "points": 10, "rounded": 10},
        "understand": {"items": 15, "points": 15, "rounded": 15},
        "apply": {...},
        "analyze": {...},
        "evaluate": {...},
        "create": {...}
    },
    "grand_total_items": 60,
    "grand_total_points": 60
}
```

**Rounding Strategy**:
- Uses Python's `round()` function (rounds to nearest even for .5)
- Applied per Bloom level and grand total
- Ensures printed totals are whole numbers

**Example**:
```
Input Items:
  Remember: 9.5 items → Rounded: 10 items (for printing)
  Understand: 14.7 items → Rounded: 15 items
  Apply: 12.2 items → Rounded: 12 items
  Analyze: 11.3 items → Rounded: 11 items
  Evaluate: 8.9 items → Rounded: 9 items
  Create: 4.4 items → Rounded: 4 items
  ────────────────────────────────────
  Grand Total: 60.0 items → Rounded: 60 items
```

---

## Section 5: Totals & Roundings Rows

### Function: `render_totals_and_roundings(ws, col_map, totals_data, current_row)`

**Purpose**: Render the ROUNDINGS and TOTAL rows at the bottom of the table.

**Two-Row Footer**:

1. **ROUNDINGS Row**:
   ```
   [blank] | ROUNDINGS | [rounded items] | [rounded pts] | [] | ... | [total items] | [total pts]
   ```
   - Shows rounded values per Bloom level
   - Bold font, gray background
   - Gap before this row (`current_row + 2`)

2. **TOTAL Row**:
   ```
   [blank] | TOTAL | [total items] | [total pts] | [] | ... | [grand total items] | [grand total pts]
   ```
   - Shows actual totals (not rounded)
   - Bold font (size 11)
   - Immediately after ROUNDINGS row

**Example Output**:
```
┌──────────┬───────────┬───────────┬──────────┬─────┬──────────┐
│          │ ROUNDINGS │ 10        │ 10       │ ... │ 60       │
├──────────┼───────────┼───────────┼──────────┼─────┼──────────┤
│          │ TOTAL     │ 10        │ 10       │ ... │ 60       │
└──────────┴───────────┴───────────┴──────────┴─────┴──────────┘
```

**Styling**:
- Bold headers
- Thin borders
- Fixed row height: 20px (ROUNDINGS), 22px (TOTAL)
- Center alignment

---

## Section 6: Formatting Enforcement

### Function: `apply_fixed_formatting(ws)`

**Purpose**: Apply fixed column widths and row heights to entire worksheet.

**Fixed Dimensions**:
- **Column Width**: 15 units (all columns A-X)
- **Row Heights**:
  - Header rows (1-8): 20px
  - Data rows: 20px (set during injection)
  - Footer rows: 20-22px (set during rendering)

**No Dynamic Resizing**:
- Widths are hardcoded, not auto-fitted
- Heights are explicitly set, not auto-adjusted
- Ensures consistent printing behavior

---

## Section 7: Main Export Function

### Function: `export_tos_fixed_template(meta, outcomes, tos_matrix, total_items, total_points)`

**Purpose**: Master orchestration function combining all sections.

**Complete Workflow**:

```python
def export_tos_fixed_template(meta, outcomes, tos_matrix, total_items, total_points):
    # Step 1: Create workbook
    wb = Workbook()
    ws = wb.active
    
    # Step 2: Render header
    render_header_section(ws, meta_enriched)
    
    # Step 3: Create fixed table headers
    col_map = create_fixed_table_headers(ws, start_row=9)
    
    # Step 4: Inject outcome data
    last_data_row, row_totals = inject_outcome_data(
        ws, col_map, outcomes, tos_matrix, start_row=11
    )
    
    # Step 5: Compute totals
    totals_data = compute_totals_and_roundings(
        col_map, outcomes, row_totals, tos_matrix
    )
    
    # Step 6: Render footers
    render_totals_and_roundings(
        ws, col_map, totals_data, last_data_row + 2
    )
    
    # Step 7: Apply formatting
    apply_fixed_formatting(ws)
    
    # Step 8: Output
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
```

**Input Parameters**:
```python
meta = {
    "name": "Instructor Name",
    "subject_code": "BIOL-101",
    "title": "General Biology",
    "semester": "1st Semester",
    "schedule": "M/W/F 10-11am",
    "course": "Biology 101",
    "exam_date": "2026-02-20"
}

outcomes = [
    {"text": "Identify...", "hours": 2, "bloom_level": "Remember"},
    {"text": "Explain...", "hours": 3, "bloom_level": "Understand"},
    ...
]

tos_matrix = {
    "remember": {0: 3, 1: 0, 2: 2, ...},
    "understand": {0: 0, 1: 4, 2: 1, ...},
    ...
}

total_items = 50
total_points = 100
```

**Output**: `BytesIO` Excel file

---

## Usage in app.py

### Current Integration:

```python
# Import the new function
from services.export_service import export_tos_exact_format
# (Or directly: from services.tos_template_renderer import export_tos_fixed_template)

# Call during TOS export
excel = export_tos_exact_format(
    meta={
        "name": instructor,
        "subject_code": course_code,
        "title": course_title,
        "semester": semester,
        "schedule": "",
        "course": "",
        "exam_date": "",
    },
    outcomes=st.session_state.generated_tos["outcomes"],
    tos_matrix=st.session_state.generated_tos["tos_matrix"],
    total_items=total_items,
    total_points=total_points
)

# Download in Streamlit
st.download_button(
    label="⬇ Export TOS as Excel",
    data=excel,
    file_name="TOS.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ AI Service (ai_service.py) - UNCHANGED                      │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ Input: Competencies + Bloom Distribution                ││
│ │ Output:                                                   ││
│ │  - outcomes: [{"text": "...", "hours": X, ...}, ...]    ││
│ │  - tos_matrix: {"remember": {0: 3, 1: 0, ...}, ...}     ││
│ │  - total_items: 50                                        ││
│ │  - total_points: 100                                      ││
│ └──────────────────────────────────────────────────────────┘│
└──────────────────────┬──────────────────────────────────────┘
                       │ (Data passed to renderer)
                       ↓
┌──────────────────────────────────────────────────────────────┐
│ TOS Template Renderer (tos_template_renderer.py)            │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ 1. render_header_section()          → Metadata header   ││
│ │ 2. create_fixed_table_headers()     → Fixed columns     ││
│ │ 3. inject_outcome_data()            → Data injection    ││
│ │ 4. compute_totals_and_roundings()   → Calculations      ││
│ │ 5. render_totals_and_roundings()    → Footer rows       ││
│ │ 6. apply_fixed_formatting()         → Layout fix        ││
│ │ 7. Output Excel file (BytesIO)      → Binary Excel      ││
│ └──────────────────────────────────────────────────────────┘│
└──────────────────────┬──────────────────────────────────────┘
                       │ (BytesIO Excel data)
                       ↓
┌──────────────────────────────────────────────────────────────┐
│ Streamlit (app.py)                                           │
│ ┌──────────────────────────────────────────────────────────┐│
│ │ st.download_button() → User downloads TOS.xlsx           ││
│ └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## Benefits of This Refactoring

| Aspect | Before | After |
|--------|--------|-------|
| **Layout** | Dynamic, expands with data | Fixed, always same size |
| **Content Columns** | Sometimes missing | Always present |
| **RBT Column** | Sometimes hidden | Always visible |
| **Items Column** | Sometimes hidden | Always visible |
| **Roundings Row** | Not shown | Always shown |
| **Total Row** | Sometimes incomplete | Always complete |
| **Width/Height** | Auto-fitted, inconsistent | Fixed, professional |
| **Separation** | Rendering mixed with AI | Clean separation |
| **Testing** | Hard to verify structure | Easy to validate fixed layout |
| **Maintenance** | Changes affect AI logic | Isolated to renderer |

---

## Configuration & Customization

### Change Minimum Rows
```python
# In tos_template_renderer.py, line 26:
MIN_DATA_ROWS = 20  # Change to desired number
```

### Change Column Widths
```python
# In apply_fixed_formatting(), change:
ws.column_dimensions[col_letter].width = 15  # Change value
```

### Change Row Heights
```python
# In various functions:
ws.row_dimensions[row_num].height = 20  # Change value
```

### Change Colors/Fonts
```python
# In render_header_section() or other functions:
header_fill = PatternFill(start_color="D3D3D3", ...)  # Change color code
```

---

## Testing the Refactored System

### Manual Test:
1. Open SmartLesson Streamlit app
2. Go to **Assessment Generator → Generate TOS**
3. Generate a TOS with AI
4. Click **⬇ Export TOS as Excel**
5. Open downloaded file
6. **Verify**:
   - ✅ Header metadata visible
   - ✅ All 6 Bloom columns visible
   - ✅ RBT column visible
   - ✅ At least 20 content rows visible (even if empty)
   - ✅ ROUNDINGS row visible
   - ✅ TOTAL row visible
   - ✅ Column widths consistent
   - ✅ Row heights consistent
   - ✅ Professional appearance (printable)

### Automated Test (Optional):
```python
# tests/test_tos_template.py
def test_fixed_template_structure():
    # Verify always has MIN_DATA_ROWS
    # Verify all columns present
    # Verify TOTAL and ROUNDINGS rows present
    # Verify header contains all metadata
```

---

## Backward Compatibility

The old `export_tos_exact_format()` function still exists and now delegates to the new renderer:

```python
def export_tos_exact_format(...):
    """DEPRECATED: Use export_tos_fixed_template() instead."""
    return export_tos_fixed_template(...)
```

This ensures existing code in `app.py` continues to work without changes.

---

## Summary

The refactored TOS rendering system provides:
1. **Fixed institutional template** that always maintains structure
2. **Separation of concerns**: AI logic separate from rendering
3. **Professional output** matching institutional standards
4. **Always complete**: RBT, Items, Totals, Roundings always visible
5. **Maintainable code** with clear sections and comments
6. **Easy customization** without affecting AI logic

**No changes needed in `ai_service.py` or business logic.**

---

## Questions & Support

For questions about the refactored system, refer to:
- **Header Rendering**: See `render_header_section()` docs
- **Grid Structure**: See `create_fixed_table_headers()` docs
- **Data Injection**: See `inject_outcome_data()` docs
- **Totals Logic**: See `compute_totals_and_roundings()` docs
- **Formatting**: See `apply_fixed_formatting()` docs
