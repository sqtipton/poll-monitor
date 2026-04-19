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

# Google Analytics
import streamlit.components.v1 as components
components.html("""
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-G1TK2TYB7D"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'G-G1TK2TYB7D');
    </script>
""", height=0)

# Navigation
page = st.sidebar.radio("Navigate", ["📊 Dashboard", "ℹ️ About & Methodology"])

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

# ── DASHBOARD PAGE ──
if page == "📊 Dashboard":
    st.title("📊 Poll Monitor")
    st.caption("Tracking public opinion polls in real time · Updated hourly")

    # Stat cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Total polls", len(df))
    col2.metric("Sources", df["Pollster"].nunique())
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

    # Bottom methodology summary
    st.markdown("---")
    st.caption("""
    **About Poll Monitor** · A nonpartisan project in support of American democracy. 
    Poll Monitor tracks public opinion research from 17 major pollsters and academic centers, 
    updated hourly. Topics are assigned automatically using keyword matching. 
    [Learn more →](#) *(click About & Methodology in the sidebar)*
    """)

# ── ABOUT PAGE ──
elif page == "ℹ️ About & Methodology":
    st.title("ℹ️ About & Methodology")

    st.markdown("""
    ## Our Mission
    People who care about issues – from policymakers to curious citizens – need a 
    user-friendly way to follow the latest polling so they can decide, discuss and debate. 
    **Poll Monitor is a nonpartisan project in support of American democracy.**

    ---

    ## Sources We Monitor
    Poll Monitor tracks new poll releases from 17 major pollsters and academic research centers:

    **Major Pollsters:** Gallup, Ipsos, YouGov, Morning Consult, Harris Poll, AP-NORC

    **Media Pollsters:** NBC News, ABC News, CNN

    **Academic Centers:** Pew Research, Marist Poll, University of Michigan, Monmouth University, 
    MIT Technology Review, Georgetown CSET, University of Florida, VCU Wilder School

    ---

    ## How Polls Are Selected
    Poll Monitor uses automated keyword matching to identify genuine poll releases from each 
    source's RSS feed or news index. Articles are included when they contain strong polling 
    indicators such as "poll", "survey", "public opinion", or "approval rating" — or when 
    they combine "Americans" with an opinion verb such as "say", "believe", or "support."

    Support pages, methodology documents, webinars, and non-poll content are automatically 
    excluded.

    ---

    ## How Topics Are Tagged
    Each poll is automatically assigned one of eight topics based on keyword matching:
    **Politics, Economy, Healthcare, Foreign Policy, Technology, Environment, Education, Media & Information
    or Social Issues.** Topic tagging is automated and may occasionally miscategorize 
    a poll — we are continuously improving accuracy.

    ---

    ## Update Frequency
    Poll Monitor checks all sources every hour via automated scripts running on GitHub Actions. 
    New polls typically appear within 1–2 hours of publication. A daily email digest is 
    delivered each morning summarizing the previous day's new releases.

    ---

    ## Data Limitations & Caveats
    - Poll Monitor surfaces poll *releases* — it does not verify methodology, sample size, 
      or margin of error. Always read the original poll before drawing conclusions.
    - Not all polls from all sources are captured — some pollsters do not publish via RSS 
      and may be missed.
    - Topic tags are assigned automatically and may not perfectly reflect poll content.
    - Poll Monitor is an aggregator and does not conduct original polling research.

    ---

    ## Contact
    Poll Monitor is a prototype in active development. For feedback or questions, 
    please reach out to the project team by emailing tiptons@vcu.edu.
    """)