# Twitter/X Post Discovery Tool

Discover Twitter/X conversations and creators at scale. Give it keywords, get back a CSV of authors with their contact info.

**Powered by [Bright Data](https://get.brightdata.com/1tndi4600b25) Twitter/X datasets.**

## What It Does

```
Your Keywords --> Search Tweets --> Find Unique Authors --> Extract Contact Info --> CSV File
```

1. You provide search keywords (like "ai marketing tools", "saas launch", etc.)
2. The script searches Twitter/X for tweets matching those keywords
3. It deduplicates by author - keeping the highest-engagement tweet per creator
4. It extracts contact info: bio, website, email from profiles and tweet text
5. Everything gets saved to a clean CSV file with one row per author

## Example Results

Running with keywords `ai marketing tools`, `saas launch`, `indie hacker`:

| Author        | Handle      | Followers | Email                  | Website          | Keyword      |
| ------------- | ----------- | --------- | ---------------------- | ---------------- | ------------ |
| Sarah AI      | @sarahaidev | 45,200    | sarah@sarahaitools.com | sarahaitools.com | ai marketing |
| Indie Mike    | @indiemike  | 12,800    | mike@indiemike.io      | indiemike.io     | indie hacker |
| LaunchBot     | @launchbot  | 89,000    | -                      | launchbot.co     | saas launch  |
| Growth Hacker | @growthhckr | 23,400    | hello@growthhacker.dev | -                | ai marketing |
| SaaS Queen    | @saasqueen  | 156,000   | -                      | saasqueen.com    | saas launch  |

**From 3 keywords: 200 tweets found, 145 unique authors, 12 emails extracted.**

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

### Step 3: Prepare Your Keywords

Edit `keywords.csv` with any text editor (Notepad, TextEdit, etc.):

```
keyword
ai marketing tools
saas launch
indie hacker
```

## How to Run

Open your terminal/command prompt, navigate to this folder, and run:

```
python twitter_post_scraper.py keywords.csv output_tweets.csv
```

Or simply:

```
python twitter_post_scraper.py
```

This uses the built-in default keywords and saves to `output_tweets.csv`.

### What You'll See

```
[1/5] Reading keywords from keywords.csv
  Keywords: ['ai marketing tools', 'saas launch', 'indie hacker']

[2/5] Triggering Bright Data Twitter/X Posts collection...
  Triggering collection with 3 input(s)...
  Snapshot ID: sd_abc123xyz

[3/5] Waiting for collection to complete (this may take 2-5 minutes)...
  Status: running (0s elapsed)
  Status: ready (75s elapsed)
  Downloading results...
  Got 200 results (198 tweets, 2 errors)

[4/5] Deduplicating 198 tweets by author...
  Found 145 unique authors
  Authors with emails: 12
  Total emails: 12

[5/5] Writing output to output_tweets.csv...

Done! 145 authors written to output_tweets.csv
  Authors with emails: 12
  Authors with websites: 89
  Total unique emails: 12
```

## Output CSV Format

The output file has these columns (one row per unique author):

| Column          | Description                                           |
| --------------- | ----------------------------------------------------- |
| `keyword`       | Which search keyword(s) found this author             |
| `author_handle` | Twitter @handle                                       |
| `author_name`   | Display name                                          |
| `followers`     | Follower count                                        |
| `bio`           | Author bio (first 300 characters)                     |
| `website`       | Website from profile or first external link in tweets |
| `email`         | Email address(es) found in bio or tweets              |
| `top_tweet`     | Their highest-engagement tweet text (first 280 chars) |
| `tweet_url`     | Link to the tweet                                     |
| `likes`         | Like count on the top tweet                           |
| `retweets`      | Retweet count on the top tweet                        |

## How It Works

### Author Deduplication

If the same author appears in multiple tweet results, the script keeps only one row with:

- The **highest-engagement tweet** (likes + retweets)
- All **keywords** that matched their tweets (semicolon-separated)
- **Merged emails** from all their tweets and bio

### Email Extraction

The script checks two sources for each author:

1. **Bio text** - Many Twitter users include their email in their bio
2. **Tweet text** - Occasionally people share their email in tweets

False positives are filtered out (image files, noreply addresses, placeholder emails).

### Website Detection

The script looks for websites in:

1. **Profile URL** field - The website listed in their Twitter profile
2. **Tweet URLs** - External links shared in their tweets (filtering out twitter.com, t.co, etc.)

## Tips

- **Twitter bios are goldmines**: Many creators and founders list their email or website in their bio
- **Smaller accounts respond more**: Authors with 1K-50K followers have the highest reply rates for outreach
- **Niche keywords work best**: "react native developer" finds more relevant contacts than "programming"
- **Hashtag keywords work too**: Try "#buildinpublic", "#indiehackers", "#saas"
- **Check websites**: Even without an email, the website field often leads to contact pages
- **Founders are responsive**: Search for "just launched", "building", "shipped" to find active founders
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

## Troubleshooting

| Problem                               | Solution                                                               |
| ------------------------------------- | ---------------------------------------------------------------------- |
| `ERROR: Set your Bright Data API key` | You forgot to set the environment variable (see Setup Step 2)          |
| `HTTP 401`                            | Your API key is wrong or expired                                       |
| `HTTP 400`                            | Check that your Bright Data account has the Twitter/X datasets enabled |
| `Collection timed out`                | Try with fewer keywords or check your internet connection              |
| Script hangs at "Triggering..."       | The API call can take 30-60 seconds, this is normal                    |
| `0 authors found`                     | Your keywords might be too niche. Try broader terms                    |

## Cost

This uses Bright Data's **Web Scraper API** with one Twitter/X dataset:

- **Twitter/X Posts** dataset: discovers tweets by keyword and extracts author info

Pricing depends on your Bright Data plan. A typical run with 3 keywords costs roughly a few cents.

## Disclaimer

Some links in this README are affiliate links. If you sign up for Bright Data through them, you may get extra credits on your account, and I may receive a small commission. This doesn't cost you anything extra - it helps support the project.

## License

MIT
