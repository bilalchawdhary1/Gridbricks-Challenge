
import asyncio
from datetime import date

import pandas as pd

from app.services.elexon import fetch_actuals, fetch_wind_forecasts
from app.services.matching import (
    normalize_wind_actuals,
    normalize_wind_forecasts,
)


async def main():
    start = date(2026, 1, 5)
    end = date(2026, 1, 6)

    actual_records = await fetch_actuals(start, end)
    forecast_records = await fetch_wind_forecasts(start, end)

    actuals = normalize_wind_actuals(actual_records)

    print("\nACTUALS: first 6 WIND records")
    print(actuals.head(6).to_string(index=False))

    print("\nFORECASTS: first 6 records")
    print(pd.DataFrame(forecast_records).head(6).to_string(index=False))


if __name__ == "__main__":
    asyncio.run(main())
