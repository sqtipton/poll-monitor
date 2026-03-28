import streamlit as st
from pyairtable import Api
from dotenv import load_dotenv
import os
import pandas as pd

# Load token
load_dotenv()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = "app12YVG4qT36zPuf"
TABLE_ID = "tblGkFxZjmr5BzfOk"

# Connect to Airtable
api = Api(AIRTABLE_TOKEN)
table = api.table(BASE_ID, TABLE_ID)

# Page setup
st.set_page_config(page_title="Poll Monitor", page_icon="📊", layout="wide")
st.title("📊 Poll Monitor")
st.caption("Tracking public opinion polls in real time")

# Load data
@st.cache_data(ttl=300)
def load_polls():
    records = table.all()
    rows = []
    for r in records:
        f = r["fields"]
        rows.append({
            "Title": f.get("Title", ""),
            "Pollster": f.get("Pollster", ""),
            "Topic": f.get("Topic", "Untagged"),
            "Date": f.get("Date", ""),
            "URL": f.get("URL", ""),
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("Date", ascending=False)
    return df

df = load_polls()

# Stat cards
col1, col2, col3 = st.columns(3)
col1.metric("Total polls", len(df))
col2.metric("Pollsters", df["Pollster"].nunique())
col3.metric("Most recent", df["Date"].max() if not df.empty else "N/A")

st.divider()

# Filters
st.subheader("Filters")
col1, col2 = st.columns(2)

with col1:
    pollsters = ["All"] + sorted(df["Pollster"].unique().tolist())
    selected_pollster = st.selectbox("Pollster", pollsters)

with col2:
    topics = ["All"] + sorted(df["Topic"].unique().tolist())
    selected_topic = st.selectbox("Topic", topics)

# Apply filters
filtered = df.copy()
if selected_pollster != "All":
    filtered = filtered[filtered["Pollster"] == selected_pollster]
if selected_topic != "All":
    filtered = filtered[filtered["Topic"] == selected_topic]

st.divider()

# Poll list
st.subheader(f"{len(filtered)} polls found")
for _, row in filtered.iterrows():
    with st.container():
        st.markdown(f"**[{row['Title']}]({row['URL']})**")
        st.caption(f"🗓 {row['Date']} · 📋 {row['Pollster']} · 🏷 {row['Topic']}")
        st.divider()