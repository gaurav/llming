#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "PyGithub>=2.0",
#     "python-dotenv",
#     "click",
#     "tqdm",
# ]
# ///
"""
Download GitHub PRs (authored or assigned) and Releases during an annual review period.
Writes a CSV with a blank Goal column for manual annotation before running generate_review.py.
"""

import csv
import logging
import os
import subprocess
import sys
import time
from datetime import date, datetime, timezone

import click
from dotenv import load_dotenv
from github import Auth, Github, GithubException
from tqdm import tqdm

FIELDNAMES = [
    "Goal", "Type", "Organization", "Repository", "Number",
    "Title", "URL", "Status", "Created", "Closed/Merged",
    "Days to Close", "Labels", "Description",
]

SEARCH_RESULT_WARNING_THRESHOLD = 900


def default_review_period() -> tuple[date, date]:
    today = date.today()
    if today.month < 4:
        start = date(today.year - 1, 4, 1)
        end = date(today.year, 3, 31)
    else:
        start = date(today.year, 4, 1)
        end = date(today.year + 1, 3, 31)
    return start, end


def get_github_token() -> str:
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=5
        )
        token = result.stdout.strip()
        if token:
            logging.debug("Using token from `gh auth token`")
            return token
    except FileNotFoundError:
        logging.debug("`gh` CLI not found")
    except subprocess.TimeoutExpired:
        logging.debug("`gh auth token` timed out")

    load_dotenv()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        logging.debug("Using GITHUB_TOKEN from environment / .env")
        return token

    raise click.ClickException(
        "No GitHub token found. Run `gh auth login` or set GITHUB_TOKEN in .env"
    )


def get_username(cli_value: str | None) -> str:
    if cli_value:
        return cli_value
    load_dotenv()
    username = os.getenv("GITHUB_USERNAME", "").strip()
    if username:
        return username
    raise click.ClickException(
        "GitHub username required. Use --username / -u or set GITHUB_USERNAME in .env"
    )


def check_rate_limit(g: Github) -> None:
    rl = g.get_rate_limit()
    core = rl.resources.core
    logging.info(
        f"GitHub API rate limit: {core.remaining}/{core.limit} remaining, "
        f"resets at {core.reset.strftime('%H:%M:%S UTC')}"
    )
    if core.remaining < 50:
        wait = (core.reset.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).total_seconds() + 5
        logging.warning(f"Rate limit nearly exhausted. Sleeping {wait:.0f}s until reset.")
        time.sleep(max(wait, 0))


def format_date(dt: datetime | None) -> str:
    if dt is None:
        return ""
    return dt.date().isoformat()


def collect_prs(g: Github, username: str, start: date, end: date) -> list[dict]:
    date_filter = f"created:{start.isoformat()}..{end.isoformat()}"
    queries = [
        f"is:pr author:{username} {date_filter}",
        f"is:pr assignee:{username} {date_filter}",
    ]

    seen: dict[tuple, dict] = {}
    for query in queries:
        logging.info(f"Searching: {query}")
        try:
            results = g.search_issues(query)
            issues = list(tqdm(results, desc=f"Fetching ({query[:40]}…)", unit=" PRs"))
        except GithubException as e:
            logging.error(f"Search failed: {e}")
            continue

        for issue in tqdm(issues, desc="Fetching PR details", unit=" PRs"):
            repo = issue.repository
            org = repo.owner.login
            key = (org, repo.name, issue.number)
            if key in seen:
                continue
            try:
                pr = issue.as_pull_request()
            except GithubException as e:
                logging.warning(f"Could not fetch PR details for {repo.full_name}#{issue.number}: {e}")
                continue

            if pr.merged:
                status = "merged"
                closed_dt = pr.merged_at
            elif pr.state == "open":
                status = "open"
                closed_dt = None
            else:
                status = "closed"
                closed_dt = pr.closed_at

            days_to_close = ""
            if closed_dt:
                days_to_close = str((closed_dt.date() - pr.created_at.date()).days)

            seen[key] = {
                "Goal": "",
                "Type": "PR",
                "Organization": org,
                "Repository": repo.name,
                "Number": str(issue.number),
                "Title": pr.title,
                "URL": pr.html_url,
                "Status": status,
                "Created": format_date(pr.created_at),
                "Closed/Merged": format_date(closed_dt),
                "Days to Close": days_to_close,
                "Labels": ",".join(l.name for l in pr.labels),
                "Description": (pr.body or "")[:500],
            }

    rows = list(seen.values())
    if len(rows) > SEARCH_RESULT_WARNING_THRESHOLD:
        logging.warning(
            f"Found {len(rows)} PRs — near GitHub's 1000-result search limit. "
            "Results may be incomplete. Consider narrowing the date range with --start/--end."
        )
    logging.info(f"Collected {len(rows)} unique PRs")
    return rows


