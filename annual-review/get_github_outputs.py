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
import tomllib
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


def collect_releases(g: Github, username: str, start: date, end: date,
                     extra_repos: set[str] | None = None) -> list[dict]:
    # Personal repos owned by the user
    user = g.get_user(username)
    logging.info(f"Fetching personal repos for {username}…")
    personal_repo_names = {r.full_name for r in user.get_repos()}
    logging.debug(f"Found {len(personal_repo_names)} personal repos")

    # Union with extra repos (e.g. from PR data) to cover org repos
    all_repo_names = personal_repo_names | (extra_repos or set())
    logging.info(f"Scanning {len(all_repo_names)} repos for releases by {username} in {start} – {end}")

    rows = []
    for full_name in tqdm(sorted(all_repo_names), desc="Scanning repos for releases", unit=" repos"):
        try:
            repo = g.get_repo(full_name)
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
                # Only include releases published by the user
                if not release.author or release.author.login != username:
                    continue
                rows.append({
                    "Goal": "",
                    "Type": "Release",
                    "Organization": repo.owner.login,
                    "Repository": repo.name,
                    "Number": release.tag_name,
                    "Title": release.name or release.tag_name,
                    "URL": release.html_url,
                    "Status": "released",
                    "Created": pub.isoformat(),
                    "Closed/Merged": "",
                    "Days to Close": "",
                    "Labels": "",
                    "Description": (release.body or "")[:500],
                })
        except GithubException as e:
            logging.warning(f"Could not fetch releases for {full_name}: {e}")

    logging.info(f"Collected {len(rows)} releases")
    return rows


def write_csv(rows: list[dict], path: str) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def read_repos_from_csv(path: str) -> set[str]:
    """Extract unique org/repo slugs from an existing PR CSV."""
    repos: set[str] = set()
    try:
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                org = row.get("Organization", "").strip()
                repo = row.get("Repository", "").strip()
                if org and repo:
                    repos.add(f"{org}/{repo}")
        logging.info(f"Read {len(repos)} unique repos from {path}")
    except FileNotFoundError:
        logging.warning(f"Could not read repos from {path}: file not found")
    return repos


def load_goals_config(path: str) -> tuple[dict[str, str], dict[str, str]]:
    """
    Parse a TOML goals config and return two lookup dicts:
      repo_goals: {"org/repo" -> "Goal Name"}  (specific repo rules, higher priority)
      org_goals:  {"org"      -> "Goal Name"}  (org-level fallback)
    Returns empty dicts if the file does not exist (config is optional).
    """
    repo_goals: dict[str, str] = {}
    org_goals: dict[str, str] = {}
    try:
        with open(path, "rb") as f:
            config = tomllib.load(f)
    except FileNotFoundError:
        logging.debug(f"Goals config not found at {path} — skipping")
        return repo_goals, org_goals

    for goal_name, entries in config.get("goals", {}).items():
        for entry in entries:
            if "/" in entry:
                repo_goals[entry] = goal_name
            else:
                org_goals[entry] = goal_name

    logging.info(
        f"Loaded goals config from {path}: "
        f"{len(repo_goals)} repo rules, {len(org_goals)} org rules"
    )
    return repo_goals, org_goals


def apply_goal(row: dict, repo_goals: dict[str, str], org_goals: dict[str, str]) -> dict:
    """Fill in the Goal field if blank using the goals config. Never overwrites existing values."""
    if row.get("Goal", "").strip():
        return row
    full_name = f"{row['Organization']}/{row['Repository']}"
    if full_name in repo_goals:
        row["Goal"] = repo_goals[full_name]
    elif row["Organization"] in org_goals:
        row["Goal"] = org_goals[row["Organization"]]
    return row


def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@click.command()
@click.option("--start", "start_str", default=None, metavar="YYYY-MM-DD",
              help="Start date (default: start of current review period)")
@click.option("--end", "end_str", default=None, metavar="YYYY-MM-DD",
              help="End date (default: end of current review period)")
@click.option("--username", "-u", default=None,
              help="GitHub username (overrides GITHUB_USERNAME in .env)")
@click.option("--input", "-i", "input_path", default=None, metavar="PATH",
              help="Existing CSV with manual Goal annotations; Goal values are preserved in the refreshed output")
@click.option("--output", "-o", default=None, show_default=True, metavar="PATH",
              help="Output CSV file path (default: data/github_outputs.csv; required when --input is used)")
@click.option("--releases-output", default=None, metavar="PATH",
              help="Also write releases to this separate CSV (useful for testing)")
