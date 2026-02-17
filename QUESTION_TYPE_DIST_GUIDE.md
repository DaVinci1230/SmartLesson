# Question Type Distribution Feature - Implementation Guide

## Overview

The Question Type Distribution feature extends SmartLesson's TOS (Table of Specifications) module to support:

1. **Question Type Definition**: Define assessment item types (MCQ, Essay, Problem Solving, etc.)
2. **Weighted Scoring**: Assign different point values to different item types
3. **Validation**: Ensure item counts match total test items exactly
4. **Total Points Computation**: Automatically calculate total points from question type distribution

This feature maintains **clear separation of concerns**:
- **Bloom's Distribution**: Controls WHAT knowledge is assessed (Remember, Understand, Apply, etc.)
- **Question Type Distribution**: Controls HOW items are formatted and weighted (MCQ vs Essay, point values, etc.)
- **TOS Blueprint**: Stores both distributions as the assessment specification

---

## Architecture

### Three Key Components

#### 1. **question_type_service.py** - Core Logic Module
Handles all question type distribution operations:

```
├── Data Models
│   ├── QuestionType dataclass
│   └── TOSWithQuestionTypes dataclass
├── Validation Functions
│   └── validate_question_type_distribution()
├── Computation Functions
│   ├── compute_total_points()
│   ├── compute_points_per_bloom_level()
└── Utility Functions
    ├── create_question_type()
    ├── get_default_question_types()
    └── format_question_types_for_display()
```

#### 2. **app.py** - UI Integration
New "Step 2: Question Type Distribution" in the Generate TOS tab with:
- Interactive question type editor (add/edit/delete)
- Real-time validation
- Summary metrics (items, points, validation status)
- Default question type templates

#### 3. **tos_template_renderer.py** - Export Enhancement
Updated to display "Total Number of Points" in TOS header (computed from question types)

---

## Data Model

### QuestionType
```python
@dataclass
class QuestionType:
    type: str              # e.g., "MCQ", "Essay", "Problem Solving"
    items: int            # Number of items of this type
    points_per_item: float  # Points per item
    
    def total_points(self) -> float:
        return self.items * self.points_per_item
```

### Extended TOS Structure
```python
{
    "metadata": {...},
    "outcomes": [...],
    "tos_matrix": {...},  # Bloom distribution (unchanged)
    "bloom_totals": {...},  # Bloom totals (unchanged)
    
    # NEW: Question Type Distribution
    "question_types": [
        {"type": "MCQ", "items": 40, "points_per_item": 1},
        {"type": "Essay", "items": 2, "points_per_item": 10},
        ...
    ],
    "total_items": 60,
    "total_points": 60  # Computed: sum(items × points_per_item)
}
```

---

## Validation Rules

The feature enforces three validation rules:

### Rule 1: Item Count Validation
**Sum of all Question Type Items = Total Test Items**

Example:
```
Total Items: 60
MCQ: 40 items
Essay: 2 items
Problem Solving: 18 items
-----------
Total: 60 ✅ VALID
```

### Rule 2: Type Configuration Validation
Each question type must have:
- Non-empty name
- At least 1 item (> 0)
- Positive points per item (> 0)
- No duplicate type names

### Rule 3: Computation Validation
If validation passes → TOS generation enabled
If validation fails → TOS generation disabled (button grayed out)

---

## Total Points Computation

### Formula
```
Total Points = Σ (No. of Items × Points Per Item)
```

### Example Calculation
| Question Type | Items | Points/Item | Subtotal |
|---|---|---|---|
| MCQ | 40 | 1 | 40 |
| Short Answer | 10 | 2 | 20 |
| Essay | 2 | 10 | 20 |
| Problem Solving | 8 | 3 | 24 |
| **TOTAL** | **60** | - | **104** |

Total Points = 40 + 20 + 20 + 24 = **104 points**

---

## UI Workflow

### Step 1: Define Total Test Items
Teacher enters expected number of test items
```
Total Number of Test Items: [60]
```

### Step 2: Question Type Distribution
Teacher configures question types:

#### 2a. Question Type Editor
Interactive table with columns:
- **Question Type**: Name (editable)
- **No. of Items**: Count (editable)
- **Points Per Item**: Weight (editable)
- **Action**: Delete button

#### 2b. Add New Type
Click "➕ Add Question Type" to add row with defaults

#### 2c. Summary Table
Displays all types with automatic calculation of subtotals:
```
Question Type    | No. of Items | Points Per Item | Total Points
MCQ              | 40           | 1               | 40
Essay            | 2            | 10              | 20
Problem Solving  | 18           | 2               | 36
TOTAL            | 60           | -               | 96
```

### Step 3: Validation Check
System displays:
- ✅ "Question type distribution is valid!" (if all rules pass)
- ❌ Error messages (if any validation rule fails)
- Real-time metrics:
  - Total Items (Expected): 60
  - Total Items (Configured): 60
  - Total Points (Computed): 96
  - Items Validation: ✅ Match

### Step 4: Generate TOS
"⚙ Generate TOS" button enabled only if validation passes

---

## Separation of Concerns

