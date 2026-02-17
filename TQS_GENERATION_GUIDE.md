# TQS (Test Question Sheet) Generation Module Documentation

**Status:** ✅ Complete and Ready for Integration  
**Date:** February 15, 2026  
**Files:** `services/tqs_service.py` + `test_tqs_generation.py`  

---

## 📋 Overview

The TQS (Test Question Sheet) generation module creates test questions directly from the exam blueprint's assigned slots. It uses Gemini AI to generate appropriate questions for each slot while preserving:

- ✅ **Weighted Scoring**: Points strictly follow `slot["points"]`
- ✅ **Cognitive Alignment**: Question complexity matches Bloom level
- ✅ **Type-Specific Generation**: MCQ, Short Answer, Essay, Problem Solving, Drawing
- ✅ **Rubric Integrity**: Constructed response rubrics total exactly to points
- ✅ **No TOS Modification**: Consumes blueprint as read-only input
- ✅ **Deterministic Output**: Same slots → same questions (given same AI responses)

---

## 🎯 Key Principles

### 1. Slot-Based Generation (Not Distribution-Based)

**How it works:**
- Input: List of assigned_slots from soft-mapping
- Process: For each slot → generate one question
- Output: One question per slot (1:1 mapping guaranteed)

**Why it matters:**
- No question redistribution or adjustment
- No "averaging" of point values
- Each question directly corresponds to a slot
- Teacher intent preserved throughout

### 2. Weighted Scoring Preserved

**Example exam:**
```
Slot 1: Remember, MCQ, 1 point  → Q1: 1-point MCQ
Slot 2: Apply, Essay, 5 points  → Q2: 5-point Essay
Slot 3: Analyze, PS, 4 points   → Q3: 4-point Problem Solving

Total: 3 items, 10 points (3 ≠ 10 because weighted types!)
```

**Key guarantee:**
- Each question uses its slot's points exactly
- No modification or redistribution
- Point totals emerge naturally from individual questions

### 3. Question Type Handling

| Type | Generation | Output | Rubric |
|------|-----------|--------|--------|
| **MCQ** | 4 distinct choices | Correct answer (A-D) | None |
| **Short Answer** | Constructed response | Answer key | Optional (if pts > 3) |
| **Essay** | Extended response | Sample answer | Required |
| **Problem Solving** | Multi-step solution | Sample solution | Required |
| **Drawing** | Visual response | Visual description | Required |

### 4. Cognitive Complexity Matching

**Bloom Level → Question Complexity:**

- **Remember (1-2 pts)**: Simple recall, direct questions
- **Understand (1-3 pts)**: Explain concepts, define terms
- **Apply (1-3 pts)**: Use knowledge in context
- **Analyze (2-4 pts)**: Compare, distinguish, break down
- **Evaluate (3-5 pts)**: Justify, critique, defend
- **Create (4-6 pts)**: Design, produce, synthesize

Rubric criteria and complexity automatically match the Bloom level specified in the slot.

---

## 🔧 Core Functions

### Main Function: `generate_tqs()`

```python
def generate_tqs(
    assigned_slots: List[Dict[str, Any]],
    api_key: str,
    shuffle: bool = True
) -> List[Dict[str, Any]]:
    """
    Generate complete Test Question Sheet from exam blueprint slots.
    
    WORKFLOW:
    1. For each slot: call generate_question_with_gemini()
    2. Collect all questions
    3. Shuffle (optional)
    4. Reassign question_number sequentially
    5. Return final TQS
    
    Args:
        assigned_slots: List of slot dicts from soft-mapping
        api_key: Gemini API key (from environment)
        shuffle: Whether to randomize question order (default: True)
    
    Returns:
        List of question dicts with full metadata
    """
```

### Helper Function: `generate_question_with_gemini()`

```python
def generate_question_with_gemini(
    slot: Dict[str, Any],
    api_key: str
) -> Dict[str, Any]:
    """
    Generate single question for one exam blueprint slot.
    
    CRITICAL:
    - Processes exactly ONE slot
    - Generates exactly ONE question
    - Output structure depends on slot["type"]
    - Points NEVER modified from slot["points"]
    
    Args:
        slot: Single slot dict with outcome, bloom, type, points
        api_key: Gemini API key
    
    Returns:
        Question dict with metadata and content
    """
```

### Utility Functions

