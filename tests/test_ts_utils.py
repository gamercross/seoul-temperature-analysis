"""scripts/ts_utils.py의 핵심 로직에 대한 단위 테스트. 실행: pytest"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from ts_utils import (
    extreme_day_counts,
    precipitation_summary,
    seasonal_naive_forecast,
    forecast_errors,
    HEAT_WAVE_THRESHOLD_C,
    COLD_WAVE_THRESHOLD_C,
)


def test_extreme_day_counts_basic():
    temp_max = pd.Series([30.0, 33.0, 34.0, 20.0])
    temp_min = pd.Series([-5.0, -12.0, -13.0, 5.0])
    result = extreme_day_counts(temp_max, temp_min)
    assert result["heat_days"] == 2  # 33.0, 34.0 >= 33.0
    assert result["cold_days"] == 2  # -12.0, -13.0 <= -12.0


def test_extreme_day_counts_empty_series():
    empty = pd.Series([], dtype=float)
    result = extreme_day_counts(empty, empty)
    assert result == {"heat_days": 0, "cold_days": 0}


def test_extreme_day_counts_custom_threshold():
    temp_max = pd.Series([25.0, 26.0])
    temp_min = pd.Series([0.0, 1.0])
    result = extreme_day_counts(temp_max, temp_min, heat_threshold=25.0, cold_threshold=1.0)
    assert result["heat_days"] == 2
    assert result["cold_days"] == 2


def test_default_thresholds_match_korea_meteorological_criteria():
    assert HEAT_WAVE_THRESHOLD_C == 33.0
    assert COLD_WAVE_THRESHOLD_C == -12.0


def test_precipitation_summary():
    precip = pd.Series([0.0, 5.0, 0.0, 10.0, 0.0])
    result = precipitation_summary(precip)
    assert result["rain_days"] == 2
    assert result["total_precip"] == pytest.approx(15.0)
    assert result["max_daily_precip"] == pytest.approx(10.0)


def test_precipitation_summary_all_dry():
    precip = pd.Series([0.0, 0.0, 0.0])
    result = precipitation_summary(precip)
    assert result["rain_days"] == 0
    assert result["total_precip"] == 0.0
    assert result["max_daily_precip"] == 0.0


def test_seasonal_naive_forecast_shifts_by_period():
    idx = pd.date_range("2023-01-01", periods=10, freq="D")
    series = pd.Series(range(10), index=idx, dtype=float)
    forecast = seasonal_naive_forecast(series, period=3)
    # forecast[t] should equal series[t-3]
    assert forecast.iloc[3] == series.iloc[0]
    assert forecast.iloc[9] == series.iloc[6]
    assert forecast.iloc[:3].isna().all()


def test_forecast_errors_perfect_prediction():
    actual = pd.Series([1.0, 2.0, 3.0])
    predicted = pd.Series([1.0, 2.0, 3.0])
    errors = forecast_errors(actual, predicted)
    assert errors["mae"] == pytest.approx(0.0)
    assert errors["rmse"] == pytest.approx(0.0)
    assert errors["n"] == 3


def test_forecast_errors_known_values():
    actual = pd.Series([10.0, 20.0, 30.0])
    predicted = pd.Series([12.0, 18.0, 33.0])
    errors = forecast_errors(actual, predicted)
    # abs errors: 2, 2, 3 -> mae = 7/3
    assert errors["mae"] == pytest.approx(7 / 3)
    # squared errors: 4, 4, 9 -> rmse = sqrt(17/3)
    assert errors["rmse"] == pytest.approx(np.sqrt(17 / 3))


def test_forecast_errors_ignores_nan_pairs():
    actual = pd.Series([1.0, 2.0, np.nan, 4.0])
    predicted = pd.Series([1.0, np.nan, 3.0, 4.0])
    errors = forecast_errors(actual, predicted)
    # only index 0 and 3 are valid pairs, both with zero error
    assert errors["n"] == 2
    assert errors["mae"] == pytest.approx(0.0)


def test_forecast_errors_empty_input():
    actual = pd.Series([], dtype=float)
    predicted = pd.Series([], dtype=float)
    errors = forecast_errors(actual, predicted)
    assert errors["n"] == 0
    assert np.isnan(errors["mae"])
