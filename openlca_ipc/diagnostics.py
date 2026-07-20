# ============================================================================
# FILE: openlca_ipc/diagnostics.py
# ============================================================================

"""
Runtime reliability checks for calculation results.

These are cheap invariants that catch the most common ways a result can be
misread or mis-linked. They return human-readable warning strings rather than
raising, so callers can log them, surface them in a ``ResultSummary.warnings``
list, or assert on them in tests.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)


def check_result_consistency(
    result,
    *,
    rel_tol: float = 1e-3,
    abs_tol: float = 1e-12,
) -> List[str]:
    """
    Check internal consistency of a calculation result.

    Currently verifies, for every impact category, that the per-process
    contributions sum to the reported total (within tolerance). A mismatch
    usually signals broken provider linking or a partially-computed result.

    Args:
        result: Calculation result (olca_ipc Result object).
        rel_tol: Relative tolerance, scaled by the magnitude of the total.
        abs_tol: Absolute tolerance floor (for totals near zero).

    Returns:
        List of warning strings. Empty list means all checks passed.
    """
    warnings: List[str] = []

    try:
        totals = result.get_total_impacts()
    except Exception as e:  # noqa: BLE001
        return [f"could not read total impacts: {e}"]

    for iv in totals:
        cat = getattr(iv, "impact_category", None)
        if not cat:
            continue
        total = iv.amount or 0.0

        try:
            contribs = result.get_impact_contributions_of(cat)
        except Exception as e:  # noqa: BLE001
            warnings.append(f"{cat.name}: could not read contributions: {e}")
            continue

        contrib_sum = sum((c.amount or 0.0) for c in contribs)
        tol = max(abs_tol, rel_tol * abs(total))
        if abs(contrib_sum - total) > tol:
            warnings.append(
                f"{cat.name}: contributions sum {contrib_sum:.6g} "
                f"!= total {total:.6g} (diff {contrib_sum - total:.3g})"
            )

    if warnings:
        logger.warning("Result consistency check found %d issue(s)", len(warnings))
    return warnings
