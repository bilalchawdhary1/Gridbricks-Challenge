
import asyncio
import json
from collections import Counter

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"


async def inspect(name: str, url: str, params: dict):
    print(f"\n--- {name} ---")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url, params=params)

    print("HTTP status:", response.status_code)
    response.raise_for_status()

    payload = response.json()

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("data", payload)
    else:
        print("Unexpected response:", type(payload).__name__)
        return

    if not isinstance(records, list):
        print("Response is not a record list:")
        print(json.dumps(records, indent=2)[:2000])
        return

    print("Record count:", len(records))

    if records:
        print("\nFirst record:")
        print(json.dumps(records[0], indent=2))

    if name == "FUELHH actuals":
        print("\nFuel type counts:")
        print(Counter(
            str(r.get("fuelType", "MISSING")).upper()
            for r in records
        ))

        wind_records = [
            r for r in records
            if str(r.get("fuelType", "")).upper() == "WIND"
        ]

        print("\nWind records:", len(wind_records))
        print(json.dumps(wind_records[:3], indent=2))

    if name == "WINDFOR latest":
        print("\nForecast publication range:")
        print("Earliest:", min(r["publishTime"] for r in records))
        print("Latest:", max(r["publishTime"] for r in records))

        print("\nSettlement periods:")
        print(sorted({r["settlementPeriod"] for r in records}))

        print("\nDelivery dates:")
        print(sorted({r["settlementDate"] for r in records}))



async def inspect_history():
    url = f"{BASE_URL}/forecast/generation/wind/history"

    params = {
        "publishTime": "2026-01-05T22:30:00Z",
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.get(url, params=params)

    print("\n--- WINDFOR history details ---")
    print("HTTP status:", response.status_code)
    response.raise_for_status()

    payload = response.json()
    records = payload.get("data", [])

    print("Record count:", len(records))

    if not records:
        print("No forecast records returned.")
        return

    print("\nPublication times:")
    print(Counter(r["publishTime"] for r in records))

    print("\nDelivery date counts:")
    print(Counter(r["settlementDate"] for r in records))

    print("\nSettlement periods by delivery date:")
    for date in sorted({r["settlementDate"] for r in records}):
        periods = sorted(
            r["settlementPeriod"]
            for r in records
            if r["settlementDate"] == date
        )
        print(date, ":", periods)

    print("\nFirst 3 records:")
    print(json.dumps(records[:3], indent=2))



async def main():
    await inspect(
        "FUELHH actuals",
        f"{BASE_URL}/datasets/FUELHH",
        {
            "settlementDateFrom": "2026-01-05",
            "settlementDateTo": "2026-01-05",
            "format": "json",
        },
    )

    await inspect(
        "WINDFOR latest",
        f"{BASE_URL}/forecast/generation/wind/latest",
        {
            "from": "2026-01-05T00:00:00Z",
            "to": "2026-01-06T00:00:00Z",
            "format": "json",
        },
    )

    await inspect_history()


if __name__ == "__main__":
    asyncio.run(main())
