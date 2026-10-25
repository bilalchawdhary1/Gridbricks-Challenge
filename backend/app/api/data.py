import asyncio
from datetime import date, timedelta

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.services.accuracy_metrics import calculate_metrics
from app.services.cutoff import decision_cutoff
from app.services.elexon import fetch_actuals, fetch_wind_forecast_history
from app.services.matching import (
    aggregate_actuals_hourly,
    match_forecasts_to_actuals,
    normalize_wind_actuals,
    normalize_wind_forecasts,
)

router = APIRouter(prefix="/api/data", tags=["Data"])

MIN_DATE = date(2026, 1, 1)
MAX_DATE = date(2026, 1, 31)


def _check_range(start: date, end: date) -> None:
    if end < start:
        raise HTTPException(400, "end_date must be on or after start_date")
    if start < MIN_DATE or end > MAX_DATE:
        raise HTTPException(400, "Dates must be within January 2026")


def _iso(series: pd.Series) -> list[str]:
    return pd.to_datetime(series, utc=True).map(lambda t: t.isoformat()).tolist()


async def _day_forecast(day: date) -> tuple[pd.DataFrame, str]:
    """Latest forecast per delivery hour available at D-1 cutoff, for one day."""
    cutoff = decision_cutoff(day)
    records = await fetch_wind_forecast_history(cutoff)
    f = normalize_wind_forecasts(records, cutoff.isoformat())
    f = f[f["settlement_date"] == day.isoformat()]
    return f, cutoff.isoformat()


@router.get("/forecast")
async def get_forecast(day: date = Query(..., alias="date")):
    """Requirement 1: latest forecast available when buying for `date`."""
    _check_range(day, day)
    try:
        f, cutoff = await _day_forecast(day)
    except Exception as exc:
        raise HTTPException(502, f"Elexon request failed: {exc}") from exc

    latest = (
        f.sort_values(["delivery_start", "publish_time"])
        .drop_duplicates("delivery_start", keep="last")
    )
    return {
        "delivery_date": day.isoformat(),
        "decision_cutoff": cutoff,
        "points": [
            {
                "delivery_start": s,
                "forecast_mw": float(mw),
                "publish_time": p,
            }
            for s, mw, p in zip(
                _iso(latest["delivery_start"]),
                latest["forecast_mw"],
                _iso(latest["publish_time"]),
            )
        ],
    }


@router.get("/accuracy")
async def get_accuracy(start_date: date, end_date: date):
    """Requirement 2: forecast accuracy, each day scored at its own D-1 cutoff."""
    _check_range(start_date, end_date)

    days = [
        start_date + timedelta(days=i)
        for i in range((end_date - start_date).days + 1)
    ]
    sem = asyncio.Semaphore(5)  # be polite to Elexon

    async def one_day(day: date):
        async with sem:
            return await _day_forecast(day)

    try:
        actual_records = await fetch_actuals(start_date, end_date)
        actuals = aggregate_actuals_hourly(normalize_wind_actuals(actual_records))
        per_day = await asyncio.gather(*(one_day(d) for d in days))
    except Exception as exc:
        raise HTTPException(502, f"Elexon request failed: {exc}") from exc

    parts = []
    for day, (forecasts, cutoff) in zip(days, per_day):
        a = actuals[
            pd.to_datetime(actuals["delivery_start"], utc=True).dt.date == day
        ]
        m = match_forecasts_to_actuals(a, forecasts, cutoff)
        if not m.empty:
            parts.append(m)

    matched = (
        pd.concat(parts, ignore_index=True) if parts
        else pd.DataFrame(columns=["delivery_start", "forecast_mw", "actual_mw",
                                   "absolute_error_mw", "publish_time"])
    )

    metrics = {k: None for k in
               ("mae_mw", "rmse_mw", "forecast_bias_mw", "wape_percent", "mape_percent")}
    if not matched.empty:
        metrics = calculate_metrics(
            matched["actual_mw"].tolist(), matched["forecast_mw"].tolist()
        )

    hours_expected = len(days) * 24
    out = matched.copy()
    if not out.empty:
        out["delivery_start"] = _iso(out["delivery_start"])
        out["publish_time"] = _iso(out["publish_time"])

    return {
        "period": {"start": start_date.isoformat(), "end_inclusive": end_date.isoformat()},
        "matched_intervals": len(matched),
        "eligible_intervals": hours_expected,
        "forecast_coverage_percent": len(matched) / hours_expected * 100,
        **metrics,
        "matches": out.replace({np.nan: None}).to_dict(orient="records"),
        "evaluation_note": (
            "Each delivery day is scored using the latest forecast published "
            "by 09:00 UK time on the previous day. Half-hourly actuals are "
            "averaged to hourly."
        ),
    }