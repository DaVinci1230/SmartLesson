# Excel Learning Outcomes Extraction - Fix Summary

## Problem
The Excel TOS parser failed to extract learning outcomes reliably from real-world Excel files that contained:
- Merged cells in title rows
- Blank separator rows
- Formatted totals and percentage rows
- Complex table structures with multiple sections

## Root Causes
1. **Simple text parsing** - Using raw openpyxl iteration without proper cell merging
2. **Inflexible header detection** - Assumed first row of data started immediately after header
3. **Poor row filtering** - Couldn't distinguish outcome rows from metadata/total rows
4. **Merged cell issues** - No forward-fill mechanism for merged cells

## Solution Implemented

### 1. Added Pandas for Robust Excel Processing
```python
import pandas as pd
```
- **Benefit**: Pandas automatically handles merged cells and provides proper data structures
- **Method**: `pd.read_excel()` with dynamic header detection

### 2. Dynamic Header Row Detection with Bloom Keywords
Created `_detect_header_row_in_df()` method that:
- Reads Excel without header first
- Searches for rows containing Bloom keywords: Remember, Understand, Apply, Analyze, Evaluate, Create
- Requires ≥2 Bloom keywords for confidence
- Works with any number of title rows before actual header

### 3. Flexible Learning Outcome Extraction
New `_extract_tos_from_dataframe()` method handles:
- **Merged cells**: Uses pandas `ffill()` to forward-fill outcome column
- **Empty rows**: Skipped automatically
- **Smart filtering**: Skips rows containing:
  - "total", "percentage", "percent", "sum", "subtotal", "mean", "average"
  - Purely numeric values (like totals or indices)
- **Outcome validation**: Only includes rows with actual Bloom distribution data

### 4. Improved Column Identification
- Normalized column names (lowercase, whitespace stripped)
- Flexible outcome column detection:
  - Looks for "outcome" or "learning" in column name
  - Falls back to first column if not explicit
- Maps Bloom levels to columns case-insensitively

### 5. Better Error Messages
- Clear error if no header found
- Specific error if no valid outcomes extracted
- Shows number of rows checked and reason for filtering

## Key Code Changes

### File: `services/tos_file_parser.py`

**Added imports:**
```python
import pandas as pd
```

**New methods:**
1. `_extract_tos_from_xlsx_file()` - Main entry point for pandas-based Excel parsing
2. `_detect_header_row_in_df()` - Dynamic header detection
3. `_extract_tos_from_dataframe()` - Core outcome extraction logic

**Updated method:**
- Deprecated fillna with 'method' parameter → use ffill() instead

## Testing
The parser now successfully handles:
- ✅ Excel files with title rows before header
- ✅ Merged cells in formatting rows
- ✅ Blank separator rows
- ✅ Totals and percentage rows (properly skipped)
- ✅ Complex real-world Excel formatting
- ✅ Flexible column naming and ordering

## Backward Compatibility
- ✅ JSON parsing unchanged
- ✅ PDF parsing unchanged
- ✅ DOCX parsing unchanged
- ✅ All existing tests pass
- ✅ Seamless integration with existing workflow

## Performance Impact
- Minimal: Pandas overhead is negligible for typical TOS files
- Excel files are typically small (<50 rows)
- Improved reliability worth any minor perf trade-off

## Example: Complex Excel File Handling

```
Row 1: "Assessment Specification"  (title - merged cells)
Row 2: "2025-2026"                  (title - merged cells)
Row 3: ""                           (empty separator)
Row 4: "Learning Outcome" | "Remember" | ... (header detected here)
Row 5: "Identify concepts" | 3 | 1 | 0 | ...  (outcome)
Row 6: "Analyze behavior" | 1 | 2 | 3 | ...   (outcome)
Row 7: ""                           (empty separator)
Row 8: "TOTAL" | 4 | 3 | 3 | ...   (skipped - contains "total")
Row 9: "Percentage" | 50% | %...    (skipped - contains "percentage")
```

Result: 2 outcomes correctly extracted, totals/percentages skipped.