def collect_releases(g: Github, username: str, start: date, end: date) -> list[dict]:
    user = g.get_user(username)
    logging.info(f"Fetching repos for {username}…")
    repos = list(user.get_repos())
    logging.info(f"Scanning {len(repos)} repos for releases in {start} – {end}")

    rows = []
    for repo in tqdm(repos, desc="Scanning repos", unit=" repos"):
        try:
            for release in repo.get_releases():
                if release.draft:
                    continue
                if release.published_at is None:
                    continue
                pub = release.published_at.date()
                if pub < start:
                    break  # releases are newest-first; nothing older will match
                if pub > end:
                    continue
                rows.append({
                    "Goal": "",
                    "Type": "Release",
                    "Organization": repo.owner.login,
                    "Repository": repo.name,
                    "Number": release.tag_name,
                    "Title": release.title or release.tag_name,
                    "URL": release.html_url,
                    "Status": "released",
                    "Created": pub.isoformat(),
                    "Closed/Merged": "",
                    "Days to Close": "",
                    "Labels": "",
                    "Description": (release.body or "")[:500],
                })
        except GithubException as e:
            logging.warning(f"Could not fetch releases for {repo.full_name}: {e}")

    logging.info(f"Collected {len(rows)} releases")
    return rows


@click.command()
@click.option("--start", "start_str", default=None, metavar="YYYY-MM-DD",
              help="Start date (default: start of current review period)")
@click.option("--end", "end_str", default=None, metavar="YYYY-MM-DD",
              help="End date (default: end of current review period)")
@click.option("--username", "-u", default=None,
              help="GitHub username (overrides GITHUB_USERNAME in .env)")
@click.option("--output", "-o", default="data/github_outputs.csv", show_default=True,
              help="Output CSV file path")
@click.option("--log-level", default="INFO", show_default=True,
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
              help="Logging verbosity")
def main(start_str: str | None, end_str: str | None, username: str | None,
         output: str, log_level: str) -> None:
    """Download GitHub PRs and Releases for an annual review period."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    default_start, default_end = default_review_period()
    start = date.fromisoformat(start_str) if start_str else default_start
    end = date.fromisoformat(end_str) if end_str else default_end
    logging.info(f"Review period: {start} to {end}")

    username = get_username(username)
    logging.info(f"GitHub username: {username}")

    token = get_github_token()
    g = Github(auth=Auth.Token(token))
    check_rate_limit(g)

    pr_rows = collect_prs(g, username, start, end)
    check_rate_limit(g)
    release_rows = collect_releases(g, username, start, end)

    all_rows = sorted(pr_rows + release_rows, key=lambda r: r["Created"])

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_rows)

    pr_count = sum(1 for r in all_rows if r["Type"] == "PR")
    release_count = sum(1 for r in all_rows if r["Type"] == "Release")
    logging.info(
        f"Wrote {len(all_rows)} rows to {output} "
        f"({pr_count} PRs, {release_count} releases)"
    )
    logging.info(f"Next step: fill in the Goal column in {output}, then run generate_review.py")


if __name__ == "__main__":
    main()