**Statistics:**
```python
stats = get_tqs_statistics(tqs)
# Returns: {
#     "total_questions": 12,
#     "total_points": 28,
#     "questions_by_type": {"MCQ": 7, "Essay": 2, ...},
#     "questions_by_bloom": {"Remember": 5, "Apply": 4, ...},
#     "points_by_type": {"MCQ": 7, "Essay": 10, ...},
#     "points_by_bloom": {"Remember": 5, "Apply": 8, ...}
# }
```

**Export:**
```python
export_tqs_to_json(tqs, "tqs_exam_001.json")
# Saves TQS to JSON file
```

**Preview:**
```python
display_tqs_preview(tqs, max_questions=3)
# Shows first N questions for debugging
```

---

## 📊 Input/Output Structures

### Input: Assigned Slot

```python
{
    "outcome_id": 0,
    "outcome": "Identify the main components of photosynthesis",
    "outcome_hours": 2,
    "bloom": "Remember",  # or Understand, Apply, Analyze, Evaluate, Create
    "type": "MCQ",        # or Short Answer, Essay, Problem Solving, Drawing
    "points": 1
}
```

### Output: Generated Question (varies by type)

**MCQ Question:**
```python
{
    "question_number": 1,
    "outcome_id": 0,
    "outcome": "Identify the main components of photosynthesis",
    "bloom": "Remember",
    "type": "MCQ",
    "points": 1,
    "question_text": "Which of the following is the primary photosynthetic pigment?",
    "choices": [
        "Chlorophyll a",
        "Chlorophyll b",
        "Carotenoid",
        "Xanthophyll"
    ],
    "correct_answer": "A",
    "answer_key": "A"
}
```

**Short Answer Question:**
```python
{
    "question_number": 2,
    "outcome_id": 1,
    "outcome": "Define cellular respiration and its importance",
    "bloom": "Apply",
    "type": "Short Answer",
    "points": 3,
    "question_text": "Describe the process of aerobic respiration and explain why it's more efficient than anaerobic respiration.",
    "answer_key": "Aerobic respiration uses oxygen to break down glucose, producing ATP. It yields ~30 ATP vs ~2 ATP for anaerobic respiration.",
    "rubric": {
        "criteria": [
            {"descriptor": "Accurate description of aerobic process", "points": 1},
            {"descriptor": "Explains importance/efficiency", "points": 1},
            {"descriptor": "Correct ATP comparison", "points": 1}
        ],
        "total_points": 3
    }
}
```

**Essay Question:**
```python
{
    "question_number": 3,
    "outcome_id": 0,
    "outcome": "Identify the main components of photosynthesis",
    "bloom": "Evaluate",
    "type": "Essay",
    "points": 5,
    "question_text": "Analyze how photosynthesis and cellular respiration are complementary processes. Discuss their ecological importance and how they balance carbon and oxygen in the atmosphere.",
    "sample_answer": "Photosynthesis produces glucose and oxygen from CO2 and water using light energy. Cellular respiration reverses this, breaking down glucose to release energy and produce CO2. Together they form a cycle: plants capture solar energy (photosynthesis) and organisms use it (respiration). This reciprocal relationship maintains atmospheric O2 and CO2 balance...",
    "rubric": {
        "criteria": [
            {"descriptor": "Discusses complementary nature of processes", "points": 2},
            {"descriptor": "Explains ecological importance", "points": 2},
            {"descriptor": "Describes carbon/oxygen cycling", "points": 1}
        ],
        "total_points": 5
    }
}
```

**Problem Solving Question:**
```python
{
    "question_number": 4,
    "outcome_id": 1,
    "outcome": "Define cellular respiration and its importance",
    "bloom": "Analyze",
    "type": "Problem Solving",
    "points": 4,
    "question_text": "A cell undergoes anaerobic respiration for 1 hour, producing 100 ATP. When oxygen becomes available, how much ATP could be produced from the same amount of glucose in aerobic respiration? Show your calculation and explain the difference.",
    "sample_answer": "Anaerobic respiration produces 2 ATP per glucose via fermentation. If 100 ATP was produced, that means 50 glucose molecules were used. Aerobic respiration produces ~30 ATP per glucose. So 50 glucose × 30 ATP = 1500 ATP. The 15-fold increase is because aerobic respiration extracts energy more efficiently using the electron transport chain and oxidative phosphorylation...",
    "rubric": {
        "criteria": [
            {"descriptor": "Correct calculation (15x increase)", "points": 1.5},
            {"descriptor": "Identifies efficiency difference", "points": 1"},
            {"descriptor": "Explains electron transport/oxidative phosphorylation", "points": 1.5}
        ],
        "total_points": 4
    }
}
```

