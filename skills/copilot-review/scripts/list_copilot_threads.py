#!/usr/bin/env python3
"""List unresolved GitHub Copilot review threads for a pull request.

Usage: list_copilot_threads.py OWNER REPO PR_NUMBER

Calls `gh api graphql` (so `gh` must be authenticated), pages through every review
thread on the PR, and prints one readable block per *unresolved* thread authored by
`copilot-pull-request-reviewer`. Each block carries the fields the copilot-review skill
needs to act on the thread:

  - the thread's GraphQL node id (pass to resolveReviewThread)
  - the top comment's databaseId (pass to the REST .../replies endpoint)
  - the file path and line, the isOutdated flag, and the comment url
  - the full text of every comment in the thread (Copilot's comment plus any replies)

Prints "No unresolved Copilot review threads." when there is nothing to do.
"""

import json
import subprocess
import sys

COPILOT_LOGIN = "copilot-pull-request-reviewer"

QUERY = """
query($owner:String!,$repo:String!,$pr:Int!,$cursor:String){
  repository(owner:$owner,name:$repo){
    pullRequest(number:$pr){
      reviewThreads(first:100, after:$cursor){
        pageInfo{ hasNextPage endCursor }
        nodes{
          id isResolved isOutdated path line
          comments(first:20){ nodes{ author{login} body databaseId url } }
        }
      }
    }
  }
}
"""


def fetch_threads(owner, repo, pr):
    """Yield every review-thread node on the PR, paging until GraphQL runs out."""
    cursor = None
    while True:
        args = [
            "gh", "api", "graphql",
            "-f", f"query={QUERY}",
            "-F", f"owner={owner}",
            "-F", f"repo={repo}",
            "-F", f"pr={pr}",
        ]
        if cursor:
            # Force string: GraphQL cursors are opaque and must not be coerced to a number.
            args += ["-f", f"cursor={cursor}"]
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            raise SystemExit(f"gh api graphql failed:\n{result.stderr.strip()}")
        threads = json.loads(result.stdout)["data"]["repository"]["pullRequest"]["reviewThreads"]
        yield from threads["nodes"]
        page = threads["pageInfo"]
        if not page["hasNextPage"]:
            break
        cursor = page["endCursor"]


def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: list_copilot_threads.py OWNER REPO PR_NUMBER")
    owner, repo, pr = sys.argv[1], sys.argv[2], sys.argv[3]

    found = 0
    for thread in fetch_threads(owner, repo, pr):
        comments = thread["comments"]["nodes"]
        if not comments:
            continue
        top = comments[0]
        author = (top["author"] or {}).get("login")
        if author != COPILOT_LOGIN or thread["isResolved"]:
            continue

        found += 1
        print(f"=== THREAD {thread['id']} | top_comment_db_id {top['databaseId']}")
        print(f"path: {thread['path']} line: {thread['line']} outdated: {thread['isOutdated']} url: {top['url']}")
        for comment in comments:
            print(f"--- {(comment['author'] or {}).get('login')}:")
            print(comment["body"])
        print()

    if found == 0:
        print("No unresolved Copilot review threads.")


if __name__ == "__main__":
    main()
