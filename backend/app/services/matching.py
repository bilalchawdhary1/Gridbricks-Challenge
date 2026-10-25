
import pandas as pd


def normalize_wind_actuals(records: list[dict]) -> pd.DataFrame:
    """Filter FUELHH to WIND and normalize actual generation."""
    df = pd.DataFrame(records)

    columns = [
        "delivery_start",
        "settlement_date",
        "settlement_period",
        "actual_mw",
    ]

    if df.empty:
        return pd.DataFrame(columns=columns)

    required = {
        "fuelType",
        "startTime",
        "settlementDate",
        "settlementPeriod",
        "generation",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"FUELHH response missing fields: {missing}")

    df = df.loc[
        df["fuelType"].astype(str).str.upper() == "WIND"
    ].copy()

    df["delivery_start"] = pd.to_datetime(
        df["startTime"], utc=True, errors="raise"
    )
    df["settlement_date"] = df["settlementDate"]
    df["settlement_period"] = pd.to_numeric(
        df["settlementPeriod"], errors="raise"
    ).astype(int)
    df["actual_mw"] = pd.to_numeric(
        df["generation"], errors="raise"
    )

    result = df[columns].copy()

    if result.duplicated(
        ["settlement_date", "settlement_period"]
    ).any():
        raise ValueError("Duplicate actual settlement intervals found")
    return result.sort_values("delivery_start").reset_index(drop=True)


def normalize_wind_forecasts(
    records: list[dict],
    decision_cutoff: str,
) -> pd.DataFrame:
    """Keep forecasts published by the decision cutoff."""
    columns = [
        "delivery_start",
        "settlement_date",
        "settlement_period",
        "forecast_mw",
        "publish_time",
    ]

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(columns=columns)

    required = {
        "publishTime",
        "startTime",
        "settlementDate",
        "settlementPeriod",
        "generation",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"WINDFOR response missing fields: {missing}")

    df["publish_time"] = pd.to_datetime(
        df["publishTime"], utc=True, errors="raise"
    )
    cutoff = pd.Timestamp(decision_cutoff)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    else:
        cutoff = cutoff.tz_convert("UTC")

    df = df.loc[df["publish_time"] <= cutoff].copy()

    df["delivery_start"] = pd.to_datetime(
        df["startTime"], utc=True, errors="raise"
    )
    df["settlement_date"] = df["settlementDate"]
    df["settlement_period"] = pd.to_numeric(
        df["settlementPeriod"], errors="raise"
    ).astype(int)
    df["forecast_mw"] = pd.to_numeric(
        df["generation"], errors="raise"
    )

    result = df[columns].copy()

    if result.duplicated(
        ["delivery_start", "publish_time"]
    ).any():
        raise ValueError("Duplicate forecast records found")

    return result.sort_values(
        ["delivery_start", "publish_time"]
    ).reset_index(drop=True)

def match_forecasts_to_actuals(
    actuals: pd.DataFrame,
    forecasts: pd.DataFrame,
    decision_cutoff: str,
) -> pd.DataFrame:
    """Match actuals with the latest eligible forecast at each delivery time."""

   
    output_columns = [
        "delivery_start",
        "forecast_mw",
        "actual_mw",
        "absolute_error_mw",
    ]

    if actuals.empty or forecasts.empty:
        return pd.DataFrame(columns=output_columns)

    required_actual = {"delivery_start", "actual_mw"}
    required_forecast = {
        "delivery_start",
        "publish_time",
        "forecast_mw",
    }

    if not required_actual.issubset(actuals.columns):
        raise ValueError("Actuals DataFrame is missing required columns")

    if not required_forecast.issubset(forecasts.columns):
        raise ValueError("Forecasts DataFrame is missing required columns")

    actual_data = actuals[
        ["delivery_start", "actual_mw"]
    ].copy()

    forecast_data = forecasts[
        ["delivery_start", "publish_time", "forecast_mw"]
    ].copy()

    actual_data["delivery_start"] = pd.to_datetime(
        actual_data["delivery_start"], utc=True, errors="raise"
    )

    forecast_data["delivery_start"] = pd.to_datetime(
        forecast_data["delivery_start"], utc=True, errors="raise"
    )

    forecast_data["publish_time"] = pd.to_datetime(
        forecast_data["publish_time"], utc=True, errors="raise"
    )

    cutoff = pd.Timestamp(decision_cutoff)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    else:
        cutoff = cutoff.tz_convert("UTC")

    # Exclude forecasts published after the decision cutoff.
    forecast_data = forecast_data.loc[
        forecast_data["publish_time"] <= cutoff
    ].copy()

    if forecast_data.empty:
        return pd.DataFrame(columns=output_columns)

    # Select the latest eligible forecast for each delivery interval.
    forecast_data = (
        forecast_data
        .sort_values(["delivery_start", "publish_time"])
        .drop_duplicates("delivery_start", keep="last")
    )

    if actual_data["delivery_start"].duplicated().any():
        raise ValueError("Duplicate actual delivery times found")

    result = actual_data.merge(
        forecast_data[
            ["delivery_start", "forecast_mw", "publish_time"]
        ],
        on="delivery_start",
        how="inner",
        validate="one_to_one",
    )

    result["absolute_error_mw"] = (
        result["actual_mw"] - result["forecast_mw"]
    ).abs()

    return result.sort_values(
        "delivery_start"
    ).reset_index(drop=True)

