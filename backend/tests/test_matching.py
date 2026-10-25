
import pandas as pd
from app.services.matching import aggregate_actuals_hourly
from app.services.matching import  (
    match_forecasts_to_actuals,
    align_hourly_forecasts_to_actuals,
)


def test_future_forecast_is_not_used():
    actuals = pd.DataFrame([
        {
            "delivery_start": "2026-01-05T10:00:00Z",
            "actual_mw": 100.0,
        }
    ])

    forecasts = pd.DataFrame([
        {
            "delivery_start": "2026-01-05T10:00:00Z",
            "publish_time": "2026-01-05T08:00:00Z",
            "forecast_mw": 90.0,
        },
        {
            "delivery_start": "2026-01-05T10:00:00Z",
            "publish_time": "2026-01-05T09:30:00Z",
            "forecast_mw": 105.0,
        },
    ])

    result = match_forecasts_to_actuals(
        actuals,
        forecasts,
        "2026-01-05T09:00:00Z",
    )

    assert result.loc[0, "forecast_mw"] == 90.0
    assert result.loc[0, "absolute_error_mw"] == 10.0

def test_forecast_published_exactly_at_cutoff_is_allowed():
    actuals = pd.DataFrame([
        {
            "delivery_start": "2026-01-05T10:00:00Z",
            "actual_mw": 100.0,
        }
    ])

    forecasts = pd.DataFrame([
        {
            "delivery_start": "2026-01-05T10:00:00Z",
            "publish_time": "2026-01-05T09:00:00Z",
            "forecast_mw": 95.0,
        }
    ])

    result = match_forecasts_to_actuals(
        actuals,
        forecasts,
        "2026-01-05T09:00:00Z",
    )

    assert len(result) == 1
    assert result.loc[0, "forecast_mw"] == 95.0
    assert result.loc[0, "absolute_error_mw"] == 5.0

def test_no_eligible_forecast_returns_empty_result():
    actuals = pd.DataFrame([
        {
            "delivery_start": "2026-01-05T10:00:00Z",
            "actual_mw": 100.0,
        }
    ])

    forecasts = pd.DataFrame([
        {
            "delivery_start": "2026-01-05T10:00:00Z",
            "publish_time": "2026-01-05T09:30:00Z",
            "forecast_mw": 105.0,
        }
    ])

    result = match_forecasts_to_actuals(
        actuals,
        forecasts,
        "2026-01-05T09:00:00Z",
    )

    assert result.empty
    assert "absolute_error_mw" in result.columns

def test_hourly_forecasts_match_actuals_at_exact_timestamps():
    actuals = pd.DataFrame([
        {
            "delivery_start": "2026-01-05T10:00:00Z",
            "actual_mw": 100.0,
        },
        {
            "delivery_start": "2026-01-05T10:30:00Z",
            "actual_mw": 110.0,
        },
        {
            "delivery_start": "2026-01-05T11:00:00Z",
            "actual_mw": 120.0,
        },
    ])

    forecasts = pd.DataFrame([
        {
            "delivery_start": "2026-01-05T10:00:00Z",
            "forecast_mw": 90.0,
        },
        {
            "delivery_start": "2026-01-05T11:00:00Z",
            "forecast_mw": 115.0,
        },
    ])

    result = align_hourly_forecasts_to_actuals(
        actuals,
        forecasts,
    )

    assert len(result) == 2
    assert result.loc[0, "forecast_mw"] == 90.0
    assert result.loc[0, "actual_mw"] == 100.0
    assert result.loc[0, "absolute_error_mw"] == 10.0
    assert result.loc[1, "absolute_error_mw"] == 5.0


def test_latest_eligible_forecast_is_selected():
    actuals = pd.DataFrame([
        {
            "delivery_start": "2026-01-15T00:00:00Z",
            "actual_mw": 100.0,
        }
    ])

    forecasts = pd.DataFrame([
        {
            "delivery_start": "2026-01-15T00:00:00Z",
            "publish_time": "2026-01-14T08:00:00Z",
            "forecast_mw": 90.0,
        },
        {
            "delivery_start": "2026-01-15T00:00:00Z",
            "publish_time": "2026-01-14T09:30:00Z",
            "forecast_mw": 95.0,
        },
        {
            "delivery_start": "2026-01-15T00:00:00Z",
            "publish_time": "2026-01-14T11:00:00Z",
            "forecast_mw": 120.0,
        },
    ])

    result = match_forecasts_to_actuals(
        actuals,
        forecasts,
        "2026-01-14T10:30:00Z",
    )

    assert len(result) == 1
    assert result.loc[0, "forecast_mw"] == 95.0
    assert result.loc[0, "absolute_error_mw"] == 5.0
