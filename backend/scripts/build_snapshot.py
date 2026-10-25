"""One-off: download January 2026 data from Elexon into backend/data/."""
import asyncio
import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

os.environ["USE_SNAPSHOT"] = "0"  # force live API calls
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.cutoff import decision_cutoff  # noqa: E402
from app.services.elexon import fetch_actuals, fetch_wind_forecast_history  # noqa: E402

DATA = Path(__file__).resolve().parents[1] / "data"
ACTUAL_KEYS = ["fuelType", "startTime", "settlementDate", "settlementPeriod", "generation"]
FORECAST_KEYS = ["publishTime", "startTime", "settlementDate", "settlementPeriod", "generation"]


def pick(records, keys):
    return [{k: r[k] for k in keys} for r in records]


async def main():
    DATA.mkdir(exist_ok=True)
    start, end = date(2026, 1, 1), date(2026, 1, 31)

    actuals = await fetch_actuals(start, end)
    wind = [r for r in actuals if str(r.get("fuelType", "")).upper() == "WIND"]
    (DATA / "actuals_wind.json").write_text(json.dumps(pick(wind, ACTUAL_KEYS)))
    print(f"actuals: {len(wind)} wind records")

    day = start
    while day <= end:
        cutoff = decision_cutoff(day)
        records = await fetch_wind_forecast_history(cutoff)
        records = [r for r in records if r["settlementDate"] == day.isoformat()]
        name = f"forecast_{cutoff:%Y%m%dT%H%M%SZ}.json"
        (DATA / name).write_text(json.dumps(pick(records, FORECAST_KEYS)))
        print(day, len(records), "records")
        day += timedelta(days=1)


asyncio.run(main())