"""
TOS Validation Module

Provides validation utilities for TOS files and data structures.
Ensures uploaded TOS meets requirements for TQS generation.
"""

import logging
from typing import Tuple, List, Dict, Any, Optional

logger = logging.getLogger(__name__)

BLOOM_LEVELS = [
    "Remember",
    "Understand",
    "Apply",
    "Analyze",
    "Evaluate",
    "Create"
]


class TOSValidator:
    """Comprehensive validator for TOS structures."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate(self, tos_data: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate complete TOS structure.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # Check structure
        self._validate_structure(tos_data)
        
        if self.errors:
            return False, self.errors, self.warnings
        
        # Check content
        self._validate_outcomes(tos_data)
        self._validate_bloom_distribution(tos_data)
        self._validate_tos_matrix(tos_data)
        self._validate_consistency(tos_data)
        
        return len(self.errors) == 0, self.errors, self.warnings
    
    def _validate_structure(self, tos_data: Dict[str, Any]):
        """Validate required top-level structure."""
        required_fields = [
            "learning_outcomes",
            "bloom_distribution",
            "tos_matrix"
        ]
        
        for field in required_fields:
            if field not in tos_data:
                self.errors.append(f"Missing required field: {field}")
        
        if not isinstance(tos_data.get("learning_outcomes"), list):
            self.errors.append("learning_outcomes must be a list")
        
        if not isinstance(tos_data.get("bloom_distribution"), dict):
            self.errors.append("bloom_distribution must be a dict")
        
        if not isinstance(tos_data.get("tos_matrix"), dict):
            self.errors.append("tos_matrix must be a dict")
    
    def _validate_outcomes(self, tos_data: Dict[str, Any]):
        """Validate learning outcomes list."""
        outcomes = tos_data.get("learning_outcomes", [])
        
        if not outcomes:
            self.errors.append("learning_outcomes cannot be empty")
            return
        
        for i, outcome in enumerate(outcomes):
            if not isinstance(outcome, dict):
                self.errors.append(f"Outcome {i}: must be a dict, got {type(outcome)}")
                continue
            
            # Check text field (required)
            if "text" not in outcome and "description" not in outcome:
                self.errors.append(
                    f"Outcome {i}: must have 'text' or 'description' field"
                )
            
            # Check ID field (required for matrix cross-reference)
            if "id" not in outcome:
                self.warnings.append(
                    f"Outcome {i}: missing 'id' field (will be auto-assigned)"
                )
    
    def _validate_bloom_distribution(self, tos_data: Dict[str, Any]):
        """Validate Bloom's taxonomy distribution."""
        bloom_dist = tos_data.get("bloom_distribution", {})
        
        if not bloom_dist:
            self.errors.append("bloom_distribution cannot be empty")
            return
        
        # Check all levels are present
        missing_levels = [b for b in BLOOM_LEVELS if b not in bloom_dist]
        if missing_levels:
            self.errors.append(
                f"Missing Bloom levels: {', '.join(missing_levels)}"
            )
        
        # Check all values are numeric
        for bloom, value in bloom_dist.items():
            if not isinstance(value, (int, float)):
                self.errors.append(
                    f"Bloom '{bloom}': value must be numeric, got {type(value)}"
                )
            elif value < 0:
                self.errors.append(
                    f"Bloom '{bloom}': value cannot be negative"
                )
        
        # Check sum (if percentages)
        total = sum(v for v in bloom_dist.values() if isinstance(v, (int, float)))
        if 90 <= total <= 110:  # Allow 10% variance for counts vs percentages
            pass
        elif total in [100]:  # Standard percentage check
            pass
        else:
            self.warnings.append(
                f"Bloom distribution sum is {total}. "
                f"Expected 100 (percentages) or counts summing to total items."
            )
    
    def _validate_tos_matrix(self, tos_data: Dict[str, Any]):
        """Validate TOS matrix structure and values."""
        tos_matrix = tos_data.get("tos_matrix", {})
        
        if not tos_matrix:
            self.errors.append("tos_matrix cannot be empty")
            return
        
        # Check all Bloom levels are in matrix
        for bloom in BLOOM_LEVELS:
            if bloom not in tos_matrix:
                self.warnings.append(f"TOS matrix missing Bloom level: {bloom}")
        
        # Validate each row
        for bloom, row in tos_matrix.items():
            if not isinstance(row, dict):
                self.errors.append(
                    f"TOS matrix row for '{bloom}' must be a dict, got {type(row)}"
                )
                continue
            
            for outcome_id, count in row.items():
                # Convert outcome_id to canonical form if it's a number
                if not isinstance(count, (int, float)):
                    self.errors.append(
                        f"TOS matrix[{bloom}][{outcome_id}]: "
                        f"must be numeric, got {type(count)}"
                    )
                elif count < 0:
                    self.errors.append(
                        f"TOS matrix[{bloom}][{outcome_id}]: "
                        f"cannot be negative"
                    )
    
    def _validate_consistency(self, tos_data: Dict[str, Any]):
        """Validate consistency between different sections."""
        outcomes = tos_data.get("learning_outcomes", [])
        tos_matrix = tos_data.get("tos_matrix", {})
        
        # Extract outcome IDs - normalize to integers for comparison
        outcome_ids = set()
        for outcome in outcomes:
            oid = outcome.get("id")
            if oid is not None:
                # Normalize to int if possible
                try:
                    oid = int(oid) if isinstance(oid, str) else oid
                except (ValueError, TypeError):
                    pass
                outcome_ids.add(oid)
        
        # Check matrix references valid outcomes
        for bloom, row in tos_matrix.items():
            for outcome_id in row.keys():
                # Normalize outcome_id for comparison
                compare_id = outcome_id
                try:
                    compare_id = int(outcome_id) if isinstance(outcome_id, str) else outcome_id
                except (ValueError, TypeError):
                    pass
                    
                if outcome_ids and compare_id not in outcome_ids:
                    self.warnings.append(
                        f"TOS matrix references outcome_id {outcome_id} "
                        f"not found in learning_outcomes"
                    )
        
        # Compute total items
        total_items = 0
        for row in tos_matrix.values():
            for count in row.values():
                if isinstance(count, (int, float)):
                    total_items += count
        
        if total_items == 0:
            self.errors.append("TOS matrix contains no items (all counts are 0)")
        else:
            tos_data["total_items"] = total_items


