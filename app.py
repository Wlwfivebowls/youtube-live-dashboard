
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

# 左側選單
mode = st.sidebar.radio("選擇模式", ["單一頻道分析", "各頻道比較"])

channels = sorted(df["頻道名稱"].unique())
min_date = df["時間"].min().date()
max_date = df["時間"].max().date()
selected_range = st.sidebar.date_input("選擇日期區間", [min_date, max_date])

filtered = df[(df["日期"] >= selected_range[0]) & (df["日期"] <= selected_range[1])]

if mode == "單一頻道分析":
    selected_channel = st.sidebar.selectbox("選擇頻道", channels)
    filtered = filtered[filtered["頻道名稱"] == selected_channel]

    st.subheader(f"📊 {selected_channel} 每日每小時在線人數")
    hourly_avg = filtered.groupby(["日期", "小時"])["在線人數"].mean().reset_index()
    chart = alt.Chart(hourly_avg).mark_line().encode(
        x=alt.X("小時:O", title="小時"),
        y=alt.Y("在線人數:Q", title="平均在線人數"),
        color="日期:N",
        tooltip=["日期", "小時", "在線人數"]
    ).interactive().properties(height=400)
    st.altair_chart(chart, use_container_width=True)
else:
    st.subheader("📊 各頻道每日平均在線人數比較")
    daily_avg = filtered.groupby(["日期", "頻道名稱"])["在線人數"].mean().reset_index()
    chart = alt.Chart(daily_avg).mark_line().encode(
        x=alt.X("日期:T", title="日期"),
        y=alt.Y("在線人數:Q", title="平均在線人數"),
        color="頻道名稱:N",
        tooltip=["頻道名稱", "日期", "在線人數"]
    ).interactive().properties(height=400)
    st.altair_chart(chart, use_container_width=True)

# 計算每日統計 + 區段平均
def calculate_daily_stats(group):
    full_day = group["在線人數"].mean()
    avg_11_14 = group[group["小時"].between(11, 13)]["在線人數"].mean()
    avg_19_22 = group[group["小時"].between(19, 21)]["在線人數"].mean()
    return pd.Series({
        "每日平均在線人數": round(full_day, 2),
        "11:00–14:00 平均": round(avg_11_14, 2),
        "19:00–22:00 平均": round(avg_19_22, 2),
    })

summary = filtered.groupby(["頻道名稱", "日期"]).apply(calculate_daily_stats).reset_index()

st.subheader("📈 每日在線人數統計表")
# 加入均值列
if not summary.empty:
    mean_row = summary.drop(columns=["日期", "頻道名稱"]).mean(numeric_only=True)
    mean_df = pd.DataFrame([["全部頻道均值", ""] + list(mean_row.values)], columns=summary.columns)
    summary = pd.concat([summary, mean_df], ignore_index=True)

st.dataframe(summary, use_container_width=True)

# 匯出功能
csv = summary.to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 下載統計表（Excel）", data=csv, file_name="每日在線統計表.csv", mime="text/csv")
