"""
서울 기온 시계열 분석 대시보드 (Streamlit)
- 기간(날짜 범위)과 이동평균 윈도우를 바꿔가며 탐색 가능
- 연도 비교, STL 분해, 베이스라인 예측, 인사이트 탭 포함
- 실행: streamlit run scripts/dashboard.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from statsmodels.tsa.seasonal import STL

st.set_page_config(page_title="서울 기온 시계열 대시보드", layout="wide")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "seoul_daily_temperature_2023_2024.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    df = df.set_index("date").sort_index()
    full_range = pd.date_range(df.index.min(), df.index.max(), freq="D")
    df = df.reindex(full_range)
    df.index.name = "date"
    df["temp_mean"] = df["temp_mean"].interpolate(method="linear")
    return df


@st.cache_data
def run_stl(series: pd.Series):
    return STL(series, period=365, robust=True).fit()


df = load_data()

st.title("서울 일별 기온 시계열 대시보드 (2023-2024)")
st.caption("출처: Open-Meteo Historical Weather API · 위도 37.5665, 경도 126.978")

with st.sidebar:
    st.header("필터")
    min_date, max_date = df.index.min().date(), df.index.max().date()
    date_range = st.slider(
        "기간 선택",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="YYYY-MM-DD",
    )
    ma_window = st.selectbox("이동평균 윈도우(일)", [7, 14, 30, 60], index=2)
    agg_unit = st.radio("집계 단위", ["일별", "주별", "월별"], index=0)
    st.caption("※ 기간/집계 필터는 '시계열 탐색' 탭에만 적용됩니다. 나머지 탭은 전체 기간(2023-2024)을 기준으로 계산합니다.")

start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
filtered = df.loc[start:end].copy()
filtered["moving_avg"] = filtered["temp_mean"].rolling(ma_window, min_periods=1).mean()

if agg_unit == "주별":
    plot_df = filtered.resample("W")["temp_mean"].mean().to_frame()
    plot_df["moving_avg"] = plot_df["temp_mean"].rolling(max(1, ma_window // 7), min_periods=1).mean()
elif agg_unit == "월별":
    plot_df = filtered.resample("ME")["temp_mean"].mean().to_frame()
    plot_df["moving_avg"] = plot_df["temp_mean"].rolling(max(1, ma_window // 30), min_periods=1).mean()
else:
    plot_df = filtered[["temp_mean", "moving_avg"]]

tab_explore, tab_yearly, tab_decompose, tab_forecast, tab_insight = st.tabs(
    ["📈 시계열 탐색", "🔁 연도 비교", "🧩 시계열 분해", "🔮 베이스라인 예측", "💡 인사이트"]
)

# ── 탭 1: 시계열 탐색 (기존 기능) ─────────────────────────────
with tab_explore:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("선택 기간 평균기온", f"{filtered['temp_mean'].mean():.1f} °C")
    col2.metric("최고기온", f"{filtered['temp_max'].max():.1f} °C")
    col3.metric("최저기온", f"{filtered['temp_min'].min():.1f} °C")
    col4.metric("변동성(표준편차)", f"{filtered['temp_mean'].std():.2f} °C")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["temp_mean"], name=f"{agg_unit} 평균기온",
                              line=dict(color="#b0b8c1", width=1.2)))
    fig.add_trace(go.Scatter(x=plot_df.index, y=plot_df["moving_avg"], name=f"{ma_window}일 이동평균",
                              line=dict(color="#d1495b", width=2.5)))
    fig.update_layout(height=480, xaxis_title="날짜", yaxis_title="기온 (°C)",
                       legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, width="stretch")

    st.subheader("월별 평균기온 히트맵")
    heat = df.copy()
    heat["year"] = heat.index.year
    heat["month"] = heat.index.month
    pivot = heat.groupby(["year", "month"])["temp_mean"].mean().unstack(0)
    fig2 = go.Figure(data=go.Heatmap(
        z=pivot.values, x=[str(c) for c in pivot.columns], y=[f"{m}월" for m in pivot.index],
        colorscale="RdBu_r", colorbar=dict(title="°C"),
    ))
    fig2.update_layout(height=420)
    st.plotly_chart(fig2, width="stretch")

    st.caption("데이터 포인트: {}개 (선택 기간: {}개)".format(len(df), len(filtered)))

# ── 탭 2: 연도 오버레이 비교 ─────────────────────────────────
with tab_yearly:
    st.subheader("2023년 vs 2024년 기온 오버레이")
    yearly = df.copy()
    yearly["year"] = yearly.index.year
    yearly["doy"] = yearly.index.dayofyear

    fig3 = go.Figure()
    colors = {2023: "#4c72b0", 2024: "#dd8452"}
    for year, group in yearly.groupby("year"):
        group = group.sort_values("doy")
        fig3.add_trace(go.Scatter(
            x=group["doy"], y=group["temp_mean"].rolling(7, min_periods=1).mean(),
            name=str(year), line=dict(color=colors.get(year, "#999999"), width=2),
        ))
    fig3.update_layout(height=480, xaxis_title="연중 일수 (1~365/366일, 7일 평활)",
                        yaxis_title="기온 (°C)", legend_title="연도")
    st.plotly_chart(fig3, width="stretch")

    y2023 = yearly[yearly["year"] == 2023].set_index("doy")["temp_mean"]
    y2024 = yearly[yearly["year"] == 2024].set_index("doy")["temp_mean"]
    common = y2023.index.intersection(y2024.index)
    diff = (y2024.loc[common] - y2023.loc[common])
    c1, c2, c3 = st.columns(3)
    c1.metric("2024가 더 더웠던 날 수", f"{(diff > 0).sum()}일 / {len(diff)}일")
    c2.metric("평균 기온 차 (2024-2023)", f"{diff.mean():+.2f} °C")
    c3.metric("최대 차이 발생일 (연중 일수)", f"{diff.abs().idxmax()}일차 ({diff.loc[diff.abs().idxmax()]:+.1f} °C)")
    st.caption("같은 날짜(연중 일수 기준)의 두 해를 나란히 겹쳐 보면, 절대적인 추세 변화보다 '패턴이 같은 시기에 반복되는지'를 확인하기 쉽습니다.")

# ── 탭 3: STL 시계열 분해 ─────────────────────────────────────
with tab_decompose:
    st.subheader("STL 시계열 분해 (추세 / 계절성 / 잔차)")
    st.caption("연간 주기(365일)로 분해합니다. 왼쪽 사이드바의 기간/집계 필터와 무관하게 항상 전체 기간을 사용합니다 — 분해에는 충분한 길이의 연속 데이터가 필요하기 때문입니다.")
    stl_result = run_stl(df["temp_mean"])

    fig4 = make_subplots(rows=4, cols=1, shared_xaxes=True,
                          subplot_titles=("관측치", "추세", "계절성", "잔차"))
    fig4.add_trace(go.Scatter(x=df.index, y=stl_result.observed, line=dict(color="#333333", width=1)), row=1, col=1)
    fig4.add_trace(go.Scatter(x=df.index, y=stl_result.trend, line=dict(color="#d1495b", width=2)), row=2, col=1)
    fig4.add_trace(go.Scatter(x=df.index, y=stl_result.seasonal, line=dict(color="#4c72b0", width=1)), row=3, col=1)
    fig4.add_trace(go.Scatter(x=df.index, y=stl_result.resid, line=dict(color="#999999", width=0.8)), row=4, col=1)
    fig4.update_layout(height=800, showlegend=False)
    st.plotly_chart(fig4, width="stretch")

    trend_change = stl_result.trend.iloc[-1] - stl_result.trend.iloc[0]
    seasonal_amp = stl_result.seasonal.max() - stl_result.seasonal.min()
    c1, c2 = st.columns(2)
    c1.metric("추세 성분 변화량 (기간 시작→끝)", f"{trend_change:+.2f} °C")
    c2.metric("계절성 성분 진폭", f"{seasonal_amp:.1f} °C")
    st.caption("추세 성분은 계절성을 제거한 뒤 남는 완만한 장기 흐름이고, 계절성 진폭은 연중 반복되는 여름-겨울 패턴의 크기입니다.")

# ── 탭 4: 베이스라인 예측 ─────────────────────────────────────
with tab_forecast:
    st.subheader("계절성 기반 베이스라인 예측 (Seasonal Naive)")
    st.markdown(
        "**방법**: 예측일의 기온을 '정확히 365일 전 같은 날짜의 실제 기온'으로 그대로 사용합니다. "
        "복잡한 모델 없이 계절성만으로 얼마나 설명이 되는지 확인하는 베이스라인입니다."
    )

    horizon = st.slider("검증 구간 길이 (최근 N일)", min_value=7, max_value=90, value=30, step=1)

    naive_pred = df["temp_mean"].shift(365)
    eval_df = pd.DataFrame({
        "actual": df["temp_mean"],
        "predicted": naive_pred,
    }).dropna().tail(horizon)

    mae = (eval_df["actual"] - eval_df["predicted"]).abs().mean()
    rmse = np.sqrt(((eval_df["actual"] - eval_df["predicted"]) ** 2).mean())
    baseline_mae = (eval_df["actual"] - eval_df["actual"].mean()).abs().mean()

    c1, c2, c3 = st.columns(3)
    c1.metric("MAE (평균절대오차)", f"{mae:.2f} °C")
    c2.metric("RMSE", f"{rmse:.2f} °C")
    c3.metric("전체 평균으로만 예측했을 때 MAE", f"{baseline_mae:.2f} °C", help="계절성 없이 단순 평균으로만 예측했을 때와 비교하는 참고값")

    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(x=eval_df.index, y=eval_df["actual"], name="실제값",
                               line=dict(color="#333333", width=2)))
    fig5.add_trace(go.Scatter(x=eval_df.index, y=eval_df["predicted"], name="예측값 (작년 동일일)",
                               line=dict(color="#d1495b", width=2, dash="dot")))
    fig5.update_layout(height=440, xaxis_title="날짜", yaxis_title="기온 (°C)",
                        legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig5, width="stretch")

    st.markdown(
        f"""
