"""
TOS SERVICE INPUT CONTRACT

Expected inputs:
- outcomes: list of dicts
    {
        "id": int,
        "text": str,
        "hours": float
    }

- bloom_weights: dict
    {
        "Remember": int,
        "Understand": int,
        "Apply": int,
        "Analyze": int,
        "Evaluate": int,
        "Create": int
    }

- total_items: int
"""
import math

BLOOM_LEVELS = [
    "Remember",
    "Understand",
    "Apply",
    "Analyze",
    "Evaluate",
    "Create"
]


def compute_bloom_item_totals(bloom_weights, total_items):
    """
    Step 1: Compute fixed number of items per Bloom level
    """
    bloom_items = {}
    remainder = total_items

    for bloom in BLOOM_LEVELS[:-1]:
        count = int(total_items * (bloom_weights[bloom] / 100))
        bloom_items[bloom] = count
        remainder -= count

    # Assign remaining items to last Bloom level
    bloom_items[BLOOM_LEVELS[-1]] = remainder

    return bloom_items


def compute_outcome_weights(outcomes):
    """
    Step 2: Compute outcome weights based on hours
    """
    total_hours = sum(o["hours"] for o in outcomes)

    if total_hours == 0:
        raise ValueError("Total outcome hours cannot be zero.")

    for o in outcomes:
        o["weight"] = o["hours"] / total_hours

    return outcomes


def allocate_items_largest_remainder(outcomes, bloom_items):
    """
    Step 3: Allocate Bloom items to outcomes using
    Largest Remainder Method
    """
    tos_matrix = {}

    for bloom, total_bloom_items in bloom_items.items():
        raw = []
        for o in outcomes:
            value = total_bloom_items * o["weight"]
            raw.append((o["id"], value))

        # Floor values
        allocated = {oid: math.floor(v) for oid, v in raw}
        used = sum(allocated.values())
        remaining = total_bloom_items - used

        # Sort by remainder
        remainders = sorted(
            raw,
            key=lambda x: x[1] - math.floor(x[1]),
            reverse=True
        )

        for oid, _ in remainders[:remaining]:
            allocated[oid] += 1

        tos_matrix[bloom] = allocated

    return tos_matrix


def generate_tos(outcomes, bloom_weights, total_items):
    """
    MASTER FUNCTION
    """
    bloom_items = compute_bloom_item_totals(
        bloom_weights, total_items
    )

    outcomes = compute_outcome_weights(outcomes)

    tos_matrix = allocate_items_largest_remainder(
        outcomes, bloom_items
    )

    return {
        "bloom_totals": bloom_items,
        "tos_matrix": tos_matrix
    }


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
    
    Example:
    Before: Remember = 10 items, 10 points (1-1 mapping)
    After:  Remember = 7 MCQ × 1pt + 3 ID × 1pt = 10 items, 10 points
            OR
            Remember = 5 MCQ × 1pt + 2 Essay × 5pts = 7 items, 15 points
    
    The key insight: Item count and point totals are NOW INDEPENDENT.
    
    Args:
        assigned_slots: List of dicts with structure:
            {
                "outcome_id": int,
                "outcome_text": str,
                "bloom": str,
                "type": str,
                "points": float
            }
    
    Returns:
        Tuple of (tos_matrix, bloom_totals, points_matrix)
        where:
        - tos_matrix: {bloom: {outcome_id: item_count}}
        - bloom_totals: {bloom: item_count}
        - points_matrix: {bloom: {outcome_id: total_points}}
    
    INTEGRITY:
    - Total items = len(assigned_slots)
    - Total points = sum(slot["points"] for slot in assigned_slots)
    - Each (outcome, bloom) pair computed from actual slots
    """
    
    # Initialize empty matrices
    tos_items_matrix = {}
    tos_points_matrix = {}
    
    # Initialize all cells to 0 to ensure complete structure
    for slot in assigned_slots:
        bloom = slot["bloom"]
        outcome_id = slot["outcome_id"]
        
        if bloom not in tos_items_matrix:
            tos_items_matrix[bloom] = {}
            tos_points_matrix[bloom] = {}
        
        if outcome_id not in tos_items_matrix[bloom]:
            tos_items_matrix[bloom][outcome_id] = 0
            tos_points_matrix[bloom][outcome_id] = 0
    
    # Aggregate from assigned slots
    for slot in assigned_slots:
        bloom = slot["bloom"]
        outcome_id = slot["outcome_id"]
        points = slot["points"]
        
        # Increment item count
        tos_items_matrix[bloom][outcome_id] += 1
        
        # Add to points total
        tos_points_matrix[bloom][outcome_id] += points
    
    # Compute Bloom totals (items only, not points)
    bloom_totals = {}
    for bloom in tos_items_matrix:
        bloom_totals[bloom] = sum(tos_items_matrix[bloom].values())
    
    return tos_items_matrix, bloom_totals, tos_points_matrix


def compute_tos_totals(tos_items_matrix, tos_points_matrix):
    """
    Compute TOTAL row for TOS table.
    
    Returns:
        Tuple of (total_items, total_points, items_by_bloom, points_by_bloom)
    """
    total_items = 0
    total_points = 0
    items_by_bloom = {}
    points_by_bloom = {}
    
    # Sum by bloom level
    for bloom in tos_items_matrix:
        items_by_bloom[bloom] = sum(tos_items_matrix[bloom].values())
        points_by_bloom[bloom] = sum(tos_points_matrix[bloom].values())
        
        total_items += items_by_bloom[bloom]
        total_points += points_by_bloom[bloom]
    
    return total_items, total_points, items_by_bloom, points_by_bloom


print("tos_service loaded successfully")

