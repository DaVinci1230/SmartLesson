# TOS File Upload - Example Structures & Guide

## Overview

The TQS generation tab now supports uploading TOS (Table of Specifications) files in multiple formats:
- **JSON**: Recommended for direct data
- **PDF**: For scanned or exported TOS documents
- **DOCX**: For Word document TOS files

This document provides examples of expected TOS structures for each format.

---

## JSON Format (Recommended)

JSON is the most reliable format as it directly represents the data structure expected by the TQS generator.

### Basic JSON Structure

```json
{
  "learning_outcomes": [
    {
      "id": 0,
      "text": "Identify the main components of photosynthesis",
      "hours": 2.5
    },
    {
      "id": 1,
      "text": "Define cellular respiration and its importance",
      "hours": 1.5
    },
    {
      "id": 2,
      "text": "Describe the structure of DNA",
      "hours": 2.0
    }
  ],
  "bloom_distribution": {
    "Remember": 30,
    "Understand": 30,
    "Apply": 20,
    "Analyze": 10,
    "Evaluate": 5,
    "Create": 5
  },
  "tos_matrix": {
    "Remember": {
      "0": 2,
      "1": 2,
      "2": 2
    },
    "Understand": {
      "0": 2,
      "1": 2,
      "2": 2
    },
    "Apply": {
      "0": 1,
      "1": 1,
      "2": 2
    },
    "Analyze": {
      "0": 1,
      "1": 0,
      "2": 1
    },
    "Evaluate": {
      "0": 0,
      "1": 1,
      "2": 0
    },
    "Create": {
      "0": 0,
      "1": 0,
      "2": 1
    }
  },
  "total_items": 20,
  "metadata": {
    "course_code": "BIO101",
    "course_title": "Biology Fundamentals",
    "semester": "1st",
    "exam_term": "Midterm"
  }
}
```

### Field Descriptions

#### `learning_outcomes` (required)
Array of learning outcomes. Each outcome must have:
- `id` (integer): Unique identifier, starting from 0
- `text` (string): The outcome description
- `hours` (float, optional): Teaching hours allocated to this outcome

```json
{
  "id": 0,
  "text": "Identify the main components of photosynthesis",
  "hours": 2.5
}
```

#### `bloom_distribution` (required)
Percentage (or count) distribution across Bloom's levels.
Must include all 6 levels: Remember, Understand, Apply, Analyze, Evaluate, Create

```json
{
  "Remember": 30,
  "Understand": 30,
  "Apply": 20,
  "Analyze": 10,
  "Evaluate": 5,
  "Create": 5
}
```

**Note**: Values can be percentages (sum to 100) or item counts (sum to total_items).

#### `tos_matrix` (required)
TOS (Table of Specifications) mapping: Bloom level × Outcome ID → Item count

Structure:
```json
{
  "Bloom_Level": {
    "outcome_id": item_count,
    ...
  },
  ...
}
```

Example:
```json
{
  "Remember": {
    "0": 2,
    "1": 2,
    "2": 2
  },
  "Understand": {
    "0": 2,
    "1": 2,
    "2": 2
  },
  ...
}
```

**Important**:
- Keys in the inner dict should match outcome `id` values
- Values are integer counts (number of questions)
- Can have 0 for combinations not assessed

#### `total_items` (calculated)
Total number of test items. The parser auto-calculates this by summing all entries in `tos_matrix`.

#### `metadata` (optional)
Additional course information:
- `course_code`: Course identifier
- `course_title`: Full course name
- `semester`: Semester number
- `exam_term`: "Midterm" or "Final"
- `file_name`: (Auto-populated by parser)
- `parsed_at`: (Auto-populated by parser)

---

## Complete Example: Biology 101 Midterm

