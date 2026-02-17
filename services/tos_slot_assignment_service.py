"""
TOS Soft-Mapping Assignment Service

This module assigns question types to Bloom taxonomy slots using a soft-preference
mapping algorithm. It bridges the gap between:

1. TOS Bloom Distribution (WHAT to assess - locked)
2. Question Type Distribution (HOW to assess - locked)

This service creates deterministic exam blueprints that preserve:
✓ Exact Bloom distribution (from TOS matrix)
✓ Exact Question Type distribution (from config)
✓ Exact Points per Item (from teacher configuration)

Key Concept: SOFT-PREFERENCE MAPPING
- Prefers question types that align with cognitive difficulty
- Falls back to any available type if preference unavailable
- Guarantees 100% slot coverage with no gaps or duplication
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import random


@dataclass
class BloomSlot:
    """Represents a single assessment item slot from TOS Bloom distribution."""
    outcome_id: int
    outcome_text: str
    bloom_level: str
    
    def to_dict(self) -> Dict:
        return {
            "outcome_id": self.outcome_id,
            "outcome_text": self.outcome_text,
            "bloom_level": self.bloom_level
        }


@dataclass
class TypeSlot:
    """Represents a single assessment item slot from Question Type distribution."""
    question_type: str
    points_per_item: float
    
    def to_dict(self) -> Dict:
        return {
            "type": self.question_type,
            "points": self.points_per_item
        }


@dataclass
class AssignedSlot:
    """Result of mapping a type to a Bloom slot."""
    outcome_id: int
    outcome_text: str
    bloom_level: str
    question_type: str
    points: float
    
    def to_dict(self) -> Dict:
        return {
            "outcome_id": self.outcome_id,
            "outcome_text": self.outcome_text,
            "bloom_level": self.bloom_level,
            "question_type": self.question_type,
            "points": self.points
        }


# ======================================================
# SOFT-PREFERENCE MAPPING CONFIGURATION
# ======================================================

PREFERRED_TYPES = {
    """
    WHY THIS MAPPING?
    
    This mapping aligns cognitive complexity with assessment format:
    
    Remember:
    - Recall facts → MCQ (quick check) or Identification (match)
    - Prefers: MCQ (fastest verification), Identification (pattern matching)
    
    Understand:
    - Explain concepts → MCQ (comprehension check) or Short Answer
    - Prefers: MCQ (concept verification), Short Answer (explain reasoning)
    
    Apply:
    - Use knowledge in context → MCQ (simulated scenario) or Problem Solving
    - Prefers: MCQ (scenario-based), Problem Solving (hands-on application)
    
    Analyze:
    - Break down components → Short Answer (explain) or Problem Solving
    - Prefers: Short Answer (written analysis), Problem Solving (complex steps)
    
    Evaluate:
    - Judge and justify → Essay (deep argument) or Problem Solving (critical thinking)
    - Prefers: Essay (extended argument), Problem Solving (judgment with evidence)
    
    Create:
    - Produce original work → Essay (written composition) or Drawing (visual design)
    - Prefers: Essay (new composition), Drawing (design/visualization)
    """
    "Remember": ["MCQ", "Identification"],
    "Understand": ["MCQ", "Short Answer"],
    "Apply": ["MCQ", "Problem Solving"],
    "Analyze": ["Short Answer", "Problem Solving"],
    "Evaluate": ["Essay", "Problem Solving"],
    "Create": ["Essay", "Drawing/Diagram"],
}


# ======================================================
# SLOT EXPANSION FUNCTIONS
# ======================================================

def expand_bloom_slots(
    tos_matrix: Dict[str, Dict[int, int]],
    outcomes: List[Dict]
) -> List[BloomSlot]:
    """
    Expand TOS Bloom matrix into individual cognitive slots.
    
    WHAT THIS DOES:
    Takes the Bloom distribution (e.g., "Remember: 10 items, Apply: 15 items")
    and expands it into individual slots, each tagged with its outcome and level.
    
    Example Input:
        tos_matrix = {
            "Remember": {0: 5, 1: 5},      # 5 items from outcome 0, 5 from outcome 1
            "Apply": {0: 8, 1: 7}
        }
        outcomes = [
            {"id": 0, "text": "Define key concepts"},
            {"id": 1, "text": "Classify entities"}
        ]
    
    Example Output:
        [
            BloomSlot(outcome_id=0, bloom_level="Remember", ...),
            BloomSlot(outcome_id=0, bloom_level="Remember", ...),
            ...
            BloomSlot(outcome_id=0, bloom_level="Apply", ...),
            ...
        ]
    
    Args:
        tos_matrix: TOS distribution {bloom_level: {outcome_id: item_count}}
        outcomes: List of learning outcomes with id and text
    
    Returns:
        List[BloomSlot]: Individual slots (total count = sum of all items)
    """
    slots = []
    
    # Iterate through each Bloom level and outcome combination
    for bloom_level in tos_matrix:
        for outcome_id in tos_matrix[bloom_level]:
            item_count = tos_matrix[bloom_level][outcome_id]
            
            # Find the outcome text
            outcome_text = next(
                (o["text"] for o in outcomes if o["id"] == outcome_id),
                f"Outcome {outcome_id}"
            )
            
            # Create individual slots for each item
            for _ in range(item_count):
                slots.append(
                    BloomSlot(
                        outcome_id=outcome_id,
                        outcome_text=outcome_text,
                        bloom_level=bloom_level
                    )
                )
    
    return slots


def expand_type_slots(
    question_types_list: List
) -> List[TypeSlot]:
    """
    Expand Question Type distribution into individual type slots.
    
    WHAT THIS DOES:
    Takes question type configuration (e.g., "MCQ: 40 items @ 1 point each")
    and expands into individual slots, each preserving the points value.
    
    CRITICAL: Points are NOT auto-calculated or distributed.
    Each slot PRESERVES the points_per_item from the configuration.
    
    Example Input:
        question_types = [
            QuestionType("MCQ", 40, 1),        # 40 MCQ @ 1 point each
            QuestionType("Essay", 2, 10)       # 2 essays @ 10 points each
        ]
    
    Example Output:
        [
            TypeSlot(question_type="MCQ", points_per_item=1),
            TypeSlot(question_type="MCQ", points_per_item=1),
            ... (40 times)
            TypeSlot(question_type="Essay", points_per_item=10),
            TypeSlot(question_type="Essay", points_per_item=10)
        ]
    
    Args:
        question_types_list: List of QuestionType objects
        
    Returns:
        List[TypeSlot]: Individual type slots (total count = total items)
    """
    slots = []
    
    for qt in question_types_list:
        # Create individual slots for each item of this type
        for _ in range(qt.items):
            slots.append(
                TypeSlot(
                    question_type=qt.type,
                    points_per_item=qt.points_per_item
                )
            )
    
    return slots


# ======================================================
# SOFT-PREFERENCE MAPPING ALGORITHM
# ======================================================

def assign_question_types_to_bloom_slots(
    tos_matrix: Dict[str, Dict[int, int]],
    outcomes: List[Dict],
    question_types_list: List,
    shuffle: bool = True
) -> Tuple[List[AssignedSlot], Dict[str, any]]:
    """
    Assign question types to Bloom slots using soft-preference mapping.
    
    WHAT THIS DOES:
    
    This is the CORE ALGORITHM that bridges assessment design and implementation.
    It takes:
    - TOS Bloom distribution (locked - what to assess)
    - Question Type distribution (locked - how to assess)
    
    And produces:
    - A complete exam blueprint mapping each question to its cognitive level,
      format, and point value.
    
    ALGORITHM OVERVIEW:
    
    1. Expand TOS matrix into individual Bloom slots (one per item)
    2. Expand question type config into individual type slots (one per item)
    3. For each Bloom slot:
       a. Look for available type matching preferred types for that bloom level
       b. If preferred type exists → assign it
       c. If none available → assign any remaining type
       d. Mark type slot as used
    4. Return final mapping with integrity preservation
    
    WHY SOFT-PREFERENCE MAPPING?
    
    A hard mapping (e.g., "Always use MCQ for Remember") is too rigid—
    teacher might configure 0 MCQs, or preferences might conflict.
    
    Soft mapping:
    - PREFERS types aligned with cognitive complexity
    - FALLS BACK to any available type if preference unavailable
    - GUARANTEES complete coverage (no gaps, no duplication)
    - PRESERVES teacher's exact type and point configuration
    
    WHY NOT AUTO-ASSIGN POINTS?
    
    The teacher explicitly configured:
    - "MCQ: 40 items @ 1 point each"
    - "Essay: 2 items @ 10 points each"
    
    This is NOT accidental distribution—it's intentional weighting:
    MCQ = quick check (lower weight)
    Essay = deep thinking (higher weight)
    
    Auto-assigning would override this intent. We must preserve it exactly.
    
    INTEGRITY PRESERVATION:
    
    This algorithm guarantees:
    ✓ Exact Bloom distribution (every slot has its bloom level)
    ✓ Exact Type distribution (every type is used exactly as configured)
    ✓ Exact Points (every item has its configured points)
    ✓ No duplication (no type/slot used twice)
    ✓ No gaps (all slots filled, no leftovers)
    
    Args:
        tos_matrix: TOS {bloom_level: {outcome_id: count}}
        outcomes: List of learning outcomes
        question_types_list: List of QuestionType objects
        shuffle: Whether to randomize final order (default: True)
    
    Returns:
        Tuple[assigned_slots, metadata]:
        - assigned_slots: List[AssignedSlot] - complete exam blueprint
        - metadata: Coverage statistics and validation info
    
    Raises:
        ValueError: If Bloom slots ≠ Type slots (integrity violation)
    """
    
    # ========================================================================
    # STEP 1: EXPAND BLOOM SLOTS (WHAT to assess)
    # ========================================================================
    bloom_slots = expand_bloom_slots(tos_matrix, outcomes)
    total_bloom_items = len(bloom_slots)
    
    # ========================================================================
    # STEP 2: EXPAND TYPE SLOTS (HOW to assess, with EXACT points)
    # ========================================================================
    type_slots = expand_type_slots(question_types_list)
    total_type_items = len(type_slots)
    
    # ========================================================================
    # VALIDATION: Bloom slots must equal Type slots
    # ========================================================================
    if total_bloom_items != total_type_items:
        raise ValueError(
            f"Integrity violation: Bloom distribution ({total_bloom_items} items) "
            f"does not match question type distribution ({total_type_items} items). "
            f"This indicates misconfiguration in TOS or question types."
        )
    
    # ========================================================================
    # STEP 3: SOFT-PREFERENCE MAPPING
    # ========================================================================
    
    # Make a mutable copy of type slots (we'll remove as we assign)
    available_types = list(type_slots)
    assigned = []
    
    # Metrics for tracking assignment quality
    preferred_matches = 0
    fallback_matches = 0
    
    for bloom_slot in bloom_slots:
        bloom_level = bloom_slot.bloom_level
        
        # Get preferred types for this Bloom level
        preferred = PREFERRED_TYPES.get(bloom_level, [])
        
        # Try to find a preferred type in available pool
        assigned_type = None
        assigned_idx = None
        
        for pref_type in preferred:
            # Look for this preference in available types
            for idx, type_slot in enumerate(available_types):
                if type_slot.question_type == pref_type:
                    assigned_type = type_slot
                    assigned_idx = idx
                    preferred_matches += 1
                    break
            if assigned_type is not None:
                break
        
        # Fallback: If no preferred type available, use any remaining type
        if assigned_type is None:
            if available_types:
                assigned_type = available_types[0]
                assigned_idx = 0
                fallback_matches += 1
            else:
                # Should never happen if validation passed
                raise ValueError("No available question types to assign (logic error)")
        
        # Create the combined assignment
        assigned_slot = AssignedSlot(
            outcome_id=bloom_slot.outcome_id,
            outcome_text=bloom_slot.outcome_text,
            bloom_level=bloom_slot.bloom_level,
            question_type=assigned_type.question_type,
            points=assigned_type.points_per_item
        )
        assigned.append(assigned_slot)
        
        # Remove the used type slot from available pool
        available_types.pop(assigned_idx)
    
    # ========================================================================
    # STEP 4: RANDOMIZE (for realistic exam distribution)
    # ========================================================================
    if shuffle:
        random.shuffle(assigned)
    
    # ========================================================================
    # METADATA: Coverage statistics
    # ========================================================================
    metadata = {
        "total_slots": len(assigned),
        "preferred_matches": preferred_matches,
        "fallback_matches": fallback_matches,
        "coverage_quality": f"{(preferred_matches / len(assigned) * 100):.1f}% preferred",
        "integrity_check": {
            "bloom_slots_expanded": total_bloom_items,
            "type_slots_expanded": total_type_items,
            "slots_assigned": len(assigned),
            "all_types_used": len(available_types) == 0,
            "valid": (total_bloom_items == total_type_items == len(assigned))
        }
    }
    
    return assigned, metadata


# ======================================================
# INTEGRITY VERIFICATION
# ======================================================

def verify_assignment_integrity(
    assigned_slots: List[AssignedSlot],
    tos_matrix: Dict[str, Dict[int, int]],
    question_types_list: List
) -> Tuple[bool, List[str]]:
    """
    Verify that assignment preserves all distributions.
    
    Checks:
    1. Bloom distribution preserved (item count per level matches TOS)
    2. Question type distribution preserved (count and points match config)
    3. No duplicates (each type slot used exactly once)
    4. No gaps (all slots filled)
    5. Total points correct (matches configuration)
    
    Args:
        assigned_slots: Output from assign_question_types_to_bloom_slots()
        tos_matrix: Original TOS matrix
        question_types_list: Original question type list
    
    Returns:
        Tuple[is_valid, list_of_errors]
    """
    errors = []
    
    # Check 1: Bloom distribution
    bloom_counts = {}
    for slot in assigned_slots:
        bloom_counts[slot.bloom_level] = bloom_counts.get(slot.bloom_level, 0) + 1
    
    for bloom_level in tos_matrix:
        expected_count = sum(tos_matrix[bloom_level].values())
        actual_count = bloom_counts.get(bloom_level, 0)
        if expected_count != actual_count:
            errors.append(
                f"Bloom '{bloom_level}' expected {expected_count} items, "
                f"got {actual_count}"
            )
    
    # Check 2: Question type distribution
    type_counts = {}
    type_points_sum = {}
    for slot in assigned_slots:
        type_counts[slot.question_type] = type_counts.get(slot.question_type, 0) + 1
        pts_key = slot.question_type
        type_points_sum[pts_key] = type_points_sum.get(pts_key, 0) + slot.points
    
    for qt in question_types_list:
        expected_count = qt.items
        actual_count = type_counts.get(qt.type, 0)
        if expected_count != actual_count:
            errors.append(
                f"Question type '{qt.type}' expected {expected_count} items, "
                f"got {actual_count}"
            )
        
        expected_points = qt.items * qt.points_per_item
        actual_points = type_points_sum.get(qt.type, 0)
        if expected_points != actual_points:
            errors.append(
                f"Question type '{qt.type}' expected {expected_points} total points, "
                f"got {actual_points}"
            )
    
    # Check 3 & 4: Implicit in the algorithm, but verify no duplicates
    if len(assigned_slots) != len(set(id(slot) for slot in assigned_slots)):
        errors.append("Duplicate assignments detected (data structure issue)")
    
    is_valid = len(errors) == 0
    return is_valid, errors


# ======================================================
# UTILITY FUNCTIONS
# ======================================================

def get_assignment_summary(assigned_slots: List[AssignedSlot]) -> Dict:
    """
    Generate summary statistics of the exam blueprint assignment.
    
    Returns breakdown by:
    - Bloom level (how many items per level)
    - Question type (how many items per type)
    - Total points (by type, by level, overall)
    """
    summary = {
        "by_bloom": {},
        "by_type": {},
        "total_items": len(assigned_slots),
        "total_points": 0
    }
    
    for slot in assigned_slots:
        # By Bloom
        if slot.bloom_level not in summary["by_bloom"]:
            summary["by_bloom"][slot.bloom_level] = {"items": 0, "points": 0}
        summary["by_bloom"][slot.bloom_level]["items"] += 1
        summary["by_bloom"][slot.bloom_level]["points"] += slot.points
        
        # By Type
        if slot.question_type not in summary["by_type"]:
            summary["by_type"][slot.question_type] = {"items": 0, "points": 0}
        summary["by_type"][slot.question_type]["items"] += 1
        summary["by_type"][slot.question_type]["points"] += slot.points
        
        # Total
        summary["total_points"] += slot.points
    
    return summary


def format_assignment_for_export(assigned_slots: List[AssignedSlot]) -> List[Dict]:
    """Format assigned slots for JSON or database storage."""
    return [slot.to_dict() for slot in assigned_slots]