### What This Feature DOES
✅ Store question type distribution as part of TOS blueprint
✅ Validate item counts match total test items
✅ Compute total points from question type weights
✅ Display validation status and error messages
✅ Integrate with TOS export (show total points in header)

### What This Feature DOES NOT Do
❌ Generate actual test questions (future TQS module)
❌ Modify Bloom's Taxonomy distribution logic
❌ Change TOS matrix structure or column layout
❌ Handle AI question generation
❌ Manage test delivery or grading

### Why This Matters
TOS is a **blueprint** for assessment design. It answers:
- WHAT knowledge to assess? (Bloom's levels)
- HOW to assess? (Question types, point values)
- HOW MUCH? (Total items and total points)

Question generation (TQS) is separate and uses this blueprint.

---

## Integration Points

### 1. Session State Management
```python
st.session_state.question_types  # List of QuestionType objects
st.session_state.generated_tos["question_types"]  # Stored with TOS
st.session_state.generated_tos["total_points"]  # Computed total
```

### 2. TOS Export
Total Points from question types now appears in:
- TOS Excel header ("Total Number of Points")
- Can be used for test generation later

### 3. Bloom's Distribution (UNCHANGED)
- Bloom logic still works exactly as before
- Question types are SEPARATE from Bloom levels
- Both are stored in generated TOS

---

## Code Examples

### Creating Question Types Programmatically
```python
from services.question_type_service import (
    QuestionType,
    validate_question_type_distribution,
    compute_total_points
)

# Create types
types = [
    QuestionType("MCQ", 40, 1),
    QuestionType("Essay", 2, 10),
    QuestionType("Problem Solving", 18, 2)
]

# Validate
is_valid, errors = validate_question_type_distribution(types, total_items=60)
if is_valid:
    total_pts = compute_total_points(types)
    print(f"Total Points: {total_pts}")  # Output: 96.0
```

### Adding to TOS
```python
st.session_state.generated_tos = {
    "outcomes": [...],
    "tos_matrix": {...},
    "bloom_totals": {...},
    # NEW:
    "question_types": st.session_state.question_types,
    "total_items": 60,
    "total_points": compute_total_points(st.session_state.question_types)
}
```

### Exporting with Total Points
```python
excel = export_tos_exact_format(
    meta={
        ...
        "total_items": 60,
        "total_points": 96  # From question type distribution
    },
    ...
)
```

---

## Default Question Types

The system provides these default templates (editable):

1. **Multiple Choice (MCQ)** - 1 point each
2. **Short Answer** - 2 points each
3. **Essay** - 5 points each
4. **Problem Solving** - 3 points each
5. **Drawing/Diagram** - 2 points each
6. **Identification** - 1 point each

Teachers can:
- Rename any type
- Change item counts and point values
- Delete unused types
- Add custom types

---

## Error Handling

### Validation Errors Displayed
1. **"At least one question type must be defined."**
   - Fix: Add question type row

2. **"Sum of question type items (X) must equal total test items (Y)."**
   - Fix: Adjust item counts in question types

3. **"Question type 'X' must have at least 1 item."**
   - Fix: Enter item count > 0

4. **"Question type 'X' must have positive points per item."**
   - Fix: Enter points per item > 0

5. **"Duplicate question types found: X, Y"**
   - Fix: Rename duplicate types

---

## Testing Checklist

- [ ] Add question types with default values
- [ ] Edit question type names
- [ ] Edit item counts and verify sum validation
- [ ] Edit point values and verify total points update
- [ ] Delete question type and verify validation updates
- [ ] Add new question type
- [ ] Generate TOS with valid distribution
- [ ] Generate TOS with invalid distribution (button disabled)
- [ ] Export TOS and verify total points in header
- [ ] Verify Bloom's distribution still works correctly
- [ ] Verify TOS matrix unchanged

---

## Future Extensions

This foundation enables:

1. **TQS (Test Question Service)** - Uses question types to generate questions
2. **Weighted Question Generation** - Prioritize high-point questions
3. **Difficulty Distribution** - Question type + Bloom level for complex assessment
4. **Question Bank Mapping** - Link bank items to question types
5. **Grading Rubrics** - Use point weights for automated scoring

---

## Comments in Code

### question_type_service.py
- Extensive docstrings for each function
- Clear comments on validation rules
- Examples in docstrings
- Separation of concerns documented

### app.py
```python
# ============================================================
# SECTION 2: QUESTION TYPE DISTRIBUTION
# ============================================================
# NEW: Question Type Distribution
"question_types": st.session_state.question_types,
# NEW: Computed total points
"total_points": compute_total_points(st.session_state.question_types)
```

### tos_template_renderer.py
```python
# From question type distribution
"Total Number of Points:", meta.get("total_points", "")
```

---

## Summary

The Question Type Distribution feature:

✅ **Extends TOS** with weighted scoring configuration
✅ **Validates** item counts and point values
✅ **Computes** total points automatically
✅ **Maintains** separation between Bloom and question types
✅ **Preserves** all existing Bloom distribution logic
✅ **Prepares** for future TQS module
✅ **Clearly documents** all code and workflows

This implementation follows the principle: **TOS is a blueprint; question generation is separate.**