def align_hourly_forecasts_to_actuals(
    actuals: pd.DataFrame,
    forecasts: pd.DataFrame,
) -> pd.DataFrame:
    """Match hourly forecasts to actuals at the same delivery hour.

    Assumes each forecast's delivery_start marks the beginning
    of its delivery hour. The forecast is matched to the actual
    at that timestamp, without duplicating it into two intervals.
    """
    columns = [
        "delivery_start",
        "forecast_mw",
        "actual_mw",
        "absolute_error_mw",
    ]

    if actuals.empty or forecasts.empty:
        return pd.DataFrame(columns=columns)

    required_actual = {"delivery_start", "actual_mw"}
    required_forecast = {"delivery_start", "forecast_mw"}

    if not required_actual.issubset(actuals.columns):
        raise ValueError("Actuals DataFrame is missing required columns")

    if not required_forecast.issubset(forecasts.columns):
        raise ValueError("Forecasts DataFrame is missing required columns")

    actual_data = actuals[
        ["delivery_start", "actual_mw"]
    ].copy()

    forecast_data = forecasts[
        ["delivery_start", "forecast_mw"]
    ].copy()

    actual_data["delivery_start"] = pd.to_datetime(
        actual_data["delivery_start"], utc=True, errors="raise"
    )
    forecast_data["delivery_start"] = pd.to_datetime(
        forecast_data["delivery_start"], utc=True, errors="raise"
    )

    if actual_data["delivery_start"].duplicated().any():
        raise ValueError("Duplicate actual delivery times found")

    if forecast_data["delivery_start"].duplicated().any():
        raise ValueError("Duplicate forecast delivery times found")

    result = actual_data.merge(
        forecast_data,
        on="delivery_start",
        how="inner",
        validate="one_to_one",
    )

    result["absolute_error_mw"] = (
        result["actual_mw"] - result["forecast_mw"]
    ).abs()

    return result[columns].sort_values(
        "delivery_start"
    ).reset_index(drop=True)

def aggregate_actuals_hourly(actuals: pd.DataFrame) -> pd.DataFrame:
    """Aggregate half-hourly actual MW values into hourly averages."""
    columns = ["delivery_start", "actual_mw"]

    if actuals.empty:
        return pd.DataFrame(columns=columns)

    required = {"delivery_start", "actual_mw"}
    if not required.issubset(actuals.columns):
        raise ValueError("Actuals DataFrame is missing required columns")

    df = actuals[columns].copy()
    df["delivery_start"] = pd.to_datetime(
        df["delivery_start"], utc=True, errors="raise"
    )
    df["actual_mw"] = pd.to_numeric(
        df["actual_mw"], errors="raise"
    )

    if df["delivery_start"].duplicated().any():
        raise ValueError("Duplicate actual delivery times found")

    df["delivery_start"] = df["delivery_start"].dt.floor("h")

    grouped = (
        df.groupby("delivery_start", as_index=False)
        .agg(actual_mw=("actual_mw", "mean"), n=("actual_mw", "count"))
    )
    grouped = grouped[grouped["n"] == 2].drop(columns="n")  # full hours only
    return grouped.sort_values("delivery_start").reset_index(drop=True)

def filter_wind_actuals(records: list[dict]) -> pd.DataFrame:
    """Filter FUELHH records to WIND and return a DataFrame."""
    df = normalize_wind_actuals(records)

    return df
