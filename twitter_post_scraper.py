#!/usr/bin/env python3
"""Twitter/X Post Discovery Tool via Bright Data.

Workflow: Keywords CSV -> BD Twitter Posts Dataset -> Extract tweets + author info -> Deduplicate by author -> Output CSV

Usage:
    python twitter_post_scraper.py keywords.csv output_tweets.csv

Requires:
    - Python 3.9+
    - Bright Data API key (set BRIGHT_DATA_API_KEY environment variable)
    - Active Bright Data subscription with Twitter/X datasets enabled
"""

import csv
import json
import os
import re
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ============================================================
# CONFIGURATION - Set your API key as an environment variable
# ============================================================
API_KEY = os.environ.get("BRIGHT_DATA_API_KEY", "")
if not API_KEY:
    print("ERROR: Set your Bright Data API key:")
    print("  Windows:  set BRIGHT_DATA_API_KEY=your-api-key-here")
    print("  Mac/Linux: export BRIGHT_DATA_API_KEY=your-api-key-here")
    print()
    print("Get your API key from: https://brightdata.com/cp/setting/users")
    sys.exit(1)

# Bright Data dataset ID
POSTS_DATASET_ID = "gd_lwxkxvnf1cynvib9co"  # Twitter/X - Posts

BASE_URL = "https://api.brightdata.com/datasets/v3"

POLL_INTERVAL = 15  # seconds between status checks
POLL_TIMEOUT = 1800  # 30 minutes max wait

# Regex patterns
EMAIL_REGEX = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
URL_REGEX = re.compile(r'https?://[^\s\)\]\}>"\']+', re.IGNORECASE)

# False-positive email patterns to filter out
EMAIL_BLACKLIST_PATTERNS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".webp",
    "noreply@",
    "no-reply@",
    "example.com",
    "email.com",
    "yourname@",
    "username@",
    "test@",
}

# Internal Twitter/media domains to filter from external links
INTERNAL_DOMAINS = {
    "twitter.com",
    "www.twitter.com",
    "x.com",
    "www.x.com",
    "t.co",
    "pic.twitter.com",
    "pbs.twimg.com",
    "video.twimg.com",
    "abs.twimg.com",
}

# Default keywords used when no CSV is provided
DEFAULT_KEYWORDS = [
    "ai marketing tools",
    "saas launch",
    "indie hacker",
]


def api_request(method, url, data=None):
    """Make an HTTP request to the Bright Data API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=180) as resp:
            raw = resp.read().decode()
            if not raw.strip():
                return None
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw.strip()
    except HTTPError as e:
        body_text = e.read().decode() if e.fp else ""
        print(f"  HTTP {e.code}: {body_text[:500]}")
        raise
    except URLError as e:
        print(f"  Network error: {e.reason}")
        raise


def read_keywords_csv(path):
    """Read keywords from a CSV file.

    Expected format:
        keyword
        ai marketing tools
        saas launch
    """
    keywords = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header and header[0].lower().strip() not in ("keyword", "keywords"):
            keywords.append(header[0].strip())
        for row in reader:
            if not row or not row[0].strip():
                continue
            keywords.append(row[0].strip())
    return keywords


def trigger_collection(dataset_id, inputs, discover_by=None):
    """Trigger a Bright Data dataset collection. Returns snapshot_id."""
    url = f"{BASE_URL}/trigger?dataset_id={dataset_id}&notify=false&include_errors=true"
    if discover_by:
        url += f"&type=discover_new&discover_by={discover_by}"
    payload = {"input": inputs}
    print(f"  Triggering collection with {len(inputs)} input(s)...")
    resp = api_request("POST", url, payload)
    if isinstance(resp, dict) and "snapshot_id" in resp:
        return resp["snapshot_id"]
    if isinstance(resp, str):
        return resp
    raise RuntimeError(f"Unexpected trigger response: {resp}")


def poll_until_ready(snapshot_id):
    """Poll Bright Data until the snapshot data is ready for download."""
    url = f"{BASE_URL}/progress/{snapshot_id}"
    start = time.time()
    last_status = None
    while time.time() - start < POLL_TIMEOUT:
        try:
            resp = api_request("GET", url)
        except HTTPError:
            time.sleep(POLL_INTERVAL)
            continue

        status = resp.get("status") if isinstance(resp, dict) else str(resp)
        if status != last_status:
            elapsed = int(time.time() - start)
            print(f"  Status: {status} ({elapsed}s elapsed)")
            last_status = status

        if status == "ready":
            time.sleep(5)
            return
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(
                f"Collection failed with status: {status}. Details: {resp}"
            )

        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Collection timed out after {POLL_TIMEOUT}s")


def download_snapshot(snapshot_id, retries=3):
    """Download snapshot results as JSON. Retries if data isn't ready yet."""
    url = f"{BASE_URL}/snapshot/{snapshot_id}?format=json"
    for attempt in range(retries):
        print(
            f"  Downloading snapshot {snapshot_id} (attempt {attempt + 1}/{retries})..."
        )
        try:
            result = api_request("GET", url)
        except Exception as e:
            print(f"  Download error: {e}")
            if attempt < retries - 1:
                time.sleep(10)
                continue
            raise

        if isinstance(result, dict) and "snapshot_id" in result:
            print(f"  Data not ready yet, retrying...")
            if attempt < retries - 1:
                time.sleep(15)
                continue
            raise RuntimeError(f"Snapshot data not available after {retries} attempts")

        if isinstance(result, list):
            return result

        print(f"  Unexpected response type: {type(result).__name__}, retrying...")
        if attempt < retries - 1:
            time.sleep(10)
            continue
        return result

    return None


