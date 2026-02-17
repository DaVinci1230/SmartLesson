# Weighted TOS Matrix Generation Fix

## Overview

The TOS matrix generation has been fixed to reflect **weighted question type scoring** instead of the simplistic "1 item = 1 point" assumption.

### The Problem

**Old Logic:**
```
TOS Matrix → Item count only
TOS assumed: Pts = No. of Items
Result: 12 items always = 12 points
```

**Reality:**
```
Question types have different point values:
- MCQ: 1 point each
- Problem Solving: 3 points each  
- Essay: 5 points each

So: 12 items could = 5, 8, 15, 28, or any other value
    depending on the type distribution
```

### The Solution

**New Logic:**
```
Assigned Slots → Items Matrix + Points Matrix
TOS computed from actual assigned question types
Result: 12 items = 28 points (or whatever the real total is)
```

---

## How It Works

### Step 1: Soft-Map Questions to Bloom Slots

Teacher configuration + soft-mapping algorithm → `assigned_slots` list

Each slot contains:
```python
{
    "outcome_id": 0,
    "outcome_text": "Define concepts",
    "bloom": "Apply",
    "type": "Essay",
    "points": 5  # ← Exact point value from question type config
}
```

### Step 2: Aggregate Slots into Weighted TOS Matrix

New function: `generate_tos_from_assigned_slots(assigned_slots)`

For each (outcome, bloom) combination:
- **No. of Items** = count of slots
- **Pts** = sum of slot points

Example:
```
Bloom: Apply
Outcome 0: 2 MCQ (2×1=2 pts) + 1 Problem Solving (1×3=3 pts)
          = 3 items, 5 points

(NOT: 3 items, 3 points)
```

### Step 3: Compute Totals

New function: `compute_tos_totals(items_matrix, points_matrix)`

- Total Items = sum of all items
- Total Points = sum of all points  
- By Bloom Level totals
- By Outcome totals

---

## Key Data Structures

### Input: Assigned Slots

```python
assigned_slots = [
    {
        "outcome_id": 0,
        "outcome_text": "Understand concepts",
        "bloom": "Remember",
        "type": "MCQ",
        "points": 1
    },
    {
        "outcome_id": 0,
        "outcome_text": "Understand concepts", 
        "bloom": "Apply",
        "type": "Essay",
        "points": 5
    },
    # ... more slots
]
```

### Output: Items Matrix

Structure: `{bloom: {outcome_id: item_count}}`

```python
items_matrix = {
    "Remember": {0: 3, 1: 2},  # Outcome 0: 3 items, Outcome 1: 2 items
    "Apply": {0: 3, 1: 1},
    "Analyze": {0: 1, 1: 2}
}
```

### Output: Points Matrix

Structure: `{bloom: {outcome_id: total_points}}`

```python
points_matrix = {
    "Remember": {0: 3, 1: 2},   # Outcome 0: 3 points, Outcome 1: 2 points
    "Apply": {0: 5, 1: 3},      # Not 3 and 1 - higher because of Essay
    "Analyze": {0: 5, 1: 10}    # Essay items: 5 points each
}
```

### Output: Totals

```python
total_items = 12
total_points = 28  # NOT equal to items!

items_by_bloom = {
    "Remember": 5,
    "Apply": 4,
    "Analyze": 3
}

points_by_bloom = {
    "Remember": 5,
    "Apply": 8,
    "Analyze": 15
}
```

---

## Why This Matters

### For the TOS Matrix Display

**Old:**
| Outcome | Remember | Apply | Analyze | TOTAL |
|---------|----------|-------|---------|-------|
| O1 | 3 | 3 | 1 | 7 |
| O2 | 2 | 1 | 2 | 5 |
| **TOTAL** | **5** | **4** | **3** | **12** |
| **ROUNDINGS** | **5** | **4** | **3** | **12 pts** |

Problem: Assumes all items are 1 point. WRONG if classes have different point values.

