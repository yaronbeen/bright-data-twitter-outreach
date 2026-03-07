# Twitter/X Profile Post Scraper

Scrape tweets from Twitter/X profiles at scale. Give it a list of handles (or profile URLs), get back a CSV of authors with their contact info, top tweets, and engagement data.

**Powered by [Bright Data](https://get.brightdata.com/1tndi4600b25) Twitter/X datasets.**

## What It Does

```
Your Profiles List --> Bright Data Twitter/X API --> Scrape Tweets by Profile --> Extract Contact Info --> CSV File
```

1. You provide a list of Twitter/X handles or profile URLs
2. The script sends them to Bright Data's Twitter/X Posts dataset (discover by profile)
3. It deduplicates by author - keeping the highest-engagement tweet per creator
4. It extracts contact info: bio, website, email from profiles and tweet text
5. Everything gets saved to a clean CSV file with one row per author

## Example Results

Running with profiles `hubspot`, `garyvee`, `elaboratehack`:

| Author Handle  | Author Name     | Followers | Verified | Email             | Website           |
| -------------- | --------------- | --------- | -------- | ----------------- | ----------------- |
| @hubspot       | HubSpot         | 893,000   | yes      | -                 | hubspot.com       |
| @garyvee       | Gary Vaynerchuk | 3,200,000 | yes      | -                 | garyvee.com       |
| @elaboratehack | Yaron Been      | 5,400     | no       | yaron@example.com | elaboratehack.com |

**From 3 profiles: tweets scraped, unique authors identified, contact info extracted.**

## Requirements

- **Python 3.9 or higher** (comes pre-installed on most Macs; [download for Windows](https://www.python.org/downloads/))
- **Bright Data account** with API access ([sign up here](https://get.brightdata.com/1tndi4600b25) - you'll get extra credits when signing up through this link)
- No extra libraries needed - uses only Python built-in modules

## Setup (5 minutes)

### Step 1: Get Your Bright Data API Key

1. Log into [Bright Data](https://get.brightdata.com/1tndi4600b25)
2. Go to **Settings > Account settings**
3. Copy your **API token**

### Step 2: Set Your API Key

**On Windows** (Command Prompt):

```
set BRIGHT_DATA_API_KEY=your-api-key-here
```

**On Windows** (PowerShell):

```
$env:BRIGHT_DATA_API_KEY = "your-api-key-here"
```

**On Mac/Linux** (Terminal):

```
export BRIGHT_DATA_API_KEY=your-api-key-here
```

### Step 3: Prepare Your Profiles List

Edit `profiles.csv` with any text editor (Notepad, TextEdit, etc.):

```
username
hubspot
garyvee
elaboratehack
```

You can also use full URLs:

```
username
https://x.com/hubspot
https://twitter.com/garyvee
```

Or mix formats -- the script auto-detects:

```
username
hubspot
@garyvee
https://x.com/elaboratehack
```

## How to Run

Open your terminal/command prompt, navigate to this folder, and run:

```
python twitter_post_scraper.py profiles.csv output_tweets.csv
```

Or simply:

```
python twitter_post_scraper.py
```

This uses the built-in default profiles and saves to `output_tweets.csv`.

### What You'll See

```
[1/5] Reading profiles from profiles.csv
  Profiles to scrape: 3
    @hubspot
    @garyvee
    @elaboratehack

[2/5] Triggering Bright Data Twitter/X Posts collection...
  Triggering collection with 3 input(s)...
  Snapshot ID: sd_abc123xyz

[3/5] Waiting for collection to complete (this may take 2-5 minutes)...
  Status: running (0s elapsed)
  Status: ready (75s elapsed)
  Downloading results...
  Got 200 results (198 tweets, 2 errors)

[4/5] Extracting contact info from 198 tweets...
  Found 3 unique authors
  Authors with emails: 1
  Total emails: 1

[5/5] Writing output to output_tweets.csv...

Done! 3 authors written to output_tweets.csv
  Authors with emails: 1
  Authors with websites: 3
  Total unique emails: 1
```

## Output CSV Format

The output file has these columns (one row per unique author):

| Column          | Description                                           |
| --------------- | ----------------------------------------------------- |
| `author_handle` | Twitter @handle                                       |
| `author_name`   | Display name                                          |
| `followers`     | Follower count                                        |
| `is_verified`   | Whether the account has a verification badge          |
| `bio`           | Author bio (first 300 characters)                     |
| `website`       | Website from profile or first external link in tweets |
| `email`         | Email address(es) found in bio or tweets              |
| `top_tweet`     | Their highest-engagement tweet text (first 280 chars) |
| `tweet_url`     | Link to the tweet                                     |
| `likes`         | Like count on the top tweet                           |
| `retweets`      | Retweet count on the top tweet                        |

## How It Works

### Profile-Based Discovery

The script uses Bright Data's `discover_by=profile_url` mode to fetch tweets from specific Twitter/X profiles. For each handle in your list, it constructs a profile URL (`https://x.com/{handle}`) and sends it to the API.

This is different from keyword search -- you're targeting specific accounts rather than searching for topics.

### Author Deduplication

If the same author appears in multiple tweet results, the script keeps only one row with:

- The **highest-engagement tweet** (likes + retweets)
- **Merged emails** from all their tweets and bio

### Email Extraction

The script checks two sources for each author:

1. **Bio text** - Many Twitter users include their email in their bio
2. **Tweet text** - Occasionally people share their email in tweets

False positives are filtered out (image files, noreply addresses, placeholder emails).

### Website Detection

The script looks for websites in:

1. **Profile URL** field - The website listed in their Twitter profile
2. **Tweet URLs** - External links shared in their tweets (filtering out twitter.com, x.com, t.co, etc.)

## Tips

- **Twitter bios are goldmines**: Many creators and founders list their email or website in their bio
- **Smaller accounts respond more**: Authors with 1K-50K followers have the highest reply rates for outreach
- **Target niche creators**: Build a focused list of profiles in your industry for better results
- **Check websites**: Even without an email, the website field often leads to contact pages
- **Founders are responsive**: Target profiles of people who are actively building and shipping
- **No rate limits**: Bright Data handles all the scraping infrastructure

## Sending Emails (Google Apps Script)

The `apps_script.gs` file is a Google Apps Script that sends personalized outreach emails directly from Google Sheets.

### Setup

1. Create a Google Sheet with columns: `profile_name`, `email`, `followers`, `subject`, `body`, `status`
2. Import your scraped data into the sheet
3. Go to **Extensions > Apps Script**
4. Paste the contents of `apps_script.gs`
5. Save and refresh the sheet
6. Use the new **Outreach** menu to send emails

## Running Tests

The project includes unit tests and end-to-end tests against the live Bright Data API.

```bash
# Install pytest (if not already installed)
pip install pytest

# Run unit tests only (no API key needed, runs in <1 second)
pytest -m "not e2e" -v

# Run everything including live API tests (requires API key, ~2-3 minutes)
export BRIGHT_DATA_API_KEY=your-api-key-here
pytest -v
```

E2E tests are automatically skipped when no API key is set.

## Troubleshooting

| Problem                               | Solution                                                               |
| ------------------------------------- | ---------------------------------------------------------------------- |
| `ERROR: Set your Bright Data API key` | You forgot to set the environment variable (see Setup Step 2)          |
| `HTTP 401`                            | Your API key is wrong or expired                                       |
| `HTTP 400`                            | Check that your Bright Data account has the Twitter/X datasets enabled |
| `Collection timed out`                | Try with fewer profiles or check your internet connection              |
| Script hangs at "Triggering..."       | The API call can take 30-60 seconds, this is normal                    |
| `0 authors found`                     | The profiles might not have recent tweets, try other accounts          |

## Cost

This uses Bright Data's **Web Scraper API** with one Twitter/X dataset:

- **Twitter/X Posts** dataset: discovers tweets by profile and extracts author info

Pricing depends on your Bright Data plan. A typical run with 3 profiles costs roughly a few cents.

## Disclaimer

Some links in this README are affiliate links. If you sign up for Bright Data through them, you may get extra credits on your account, and I may receive a small commission. This doesn't cost you anything extra -- it helps support the project.

## License

MIT
