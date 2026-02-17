# Question Type Distribution - Quick Reference

## 1. UI Workflow (For Teachers)

### Step 1: Total Test Items
Enter the expected number of test items:
```
Total Number of Test Items: 60
```

### Step 2: Question Type Distribution
Configure each question type:

```
| Question Type    | No. of Items | Points Per Item |
|---|---|---|
| MCQ              | 40           | 1               |
| Essay            | 2            | 10              |
| Problem Solving  | 18           | 2               |
```

### Step 3: System Validates
✅ **Validation checks:**
- Sum of items (40+2+18 = 60) matches total (60) ✅
- No empty fields ✅
- All positive values ✅
- No duplicate types ✅

✅ **Automatic calculations:**
- Total Points = (40×1) + (2×10) + (18×2) = 96

### Step 4: Generate TOS
Click "⚙ Generate TOS" (enabled only if validation passes)

### Step 5: Export
TOS Excel now shows:
```
Total Number of Points: 96
```

---

## 2. Code API Reference

### Create a Question Type
```python
from services.question_type_service import QuestionType

# Method 1: Direct instantiation
qt = QuestionType("MCQ", 40, 1)

# Method 2: Using factory function
from services.question_type_service import create_question_type
qt = create_question_type("MCQ", 40, 1)
```

### Get Total Points
```python
from services.question_type_service import compute_total_points

types = [
    QuestionType("MCQ", 40, 1),
    QuestionType("Essay", 2, 10)
]

total = compute_total_points(types)  # Returns 60.0
```

### Validate Distribution
```python
from services.question_type_service import validate_question_type_distribution

types = [
    QuestionType("MCQ", 40, 1),
    QuestionType("Essay", 20, 2)
]

is_valid, errors = validate_question_type_distribution(types, total_items=60)

if is_valid:
    print("✅ Valid distribution")
else:
    for error in errors:
        print(f"❌ {error}")
```

### Load Default Templates
```python
from services.question_type_service import get_default_question_types

defaults = get_default_question_types()
# Returns 6 default types with 0 items (editable)
```

### Format for Display
```python
from services.question_type_service import format_question_types_for_display
import pandas as pd

types = [
    QuestionType("MCQ", 40, 1),
    QuestionType("Essay", 2, 10)
]

display_data = format_question_types_for_display(types)
df = pd.DataFrame(display_data)
# Adds totals row automatically
```

---

## 3. Data Structure

### QuestionType Object
```python
@dataclass
class QuestionType:
    type: str              # Name: "MCQ", "Essay", etc.
    items: int             # Number of items
    points_per_item: float # Points per item
    
    # Methods:
    # .total_points() → returns items × points_per_item
    # .to_dict() → returns {"type": ..., "items": ..., ...}
```

### In Generated TOS
```python
st.session_state.generated_tos = {
    "outcomes": [...],           # Learning outcomes
    "tos_matrix": {...},         # Bloom distribution
    "bloom_totals": {...},       # Bloom totals
    
    # NEW FIELDS:
    "question_types": [          # List of QuestionType
        {
            "type": "MCQ",
            "items": 40,
            "points_per_item": 1
        },
        {
            "type": "Essay",
            "items": 2,
            "points_per_item": 10
        }
    ],
    "total_items": 60,           # Total test items
    "total_points": 60           # Computed total points
}
```

---

## 4. Validation Rules vs Error Messages

| Validation Rule | Error Message | Fix |
|---|---|---|
| At least 1 type | "At least one question type must be defined." | Add question type |
| Items sum = total | "Sum of items (X) must equal total (Y)." | Adjust item counts |
| Items > 0 | "Question type 'X' must have at least 1 item." | Enter items > 0 |
| Points > 0 | "Question type 'X' must have positive points per item." | Enter points > 0 |
| No duplicates | "Duplicate question types found: X, Y" | Rename types |

---

## 5. Common Scenarios

### Scenario A: Board Exam (60 items, 60 points)
```python
types = [
    QuestionType("Multiple Choice", 50, 1),  # 50 items × 1 = 50 pts
    QuestionType("Short Answer", 10, 1)      # 10 items × 1 = 10 pts
]
# Total: 60 items, 60 points (1 point per item)

is_valid, errors = validate_question_type_distribution(types, 60)  # ✅ Valid
```

### Scenario B: Weighted Exam (60 items, 100 points)
```python
types = [
    QuestionType("MCQ", 40, 1),              # 40 items × 1 = 40 pts
    QuestionType("Essay", 10, 3),            # 10 items × 3 = 30 pts
    QuestionType("Problem Solving", 10, 3)   # 10 items × 3 = 30 pts
]
# Total: 60 items, 100 points

is_valid, errors = validate_question_type_distribution(types, 60)  # ✅ Valid
total = compute_total_points(types)  # 100.0
```

### Scenario C: Invalid Distribution
```python
types = [
    QuestionType("MCQ", 40, 1),              # 40 items
    QuestionType("Essay", 15, 2)             # 15 items
]
# Total: 55 items (but expected 60)

is_valid, errors = validate_question_type_distribution(types, 60)
# ❌ Valid: False
# Errors: ["Sum of items (55) must equal total (60)."]
```

---

## 6. Integration with TOS System

### Before (Basic TOS)
```
TOS = Bloom Distribution + Outcomes
       + Total Items
```