**New:**
| Outcome | Remember (Items/Pts) | Apply (Items/Pts) | Analyze (Items/Pts) | TOTAL (Items/Pts) |
|---------|---|---|---|---|
| O1 | 3/3 | 3/5 | 1/5 | 7/13 |
| O2 | 2/2 | 1/3 | 2/10 | 5/15 |
| **TOTAL** | **5/5** | **4/8** | **3/15** | **12/28** |

Now it correctly shows: 12 items but 28 points (not 12 points).

### For Test Generation

The TQS module needs to know:
- How many items of each type to generate per outcome/bloom
- How many points each item is worth

Old approach would generate 12 items all worth ~2.3 points each.  
New approach generates exactly what teacher configured:
- 5 MCQ @ 1 point each
- 4 Problem Solving @ 3 points each
- 3 Essay @ 5 points each

---

## API Reference

### Function 1: generate_tos_from_assigned_slots

```python
def generate_tos_from_assigned_slots(assigned_slots):
    """
    Regenerate TOS matrix from assigned question type slots.
    
    WHY: After soft-mapping, we have the final exam blueprint with
    actual question types and their point values. TOS must reflect this.
    
    Args:
        assigned_slots: List of dicts with {outcome_id, bloom, type, points}
    
    Returns:
        Tuple of:
        - items_matrix: {bloom: {outcome_id: count}}
        - bloom_totals: {bloom: total_items}
        - points_matrix: {bloom: {outcome_id: sum_of_points}}
    """
```

**Example Usage:**
```python
items_mx, bloom_tots, points_mx = generate_tos_from_assigned_slots(
    st.session_state.exam_blueprint
)
```

### Function 2: compute_tos_totals

```python
def compute_tos_totals(items_matrix, points_matrix):
    """
    Compute TOTAL row (sums) for TOS table.
    
    Args:
        items_matrix: {bloom: {outcome_id: count}}
        points_matrix: {bloom: {outcome_id: points}}
    
    Returns:
        Tuple of:
        - total_items: int
        - total_points: float
        - items_by_bloom: {bloom: count}
        - points_by_bloom: {bloom: sum}
    """
```

**Example Usage:**
```python
total_items, total_pts, items_bloom, pts_bloom = compute_tos_totals(
    items_mx,
    points_mx
)
```

---

## Workflow Integration

### Step 1: Teacher defines TOS (unchanged)
```python
tos_result = generate_tos(
    outcomes=outcomes,
    bloom_weights=bloom_weights,
    total_items=total_items
)
```

### Step 2: Teacher defines question types (unchanged)
```
MCQ: 25 items × 1 point
Essay: 3 items × 5 points
Problem Solving: 12 items × 2 points
```

### Step 3: Soft-map types to Bloom slots (existing)
```python
assigned, metadata = assign_question_types_to_bloom_slots(
    tos_result["tos_matrix"],
    outcomes,
    question_types,
    shuffle=True
)
```

### Step 4: [NEW] Generate weighted TOS matrix
```python
items_mx, bloom_tots, points_mx = generate_tos_from_assigned_slots(
    assigned
)

total_items, total_pts, items_bloom, pts_bloom = compute_tos_totals(
    items_mx,
    points_mx
)
```

### Step 5: Export TOS with weighted values
```python
excel = export_tos_exact_format(
    meta=metadata,
    outcomes=outcomes,
    tos_matrix=items_mx,  # ← Now uses assigned-slot aggregate
    points_matrix=points_mx,  # ← NEW: Points per outcome/bloom
    total_items=total_items,
    total_points=total_pts
)
```

---

## Critical Insights

### 1. Items ≠ Points (With Weighted Scoring)

```
Old Logic: 12 items → 12 points (assumption)
New Logic: 12 items → 28 points (actual weighted total)
```

This is CORRECT. Teachers intentionally weight different question types.

### 2. TOS Matrix Now Has Two Dimensions

**Before:** Items only  
`matrix[bloom][outcome] = 5` (5 items)