@click.option("--releases-only", is_flag=True, default=False,
              help="Skip PR download; read repos from --output (if it exists) and write releases to --releases-output")
@click.option("--goals", "goals_path", default="goals.toml", show_default=True, metavar="PATH",
              help="TOML config mapping repos/orgs to goal names (skipped if file not found)")
@click.option("--apply-goals", is_flag=True, default=False,
              help="Apply goals config to blank Goal cells in existing --output CSV (no GitHub download)")
@click.option("--log-level", default="INFO", show_default=True,
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"], case_sensitive=False),
              help="Logging verbosity")
def main(start_str: str | None, end_str: str | None, username: str | None,
         input_path: str | None, output: str | None, releases_output: str | None,
         releases_only: bool, goals_path: str, apply_goals: bool, log_level: str) -> None:
    """Download GitHub PRs and Releases for an annual review period."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    if input_path and output is None:
        raise click.ClickException(
            "--output is required when using --input (to avoid overwriting the input file)"
        )
    if output is None:
        output = "data/github_outputs.csv"

    repo_goals, org_goals = load_goals_config(goals_path)

    if apply_goals:
        rows = read_csv(output)
        before = sum(1 for r in rows if r.get("Goal", "").strip())
        rows = [apply_goal(r, repo_goals, org_goals) for r in rows]
        after = sum(1 for r in rows if r.get("Goal", "").strip())
        write_csv(rows, output)
        logging.info(
            f"Applied goals to {output}: "
            f"{after - before} new goals set, {before} existing preserved "
            f"({len(rows) - after} still unset)"
        )
        return

    # Load manual Goal annotations from an existing CSV (if --input was given).
    # These override goals.toml results after the normal pipeline runs.
    manual_goals: dict[tuple[str, str, str, str], str] = {}
    if input_path:
        for row in read_csv(input_path):
            goal = row.get("Goal", "").strip()
            if goal:
                key = (row["Organization"], row["Repository"], row["Type"], row["Number"])
                manual_goals[key] = goal
        logging.info(f"Loaded {len(manual_goals)} manual goal annotations from {input_path}")

    default_start, default_end = default_review_period()
    start = date.fromisoformat(start_str) if start_str else default_start
    end = date.fromisoformat(end_str) if end_str else default_end
    logging.info(f"Review period: {start} to {end}")

    username = get_username(username)
    logging.info(f"GitHub username: {username}")

    token = get_github_token()
    g = Github(auth=Auth.Token(token))
    check_rate_limit(g)

    if releases_only:
        # Skip PR download; use repos from the existing output CSV
        extra_repos = read_repos_from_csv(output)
        release_rows = collect_releases(g, username, start, end, extra_repos=extra_repos)
        dest = releases_output or output
        write_csv(release_rows, dest)
        logging.info(f"Wrote {len(release_rows)} releases to {dest}")
        return

    pr_rows = collect_prs(g, username, start, end)
    check_rate_limit(g)

    # Pass PR repos so org repos (not in get_repos()) are also scanned for releases
    pr_repos = {f"{r['Organization']}/{r['Repository']}" for r in pr_rows}
    release_rows = collect_releases(g, username, start, end, extra_repos=pr_repos)

    if releases_output:
        write_csv(release_rows, releases_output)
        logging.info(f"Wrote {len(release_rows)} releases to {releases_output}")

    all_rows = sorted(pr_rows + release_rows, key=lambda r: r["Created"])
    all_rows = [apply_goal(r, repo_goals, org_goals) for r in all_rows]

    if manual_goals:
        for row in all_rows:
            key = (row["Organization"], row["Repository"], row["Type"], row["Number"])
            if key in manual_goals:
                row["Goal"] = manual_goals[key]
        logging.info(f"Applied {len(manual_goals)} manual goal annotations from {input_path}")

    write_csv(all_rows, output)

    pr_count = sum(1 for r in all_rows if r["Type"] == "PR")
    release_count = sum(1 for r in all_rows if r["Type"] == "Release")
    goal_count = sum(1 for r in all_rows if r.get("Goal", "").strip())
    unfilled = len(all_rows) - goal_count
    pct_unfilled = (unfilled / len(all_rows) * 100) if all_rows else 0
    logging.info(
        f"Wrote {len(all_rows)} rows to {output} "
        f"({pr_count} PRs, {release_count} releases, {goal_count} with goals pre-filled, "
        f"{unfilled} not yet filled ({pct_unfilled:.0f}%))"
    )
    logging.info(f"Next step: fill in any remaining Goal cells in {output}, then run generate_review.py")


if __name__ == "__main__":
    main()