```json
{
  "learning_outcomes": [
    {
      "id": 0,
      "text": "Identify the main components of photosynthesis",
      "hours": 2.5
    },
    {
      "id": 1,
      "text": "Define cellular respiration and its importance",
      "hours": 1.5
    },
    {
      "id": 2,
      "text": "Describe the structure of DNA",
      "hours": 2.0
    },
    {
      "id": 3,
      "text": "Analyze the relationship between photosynthesis and respiration",
      "hours": 1.0
    }
  ],
  "bloom_distribution": {
    "Remember": 25,
    "Understand": 35,
    "Apply": 20,
    "Analyze": 15,
    "Evaluate": 3,
    "Create": 2
  },
  "tos_matrix": {
    "Remember": {
      "0": 2,
      "1": 1,
      "2": 2,
      "3": 0
    },
    "Understand": {
      "0": 2,
      "1": 2,
      "2": 2,
      "3": 1
    },
    "Apply": {
      "0": 1,
      "1": 1,
      "2": 1,
      "3": 1
    },
    "Analyze": {
      "0": 1,
      "1": 0,
      "2": 1,
      "3": 1
    },
    "Evaluate": {
      "0": 0,
      "1": 0,
      "2": 0,
      "3": 1
    },
    "Create": {
      "0": 0,
      "1": 0,
      "2": 1,
      "3": 0
    }
  },
  "total_items": 30,
  "metadata": {
    "course_code": "BIO101",
    "course_title": "Biology Fundamentals",
    "semester": "1st",
    "exam_term": "Midterm",
    "academic_year": "2025-2026",
    "instructor": "Dr. Sarah Johnson"
  }
}
```

---

## PDF Format

When uploading a PDF TOS file, the parser expects a well-structured table with:

### Expected Table Structure

| Learning Outcome | Remember | Understand | Apply | Analyze | Evaluate | Create | Total |
|------------------|----------|------------|-------|---------|----------|--------|-------|
| Outcome A        | 2        | 2          | 1     | 1       | 0        | 0      | 6     |
| Outcome B        | 1        | 2          | 1     | 0       | 0        | 0      | 4     |
| **Total**        | **3**    | **4**      | **2** | **1**   | **0**    | **0**  | **10**|

### Requirements

1. **First column**: Learning outcome descriptions
2. **Header row**: Bloom's levels (Remember, Understand, Apply, Analyze, Evaluate, Create)
3. **Data rows**: One per outcome with item counts
4. **Numeric values**: Must be integers (item counts)

### Tips for PDF Creation

1. Create a well-formatted table in Word/Excel
2. Export or save as PDF
3. Ensure text is selectable (not image-based)
4. Use clear header names for Bloom levels

---

## DOCX Format

For DOCX files, the parser looks for the first table with the structure described above.

### Expected Table Structure

Same as PDF - a table with:
- Column 1: Learning Outcomes
- Columns 2-7: Bloom's levels (Remember, Understand, Apply, Analyze, Evaluate, Create)
- Data: Integer item counts

### Example DOCX Structure

Create a table in Word:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ Learning Outcome                      │ Remember │ Understand │ Apply │ ...  │
├──────────────────────────────────────────────────────────────────────────────┤
│ Identify main components of...        │    2     │     2      │   1   │ ...  │
│ Define cellular respiration...        │    1     │     2      │   1   │ ...  │
│ Describe structure of DNA             │    2     │     2      │   1   │ ...  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Validation Rules

The uploaded TOS must meet these requirements:

### Must Have
✅ At least one learning outcome
✅ Non-empty TOS matrix with item counts
✅ All 6 Bloom levels in distribution
✅ Numeric values in TOS matrix
✅ Matrix entries ≥ 0

### Should Have
✅ All outcomes referenced in TOS matrix
✅ All Bloom levels have at least one item
✅ Outcome IDs consistent across sections
✅ Meaningful outcome descriptions

### Auto-Fixed
🔧 Missing outcome IDs → Auto-assigned (0, 1, 2, ...)
🔧 Missing Bloom levels → Added with 0 items
🔧 Missing outcome in matrix → Added with 0 items
🔧 total_items → Auto-calculated

---

## Workflow After Upload