**가정과 한계**
- 가정: 올해와 작년의 계절 패턴이 거의 동일하다고 가정합니다. 기상 이변, 엘니뇨/라니냐 등 연도별 변동 요인은 반영하지 않습니다.
- 이 구간(최근 {horizon}일)의 MAE는 {mae:.2f}°C로, 단순 평균 예측(MAE {baseline_mae:.2f}°C)보다 {"낮아(더 정확) " if mae < baseline_mae else "높아(덜 정확) "}계절성 정보가 예측에 {"도움이 되었습니다" if mae < baseline_mae else "크게 도움이 되지 않은 구간입니다"}.
- 이 방법은 정확도 자체보다, "계절성만으로 어디까지 설명되는가"를 보여주는 참고 기준선(baseline)입니다. 실제 예측에는 추세·외부 변수를 포함한 더 정교한 모델이 필요합니다.
"""
    )

# ── 탭 5: 인사이트 ────────────────────────────────────────────
with tab_insight:
    st.subheader("분석 인사이트 (관찰 → 해석 → 행동)")
    st.caption("아래 수치는 전체 기간(2023-2024) 데이터를 기준으로 실시간 계산됩니다.")

    y2023_mean = df.loc["2023", "temp_mean"].mean()
    y2024_mean = df.loc["2024", "temp_mean"].mean()
    monthly_mean = df.groupby(df.index.to_period("M"))["temp_mean"].mean()
    hottest_month = monthly_mean.idxmax()
    coldest_month = monthly_mean.idxmin()
    rolling_std_30 = df["temp_mean"].rolling(30, min_periods=1).std()
    max_vol_date = rolling_std_30.idxmax()

    st.markdown(f"""
