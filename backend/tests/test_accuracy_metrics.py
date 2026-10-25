
import pytest

from app.services.accuracy_metrics import calculate_metrics

def test_calculate_metrics_known_values():
    result = calculate_metrics(
        actuals=[100, 200, 300],
        forecasts=[110, 180, 330],
    )

    assert result["mae_mw"] == pytest.approx(20.0)
    assert result["rmse_mw"] == pytest.approx((1400 / 3) ** 0.5)
    assert result["mape_percent"] == pytest.approx(10.0)
    assert result["forecast_bias_mw"] == pytest.approx(20 / 3)
    assert result["wape_percent"] == pytest.approx(
        (60 / 600) * 100
    )
    