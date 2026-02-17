"""
Export Service - TOS Export Functions

NOTE: This module now delegates to tos_template_renderer.py for fixed
institutional template rendering. The old dynamic rendering is deprecated.

For new TOS exports, use:
    from services.tos_template_renderer import export_tos_fixed_template

This maintains AI logic separation and enforces strict template structure.
"""

from services.tos_template_renderer import export_tos_fixed_template
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter
from io import BytesIO

BLOOM_ORDER = [
    "remember",
    "understand",
    "apply",
    "analyze",
    "evaluate",
    "create"
]
blooms = [b.upper() for b in BLOOM_ORDER]


# ======================================================
# DEPRECATED FUNCTION (for backward compatibility)
# ======================================================

def export_tos_exact_format(meta, outcomes, tos_matrix, total_items, total_points):
    """
    DEPRECATED: Use export_tos_fixed_template() instead.
    
    This function is preserved for backward compatibility but now
    delegates to the fixed template renderer.
    """
    return export_tos_fixed_template(meta, outcomes, tos_matrix, total_items, total_points)