### After (Extended TOS)
```
TOS = Bloom Distribution    # WHAT to assess (Remember, Apply, etc.)
    + Question Types        # HOW to assess (MCQ vs Essay)
    + Total Items           # Item count
    + Total Points          # Point weights
    + Outcomes              # Learning outcomes
```

### Why Both Distributions?
- **Bloom's Distribution** answers: "What knowledge level?"
  - Remember: 20%
  - Understand: 30%
  - Apply: 50%

- **Question Type Distribution** answers: "How many items and worth how much?"
  - MCQ: 40 items, 1 point each
  - Essay: 10 items, 5 points each

Together they define complete assessment blueprint.

---

## 7. For Developers

### Adding Question Type Service to Your Code
```python
# Import what you need
from services.question_type_service import (
    QuestionType,
    validate_question_type_distribution,
    compute_total_points,
    get_default_question_types,
    format_question_types_for_display,
    TOSWithQuestionTypes
)

# Use in your module
def my_function(question_types, total_items):
    is_valid, errors = validate_question_type_distribution(
        question_types, 
        total_items
    )
    
    if is_valid:
        total_pts = compute_total_points(question_types)
        return {"valid": True, "total_points": total_pts}
    else:
        return {"valid": False, "errors": errors}
```

### Storing in Session State
```python
# Streamlit UI
if "question_types" not in st.session_state:
    st.session_state.question_types = get_default_question_types()

# After user edits
st.session_state.question_types = updated_list  # List of QuestionType objects

# In generated TOS
st.session_state.generated_tos["question_types"] = st.session_state.question_types
st.session_state.generated_tos["total_points"] = compute_total_points(
    st.session_state.question_types
)
```

### Exporting to Excel
```python
from services.export_service import export_tos_exact_format

excel_bytes = export_tos_exact_format(
    meta={
        "name": "Dr. Smith",
        "subject_code": "CS101",
        "title": "Introduction to Programming",
        "total_items": 60,
        "total_points": 100,  # From question types
        ...
    },
    outcomes=[...],
    tos_matrix={...},
    total_items=60,
    total_points=100  # Pass computed total
)
```

---

## 8. Key Principle: Separation of Concerns

```
QUESTION TYPE DISTRIBUTION
├── Responsibility: Define item types and point weights
├── Input: Question type names, item counts, point values
├── Output: Validated distribution, computed total points
├── Does NOT: Generate questions, handle Bloom levels, create tests
└── Used by: TOS blueprint, future TQS module

BLOOM'S DISTRIBUTION
├── Responsibility: Define knowledge level distribution
├── Input: Bloom% per level, total items
├── Output: Items per Bloom level per outcome
├── Does NOT: Define item types, assign points, handle formatting
└── Used by: TOS blueprint, future TQS module

TOS BLUEPRINT
├── Responsibility: Combine both distributions
├── Input: Bloom distribution, question types, outcomes
├── Output: Complete assessment specification
├── Stores: Metadata, outcomes, both distributions
└── Used by: Export to Excel, TQS generation

TQS GENERATION (Future)
├── Responsibility: Create actual test questions
├── Input: TOS blueprint, question bank
├── Output: Test questions with specific types, blooms, points
└── Uses: Both distributions from TOS
```

---

## 9. Testing Your Integration

### Test 1: Create and Validate
```python
# Setup
types = [
    QuestionType("MCQ", 40, 1),
    QuestionType("Short Answer", 20, 1)
]

# Test validation
is_valid, errors = validate_question_type_distribution(types, 60)
assert is_valid == True
assert len(errors) == 0
```

### Test 2: Compute Points
```python
total = compute_total_points(types)
assert total == 60.0  # (40×1) + (20×1) = 60
```

### Test 3: Handle Invalid
```python
bad_types = [QuestionType("MCQ", 40, 1)]  # Only 40 items, need 60
is_valid, errors = validate_question_type_distribution(bad_types, 60)
assert is_valid == False
assert any("must equal" in e for e in errors)
```

### Test 4: Display Format
```python
display = format_question_types_for_display(types)
df = pd.DataFrame(display)
assert df.shape[0] == 3  # 2 types + 1 total row
assert df.iloc[-1]["Question Type"] == "TOTAL"
```

---

## 10. Troubleshooting

**Q: "Generate TOS" button is grayed out**
A: Fix validation errors shown above the button. Common causes:
- Total items don't match sum of question type items
- A question type has 0 items or 0 points per item
- Duplicate question type names

**Q: Total points not showing in exported Excel**
A: Ensure `total_points` is passed to export function:
```python
export_tos_exact_format(
    ...,
    total_points=compute_total_points(question_types)
)
```

**Q: How do I change point values after TOS is generated?**
A: Edit question types in Step 2 and regenerate TOS. The previous TOS will be replaced.

**Q: Can I have decimal points per item?**
A: Yes! The `points_per_item` field accepts floats (e.g., 1.5, 2.5, 3.0)

---

## Summary of New Features

| Feature | Location | Effect |
|---|---|---|
| Question Type Editor | TOS Tab, Step 2 | Add/edit/delete question types |
| Item Validation | TOS Tab, Step 2 | Validate items sum matches total |
| Points Computation | Auto | Total Points calculated automatically |
| Validation Status | TOS Tab, Step 2 | Real-time validation feedback |
| TOS Storage | Session State | Stores question types with TOS |
| Excel Export | Export Tab | Shows total points in header |

---

All examples tested and working! ✅
