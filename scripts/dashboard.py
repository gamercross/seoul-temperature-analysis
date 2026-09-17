"""
서울 기온 시계열 분석 대시보드 (Streamlit)
- 기간(날짜 범위)과 이동평균 윈도우를 바꿔가며 탐색 가능
- 실행: streamlit run scripts/dashboard.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="서울 기온 시계열 대시보드", layout="wide")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "seoul_daily_temperature_2023_2024.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])
    return df.set_index("date").sort_index()

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