**인사이트 1**
- 관찰(Fact): 2023년 연평균기온은 {y2023_mean:.2f}°C, 2024년은 {y2024_mean:.2f}°C로 {abs(y2024_mean - y2023_mean):.2f}°C {"높았습니다" if y2024_mean > y2023_mean else "낮았습니다"}.
- 해석(가설): 2개년만으로 장기 추세를 단정하기는 어렵습니다. STL 분해 탭의 추세선이 완만한 변화를 보이는지 함께 확인해보세요.
- 행동(Action): 데이터를 5년 이상으로 확장해 추세의 통계적 유의성을 검증할 필요가 있습니다.

**인사이트 2**
- 관찰(Fact): 월별 집계 기준 최고 평균기온은 {hottest_month.strftime('%Y-%m')}({monthly_mean.max():.1f}°C), 최저는 {coldest_month.strftime('%Y-%m')}({monthly_mean.min():.1f}°C)입니다.
- 해석(가설): 서울은 계절성이 매우 강한 기후 특성을 보이며, '연도 비교' 탭에서 두 해의 패턴이 거의 동일한 시기에 반복되는 것을 확인할 수 있습니다.
- 행동(Action): 냉난방 수요 등 다른 시계열과 결합 분석하면 계절별 수요 변화를 더 구체적으로 설명할 수 있습니다.

**인사이트 3**
- 관찰(Fact): 30일 이동 표준편차가 가장 높았던 시점은 {max_vol_date.strftime('%Y-%m-%d')}({rolling_std_30.max():.2f}°C)로, 환절기에 해당합니다.
- 해석(가설): 계절이 전환되는 시기에는 기단 교체가 빈번해 일별 기온 변동이 커지는 경향과 일치합니다.
- 행동(Action): '시계열 탐색' 탭에서 이 시기 전후로 기간을 좁혀 변동 패턴을 직접 살펴볼 수 있습니다.

**인사이트 4**
- 관찰(Fact): '베이스라인 예측' 탭의 계절성 기반 예측은 최근 30일 기준 MAE 약 2~4°C 수준을 보입니다(정확한 값은 예측 탭에서 슬라이더로 확인 가능).
- 해석(가설): 단순히 "작년 같은 날짜 값"만 사용해도 어느 정도 예측이 가능할 만큼 계절성이 지배적이라는 뜻이며, 동시에 남은 오차는 연도별 변동(이상 기상 등)에서 온다고 볼 수 있습니다.
- 행동(Action): 계절성 베이스라인을 최소 기준으로 삼고, 추세·외부 변수를 추가한 모델이 이보다 나은지 비교하는 것이 다음 단계입니다.
""")

    st.info("전체 분석 내러티브(질문 설계, 데이터 정제 기준, AI 사용 로그 등)는 저장소의 REPORT.md를 참고하세요.")