def extract_emails(text):
    """Extract email addresses from text, filtering false positives."""
    if not text:
        return []
    raw = set(EMAIL_REGEX.findall(str(text)))
    filtered = []
    for email in raw:
        lower = email.lower()
        if any(pat in lower for pat in EMAIL_BLACKLIST_PATTERNS):
            continue
        filtered.append(email)
    return filtered


def extract_external_urls(text):
    """Extract external URLs from text, filtering out Twitter/media domains."""
    if not text:
        return []
    raw_urls = URL_REGEX.findall(str(text))
    external = []
    for url in raw_urls:
        url = url.rstrip(".,;:!?)>]}")
        domain = re.sub(r"^https?://", "", url).split("/")[0].split(":")[0].lower()
        if not domain:
            continue
        if any(internal in domain for internal in INTERNAL_DOMAINS):
            continue
        external.append(url)
    return list(dict.fromkeys(external))


def parse_follower_count(value):
    """Parse follower count from various formats to int.

    Handles: 1234, '1,234', '1.2K', '1.2M', '12K', etc.
    """
    if isinstance(value, (int, float)):
        return int(value)
    if not value:
        return 0
    s = str(value).strip().replace(",", "")
    if s.upper().endswith("K"):
        try:
            return int(float(s[:-1]) * 1_000)
        except ValueError:
            pass
    if s.upper().endswith("M"):
        try:
            return int(float(s[:-1]) * 1_000_000)
        except ValueError:
            pass
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return 0