---

## 🚀 Usage Guide

### Basic Usage

```python
from services.tqs_service import generate_tqs, get_tqs_statistics
from services.tos_slot_assignment_service import assign_question_types_to_bloom_slots
import os

# Step 1: Get assigned_slots from soft-mapping (already exists from Phase 2)
assigned_slots = assign_question_types_to_bloom_slots(
    tos_matrix=exam_blueprint["tos_matrix"],
    outcomes=exam_blueprint["outcomes"],
    question_types_list=question_types_config,
    shuffle=True
)

# Step 2: Generate TQS
api_key = os.environ.get("GEMINI_API_KEY")
tqs = generate_tqs(assigned_slots, api_key, shuffle=True)

# Step 3: Use the TQS
print(f"Generated {len(tqs)} questions worth {sum(q['points'] for q in tqs)} points")

# Step 4: Get statistics
stats = get_tqs_statistics(tqs)
print(f"By type: {stats['questions_by_type']}")
print(f"By Bloom: {stats['questions_by_bloom']}")
```

### With Error Handling

```python
try:
    tqs = generate_tqs(assigned_slots, api_key)
except ValueError as e:
    print(f"Generation failed: {e}")
    # Handle error (retry, fallback, etc.)
```

### Export for Use

```python
from services.tqs_service import export_tqs_to_json

# Save to file
export_tqs_to_json(tqs, "exam_midterm_2024.json")

# Use in display
for q in tqs:
    print(f"Q{q['question_number']}: {q['question_text']}")
    if q['type'] == 'MCQ':
        for i, choice in enumerate(q['choices']):
            print(f"  {chr(65+i)}) {choice}")
```

---

## 🧪 Testing

### Run Tests

```bash
cd d:\SOFTWARE ENGINEERING\SmartLesson
python test_tqs_generation.py
```

### Test Coverage

| Test | Purpose | Status |
|------|---------|--------|
| **TQS Generation** | Full end-to-end generation | ✅ |
| **Point Preservation** | Points match slots exactly | ✅ |
| **Statistics** | Correct aggregation | ✅ |
| **Rubric Validation** | Rubric totals equal points | ✅ |

### Example Test Data

The test file includes 12 realistic slots:
- 5 Remember MCQ @ 1pt
- 2 Apply MCQ @ 1pt each
- 1 Apply Short Answer @ 3pts
- 2 Analyze Problem Solving @ 4pts each
- 2 Analyze Essay @ 5pts each

**Total: 12 items, 28 points**

---

## ⚙️ Configuration

### Environment Variables

```bash
GEMINI_API_KEY=<your-key>  # Required for Gemini API calls
```

### Gemini Model

- **Model**: `gemini-2.5-flash`
- **Features**: Fast generation, reliable JSON parsing
- **Cost**: Low (flash model)

---

## 🔍 Design Details

### Question Generation Process

```
Input Slot
    ↓
    ├─ If MCQ: 4-choice question with answer
    ├─ If Short Answer: text + answer key (+ rubric if points > 3)
    ├─ If Essay/PS/Drawing: text + sample answer + detailed rubric
    ↓
Validate Output
    ├─ Check required fields present
    ├─ Validate JSON schema
    ├─ Verify rubric total = points
    ├─ Confirm choices count (MCQ only)
    ↓
Enrich with Metadata
    ├─ Add outcome_id, outcome, bloom, type, points
    ↓
Return Question
```

### Rubric Validation Logic

For constructed response questions (Essay, Problem Solving, Drawing):

```python
rubric_total = sum(criterion["points"] for criterion in rubric["criteria"])

if rubric_total != slot["points"]:
    # Scale rubric proportionally
    scale_factor = slot["points"] / rubric_total
    for criterion in rubric["criteria"]:
        criterion["points"] *= scale_factor
```

This ensures rubric totals ALWAYS match the required points.

### Shuffling & Numbering

```
Original Questions (by slot order)
    ↓
[Optional] Shuffle
    ↓
Reassign question_number sequentially (1, 2, 3, ...)
    ↓
Final TQS
```

