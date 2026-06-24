"""
Master orchestrator, per doc section 6.4. Runs fireflies_sync and gmail_sync,
scans Vault 1 client files for open issues and dormancy, builds a Daily Brief
markdown note, writes it to _Daily-Brief/, and sends it as a real email to
the user, replacing the doc's Slack push (no Slack workspace available here).
"""
import os
import re
from datetime import datetime, date
from email.mime.text import MIMEText
import base64

import frontmatter
from dotenv import load_dotenv

import fireflies_sync
import gmail_sync

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

VAULT1 = os.path.join(BASE_DIR, "Vault1-ClientIntelligence")
DAILY_BRIEF_DIR = os.path.join(VAULT1, "_Daily-Brief")
CLIENTS_DIR = os.path.join(VAULT1, "Clients")

SEND_TO = os.environ.get("DAILY_BRIEF_RECIPIENT", "")


def iter_client_files():
    for client_name in sorted(os.listdir(CLIENTS_DIR)):
        path = os.path.join(CLIENTS_DIR, client_name, "Overview.md")
        if os.path.exists(path):
            yield client_name, path


def check_dormancy(post):
    last_contact = post.get("last_contact")
    threshold = post.get("dormancy_threshold", 7)
    if not last_contact:
        return None
    last_contact_date = datetime.strptime(str(last_contact), "%Y-%m-%d").date()
    days_since = (date.today() - last_contact_date).days
    if days_since > threshold:
        return days_since
    return None


def collect_open_issues(post):
    return re.findall(r"^- \[ \] (.+)$", post.content, re.MULTILINE)


def build_brief(fireflies_result, gmail_result):
    today_str = date.today().strftime("%A, %d %B %Y")
    lines = [f"# Daily Brief — {today_str}\n"]

    lines.append("## Sync Summary")
    lines.append(f"- Fireflies: {fireflies_result['synced']} transcript(s) processed")
    if fireflies_result["unmatched"]:
        lines.append(f"  - Unmatched (no routing match): {len(fireflies_result['unmatched'])}")
    lines.append(f"- Gmail: {gmail_result['synced']} email(s) matched and logged "
                 f"out of {gmail_result['total_checked']} checked\n")

    dormancy_lines = []
    issue_lines = []
    for client_name, path in iter_client_files():
        post = frontmatter.load(path)
        days_since = check_dormancy(post)
        if days_since is not None:
            dormancy_lines.append(f"- {client_name} — last contact {days_since} days ago")
        for issue in collect_open_issues(post):
            issue_lines.append(f"- {client_name}: {issue}")

    lines.append("## Dormancy Alerts — Clients")
    lines.extend(dormancy_lines if dormancy_lines else ["- None"])
    lines.append("")

    lines.append("## Open Issues (all clients)")
    lines.extend(issue_lines if issue_lines else ["- None"])
    lines.append("")

    lines.append("---")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                  f"Predixion Obsidian Sync MVP")

    return "\n".join(lines)


def write_brief_file(brief_text):
    os.makedirs(DAILY_BRIEF_DIR, exist_ok=True)
    path = os.path.join(DAILY_BRIEF_DIR, f"{date.today().isoformat()}.md")
    with open(path, "w") as f:
        f.write(brief_text)
    return path


def send_brief_email(brief_text):
    service = gmail_sync.get_gmail_service()
    message = MIMEText(brief_text)
    message["to"] = SEND_TO
    message["subject"] = f"Daily Brief — {date.today().isoformat()}"
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return sent["id"]


def run():
    fireflies_result = fireflies_sync.run()
    gmail_result = gmail_sync.run()
    brief_text = build_brief(fireflies_result, gmail_result)
    file_path = write_brief_file(brief_text)
    message_id = send_brief_email(brief_text)
    return {"file_path": file_path, "message_id": message_id, "brief_text": brief_text}


if __name__ == "__main__":
    result = run()
    print(f"daily_brief: written to {result['file_path']}")
    print(f"daily_brief: emailed to {SEND_TO}, message id {result['message_id']}")
