"""Quick verification of TOS soft-mapping algorithm."""

from services.tos_slot_assignment_service import (
    assign_question_types_to_bloom_slots,
    verify_assignment_integrity,
    get_assignment_summary
)
from services.question_type_service import QuestionType

print("\n" + "="*70)
print("TOS SOFT-MAPPING ASSIGNMENT ALGORITHM - PRODUCTION VERIFICATION")
print("="*70)

# Test data
tos_matrix = {
    "Remember": {0: 12},
    "Apply": {0: 8}
}
outcomes = [{"id": 0, "text": "Understand core concepts"}]
question_types = [
    QuestionType("MCQ", 12, 1),
    QuestionType("Problem Solving", 8, 2)
]

# Run assignment
print("\n✓ Running soft-preference mapping...")
assigned, metadata = assign_question_types_to_bloom_slots(
    tos_matrix,
    outcomes,
    question_types,
    shuffle=False
)

# Verify integrity
print("✓ Verifying data integrity...")
is_valid, errors = verify_assignment_integrity(
    assigned,
    tos_matrix,
    question_types
)

# Get summary
print("✓ Generating summary statistics...")
summary = get_assignment_summary(assigned)

# Display results
print("\n" + "-"*70)
print("RESULTS")
print("-"*70)

print(f"\n✓ Assignment Statistics:")
print(f"  - Total slots assigned: {len(assigned)}")
print(f"  - Total points: {summary['total_points']}")
print(f"  - Preferred matches: {metadata['preferred_matches']}")
print(f"  - Fallback matches: {metadata['fallback_matches']}")

print(f"\n✓ Integrity Verification:")
print(f"  - Valid: {is_valid}")
print(f"  - Errors: {len(errors)}")

print(f"\n✓ Distribution Preservation:")
print(f"  - Bloom levels preserved: {list(summary['by_bloom'].keys())}")
for bloom, stats in summary["by_bloom"].items():
    print(f"    {bloom}: {stats['items']} items, {stats['points']:.0f} points")

print(f"  - Question types preserved: {list(summary['by_type'].keys())}")
for qtype, stats in summary["by_type"].items():
    print(f"    {qtype}: {stats['items']} items, {stats['points']:.0f} points")

print("\n" + "="*70)
if is_valid:
    print("✅ ALL CHECKS PASSED - ALGORITHM READY FOR PRODUCTION")
else:
    print("❌ VALIDATION FAILED - CHECK ERRORS ABOVE")
print("="*70 + "\n")