Benefits of shuffling:
- Randomizes question order on exam
- Prevents students from predicting patterns
- Tests all outcomes fairly
- Maintains question integrity (metadata unchanged)

---

## 📊 Preservation Guarantees

### What's Preserved

✅ **Question Count**: Always equals slot count  
✅ **Point Values**: Exactly match slot points  
✅ **Outcome Mapping**: Each question links to learning outcome  
✅ **Bloom Level**: Question complexity matches slot's Bloom  
✅ **Question Type**: Question generation matches slot type  
✅ **Assessment Structure**: Rubrics match outcomes and blooms  

### What's NOT Modified

❌ TOS matrix itself  
❌ Item distribution  
❌ Point allocation  
❌ Question type assignment  
❌ Learning outcomes (text preserved exactly)

---

## 🎓 Example Workflow

### Complete Exam Creation (All 3 Systems)

```python
# PHASE 1: TOS Generation (already exist)
from services.tos_service import generate_tos
tos_result = generate_tos(
    outcomes=outcomes,
    bloom_weights=bloom_weights,
    total_items=12
)

# PHASE 2: Soft-Mapping (already exist)
from services.tos_slot_assignment_service import assign_question_types_to_bloom_slots
assigned_slots = assign_question_types_to_bloom_slots(
    tos_matrix=tos_result["tos_matrix"],
    outcomes=outcomes,
    question_types_list=question_types,
    shuffle=True
)

# PHASE 3: TQS Generation (NEW - THIS MODULE)
from services.tqs_service import generate_tqs, get_tqs_statistics
tqs = generate_tqs(assigned_slots, api_key)

# PHASE 4: Statistics & Export
stats = get_tqs_statistics(tqs)
export_tqs_to_json(tqs, "exam.json")

# RESULT: Complete exam with questions ready to print
print(f"Exam created: {stats['total_questions']} items, {stats['total_points']} points")
```

---

## 📝 Implementation Notes

### JSON Response Parsing

Gemini sometimes wraps JSON in code blocks. The service handles:

```python
# All these are parsed correctly:
```json
{...}
```

```
{...}
```

{...}
```

### Rubric Scaling

If Gemini's rubric doesn't exactly total the required points, it's automatically scaled:

```python
# Example: 4-point requirement, got rubric with 5 points
Original: [2, 2, 1] = 5 points
Scaled:   [1.6, 1.6, 0.8] = 4 points
```

This preserves the rubric structure while ensuring correctness.

### Error Handling

Graceful fallbacks for common errors:

```python
- Missing JSON in response → Try multiple parsing strategies
- Invalid schema → Log error and raise for caller to handle
- Bad rubric total → Auto-scale to correct value
- Missing fields → Validate and report which fields missing
```

---

## 🔄 Integration with Other Systems

### Inputs From
- **Soft-Mapping Service**: `assigned_slots` with outcome/bloom/type/points
- **Gemini API**: Question generation and rubric creation

### Outputs To
- **Export Service**: TQS for Excel/PDF creation
- **Streamlit App**: Display questions to teacher
- **Grading System**: Questions and rubrics for evaluation

### Data Flow

```
TOS Blueprint
    ↓
Soft-Mapping Assignment
    ↓
TQS Generation (THIS MODULE) ← Generates questions
    ↓
Export to Test Format
    ↓
Teacher Review / Student Assessment
```

---

## ✅ Quality Assurance

### Validation Checks

Every generated question passes:

- ✅ JSON schema validation
- ✅ Required fields present
- ✅ Type-specific structure correct
- ✅ Rubric totals accurate (if applicable)
- ✅ Question text quality check
- ✅ Point value preservation
- ✅ Outcome link integrity

### Test Results

- **4 test categories**: All passing
- **100% question rate**: One per slot
- **Point accuracy**: Exact preservation
- **Type handling**: All 5 types work correctly
- **Rubric validation**: Auto-scaling when needed

---

## 🚀 Ready for Production

✅ Core functionality complete  
✅ All tests passing  
✅ Error handling robust  
✅ Documentation comprehensive  
✅ No external dependencies issues  
✅ API stable and documented  

**Status: Ready to integrate into app.py**

---

## 📞 Support

For questions about:
- **How it works**: See "Design Details" section
- **Integration**: See "Usage Guide" section
- **Testing**: See "Testing" section
- **Design principles**: See "Key Principles" section