def validate_tos_structure(
    tos_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Quick validation of TOS structure.
    
    Returns:
        Tuple of (is_valid, message)
    """
    validator = TOSValidator()
    is_valid, errors, warnings = validator.validate(tos_data)
    
    if errors:
        msg = "Validation errors:\n" + "\n".join(f"- {e}" for e in errors)
        if warnings:
            msg += "\n\nWarnings:\n" + "\n".join(f"- {w}" for w in warnings)
        return False, msg
    elif warnings:
        msg = "Validation warnings:\n" + "\n".join(f"- {w}" for w in warnings)
        return True, msg
    else:
        return True, "TOS structure is valid"


def validate_outcomes_coverage(
    tos_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Validate that all outcomes have at least one question.
    
    Returns:
        Tuple of (is_valid, message)
    """
    outcomes = tos_data.get("learning_outcomes", [])
    tos_matrix = tos_data.get("tos_matrix", {})
    
    outcome_ids = {o.get("id") for o in outcomes if "id" in o}
    
    uncovered = []
    for oid in outcome_ids:
        total_for_outcome = 0
        for row in tos_matrix.values():
            # Try both the original ID and its integer/string conversion
            count = row.get(oid, 0)
            if count == 0 and isinstance(oid, str):
                count = row.get(int(oid) if oid.isdigit() else oid, 0)
            elif count == 0 and isinstance(oid, int):
                count = row.get(str(oid), 0)
            total_for_outcome += count
        
        if total_for_outcome == 0:
            uncovered.append(oid)
    
    if uncovered:
        return False, f"Outcomes with no questions: {uncovered}"
    
    return True, "All outcomes have at least one question"


def validate_bloom_coverage(
    tos_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Validate that all Bloom levels have at least one question.
    
    Returns:
        Tuple of (is_valid, message)
    """
    tos_matrix = tos_data.get("tos_matrix", {})
    
    uncovered = []
    for bloom in BLOOM_LEVELS:
        if bloom not in tos_matrix:
            uncovered.append(bloom)
            continue
        
        total_for_bloom = sum(tos_matrix[bloom].values())
        if total_for_bloom == 0:
            uncovered.append(bloom)
    
    if uncovered:
        return False, f"Bloom levels with no questions: {uncovered}"
    
    return True, "All Bloom levels are represented"


def check_tos_readiness(
    tos_data: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Comprehensive readiness check for TQS generation.
    
    Returns:
        Tuple of (is_ready, issues_or_messages)
    """
    issues = []
    
    # Basic structure
    validator = TOSValidator()
    is_valid, errors, warnings = validator.validate(tos_data)
    
    if errors:
        issues.extend([f"ERROR: {e}" for e in errors])
    
    if warnings:
        issues.extend([f"WARNING: {w}" for w in warnings])
    
    # Coverage checks
    valid, msg = validate_outcomes_coverage(tos_data)
    if not valid:
        issues.append(f"ERROR: {msg}")
    
    valid, msg = validate_bloom_coverage(tos_data)
    if not valid:
        issues.append(f"ERROR: {msg}")
    
    return len([i for i in issues if i.startswith("ERROR")]) == 0, issues


def get_tos_statistics(tos_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate statistics about a TOS structure.
    
    Returns:
        Dict with various TOS metrics
    """
    outcomes = tos_data.get("learning_outcomes", [])
    tos_matrix = tos_data.get("tos_matrix", {})
    bloom_dist = tos_data.get("bloom_distribution", {})
    
    # Count outcomes
    num_outcomes = len(outcomes)
    
    # Count items per bloom
    items_per_bloom = {}
    total_items = 0
    for bloom in BLOOM_LEVELS:
        count = sum(tos_matrix.get(bloom, {}).values())
        items_per_bloom[bloom] = count
        total_items += count
    
    # Count items per outcome
    items_per_outcome = {}
    for outcome in outcomes:
        oid = outcome.get("id")
        if oid is not None:
            count = 0
            for row in tos_matrix.values():
                # Try both the original ID and its conversion
                row_count = row.get(oid, 0)
                if row_count == 0 and isinstance(oid, str):
                    row_count = row.get(int(oid) if oid.isdigit() else oid, 0)
                elif row_count == 0 and isinstance(oid, int):
                    row_count = row.get(str(oid), 0)
                count += row_count
            items_per_outcome[oid] = count
    
    return {
        "num_outcomes": num_outcomes,
        "total_items": total_items,
        "items_per_bloom": items_per_bloom,
        "items_per_outcome": items_per_outcome,
        "bloom_distribution": bloom_dist,
        "avg_items_per_outcome": (
            total_items / num_outcomes if num_outcomes > 0 else 0
        ),
        "bloom_levels_covered": len([c for c in items_per_bloom.values() if c > 0])
    }
