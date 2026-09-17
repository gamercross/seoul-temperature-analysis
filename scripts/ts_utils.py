"""
analysis.py, dashboard.py, tests/에서 공통으로 쓰는 순수 함수 모음.
DataFrame을 직접 다루지 않고 필요한 값만 받아 계산하므로 테스트하기 쉽다.
"""
import numpy as np
import pandas as pd

HEAT_WAVE_THRESHOLD_C = 33.0   # 기상청 폭염주의보 기준: 일 최고기온 33도 이상
COLD_WAVE_THRESHOLD_C = -12.0  # 기상청 한파주의보 기준: 아침 최저기온 -12도 이하


def extreme_day_counts(temp_max: pd.Series, temp_min: pd.Series,
                        heat_threshold: float = HEAT_WAVE_THRESHOLD_C,
                        cold_threshold: float = COLD_WAVE_THRESHOLD_C) -> dict:
    """일 최고/최저기온 시리즈로 폭염일수·한파일수를 센다."""
    return {
        "heat_days": int((temp_max >= heat_threshold).sum()),
        "cold_days": int((temp_min <= cold_threshold).sum()),
    }


def precipitation_summary(precipitation: pd.Series) -> dict:
    """일 강수량 시리즈로 강수일수·총강수량·최대 일강수량을 계산한다."""
    return {
        "rain_days": int((precipitation > 0).sum()),
        "total_precip": float(precipitation.sum()),
        "max_daily_precip": float(precipitation.max()),
    }


def seasonal_naive_forecast(series: pd.Series, period: int = 365) -> pd.Series:
    """t 시점의 예측값으로 t-period 시점의 실제값을 그대로 사용하는 베이스라인."""
    return series.shift(period)


def forecast_errors(actual: pd.Series, predicted: pd.Series) -> dict:
    """실제값과 예측값 시리즈(같은 인덱스)로 MAE·RMSE를 계산한다. NaN은 제외한다."""
    paired = pd.DataFrame({"actual": actual, "predicted": predicted}).dropna()
    if paired.empty:
        return {"mae": float("nan"), "rmse": float("nan"), "n": 0}
    err = paired["actual"] - paired["predicted"]
    return {
        "mae": float(err.abs().mean()),
        "rmse": float(np.sqrt((err ** 2).mean())),
        "n": len(paired),
    }
