"""
Analogous to the doc's outlook_sync.py (section 6.2), adapted from Microsoft
Graph to Gmail since Outlook/Azure access isn't available here. Queries the
last 24h of messages, matches sender/recipient domain to a client file,
appends a formatted email summary to that file's ## Email Log section.

Real Gmail API, OAuth via credentials.json (Desktop app client). Token is
cached in token.json after the first browser approval.
"""
import os
import base64
from datetime import datetime, timedelta

import frontmatter
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

VAULT1 = os.path.join(BASE_DIR, "Vault1-ClientIntelligence")
CREDS_FILE = os.path.join(BASE_DIR, os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json"))
TOKEN_FILE = os.path.join(BASE_DIR, os.environ.get("GOOGLE_TOKEN_FILE", "token.json"))

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

DOMAIN_TO_CLIENT = {
    "arohafinance.in": os.path.join(VAULT1, "Clients", "Aroha-Finance", "Overview.md"),
    "lighthousecapital.in": os.path.join(VAULT1, "Clients", "Lighthouse-Capital", "Overview.md"),
}


def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def fetch_last_24h_messages(service):
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y/%m/%d")
    query = f"newer:{yesterday}"
    results = service.users().messages().list(userId="me", q=query, maxResults=50).execute()
    return results.get("messages", [])


def get_message_detail(service, msg_id):
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="metadata",
        metadataHeaders=["From", "To", "Subject", "Date"],
    ).execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    return {
        "id": msg_id,
        "from": headers.get("From", ""),
        "to": headers.get("To", ""),
        "subject": headers.get("Subject", ""),
        "date": headers.get("Date", ""),
        "snippet": msg.get("snippet", ""),
    }


def vault_link(file_path):
    rel = os.path.relpath(file_path, VAULT1).replace(os.sep, "/")
    return rel[:-3] if rel.endswith(".md") else rel


def write_email_file(file_path, detail, entry):
    """Mirrors the doc's section 4.1 folder structure (Emails/ subfolder per
    client). Linked back to the client file via wikilink for graph view."""
    client_dir = os.path.dirname(file_path)
    emails_dir = os.path.join(client_dir, "Emails")
    os.makedirs(emails_dir, exist_ok=True)
    out_path = os.path.join(emails_dir, f"{datetime.now().strftime('%Y-%m-%d')}-{detail['id']}.md")
    if os.path.exists(out_path):
        return False

    client_name = frontmatter.load(file_path).get("client", "")
    link_target = vault_link(file_path)
    content = (
        f"---\n"
        f'client: "[[{link_target}|{client_name}]]"\n'
        f"type: email\n"
        f"---\n"
        f"{entry.lstrip(chr(10))}"
    )
    with open(out_path, "w") as f:
        f.write(content)
    return True


def match_client_file(detail):
    for field in (detail["from"], detail["to"]):
        for domain in DOMAIN_TO_CLIENT:
            if domain in field.lower():
                return DOMAIN_TO_CLIENT[domain]
    return None


def format_email_entry(detail):
    preview = detail["snippet"][:200]
    return (
        f"\n### Email — {detail['date']}\n"
        f"- **From:** {detail['from']}\n"
        f"- **Subject:** {detail['subject']}\n"
        f"- **Preview:** {preview}\n"
        f"- **Logged:** {datetime.now().strftime('%Y-%m-%d %H:%M')} (auto)\n"
    )


def append_to_email_log(file_path, entry):
    post = frontmatter.load(file_path)
    marker = "## Email Log\n<!-- gmail_sync.py appends here -->"
    if marker in post.content:
        post.content = post.content.replace(marker, marker + entry)
    else:
        post.content += f"\n## Email Log\n{entry}"
    frontmatter.dump(post, file_path)


def run():
    service = get_gmail_service()
    messages = fetch_last_24h_messages(service)
    synced, unmatched = 0, []

    for m in messages:
        detail = get_message_detail(service, m["id"])
        file_path = match_client_file(detail)
        if file_path is None:
            unmatched.append(detail["subject"])
            continue
        entry = format_email_entry(detail)
        append_to_email_log(file_path, entry)
        write_email_file(file_path, detail, entry)
        synced += 1

    return {"synced": synced, "unmatched_count": len(unmatched), "total_checked": len(messages)}


if __name__ == "__main__":
    result = run()
    print(f"gmail_sync: {result['synced']} email(s) matched and logged "
          f"out of {result['total_checked']} checked in the last 24h")
