
import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="YouTube 在線人數儀表板", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("youtube_live_data_long.csv", parse_dates=["時間"])
    df["日期"] = pd.to_datetime(df["時間"]).dt.date
    df["小時"] = pd.to_datetime(df["時間"]).dt.hour
    return df

df = load_data()

st.title("📺 YouTube 頻道在線人數互動儀表板")

channels = sorted(df["頻道名稱"].unique())
selected_channel = st.sidebar.selectbox("選擇頻道", channels)
min_date = df["時間"].min().date()
max_date = df["時間"].max().date()
selected_range = st.sidebar.date_input("選擇日期區間", [min_date, max_date])

mask = (
    (df["頻道名稱"] == selected_channel) &
    (df["日期"] >= selected_range[0]) &
    (df["日期"] <= selected_range[1])
)
filtered = df[mask]

st.subheader(f"📊 {selected_channel} 每日每小時在線人數")
hourly_avg = filtered.groupby(["日期", "小時"])["在線人數"].mean().reset_index()
chart = alt.Chart(hourly_avg).mark_line().encode(
    x=alt.X("小時:O", title="小時"),
    y=alt.Y("在線人數:Q", title="平均在線人數"),
    color="日期:N",
    tooltip=["日期", "小時", "在線人數"]
).interactive().properties(height=400)
st.altair_chart(chart, use_container_width=True)

def calculate_daily_stats(group):
    full_day = group["在線人數"].mean()
    avg_11_14 = group[group["小時"].between(11, 13)]["在線人數"].mean()
    avg_19_22 = group[group["小時"].between(19, 21)]["在線人數"].mean()
    return pd.Series({
        "每日平均在線人數": round(full_day, 2),
        "11:00–14:00 平均": round(avg_11_14, 2),
        "19:00–22:00 平均": round(avg_19_22, 2),
    })

stats = filtered.groupby("日期").apply(calculate_daily_stats).reset_index()

st.subheader("📈 每日在線人數統計表")
st.dataframe(stats, use_container_width=True)

st.download_button("📥 下載統計表（Excel）", data=stats.to_csv(index=False).encode('utf-8-sig'),
                   file_name=f"{selected_channel}_統計表.csv", mime="text/csv")
