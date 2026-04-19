import feedparser
from datetime import datetime, timezone, timedelta
from pyairtable import Api
from dotenv import load_dotenv
import os

from dotenv import load_dotenv
import os
import anthropic

load_dotenv()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Set up Claude client
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
BASE_ID = "app12YVG4qT36zPuf"
TABLE_ID = "tblGkFxZjmr5BzfOk"
def get_topic(title):
    message = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{
            "role": "user",
           "content": f"Assign one topic to this poll title from this list only: Politics, Economy, Healthcare, International affairs, National security, Social Issues, Environment, Education, Immigration, LGBTQ+, AI/Technology, Business, Finance, Labor/workforce, Entertainment, Media & Information. Reply with just the topic word, nothing else. Poll title: {title}"
        }]
    )
    return message.content[0].text.strip()

def verify_pollster(feed_name, url):
    news_feeds = ["U. Florida", "VCU Wilder"]
    if feed_name not in news_feeds:
        return "Verified"
    domain_map = {
        "U. Florida": "ufl.edu",
        "VCU Wilder": "vcu.edu"
    }
    expected_domain = domain_map.get(feed_name, "")
    if expected_domain in url:
        return "Verified"
    else:
        return "Needs Verification"

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
    {"name": "MIT Tech Review", "url": "https://www.technologyreview.com/feed/"},
    {"name": "Georgetown CSET", "url": "https://cset.georgetown.edu/feed/"},
    {"name": "Gallup", "url": "https://news.google.com/rss/search?q=poll+site:gallup.com&hl=en-US&gl=US&ceid=US:en"},
    {"name": "YouGov", "url": "https://news.google.com/rss/search?q=yougov+poll+americans&hl=en-US&gl=US&ceid=US:en"},
    {"name": "NBC News", "url": "https://news.google.com/rss/search?q=NBC+News+poll+americans&hl=en-US&gl=US&ceid=US:en"},
    {"name": "ABC News", "url": "https://news.google.com/rss/search?q=ABC+News+poll+americans&hl=en-US&gl=US&ceid=US:en"},
    {"name": "CNN", "url": "https://news.google.com/rss/search?q=CNN+poll+americans&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Monmouth", "url": "https://monmouth.edu/polling-institute/feed/"},
    {"name": "Morning Consult", "url": "https://news.google.com/rss/search?q=morning+consult+poll+americans&hl=en-US&gl=US&ceid=US:en"},
    {"name": "Harvard/Harris Poll", "url": "https://news.google.com/rss/search?q=harvard+caps+harris+poll&hl=en-US&gl=US&ceid=US:en"},
    {"name": "HarrisX", "url": "https://news.google.com/rss/search?q=harrisx+poll+americans&hl=en-US&gl=US&ceid=US:en"},
    {"name": "U. Florida", "url": "https://news.google.com/rss/search?q=University+of+Florida+poll+survey+americans&hl=en-US&gl=US&ceid=US:en"},
    {"name": "VCU Wilder", "url": "https://news.google.com/rss/search?q=VCU+Wilder+poll+survey&hl=en-US&gl=US&ceid=US:en"},
]

# Strong single keywords
strong_keywords = ["poll", "survey", "approval rating", "respondents", "public opinion", "research finds", "study finds", "americans think", "public attitudes", "public views", "findings"]

# Combo signals
opinion_words = ["think", "say", "view", "believe", "want", "support", "oppose", "disapprove", "approve", "favor", "worry", "feel", "prefer", "trust", "concerned", "confident"]

# Skip these page types
exclude_keywords = [
    "methodology", "acknowledgment", "about this report", "how we did this",
    "time machine", "webinar", "data drops", "key insights", "data and tables",
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

def already_saved(url, title):
    url_results = table.all(formula=f"URL = '{url}'")
    if len(url_results) > 0:
        return True
    safe_title = title.replace("'", "\\'")
    title_results = table.all(formula=f"Title = '{safe_title}'")
    return len(title_results) > 0

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
        if already_saved(entry.link, entry.title):
            print(f"Already saved: {entry.title}")
            continue

        # Save to Airtable
        topic = get_topic(entry.title)
        verification = verify_pollster(feed["name"], entry.link)
        table.create({
            "Title": entry.title,
            "Pollster": feed["name"],
            "Topic": topic,
            "Date": date.strftime("%Y-%m-%d") if date else "",
            "URL": entry.link,
            "Notes": entry.get("summary", "")[:500],
            "Verification": verification
        })
        print(f"Saved: {entry.title} → {topic} → {verification}")
        total_new += 1

print(f"\n=== {total_new} new polls saved to Airtable ===")