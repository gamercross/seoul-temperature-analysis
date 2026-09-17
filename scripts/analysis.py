"""
서울 2023~2024년 일별 기온 시계열 분석
- 데이터 정제(결측치/이상치 점검)
- 시계열 분석 기법: 이동평균, 일교차 변화율, 월별 집계, 변동성(표준편차)
- 시각화 3개 생성 (images/)
- 보너스: STL 시계열 분해(추세/계절성)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from statsmodels.tsa.seasonal import STL

plt.rcParams["axes.unicode_minus"] = False
try:
    plt.rcParams["font.family"] = "AppleGothic"
except Exception:
    pass

DATA_PATH = "data/seoul_daily_temperature_2023_2024.csv"
IMG_DIR = "images"

def load_and_clean():
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 1) 기본 정보 확인
    print("기간:", df["date"].min().date(), "~", df["date"].max().date())
    print("행 수:", len(df))
    print("결측치:\n", df.isna().sum())

    # 2) 완전한 일자 인덱스로 재색인 -> 누락된 날짜(결측)를 명시적으로 드러냄
    full_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    df = df.set_index("date").reindex(full_range)
    df.index.name = "date"
    missing_dates = df["temp_mean"].isna().sum()
    print("재색인 후 결측 일수:", missing_dates)
    if missing_dates > 0:
        df["temp_mean"] = df["temp_mean"].interpolate(method="linear")
        df["temp_max"] = df["temp_max"].interpolate(method="linear")
        df["temp_min"] = df["temp_min"].interpolate(method="linear")
        df["precipitation"] = df["precipitation"].fillna(0)

    # 3) 이상치 점검 (IQR 기준, temp_mean)
    q1, q3 = df["temp_mean"].quantile([0.25, 0.75])
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    outliers = df[(df["temp_mean"] < lower) | (df["temp_mean"] > upper)]
    print(f"IQR 이상치 기준: [{lower:.1f}, {upper:.1f}], 이상치 개수: {len(outliers)}")
    # 실제 기온 관측치이므로 계절적 극값은 이상치가 아니라 자연스러운 변동으로 간주하고 제거하지 않음

    return df

def apply_time_series_techniques(df):
    # 기법 1: 이동평균 (7일, 30일)
    df["ma7"] = df["temp_mean"].rolling(window=7, min_periods=1).mean()
    df["ma30"] = df["temp_mean"].rolling(window=30, min_periods=1).mean()

    # 기법 2: 전일 대비 변화율(일교차 변화량)
    df["day_over_day_change"] = df["temp_mean"].diff()

    # 기법 3: 30일 이동 변동성(표준편차)
    df["rolling_std_30"] = df["temp_mean"].rolling(window=30, min_periods=1).std()

    # 기법 4: 월별 집계
    monthly = df.groupby(df.index.to_period("M"))["temp_mean"].agg(["mean", "std", "min", "max"])
    monthly.index = monthly.index.to_timestamp()

    return df, monthly

def make_visualizations(df, monthly):
    # 시각화 1: 일별 평균기온 추이 + 30일 이동평균
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df.index, df["temp_mean"], color="#b0b8c1", linewidth=0.8, label="일별 평균기온")
    ax.plot(df.index, df["ma30"], color="#d1495b", linewidth=2, label="30일 이동평균")
    ax.set_title("서울 일별 평균기온 추이 (2023-2024)")
    ax.set_xlabel("날짜")
    ax.set_ylabel("기온 (°C)")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{IMG_DIR}/01_temp_trend_moving_average.png", dpi=150)
    plt.close(fig)

    # 시각화 2: 월별 평균기온 (계절성)
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = ["#4c72b0" if m.year == 2023 else "#dd8452" for m in monthly.index]
    ax.bar(monthly.index, monthly["mean"], width=20, color=colors)
    ax.set_title("서울 월별 평균기온 (2023 vs 2024)")
    ax.set_xlabel("월")
    ax.set_ylabel("평균기온 (°C)")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(f"{IMG_DIR}/02_monthly_average_seasonality.png", dpi=150)
    plt.close(fig)

    # 시각화 3: 30일 이동 변동성(표준편차) 추이
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df.index, df["rolling_std_30"], color="#55a868", linewidth=1.5)
    ax.set_title("서울 기온 변동성 (30일 이동 표준편차)")
    ax.set_xlabel("날짜")
    ax.set_ylabel("표준편차 (°C)")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(f"{IMG_DIR}/03_rolling_volatility.png", dpi=150)
    plt.close(fig)

def bonus_decomposition(df):
    # STL 시계열 분해 (추세 + 계절성 + 잔차), 주기=365(연간 계절성)
    stl = STL(df["temp_mean"], period=365, robust=True)
    result = stl.fit()

    fig, axes = plt.subplots(4, 1, figsize=(11, 9), sharex=True)
    axes[0].plot(df.index, result.observed, color="#333333")
    axes[0].set_ylabel("관측치")
    axes[1].plot(df.index, result.trend, color="#d1495b")
    axes[1].set_ylabel("추세")
    axes[2].plot(df.index, result.seasonal, color="#4c72b0")
    axes[2].set_ylabel("계절성")
    axes[3].plot(df.index, result.resid, color="#999999", linewidth=0.6)
    axes[3].set_ylabel("잔차")
    axes[3].xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    axes[3].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.suptitle("서울 평균기온 STL 시계열 분해 (추세 / 계절성 / 잔차)")
    fig.tight_layout()
    fig.savefig(f"{IMG_DIR}/04_stl_decomposition.png", dpi=150)
    plt.close(fig)
    return result

def print_insight_numbers(df, monthly):
    print("\n--- 인사이트용 수치 ---")
    print("2023 연평균기온:", df.loc["2023", "temp_mean"].mean().round(2))
    print("2024 연평균기온:", df.loc["2024", "temp_mean"].mean().round(2))
    hottest_month = monthly["mean"].idxmax()
    coldest_month = monthly["mean"].idxmin()
    print("최고 평균기온 월:", hottest_month.strftime("%Y-%m"), monthly["mean"].max().round(2))
    print("최저 평균기온 월:", coldest_month.strftime("%Y-%m"), monthly["mean"].min().round(2))
    print("일교차 변화량 표준편차:", df["day_over_day_change"].std().round(2))
    max_volatility_date = df["rolling_std_30"].idxmax()
    print("변동성 최고 시점:", max_volatility_date.date(), df["rolling_std_30"].max().round(2))
    winter_2023 = df.loc["2023-12":"2024-02", "temp_mean"].mean()
    winter_2024 = df.loc["2024-12":"2024-12", "temp_mean"].mean()
    print("2023-12~2024-02 평균기온:", round(winter_2023, 2))

def main():
    df = load_and_clean()
    df, monthly = apply_time_series_techniques(df)
    make_visualizations(df, monthly)
    bonus_decomposition(df)
    print_insight_numbers(df, monthly)
    df.to_csv("data/seoul_daily_temperature_processed.csv")
    print("\n분석 완료. images/ 폴더에 4개 시각화 저장됨.")

if __name__ == "__main__":
    main()
