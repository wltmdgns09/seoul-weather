import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ------------------------------------------------------------
# 기본 설정
# ------------------------------------------------------------
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide",
)

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)
    df["날짜"] = pd.to_datetime(df["날짜"])
    df["연도"] = df["날짜"].dt.year
    return df


df = load_data()

# ------------------------------------------------------------
# 연도별 평균 계산 (데이터가 거의 없는 첫해·마지막 해는 제외)
# ------------------------------------------------------------
counts_per_year = df.groupby("연도").size()
valid_years = counts_per_year[counts_per_year >= 300].index

yearly = (
    df[df["연도"].isin(valid_years)]
    .groupby("연도")["평균기온"]
    .mean()
    .reset_index()
    .rename(columns={"평균기온": "연평균기온"})
)

# 추세선(선형회귀)
coef = np.polyfit(yearly["연도"], yearly["연평균기온"], 1)
trend_fn = np.poly1d(coef)
yearly["추세선"] = trend_fn(yearly["연도"])

first_year = int(yearly["연도"].min())
last_year = int(yearly["연도"].max())
rise_per_decade = coef[0] * 10
total_rise = trend_fn(last_year) - trend_fn(first_year)

# ------------------------------------------------------------
# 사이드바 - 기간 선택
# ------------------------------------------------------------
st.sidebar.header("🔎 기간 설정")
year_range = st.sidebar.slider(
    "살펴볼 연도 범위를 골라보세요",
    min_value=first_year,
    max_value=last_year,
    value=(first_year, last_year),
)

filtered = yearly[(yearly["연도"] >= year_range[0]) & (yearly["연도"] <= year_range[1])]

# ------------------------------------------------------------
# 헤더
# ------------------------------------------------------------
st.title("🌡️ 서울, 100년의 기온 변화")
st.markdown(
    f"서울 기상 관측이 시작된 **{first_year}년**부터 **{last_year}년**까지, "
    "연평균 기온이 어떻게 변해왔는지 한눈에 살펴보는 페이지예요."
)

col1, col2, col3 = st.columns(3)
col1.metric("데이터 기간", f"{first_year} ~ {last_year}")
col2.metric("10년당 상승 추세", f"{rise_per_decade:+.2f} °C")
col3.metric("전체 기간 상승폭", f"{total_rise:+.2f} °C")

st.divider()

# ------------------------------------------------------------
# 메인 그래프
# ------------------------------------------------------------
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=filtered["연도"],
        y=filtered["연평균기온"],
        mode="lines+markers",
        name="연평균기온",
        line=dict(color="#4C8BF5", width=2),
        marker=dict(size=5),
        hovertemplate="%{x}년<br>연평균기온 %{y:.1f}°C<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=filtered["연도"],
        y=filtered["추세선"],
        mode="lines",
        name="장기 추세선",
        line=dict(color="#FF6B6B", width=2, dash="dash"),
        hoverinfo="skip",
    )
)

fig.update_layout(
    title="연도별 서울 연평균기온 변화",
    xaxis_title="연도",
    yaxis_title="연평균기온 (°C)",
    hovermode="x unified",
    template="plotly_white",
    height=520,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

st.plotly_chart(fig, use_container_width=True)

st.caption(
    "빨간 점선은 선택한 기간의 전반적인 상승·하락 추세를 나타내는 선형 추세선입니다. "
    "실제 기온은 해마다 오르내리지만, 긴 흐름을 보면 방향성을 파악할 수 있어요."
)

# ------------------------------------------------------------
# 원본 데이터 보기
# ------------------------------------------------------------
with st.expander("📄 연도별 데이터 표 보기"):
    st.dataframe(
        filtered[["연도", "연평균기온"]].round(2).sort_values("연도", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

st.caption("데이터 출처: 기상청 서울(종로구) 관측소 일별 기온 자료")
