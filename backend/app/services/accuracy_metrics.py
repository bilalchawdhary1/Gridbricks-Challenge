
from math import sqrt
from typing import Sequence


def calculate_metrics(
    actuals: Sequence[float],
    forecasts: Sequence[float],
) -> dict[str, float]:
    """Calculate MAE, RMSE, and MAPE for actual and forecast values."""

    if len(actuals) != len(forecasts):
        raise ValueError("Actuals and forecasts must have equal lengths.")

    if len(actuals) == 0:
        raise ValueError("At least one actual/forecast pair is required.")

    if any(actual < 0 for actual in actuals):
        raise ValueError("Actual generation values cannot be negative.")

    errors = [
        forecast - actual
        for actual, forecast in zip(actuals, forecasts)
    ]

    absolute_errors = [abs(error) for error in errors]

    mae = sum(absolute_errors) / len(errors)
    rmse = sqrt(sum(error**2 for error in errors) / len(errors))
    forecast_bias = sum(errors) / len(errors)

    total_actual = sum(abs(actual) for actual in actuals)

    wape = (
        sum(absolute_errors) / total_actual * 100
        if total_actual != 0
        else None
    )

    # MAPE is undefined when any actual value is zero.
    mape = (
    sum(
        abs(forecast - actual) / actual
        for actual, forecast in zip(actuals, forecasts)
    )
    / len(actuals)
    * 100
    if all(actual != 0 for actual in actuals)
    else None
    )

    return {
        "mae_mw": mae,
        "rmse_mw": rmse,
        "forecast_bias_mw": forecast_bias,
        "wape_percent": wape,
        "mape_percent": mape
    }
