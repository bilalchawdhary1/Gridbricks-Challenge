
import asyncio
from datetime import date, datetime, timezone

import pandas as pd

from app.services.elexon import (
    fetch_actuals,
    fetch_wind_forecast_history,
)
from app.services.matching import (
    normalize_wind_actuals,
    normalize_wind_forecasts,
    aggregate_actuals_hourly,
    match_forecasts_to_actuals,
)


async def main():
    start = date(2026, 10, 24)
    end = date(2026, 10, 24)
    cutoff = datetime(2026, 10, 24, 10, 30, tzinfo=timezone.utc)

    actual_records = await fetch_actuals(start, end)
    forecast_records = await fetch_wind_forecast_history(cutoff)

    actuals = aggregate_actuals_hourly(
        normalize_wind_actuals(actual_records)
    )
    forecasts = normalize_wind_forecasts(
        forecast_records, cutoff.isoformat()
    )

    actuals = actuals.merge(
        normalize_wind_actuals(actual_records)[
            ["delivery_start", "settlement_date"]
        ].drop_duplicates("delivery_start"),
        on="delivery_start",
        how="left",
    )

    actuals = actuals[
        actuals["settlement_date"] == start.isoformat()
    ]

    matched = match_forecasts_to_actuals(
        actuals, forecasts, cutoff.isoformat()
    )

    if matched.empty:
        print("No matches found")
        return

    matched["lead_time_minutes"] = (
        cutoff - pd.to_datetime(matched["delivery_start"], utc=True)
    ).dt.total_seconds() / 60

    print(matched[
        ["delivery_start", "forecast_mw", "actual_mw",
         "lead_time_minutes", "absolute_error_mw"]
    ].to_string(index=False))


if __name__ == "__main__":
    asyncio.run(main())
