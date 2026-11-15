"""UI-only adapter for the BLOOM branch pilot.

The strict modules.data_loader.load_datasets contract is not altered.
Repository CSVs can be displayed as uploaded observations while metadata
verification_status remains 'pending'; nothing is marked verified.
"""
from __future__ import annotations

from modules.investigation_case import CaseData, load_case_data
from modules.ui_data import UIContext


def pilot_context(ctx: UIContext, data: CaseData | None = None) -> UIContext:
    """Expose validated uploaded observations to existing dashboard pages.

    Only applies in the explicitly selected NASA CSV pilot mode. If the
    strict loader already succeeded, preserve its context unchanged.
    """
    if ctx.mode != "verified" or ctx.ready:
        return ctx
    try:
        case = data if data is not None else load_case_data()
    except (FileNotFoundError, OSError, ValueError, KeyError, TypeError):
        return ctx
    return UIContext(
        mode=ctx.mode,
        area_id=ctx.area_id,
        start_year=ctx.start_year,
        end_year=ctx.end_year,
        ndvi_df=case.ndvi,
        rainfall_df=case.rainfall,
        geojson=case.geojson,
        metadata=case.metadata,
        error=None,
    )