def main():
    input_csv = sys.argv[1] if len(sys.argv) > 1 else None
    output_csv = sys.argv[2] if len(sys.argv) > 2 else "output_tweets.csv"

    # == Step 1: Get keywords =============================================
    if input_csv and os.path.exists(input_csv):
        print(f"[1/5] Reading keywords from {input_csv}")
        keywords = read_keywords_csv(input_csv)
    else:
        print("[1/5] Using default keywords (no CSV provided)")
        keywords = DEFAULT_KEYWORDS

    print(f"  Keywords: {keywords}")

    # == Step 2: Trigger post search ======================================
    print("\n[2/5] Triggering Bright Data Twitter/X Posts collection...")
    post_inputs = [{"keyword": kw} for kw in keywords]
    post_snapshot_id = trigger_collection(
        POSTS_DATASET_ID, post_inputs, discover_by="keyword"
    )
    print(f"  Snapshot ID: {post_snapshot_id}")

    # == Step 3: Wait + download ==========================================
    print("\n[3/5] Waiting for collection to complete (this may take 2-5 minutes)...")
    poll_until_ready(post_snapshot_id)

    print("  Downloading results...")
    tweets = download_snapshot(post_snapshot_id)
    if not tweets:
        print("  No tweets returned. Exiting.")
        return

    tweets = [t for t in tweets if isinstance(t, dict)]
    errors = [t for t in tweets if t.get("error")]
    print(
        f"  Got {len(tweets)} results ({len(tweets) - len(errors)} tweets, {len(errors)} errors)"
    )

    # == Step 4: Deduplicate by author ====================================
    print(f"\n[4/5] Deduplicating {len(tweets) - len(errors)} tweets by author...")
    authors_map = {}  # handle -> best tweet data

    for tweet in tweets:
        if tweet.get("error"):
            continue

        # Extract which keyword found this tweet
        kw = ""
        if isinstance(tweet.get("discovery_input"), dict):
            kw = tweet["discovery_input"].get("keyword", "")
        if not kw and isinstance(tweet.get("input"), dict):
            inp = tweet["input"]
            kw = inp.get("keyword", "")
            if not kw and isinstance(inp.get("discovery_input"), dict):
                kw = inp["discovery_input"].get("keyword", "")

        # Author info
        handle = (
            tweet.get("user_name", "")
            or tweet.get("screen_name", "")
            or tweet.get("author", "")
            or ""
        )
        if not handle:
            continue
        if not handle.startswith("@"):
            handle = f"@{handle}"

        display_name = (
            tweet.get("user_display_name", "")
            or tweet.get("name", "")
            or tweet.get("author_name", "")
            or ""
        )
        followers = parse_follower_count(
            tweet.get(
                "user_followers",
                tweet.get("followers_count", tweet.get("user_follower_count", 0)),
            )
        )
        bio = (
            tweet.get("user_description", "")
            or tweet.get("user_bio", "")
            or tweet.get("bio", "")
            or ""
        )
        website = (
            tweet.get("user_url", "")
            or tweet.get("user_website", "")
            or tweet.get("website", "")
            or ""
        )

        # Tweet content
        text = (
            tweet.get("text", "")
            or tweet.get("tweet_text", "")
            or tweet.get("content", "")
            or ""
        )
        tweet_url = (
            tweet.get("tweet_url", "")
            or tweet.get("url", "")
            or tweet.get("post_url", "")
            or ""
        )
        likes = parse_follower_count(
            tweet.get("like_count", tweet.get("likes", tweet.get("favorite_count", 0)))
        )
        retweets = parse_follower_count(
            tweet.get("retweet_count", tweet.get("retweets", 0))
        )

        # Calculate engagement score for dedup
        engagement = likes + retweets

        # Extract emails from bio + tweet text
        all_text = f"{bio} {text}"
        emails = extract_emails(all_text)

        # Extract external URLs from tweet text
        external_urls = extract_external_urls(text)

        # If no website from profile, use first external URL
        if not website and external_urls:
            website = external_urls[0]

        if handle not in authors_map or engagement > authors_map[handle]["engagement"]:
            authors_map[handle] = {
                "keyword": kw,
                "handle": handle,
                "display_name": display_name,
                "followers": followers,
                "bio": bio,
                "website": website,
                "emails": emails,
                "top_tweet": text,
                "tweet_url": tweet_url,
                "likes": likes,
                "retweets": retweets,
                "engagement": engagement,
                "keywords": {kw} if kw else set(),
            }
        else:
            if kw:
                authors_map[handle]["keywords"].add(kw)
            # Merge emails
            existing_emails = set(authors_map[handle]["emails"])
            for e in emails:
                if e not in existing_emails:
                    authors_map[handle]["emails"].append(e)

    print(f"  Found {len(authors_map)} unique authors")

    # Build output rows
    rows = []
    email_count = 0
    for handle, data in authors_map.items():
        email_str = "; ".join(data["emails"]) if data["emails"] else ""
        if data["emails"]:
            email_count += len(data["emails"])

        rows.append(
            {
                "keyword": "; ".join(sorted(data["keywords"])),
                "author_handle": data["handle"],
                "author_name": data["display_name"],
                "followers": data["followers"] if data["followers"] else "",
                "bio": str(data["bio"])[:300],
                "website": str(data["website"])[:200],
                "email": email_str,
                "top_tweet": str(data["top_tweet"])[:280],
                "tweet_url": data["tweet_url"],
                "likes": data["likes"] if data["likes"] else "",
                "retweets": data["retweets"] if data["retweets"] else "",
            }
        )

    print(f"  Authors with emails: {sum(1 for r in rows if r['email'])}")
    print(f"  Total emails: {email_count}")

    # == Step 5: Write output CSV =========================================
    print(f"\n[5/5] Writing output to {output_csv}...")
    fieldnames = [
        "keyword",
        "author_handle",
        "author_name",
        "followers",
        "bio",
        "website",
        "email",
        "top_tweet",
        "tweet_url",
        "likes",
        "retweets",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! {len(rows)} authors written to {output_csv}")
    print(f"  Authors with emails: {sum(1 for r in rows if r['email'])}")
    print(f"  Authors with websites: {sum(1 for r in rows if r['website'])}")
    print(f"  Total unique emails: {email_count}")


if __name__ == "__main__":
    main()
