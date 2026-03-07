#!/usr/bin/env python3
"""Tests for Twitter/X Post Scraper.

Unit tests for pure functions + E2E test against live Bright Data API.

Usage:
    python3 -m pytest -m "not e2e" -v   # unit tests only
    python3 -m pytest -v                # all tests (requires API key)
"""

import csv
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import twitter_post_scraper as scraper


class TestUnit(unittest.TestCase):
    """Unit tests for pure utility functions (no API calls)."""

    # -- extract_emails --------------------------------------------------

    def test_extract_emails_basic(self):
        emails = scraper.extract_emails("contact me at hello@example.org")
        self.assertIn("hello@example.org", emails)

    def test_extract_emails_multiple(self):
        text = "reach out to a@b.com or c@d.co.uk for info"
        emails = scraper.extract_emails(text)
        self.assertGreaterEqual(len(emails), 2)

    def test_extract_emails_empty(self):
        self.assertEqual(scraper.extract_emails(""), [])
        self.assertEqual(scraper.extract_emails(None), [])

    def test_extract_emails_blacklist(self):
        text = "icon@image.png noreply@svc.com real@company.com"
        emails = scraper.extract_emails(text)
        self.assertIn("real@company.com", emails)
        self.assertNotIn("noreply@svc.com", emails)

    # -- extract_external_urls -------------------------------------------

    def test_extract_external_urls_basic(self):
        text = "Check out https://myapp.com and https://another.io"
        urls = scraper.extract_external_urls(text)
        self.assertEqual(len(urls), 2)

    def test_extract_external_urls_filters_twitter(self):
        text = "https://twitter.com/user https://t.co/abc123 https://real-site.com"
        urls = scraper.extract_external_urls(text)
        self.assertEqual(len(urls), 1)
        self.assertIn("real-site.com", urls[0])

    def test_extract_external_urls_filters_x(self):
        text = "https://x.com/user https://pic.twitter.com/abc https://mysite.com"
        urls = scraper.extract_external_urls(text)
        self.assertEqual(len(urls), 1)
        self.assertIn("mysite.com", urls[0])

    def test_extract_external_urls_empty(self):
        self.assertEqual(scraper.extract_external_urls(""), [])
        self.assertEqual(scraper.extract_external_urls(None), [])

    # -- parse_follower_count --------------------------------------------

    def test_parse_follower_count_int(self):
        self.assertEqual(scraper.parse_follower_count(1234), 1234)

    def test_parse_follower_count_k(self):
        self.assertEqual(scraper.parse_follower_count("45K"), 45000)
        self.assertEqual(scraper.parse_follower_count("1.2K"), 1200)

    def test_parse_follower_count_m(self):
        self.assertEqual(scraper.parse_follower_count("1.5M"), 1500000)

    def test_parse_follower_count_comma(self):
        self.assertEqual(scraper.parse_follower_count("1,234"), 1234)

    def test_parse_follower_count_empty(self):
        self.assertEqual(scraper.parse_follower_count(""), 0)
        self.assertEqual(scraper.parse_follower_count(None), 0)

    # -- normalize_handle ------------------------------------------------

    def test_normalize_handle_plain(self):
        self.assertEqual(scraper.normalize_handle("hubspot"), "hubspot")

    def test_normalize_handle_at_prefix(self):
        self.assertEqual(scraper.normalize_handle("@hubspot"), "hubspot")

    def test_normalize_handle_x_url(self):
        self.assertEqual(scraper.normalize_handle("https://x.com/hubspot"), "hubspot")

    def test_normalize_handle_twitter_url(self):
        self.assertEqual(
            scraper.normalize_handle("https://twitter.com/hubspot"), "hubspot"
        )

    def test_normalize_handle_trailing_slash(self):
        self.assertEqual(scraper.normalize_handle("https://x.com/hubspot/"), "hubspot")

    def test_normalize_handle_empty(self):
        self.assertEqual(scraper.normalize_handle(""), "")
        self.assertEqual(scraper.normalize_handle(None), "")

    def test_normalize_handle_whitespace(self):
        self.assertEqual(scraper.normalize_handle("  @hubspot  "), "hubspot")

    # -- read_profiles_csv -----------------------------------------------

    def test_read_profiles_csv(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            f.write("username\n")
            f.write("hubspot\n")
            f.write("@garyvee\n")
            f.write("https://x.com/nike\n")
            path = f.name
        try:
            profiles = scraper.read_profiles_csv(path)
            self.assertEqual(len(profiles), 3)
            self.assertEqual(profiles[0], "hubspot")
            self.assertEqual(profiles[1], "garyvee")
            self.assertEqual(profiles[2], "nike")
        finally:
            os.unlink(path)

    def test_read_profiles_csv_no_header(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            f.write("somehandle\n")
            path = f.name
        try:
            profiles = scraper.read_profiles_csv(path)
            self.assertEqual(len(profiles), 1)
            self.assertEqual(profiles[0], "somehandle")
        finally:
            os.unlink(path)

    def test_read_profiles_csv_skips_empty(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, newline=""
        ) as f:
            f.write("handle\n")
            f.write("hubspot\n")
            f.write("\n")
            f.write("garyvee\n")
            path = f.name
        try:
            profiles = scraper.read_profiles_csv(path)
            self.assertEqual(len(profiles), 2)
        finally:
            os.unlink(path)


class TestE2E(unittest.TestCase):
    """End-to-end test against live Bright Data API.

    Requires BRIGHT_DATA_API_KEY environment variable.
    Uses 1 profile to keep costs low.
    """

    def setUp(self):
        if not os.environ.get("BRIGHT_DATA_API_KEY"):
            self.skipTest("BRIGHT_DATA_API_KEY not set")
        self.output_csv = tempfile.mktemp(suffix=".csv")
        self.input_csv = tempfile.mktemp(suffix=".csv")
        with open(self.input_csv, "w", newline="") as f:
            f.write("username\n")
            f.write("hubspot\n")

    def tearDown(self):
        for path in (self.output_csv, self.input_csv):
            if os.path.exists(path):
                os.unlink(path)

    def test_full_pipeline(self):
        """Run the full scraper pipeline with minimal input."""
        original_argv = sys.argv
        sys.argv = ["twitter_post_scraper.py", self.input_csv, self.output_csv]
        try:
            scraper.main()
        finally:
            sys.argv = original_argv

        self.assertTrue(
            os.path.exists(self.output_csv),
            f"Output CSV was not created at {self.output_csv}",
        )

        with open(self.output_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        expected_cols = {
            "author_handle",
            "author_name",
            "followers",
            "is_verified",
            "bio",
            "website",
            "email",
            "top_tweet",
            "tweet_url",
            "likes",
            "retweets",
        }
        if rows:
            actual_cols = set(rows[0].keys())
            self.assertEqual(
                actual_cols,
                expected_cols,
                f"CSV columns mismatch.\nExpected: {expected_cols}\nGot: {actual_cols}",
            )

        self.assertGreater(
            len(rows),
            0,
            "No authors found. The API may have returned no results.",
        )

        # Verify handles start with @
        for row in rows[:5]:
            if row["author_handle"]:
                self.assertTrue(
                    row["author_handle"].startswith("@"),
                    f"Handle should start with @: {row['author_handle']}",
                )

        with_emails = sum(1 for r in rows if r["email"])
        with_websites = sum(1 for r in rows if r["website"])
        print(f"\n  E2E Result: {len(rows)} unique authors found")
        print(f"  With emails: {with_emails}")
        print(f"  With websites: {with_websites}")
        print(
            f"  Sample: {rows[0]['author_handle'] if rows else 'none'} - {rows[0]['author_name'] if rows else 'none'}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
