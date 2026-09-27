# X (Twitter) Profile Post Research

Need a consistent snapshot of posts from a specific set of X accounts? Provide profile handles or URLs and this Python script collects returned posts through Bright Data's X/Twitter Posts dataset, groups them by author, and writes a CSV with profile details, a highest-engagement returned post, basic counters, and email-like strings found in the profile bio or post text. It helps a researcher compare a hand-picked account list without copying fields one by one; it does not discover accounts or establish that anyone is a prospect.

## The useful outcome

Use it when you already know which public accounts you want to inspect, for example a manually assembled set of companies or creators in a niche. Review the CSV to identify relevant themes, public websites, and posts worth opening in context.

Illustrative input and possible output (synthetic values):

```csv
username
sample_company
sample_founder
```

The script requests posts from those profiles, then produces one row per returned author. It keeps the tweet with the largest sum of likes and reposts among the returned records and merges email matches across records. That is a sorting shortcut, not a quality score, a complete account history, or proof that the selected post performs well outside the collected sample.

## What it does and does not do

- Accepts handles, `@handles`, and X/Twitter profile URLs you provide.
- Collects posts via Bright Data's X/Twitter Posts dataset in profile-discovery mode.
- Deduplicates returned records by author; retains the highest likes-plus-reposts post from those records and merges email matches.
- Does not search for accounts by topic, verify emails, infer buying intent, measure campaign results, or send DMs/emails.
- `apps_script.gs` is an optional, separate Gmail sender. It can send real email when run; it is not invoked by this scraper.

## Start here

Requirements: Python 3.9+, internet access, and a Bright Data API token/account enabled for the X/Twitter Posts dataset. Python's standard library is sufficient. The script reads `BRIGHT_DATA_API_KEY` from the process environment; there is no `.env` auto-loader.

Linux/macOS:

```bash
export BRIGHT_DATA_API_KEY="your-key"
python3 twitter_post_scraper.py profiles.csv output_tweets.csv
```

PowerShell:

```powershell
$env:BRIGHT_DATA_API_KEY = "your-key"
python twitter_post_scraper.py profiles.csv output_tweets.csv
```

Example input:

```csv
username
sample_company
@sample_founder
https://x.com/sample_publication
```

With no input path, the script uses its built-in example profiles and writes `output_tweets.csv`. Use an existing CSV to collect your own selected accounts.

## Output

One row per author represented in the collected post results. Columns: `author_handle`, `author_name`, `followers`, `is_verified`, `bio` (up to 300 characters), `website`, `email`, `top_tweet` (up to 280 characters), `tweet_url`, `likes`, and `retweets`. The `website` may come from the profile or the first external URL detected in tweet text. Emails and links are extracted from returned text and are not independently validated.

## Cost and responsible use

This command performs a live collection request. Bright Data pricing, credits, dataset access, and result counts depend on your account and current service terms. Check [current Web Scraper pricing](https://brightdata.com/pricing/web-scraper) and account billing before running; no fixed per-run charge or output count is promised. The scraper does not log in to X. Follow platform terms, applicable privacy and marketing laws, and internal retention rules. Public profile information is not permission to contact someone.

## Optional email sending

The separate `apps_script.gs` file can send messages through Gmail from a Google Sheet. The default sheet tab is `Sheet1`, with A-F columns in this order: `profile_name`, `email`, `followers`, `subject`, `body`, `status`. Inspect the script, check each address and message, and use its test-email action before considering any send action. Its 45-second pause and next-five option are operational conveniences, not compliance or deliverability guarantees.

## Tests

The tests use Python's unittest; collection is mocked for local tests. Run:

```bash
python3 test_scraper.py TestUnit
```

The integration test is separate. Run it only when an API request and possible usage charge are intended:

```bash
python3 test_scraper.py TestE2E
```

## FAQ

**Does it find X users who need my product?** No. It only collects posts from the profiles you supply.

**Is `top_tweet` the account's best-performing post?** It is the highest likes-plus-reposts record among the posts returned for this run, not necessarily the account's all-time or complete set of posts.

**Does the script contact account owners?** No. It only writes a CSV. The optional Apps Script can send email if separately configured and explicitly run.

**Are emails verified?** No. They are pattern matches in public text fields.

**Can it run offline?** Unit tests can run locally; collecting X data requires internet and Bright Data API access.

## License

MIT