1. **Upload File** → Parser validates format and structure
2. **Select Test Type** → Choose question type (MCQ, Essay, Problem Solving, Mixed)
3. **Set Points** → Define points per question
4. **Confirm TOS** → Convert to internal slot format
5. **Generate TQS** → Create actual test questions using AI

---

## Troubleshooting

### Error: "Missing required fields"
**Solution**: Ensure JSON has all three main sections:
- `learning_outcomes` (array)
- `bloom_distribution` (dict)
- `tos_matrix` (dict)

### Error: "TOS contains no items"
**Solution**: Check that your `tos_matrix` has numeric values > 0

### Error: "Could not find Bloom levels in table headers"
**Solution (PDF/DOCX)**: 
- Ensure column headers exactly match: Remember, Understand, Apply, Analyze, Evaluate, Create
- Use plain text (not images)
- Check spelling and capitalization

### Warning: "Outcome references not found in learning_outcomes"
**Solution**: Verify outcome IDs in TOS matrix match IDs in learning_outcomes

---

## Generated TQS Format

After uploading TOS and generating questions, the system creates:

```json
{
  "questions": [
    {
      "question_number": 1,
      "outcome_id": 0,
      "outcome": "Identify the main components of photosynthesis",
      "bloom": "Remember",
      "type": "MCQ",
      "points": 1.0,
      "question_text": "Which of the following is NOT a component of photosynthesis?",
      "choices": [
        "Chlorophyll",
        "Water",
        "Glucose",
        "Oxygen"
      ],
      "correct_answer": "Glucose",
      "metadata": {
        "generated_at": "2025-02-16T10:30:00",
        "question_format": "MCQ"
      }
    },
    ...
  ],
  "summary": {
    "total_questions": 30,
    "total_points": 30,
    "questions_by_type": {
      "MCQ": 20,
      "Essay": 6,
      "Problem Solving": 4
    },
    "questions_by_bloom": {
      "Remember": 8,
      "Understand": 10,
      "Apply": 6,
      "Analyze": 4,
      "Evaluate": 1,
      "Create": 1
    }
  }
}
```

---

## API Reference

### Parsing a TOS File

```python
from services.tos_file_parser import parse_tos_file, validate_tos_for_tqs_generation

# Parse file
success, result = parse_tos_file(
    file_content=file_bytes,
    file_name="tos.json",
    file_type="json"  # or "pdf", "docx" (auto-detected if omitted)
)

if success:
    tos_data = result
    # Validate for TQS generation
    is_valid, msg = validate_tos_for_tqs_generation(tos_data)
    print(f"Valid for TQS: {is_valid} - {msg}")
else:
    error = result.get("error")
    print(f"Parsing failed: {error}")
```

### Converting TOS to Assigned Slots

```python
from services.tos_file_parser import convert_tos_to_assigned_slots

success, slots = convert_tos_to_assigned_slots(
    tos_data=tos_data,
    question_type="MCQ",
    points_per_item=1.0
)

if success:
    print(f"Created {len(slots)} question slots")
    # Now use slots with generate_tqs()
else:
    print(f"Conversion failed: {slots}")
```

---

## Best Practices

1. **Use JSON format** when possible → Most reliable, no parsing ambiguity
2. **Keep outcomes concise** → Use clear, specific learning outcome statements
3. **Balance Bloom levels** → Don't leave upper levels empty
4. **Test with small examples first** → Verify format before large uploads
5. **Keep Bloom distribution reasonable** → Remember (30%), Understand (30%), Apply (20%), etc.
6. **One outcome = one row/entry** → Avoid nested or combined outcomes
7. **Use consistent IDs** → Keep outcome IDs sequential from 0

---

## Support & Validation

To validate your JSON before uploading:

1. Use online JSON validator: https://jsonlint.com/
2. Check Bloom distribution sum = 100% (or equals total items)
3. Verify all outcomes are referenced in TOS matrix
4. Count items: sum of all matrix values = expected test size

For large datasets (>50 outcomes), JSON format is strongly recommended for reliability.
