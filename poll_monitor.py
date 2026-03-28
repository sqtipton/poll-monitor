import feedparser
from datetime import datetime, timezone, timedelta
from pyairtable import Api
from dotenv import load_dotenv
import os

load_dotenv()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = "app12YVG4qT36zPuf"
TABLE_ID = "tblGkFxZjmr5BzfOk"

# Connect to Airtable
api = Api(AIRTABLE_TOKEN)
table = api.table(BASE_ID, TABLE_ID)

# Only show polls from the last 30 days
DAYS_BACK = 30
cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)

# List of pollster RSS feeds
feeds = [
    {"name": "Pew Research", "url": "https://www.pewresearch.org/feed/"},
    {"name": "Marist Poll", "url": "https://maristpoll.marist.edu/feed/"},
    {"name": "U. Michigan", "url": "https://news.umich.edu/feed/"},
    {"name": "AP-NORC", "url": "https://apnorc.org/feed/rss/"},
    {"name": "Ipsos", "url": "https://www.ipsos.com/en-us/rss.xml"},
]

# Strong single keywords
strong_keywords = ["poll", "survey", "approval rating", "respondents", "public opinion"]

# Combo signals
opinion_words = ["think", "say", "view", "believe", "want", "support", "oppose", "disapprove", "approve", "favor", "worry", "feel", "prefer"]

# Skip these page types
exclude_keywords = [
    "methodology", "acknowledgment", "about this report", "how we did this",
    "time machine", "webinar", "data drops", "key insights", "data and tables",
    "essential data", "gloves", "stroke", "microplastics", "cancer", "clinical"
]

def is_poll(entry):
    text = (entry.title + " " + entry.get("summary", "")).lower()
    if any(word in text for word in exclude_keywords):
        return False
    if any(word in text for word in strong_keywords):
        return True
    if "americans" in text and any(word in text for word in opinion_words):
        return True
    if "u-m" in text and any(word in text for word in strong_keywords):
        return True
    return False

def get_date(entry):
    try:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        return None

def already_saved(url):
    results = table.all(formula=f"URL = '{url}'")
    return len(results) > 0

# Loop through each feed
total_new = 0
for feed in feeds:
    print(f"\n--- {feed['name']} ---")
    parsed = feedparser.parse(feed["url"])

    if len(parsed.entries) == 0:
        print("No entries found or feed unavailable")
        continue

    for entry in parsed.entries[:20]:
        date = get_date(entry)
        if date and date < cutoff:
            continue
        if not is_poll(entry):
            continue
        if already_saved(entry.link):
            print(f"Already saved: {entry.title}")
            continue

        # Save to Airtable
        table.create({
            "Title": entry.title,
            "Pollster": feed["name"],
            "Date": date.strftime("%Y-%m-%d") if date else "",
            "URL": entry.link,
            "Notes": entry.get("summary", "")[:500]
        })
        print(f"Saved: {entry.title}")
        total_new += 1

print(f"\n=== {total_new} new polls saved to Airtable ===")