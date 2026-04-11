import sendgrid
from sendgrid.helpers.mail import Mail
from pyairtable import Api
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load credentials
load_dotenv()
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
BASE_ID = "app12YVG4qT36zPuf"
TABLE_ID = "tblGkFxZjmr5BzfOk"

# Email recipients — add or remove addresses from this list
RECIPIENT_EMAILS = [
    "stacia@tipton-inc.com",
    "drgloriast@gmail.com",
    "david.tiptoncpa@gmail.com",
]
# Connect to Airtable
api = Api(AIRTABLE_TOKEN)
table = api.table(BASE_ID, TABLE_ID)

# Get yesterday's polls
yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
records = table.all()

recent_polls = []
for r in records:
    f = r["fields"]
    if f.get("Date", "") >= yesterday:
        recent_polls.append(f)

# Build email body
if len(recent_polls) == 0:
    print("No new polls yesterday — no email sent")
else:
    body = f"<h2>📊 Poll Monitor — Daily Digest</h2>"
    body += f"<p>{len(recent_polls)} new polls found</p><hr>"

    for poll in recent_polls:
        body += f"<h3><a href='{poll.get('URL', '')}'>{poll.get('Title', '')}</a></h3>"
        body += f"<p>📋 {poll.get('Pollster', '')} &nbsp;|&nbsp; 🏷 {poll.get('Topic', '')} &nbsp;|&nbsp; 🗓 {poll.get('Date', '')}</p>"
        body += "<hr>"

    # Send email
    message = Mail(
        from_email="stacia@tipton-inc.com",
        to_emails=RECIPIENT_EMAILS,
        subject=f"Poll Monitor Digest — {datetime.now().strftime('%B %d, %Y')}",
        html_content=body
    )

    sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
    response = sg.send(message)
    print(f"Email sent! Status code: {response.status_code}")