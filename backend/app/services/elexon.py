import os
BASE_URL = os.getenv("ELEXON_BASE_URL", "https://data.elexon.co.uk/bmrs/api/v1")
from datetime import date, datetime, timezone
import httpx
from datetime import date, datetime, timedelta, timezone
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
USE_SNAPSHOT = os.getenv("USE_SNAPSHOT", "1") == "1"


def _load_snapshot(name: str):
    path = DATA_DIR / name
    if USE_SNAPSHOT and path.exists():
        return json.loads(path.read_text())
    return None

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


async def fetch_actuals(start_date: date, end_date: date) -> list[dict]:
    """Fetch actual generation records (snapshot first, live API as fallback)."""
    snap = _load_snapshot("actuals_wind.json")
    if snap is not None:
        return [
            r for r in snap
            if start_date.isoformat() <= r["settlementDate"] <= end_date.isoformat()
        ]
    return await _fetch_actuals_chunked(start_date, end_date)
async def _fetch_actuals_chunked(start_date: date, end_date: date) -> list[dict]:
    """FUELHH limits the date range per request, so fetch in 7-day windows."""
    records: list[dict] = []
    chunk_start = start_date
    while chunk_start <= end_date:
        chunk_end = min(chunk_start + timedelta(days=6), end_date)
        records.extend(await fetch_dataset("FUELHH", chunk_start, chunk_end))
        chunk_start = chunk_end + timedelta(days=1)
    return records

async def fetch_wind_forecasts(
    start_date: date,
    end_date: date,
) -> list[dict]:
    """Preserve the existing exploration endpoint."""
    return await fetch_dataset("WINDFOR", start_date, end_date)

_history_cache: dict[str, list[dict]] = {}


async def fetch_wind_forecast_history(publish_time: datetime) -> list[dict]:
    """Fetch the wind forecast snapshot published at publish_time (cached)."""
    if publish_time.tzinfo is None:
        publish_time = publish_time.replace(tzinfo=timezone.utc)
    publish_time = publish_time.astimezone(timezone.utc)

    key = publish_time.isoformat()
    snap = _load_snapshot(f"forecast_{publish_time:%Y%m%dT%H%M%SZ}.json")
    if snap is not None:
        return snap
    if key in _history_cache:
        return _history_cache[key]

    url = f"{BASE_URL}/forecast/generation/wind/history"
    params = {
        "publishTime": publish_time.isoformat().replace("+00:00", "Z"),
        "format": "json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()

    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
        records = payload["data"]
    else:
        raise ValueError("Unexpected response format from WINDFOR history")

    _history_cache[key] = records
    return records