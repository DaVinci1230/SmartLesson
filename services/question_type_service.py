"""
Question Type Distribution Service

This module handles the management of question type distribution and weighted
scoring for the Table of Specifications (TOS). It provides:

1. Data Model: Structure for tracking question types and their properties
2. Validation: Ensures question type distribution matches total test items
3. Computation: Calculates total points based on item counts and point weights
4. Clear Separation: TOS remains a blueprint; this service only validates config

Key Concepts:
- Question Type: Category of assessment items (MCQ, Essay, Problem Solving, etc.)
- No. of Items: Number of questions of this type
- Points Per Item: Weight/value assigned to each item of this type
- Total Points: Sum of (No. of Items × Points Per Item) across all types

The Question Type Distribution is SEPARATE from the Bloom's Taxonomy distribution.
- Bloom's Taxonomy controls WHAT knowledge is assessed
- Question Type Distribution controls HOW items are formatted and weighted
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import uuid


# ======================================================
# DATA MODELS
# ======================================================

@dataclass
class QuestionType:
    """
    Represents a single question type entry in the distribution.
    
    Attributes:
        type: Name of the question type (e.g., "MCQ", "Essay")
        items: Number of items of this type
        points_per_item: Points awarded for each item of this type
        id: Unique identifier for this question type instance
    """
    type: str
    items: int
    points_per_item: float
    id: str = None
    
    def __post_init__(self):
        """Generate UUID if not provided."""
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    def total_points(self) -> float:
        """Calculate total points for this question type."""
        return self.items * self.points_per_item
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "items": self.items,
            "points_per_item": self.points_per_item
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "QuestionType":
        """Create QuestionType from dictionary."""
        return QuestionType(
            type=data.get("type", ""),
            items=data.get("items", 0),
            points_per_item=data.get("points_per_item", 0),
            id=data.get("id", None)  # Will generate new UUID in __post_init__ if None
        )


# ======================================================
# VALIDATION FUNCTIONS
# ======================================================

def validate_question_type_distribution(
    question_types: List[QuestionType],
    total_test_items: int
) -> Tuple[bool, List[str]]:
    """
    Validate the question type distribution against total test items.
    
    Validation Rules:
    1. At least one question type must be defined
    2. All question type items must sum to exactly total_test_items
    3. Each question type must have positive items and points_per_item
    4. No duplicate question type names
    
    Args:
        question_types: List of QuestionType objects
        total_test_items: Expected total number of test items
    
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_error_messages)
        
    Examples:
        >>> valid, errors = validate_question_type_distribution(
        ...     [QuestionType("MCQ", 40, 1), QuestionType("Essay", 2, 10)],
        ...     42
        ... )
        >>> (valid, errors)
        (True, [])
    """
    errors = []
    
    # Validation: At least one type
    if not question_types:
        errors.append("At least one question type must be defined.")
        return False, errors
    
    # Validation: Total items match
    total_items = sum(qt.items for qt in question_types)
    if total_items != total_test_items:
        errors.append(
            f"Sum of question type items ({total_items}) must equal "
            f"total test items ({total_test_items})."
        )
    
    # Validation: Each type has positive values
    for qt in question_types:
        if qt.items <= 0:
            errors.append(
                f"Question type '{qt.type}' must have at least 1 item. "
                f"Current: {qt.items}"
            )
        if qt.points_per_item <= 0:
            errors.append(
                f"Question type '{qt.type}' must have positive points per item. "
                f"Current: {qt.points_per_item}"
            )
    
    # Validation: No duplicate type names
    type_names = [qt.type for qt in question_types]
    duplicates = [name for name in type_names if type_names.count(name) > 1]
    if duplicates:
        errors.append(
            f"Duplicate question types found: {', '.join(set(duplicates))}"
        )
    
    is_valid = len(errors) == 0
    return is_valid, errors


# ======================================================
# COMPUTATION FUNCTIONS
# ======================================================

def compute_total_points(question_types: List[QuestionType]) -> float:
    """
    Compute total points from question type distribution.
    
    Formula: Total Points = Σ(No. of Items × Points Per Item)
    
    Args:
        question_types: List of QuestionType objects
    
    Returns:
        float: Total points
        
    Examples:
        >>> types = [
        ...     QuestionType("MCQ", 40, 1),
        ...     QuestionType("Essay", 2, 10)
        ... ]
        >>> compute_total_points(types)
        60.0
    """
    return sum(qt.total_points() for qt in question_types)


def compute_question_type_totals(
    question_types: List[QuestionType]
) -> Tuple[int, float]:
    """
    Compute BOTH total items and total points from question type distribution.
    
    SINGLE SOURCE OF TRUTH: This is the ONLY place where totals are computed.
    All UI panels, validations, and exports must use this function.
    
    Formula:
    - Total Items = Σ(No. of Items)
    - Total Points = Σ(No. of Items × Points Per Item)
    
    Args:
        question_types: List of QuestionType objects
    
    Returns:
        Tuple[int, float]: (total_items, total_points)
        
    Examples:
        >>> types = [
        ...     QuestionType("MCQ", 40, 1),
        ...     QuestionType("Essay", 2, 10)
        ... ]
        >>> total_items, total_points = compute_question_type_totals(types)
        >>> (total_items, total_points)
        (42, 60.0)
    """
    total_items = sum(qt.items for qt in question_types)
    total_points = sum(qt.total_points() for qt in question_types)
    return total_items, total_points


def compute_points_per_bloom_level(
    question_types: List[QuestionType],
    tos_matrix: Dict,
    bloom_order: List[str] = None
) -> Dict[str, float]:
    """
    Distribute points across Bloom levels proportionally based on question types.
    
    This function takes the question type distribution (total points) and
    proportionally allocates them to each Bloom level based on the TOS matrix.
    
    NOTE: This is an ADVANCED feature used for weighted test generation.
    For basic TOS usage, use compute_total_points() only.
    
    Args:
        question_types: List of QuestionType objects
        tos_matrix: TOS matrix {bloom: {outcome_id: item_count}}
        bloom_order: Order of Bloom levels (for consistency)
    
    Returns:
        Dict[str, float]: Points per Bloom level
        
    Examples:
        >>> types = [QuestionType("MCQ", 40, 1), QuestionType("Essay", 2, 10)]
        >>> matrix = {
        ...     "remember": {0: 10, 1: 10},
        ...     "understand": {0: 10, 1: 10}
        ... }
        >>> points = compute_points_per_bloom_level(types, matrix)
        >>> points["remember"]
        20.0
    """
    if bloom_order is None:
        bloom_order = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
    
    total_points = compute_total_points(question_types)
    
    # Count items per Bloom level
    bloom_item_counts = {}
    for bloom in bloom_order:
        if bloom in tos_matrix:
            count = sum(tos_matrix[bloom].values())
            bloom_item_counts[bloom] = count
        else:
            bloom_item_counts[bloom] = 0
    
    # Distribute points proportionally
    total_items = sum(bloom_item_counts.values())
    if total_items == 0:
        return {bloom: 0.0 for bloom in bloom_order}
    
    bloom_points = {}
    for bloom in bloom_order:
        proportion = bloom_item_counts[bloom] / total_items if total_items > 0 else 0
        bloom_points[bloom] = proportion * total_points
    
    return bloom_points


# ======================================================
# TOS DATA MODEL EXTENSION
# ======================================================

@dataclass
class TOSWithQuestionTypes:
    """
    Extended TOS data structure including question type distribution.
    
    This represents the complete TOS blueprint with both:
    - Bloom's Taxonomy distribution (WHAT to assess)
    - Question Type distribution (HOW to assess)
    
    Attributes:
        metadata: Course and exam metadata
        outcomes: Learning outcomes to assess
        tos_matrix: Bloom-based item distribution
        bloom_totals: Items per Bloom level
        question_types: Question type distribution
        total_items: Total number of test items
        total_points: Computed from question types
    """
    metadata: Dict
    outcomes: List[Dict]
    tos_matrix: Dict
    bloom_totals: Dict
    question_types: List[QuestionType]
    total_items: int
    total_points: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metadata": self.metadata,
            "outcomes": self.outcomes,
            "tos_matrix": self.tos_matrix,
            "bloom_totals": self.bloom_totals,
            "question_types": [qt.to_dict() for qt in self.question_types],
            "total_items": self.total_items,
            "total_points": self.total_points
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "TOSWithQuestionTypes":
        """Create from dictionary."""
        return TOSWithQuestionTypes(
            metadata=data.get("metadata", {}),
            outcomes=data.get("outcomes", []),
            tos_matrix=data.get("tos_matrix", {}),
            bloom_totals=data.get("bloom_totals", {}),
            question_types=[
                QuestionType.from_dict(qt) 
                for qt in data.get("question_types", [])
            ],
            total_items=data.get("total_items", 0),
            total_points=data.get("total_points", 0.0)
        )


# ======================================================
# UTILITY FUNCTIONS
# ======================================================

def create_question_type(
    type_name: str,
    num_items: int,
    points_per_item: float
) -> QuestionType:
    """
    Factory function to create a QuestionType with validation.
    
    Args:
        type_name: Name of the question type
        num_items: Number of items
        points_per_item: Points per item
    
    Returns:
        QuestionType: Validated question type object
        
    Raises:
        ValueError: If validation fails
    """
    qt = QuestionType(type_name, num_items, points_per_item)
    
    if not type_name or type_name.strip() == "":
        raise ValueError("Question type name cannot be empty.")
    if num_items <= 0:
        raise ValueError(f"Number of items must be positive (got {num_items})")
    if points_per_item <= 0:
        raise ValueError(f"Points per item must be positive (got {points_per_item})")
    
    return qt


def get_default_question_types() -> List[QuestionType]:
    """
    Return default question type templates.
    
    These are common question types used in educational assessments.
    Teachers can modify these as needed.
    """
    return [
        QuestionType("Multiple Choice (MCQ)", 0, 1),
        QuestionType("Short Answer", 0, 2),
        QuestionType("Essay", 0, 5),
        QuestionType("Problem Solving", 0, 3),
        QuestionType("Drawing/Diagram", 0, 2),
        QuestionType("Identification", 0, 1),
    ]


def format_question_types_for_display(
    question_types: List[QuestionType]
) -> List[Dict]:
    """
    Format question types for table display in Streamlit.
    
    Args:
        question_types: List of QuestionType objects
    
    Returns:
        List[Dict]: Formatted data for st.dataframe()
    """
    data = []
    for qt in question_types:
        data.append({
            "Question Type": qt.type,
            "No. of Items": qt.items,
            "Points Per Item": qt.points_per_item,
            "Total Points": qt.total_points()
        })
    
    # Add summary row
    if data:
        total_items = sum(row["No. of Items"] for row in data)
        total_points = sum(row["Total Points"] for row in data)
        data.append({
            "Question Type": "TOTAL",
            "No. of Items": total_items,
            "Points Per Item": "-",
            "Total Points": total_points
        })
    
    return data


# ======================================================
# DOCUMENTATION & COMMENTS
# ======================================================

"""
QUESTION TYPE DISTRIBUTION WORKFLOW:

1. Teacher defines question types (MCQ, Essay, Problem Solving, etc.)
   - Each type has: name, number of items, points per item
   - Example: MCQ | 40 items | 1 point each = 40 points

2. System validates distribution
   - Sum of all items must equal total test items
   - No zero items or points
   - No duplicate type names

3. System computes total points
   - Total = Σ(items × points_per_item)

4. System stores with TOS
   - Question Type Distribution is stored separately from Bloom's matrix
   - Both are components of the complete TOS blueprint

5. For test generation (later module: TQS)
   - Uses question types to determine answer format (MC, essay, etc.)
   - Uses Bloom's matrix to determine content level (remember, apply, etc.)
   - Combines both for complete question specification

KEY PRINCIPLE: SEPARATION OF CONCERNS
- TOS = Blueprint for what and how to assess
- Question Type Distribution = Configuration for question format and weighting
- Test Generation = Uses both to create actual questions

This keeps TOS focused on assessment design, not question creation.
"""