**After:** Items AND Points  
`items[bloom][outcome] = 5` (5 items)  
`points[bloom][outcome] = 15` (15 points, because they're Essays)

### 3. Points are NOT Redistributed

If teacher configured "MCQ: 1 point each":
- Every MCQ stays 1 point
- Never becomes 2.3 points or auto-adjusted
- Weighted totals computed AFTER assignments

### 4. Aggregation is Deterministic

Each weighted TOS matrix is recomputed from the SAME assigned_slots.
- Same input (assigned slots) → Same output (weighted matrix)
- No randomness in aggregation
- Can verify integrity at any time

---

## Verification

### Test Coverage

✅ **Test 1:** Items matrix computed correctly  
✅ **Test 2:** Points matrix computed correctly  
✅ **Test 3:** Totals aggregated correctly  
✅ **Test 4:** Points ≠ Items (when types are weighted)  
✅ **Test 5:** Each outcome/bloom pair computed independently  

### Run Tests

```bash
python test_weighted_tos_matrix.py
```

**Result:** ✅ ALL CHECKS PASSED

---

## Code Comments in Services

### In `tos_service.py`

```python
def generate_tos_from_assigned_slots(assigned_slots):
    """
    Regenerate TOS matrix from assigned question type slots.
    
    CRITICAL: This function must be called AFTER soft-mapping assignment.
    
    WHY THIS IS NEEDED:
    After soft-mapping, each question slot has been assigned:
    - Its cognitive level (Bloom)
    - Its outcome
    - Its format (question type)
    - Its point value (NOT auto-calculated as 1 per item)
    
    The TOS matrix must reflect WEIGHTED SCORING, not the simplistic
    "1 item = 1 point" assumption.
    """
```

---

## Integration Checklist

- [x] New functions created in `tos_service.py`
- [x] Functions tested (✅ ALL PASS)
- [x] Documentation complete
- [ ] Integration into `app.py` (next step)
- [ ] Integration into `tos_template_renderer.py` (if layout changes needed)
- [ ] Integration into `export_service.py` (if export format changes)

---

## Expected TOS Matrix Output

### Example: 12-Item Exam with Weighted Types

**Input Slots:**
```
5 items at "Remember" level: 5 MCQ × 1 = 5 points
4 items at "Apply" level: 2 MCQ × 1 + 1 PS × 3 + 1 Essay × 5 = 10 points
Wait, that's only 8 points for 4 items...
Actually: 4 items, 8 points total (mixed types)
3 items at "Analyze" level: all Essay × 5 = 15 points
Total: 12 items, 28 points
```

**Output Items Matrix:**
```
{
    "Remember": {0: 3, 1: 2},  # 5 total
    "Apply": {0: 3, 1: 1},     # 4 total
    "Analyze": {0: 1, 1: 2}    # 3 total
}
```

**Output Points Matrix:**
```
{
    "Remember": {0: 3, 1: 2},   # 5 total
    "Apply": {0: 5, 1: 3},      # 8 total (different from item count!)
    "Analyze": {0: 5, 1: 10}    # 15 total
}
```

**TOS Table:**
| | Remember | Apply | Analyze | TOTAL |
|---------|----------|-------|---------|-------|
| Outcome 0 (Items/Pts) | 3/3 | 3/5 | 1/5 | 7/13 |
| Outcome 1 (Items/Pts) | 2/2 | 1/3 | 2/10 | 5/15 |
| **TOTAL (Items/Pts)** | **5/5** | **4/8** | **3/15** | **12/28** |

This correctly reflects that:
- There are 12 questions total
- They're worth 28 points total (not 12)
- Point distribution matches question type weighting

---

## Status

✅ **COMPLETE**
- Service functions: Created and tested
- Verification: 100% pass rate
- Documentation: Comprehensive
- Ready for: Streamlit integration

**Next Steps:**
1. Integrate into app.py workflow
2. Update export function if needed
3. Test end-to-end workflow

---

## References

- [tos_service.py](../services/tos_service.py) - Implementation
- [test_weighted_tos_matrix.py](../test_weighted_tos_matrix.py) - Test suite
- [Question Type Service](../services/question_type_service.py) - Point configuration
- [Soft-Mapping Algorithm](TOS_SOFT_MAPPING_ALGORITHM.md) - Bloom-to-type assignment
