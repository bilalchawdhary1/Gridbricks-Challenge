
from datetime import date, datetime, timezone

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"



async def fetch_dataset(dataset, start_date, end_date):
    url = f"{BASE_URL}/datasets/{dataset}"

    if dataset == "FUELHH":
        params = {
            "settlementDateFrom": start_date.isoformat(),
            "settlementDateTo": end_date.isoformat(),
            "format": "json",
        }
    else:
        params = {
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
            "format": "json",
        }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    if isinstance(payload, dict):
        return payload.get("data", [])

    if isinstance(payload, list):
        return payload

    return []


async def fetch_actuals(
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Fetch actual generation records."""
    return await fetch_dataset("FUELHH", start_date, end_date)


async def fetch_wind_forecasts(
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Preserve the existing exploration endpoint."""
    return await fetch_dataset("WINDFOR", start_date, end_date)

async def fetch_wind_forecast_history(
    publish_time: datetime,
) -> list[dict]:
    """Fetch a historical wind forecast vintage by publication time."""
    if publish_time.tzinfo is None:
        publish_time = publish_time.replace(tzinfo=timezone.utc)

    publish_time = publish_time.astimezone(timezone.utc)

    url = f"{BASE_URL}/forecast/generation/wind/history"
    params = {
        "publishTime": publish_time.isoformat().replace("+00:00", "Z"),
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

        print("Requested URL:", response.request.url)
        print("Response status:", response.status_code)
        print(
            "Returned publishTime values:",
            sorted({
                record.get("publishTime")
                for record in (
                    payload if isinstance(payload, list)
                    else payload.get("data", []) if isinstance(payload, dict)
                    else []
                )
                if isinstance(record, dict)
            })
        )

    # Convert the API response into a list of records
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("data", [])
        if not isinstance(records, list):
            records = []
    else:
        raise ValueError("Unexpected response format from WINDFOR history")

    # TEMPORARY DEBUGGING: check publication timestamps
   
    return records

