import numpy as np
import traceback
from datetime import date, datetime, timezone
from app.services.accuracy_metrics import calculate_metrics
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.services.elexon import (
    fetch_actuals,
    fetch_wind_forecasts,
    fetch_wind_forecast_history,
)
from app.services.matching import (
    filter_wind_actuals,
    normalize_wind_actuals,
    normalize_wind_forecasts,
    aggregate_actuals_hourly,
    match_forecasts_to_actuals,
)

router = APIRouter(prefix="/api/data", tags=["Data"])


@router.get("/explore")
async def explore_data():
    """Inspect the actual and forecast data returned by Elexon."""
    try:
        start = date(2026, 1, 1)
        end = date(2026, 2, 1)

        actual_records = await fetch_actuals(start, end)
        forecast_records = await fetch_wind_forecasts(start, end)
       

        wind_actuals = filter_wind_actuals(actual_records)

        return {
            "period": {
                "start": start.isoformat(),
                "end_exclusive": end.isoformat(),
            },
            "actual_records_received": len(actual_records),
            "wind_actual_records": len(wind_actuals),
            "forecast_records_received": len(forecast_records),
            "sample_wind_actuals": wind_actuals.head(5).to_dict(
                orient="records"
            ),
            "sample_forecasts": forecast_records[:5],
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Elexon data exploration failed: {exc}",
        ) from exc


@router.get("/accuracy")
async def get_accuracy(
    start_date: date = Query(
        ...,
        description="First Elexon settlement date, inclusive",
    ),
    end_date: date = Query(
        ...,
        description="Last Elexon settlement date, inclusive",
    ),
    decision_cutoff: datetime = Query(
        ...,
        description="UTC publication snapshot timestamp",
    ),
):
    """Evaluate a historical forecast snapshot against actual generation."""

    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="end_date must be on or after start_date",
        )

    if decision_cutoff.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="decision_cutoff must include a timezone, e.g. Z",
        )

    cutoff = decision_cutoff.astimezone(timezone.utc)

    try:
        # Fetch actual generation for the requested settlement dates.
        actual_records = await fetch_actuals(start_date, end_date)
        actuals = normalize_wind_actuals(actual_records)

        # Fetch the specific historical forecast publication snapshot.
        forecast_records = await fetch_wind_forecast_history(cutoff)
        forecasts = normalize_wind_forecasts(
            forecast_records,
            cutoff.isoformat(),
        )
    
        # Filter by Elexon settlement date, not UTC calendar date.
        actuals = actuals.loc[
            actuals["settlement_date"].between(
                start_date.isoformat(),
                end_date.isoformat(),
            )
        ].copy()

        forecasts = forecasts.loc[
            forecasts["settlement_date"].between(
                start_date.isoformat(),
                end_date.isoformat(),
            )
        ].copy()

        # Aggregate half-hourly actual generation into hourly averages.
        hourly_actuals = aggregate_actuals_hourly(actuals)

        # Match forecast and actual records at the same hourly timestamp.
        matched = match_forecasts_to_actuals(
            hourly_actuals,
            forecasts,
            cutoff.isoformat(),
        )

        # Do not score delivery intervals that began before publication.
        if not matched.empty:
            delivery_times = pd.to_datetime(
                matched["delivery_start"],
                utc=True,
            )
            matched = matched.loc[
                delivery_times >= pd.Timestamp(cutoff)
            ].copy()

        # Calculate metrics using the tested metrics service.
        if matched.empty:
            mae = None
            rmse = None
            mape_percent = None
            forecast_bias_mw = None
            wape_percent = None
        else:
            metrics = calculate_metrics(
                actuals=matched["actual_mw"].tolist(),
                forecasts=matched["forecast_mw"].tolist(),
            )

            mae = metrics["mae_mw"]
            rmse = metrics["rmse_mw"]
            mape_percent = metrics["mape_percent"]
            forecast_bias_mw = metrics["forecast_bias_mw"]
            wape_percent = metrics["wape_percent"]

            # Keep the API response JSON-safe if MAPE is undefined.
            if not np.isfinite(mape_percent):
                mape_percent = None
       
        eligible_intervals = int(
            (
                hourly_actuals["delivery_start"]
                >= pd.Timestamp(cutoff)
            ).sum()
        )

        forecast_coverage_percent = (
            float(len(matched) / eligible_intervals * 100)
            if eligible_intervals > 0
            else None
        )


        # Convert timestamps to JSON-safe strings.
        output_matches = matched.copy()
        if not output_matches.empty:
            output_matches["delivery_start"] = pd.to_datetime(
                output_matches["delivery_start"],
                utc=True,
            ).map(lambda timestamp: timestamp.isoformat())

        return {
            "period": {
                "start": start_date.isoformat(),
                "end_inclusive": end_date.isoformat(),
            },
            "decision_cutoff": cutoff.isoformat(),
            "forecast_source": "historical publication snapshot",
            "actual_intervals_received": len(actuals),
            "hourly_actual_intervals": len(hourly_actuals),
            "forecast_records_received": len(forecasts),
            "matched_intervals": len(matched),
            "mae_mw": mae,
            "rmse_mw": rmse,
            "forecast_bias_mw": forecast_bias_mw,
            "wape_percent": wape_percent,
            "mape_percent": mape_percent,
            "eligible_intervals": eligible_intervals,
            "forecast_coverage_percent": forecast_coverage_percent,
            "matches": output_matches.to_dict(orient="records"),
            "evaluation_note": (
                "Actuals are averaged hourly. Delivery intervals beginning "
                "before the publication cutoff are excluded. This is a "
                "snapshot-based evaluation; confirm any required minimum "
                "forecast lead time from the challenge specification."
            ),
        }

    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail=f"Elexon data evaluation failed: {exc}",
        ) from exc
