"""
Pulls the last 24h of Fireflies transcripts, routes each to the matching
client file by participant email domain, and appends a call summary to
that file's ## Call Log section. Updates last_contact in frontmatter.

Real Fireflies API is used when FIREFLIES_API_KEY is set in the environment.
Otherwise falls back to fixtures/fireflies_mock_response.json, shaped exactly
like the real GraphQL response, so the routing/append logic is identical
either way. Swap is transparent: set FIREFLIES_API_KEY and this script pulls
real data with no code change.
"""
import os
import json
import requests
import frontmatter
from datetime import date, datetime
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

VAULT1 = os.path.join(BASE_DIR, "Vault1-ClientIntelligence")
MOCK_FIXTURE = os.path.join(BASE_DIR, "fixtures", "fireflies_mock_response.json")

DOMAIN_TO_CLIENT = {
    "arohafinance.in": os.path.join(VAULT1, "Clients", "Aroha-Finance", "Overview.md"),
    "lighthousecapital.in": os.path.join(VAULT1, "Clients", "Lighthouse-Capital", "Overview.md"),
}

# Domain matching breaks for personal contacts on shared providers (gmail.com
# is not a single entity), so personal proof-of-concept entries route by
# exact participant email instead.
EMAIL_TO_CLIENT = {
    "anuragacharya1412@gmail.com": os.path.join(
        VAULT1, "ProofOfConcept-Personal", "Contacts", "Anurag-Acharya", "Overview.md"
    ),
}

FIREFLIES_API_URL = "https://api.fireflies.ai/graphql"
GRAPHQL_QUERY = """
query {
  transcripts(limit: 20, skip: 0) {
    id
    title
    date
    duration
    participants
    summary { overview action_items }
    transcript_url
  }
}
"""


def fetch_transcripts():
    api_key = os.environ.get("FIREFLIES_API_KEY")
    if api_key:
        resp = requests.post(
            FIREFLIES_API_URL,
            json={"query": GRAPHQL_QUERY},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()["data"]["transcripts"]

    with open(MOCK_FIXTURE) as f:
        return json.load(f)["data"]["transcripts"]


def normalize_participant_emails(transcript):
    """
    Doc spec / mock fixture: participants = [{"email": ..., "name": ...}, ...]
    Real live API (observed): participants = flat list of email strings, with
    one comma-joined "all participants" entry mixed in. Handle both.
    """
    raw = transcript["participants"]
    emails = set()
    for p in raw:
        if isinstance(p, dict):
            emails.add(p["email"].lower())
        else:
            for part in p.split(","):
                part = part.strip().lower()
                if part:
                    emails.add(part)
    return emails


def normalize_action_items(transcript):
    """Mock fixture: list of strings. Real live API (observed): one string
    with embedded newlines. Handle both."""
    items = transcript["summary"]["action_items"]
    if isinstance(items, list):
        return [i for i in items if i.strip()]
    return [line.strip() for line in items.split("\n") if line.strip()]


def normalize_date(transcript):
    """Mock fixture / doc spec: "YYYY-MM-DD" string. Real live API (observed):
    epoch milliseconds (int). Handle both."""
    d = transcript["date"]
    if isinstance(d, (int, float)):
        return datetime.fromtimestamp(d / 1000).strftime("%Y-%m-%d")
    return d


def match_client_file(transcript):
    emails = normalize_participant_emails(transcript)
    for email in emails:
        if email in EMAIL_TO_CLIENT:
            return EMAIL_TO_CLIENT[email]
        domain = email.split("@")[-1]
        if domain in DOMAIN_TO_CLIENT:
            return DOMAIN_TO_CLIENT[domain]
    return None


def format_call_entry(transcript):
    action_items = "\n".join(f"  - {a}" for a in normalize_action_items(transcript))
    participants_str = ", ".join(sorted(normalize_participant_emails(transcript)))
    call_date = normalize_date(transcript)
    return (
        f"\n<!-- id:{transcript['id']} -->\n"
        f"### Call — {call_date}\n"
        f"- **Participants:** {participants_str}\n"
        f"- **Duration:** {round(transcript['duration'])} minutes\n"
        f"- **Summary:** {transcript['summary']['overview']}\n"
        f"- **Action items:**\n{action_items}\n"
        f"- **Full transcript:** {transcript['transcript_url']}\n"
        f"- **Logged:** {datetime.now().strftime('%Y-%m-%d %H:%M')} (auto)\n"
    )


def append_to_call_log(file_path, entry, contact_date, transcript_id):
    post = frontmatter.load(file_path)
    if f"<!-- id:{transcript_id} -->" in post.content:
        return False  # already logged (matches a stable id, not the visible text,
        # so edits to the entry afterward — e.g. redactions — don't break dedup)

    marker = "## Call Log\n<!-- fireflies_sync.py appends here -->"
    if marker in post.content:
        post.content = post.content.replace(marker, marker + entry)
    else:
        post.content += f"\n## Call Log\n{entry}"

    existing = post.get("last_contact")
    if existing is None or str(existing) < contact_date:
        post["last_contact"] = contact_date

    frontmatter.dump(post, file_path)
    return True


def run():
    transcripts = fetch_transcripts()
    synced, unmatched = 0, []

    for t in transcripts:
        file_path = match_client_file(t)
        if file_path is None:
            unmatched.append(t["title"])
            continue
        was_new = append_to_call_log(
            file_path, format_call_entry(t), normalize_date(t), t["id"]
        )
        if was_new:
            synced += 1

    return {"synced": synced, "unmatched": unmatched, "transcripts": transcripts}


if __name__ == "__main__":
    result = run()
    print(f"fireflies_sync: {result['synced']} transcript(s) synced")
    if result["unmatched"]:
        print(f"  unmatched (no domain match): {result['unmatched']}")
