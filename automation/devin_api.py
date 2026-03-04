#!/usr/bin/env python3
"""Devin API helper for GitHub Actions workflows.

Provides CLI subcommands for creating sessions, terminating sessions,
and forwarding comments to active Devin sessions.

Usage:
    python automation/devin_api.py create-session --stage triage --issue 42 --repo owner/repo --context-file ctx.json
    python automation/devin_api.py check-active-session --issue 42
    python automation/devin_api.py terminate-active --issue 42
    python automation/devin_api.py forward-comment --issue 42 --author octocat --body-file /tmp/body.txt
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add repo root to path so we can import automation.orchestrator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from automation.orchestrator.devin_client import DevinClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# Labels that qualify an issue for follow-up session resumption.
# If the issue carries any of these labels, a new session will be created
# when a comment arrives and no active session exists.
_RESUMABLE_LABELS = {"devin:triage", "devin:triaged"}


def get_devin_client() -> DevinClient:
    """Create a DevinClient from environment variables."""
    api_key = os.environ.get("DEVIN_API_KEY", "")
    org_id = os.environ.get("DEVIN_ORG_ID", "")

    if not api_key or not org_id:
        logger.error("DEVIN_API_KEY and DEVIN_ORG_ID environment variables are required.")
        sys.exit(1)

    return DevinClient(api_key=api_key, org_id=org_id)


def build_triage_prompt(issue_number: int, repo: str, context: dict) -> str:
    """Build the triage session prompt from issue context.

    Args:
        issue_number: The GitHub issue number.
        repo: Repository in owner/repo format.
        context: Issue context dict from `gh issue view --json`.

    Returns:
        Formatted prompt string for the triage session.
    """
    title = context.get("title", "")
    body = context.get("body", "") or ""
    labels = _extract_label_names(context.get("labels", []))

    comments_text = _format_comments(context.get("comments", []))

    prompt = (
        f"Triage GitHub issue #{issue_number} on {repo}.\n\n"
        f"## Issue #{issue_number}: {title}\n\n"
        f"{body}\n\n"
        f"**Labels:** {', '.join(labels) if labels else 'none'}\n"
        f"**Repository:** {repo}\n"
        f"**Issue URL:** https://github.com/{repo}/issues/{issue_number}"
    )

    if comments_text:
        prompt += f"\n\n## Existing Comments\n{comments_text}"

    return prompt


def build_implement_prompt(issue_number: int, repo: str, context: dict) -> str:
    """Build the implement session prompt from issue context.

    Args:
        issue_number: The GitHub issue number.
        repo: Repository in owner/repo format.
        context: Issue context dict from `gh issue view --json`.

    Returns:
        Formatted prompt string for the implement session.
    """
    title = context.get("title", "")
    body = context.get("body", "") or ""
    labels = _extract_label_names(context.get("labels", []))

    comments_text = _format_comments(context.get("comments", []))

    prompt = (
        f"Implement a fix for GitHub issue #{issue_number} on {repo}.\n\n"
        f"## Issue #{issue_number}: {title}\n\n"
        f"{body}\n\n"
        f"**Labels:** {', '.join(labels) if labels else 'none'}\n"
        f"**Repository:** {repo}\n"
        f"**Issue URL:** https://github.com/{repo}/issues/{issue_number}"
    )

    if comments_text:
        prompt += f"\n\n## Comments (includes triage analysis and human feedback)\n{comments_text}"

    return prompt


def _extract_label_names(labels: list) -> list[str]:
    """Extract label name strings from either dicts or strings."""
    result: list[str] = []
    for label in labels:
        if isinstance(label, dict):
            result.append(label.get("name", ""))
        else:
            result.append(str(label))
    return result


def _format_comments(comments: list) -> str:
    """Format issue comments into a readable text block."""
    parts: list[str] = []
    for comment in comments:
        author_field = comment.get("author", {})
        if isinstance(author_field, dict):
            author = author_field.get("login", "unknown")
        else:
            author = str(author_field) if author_field else "unknown"
        body = comment.get("body", "")
        parts.append(f"\n### Comment by @{author}\n{body}")
    return "\n".join(parts)


def build_followup_prompt(
    issue_number: int,
    repo: str,
    author: str,
    comment_body: str,
    issue_title: str,
    issue_body: str,
    prior_comments: str,
) -> str:
    """Build a prompt for a follow-up session on a previously triaged issue.

    This is used when a user comments on an issue whose triage session has
    already completed.  A new Devin session is started with the full issue
    context so that Devin can continue the conversation.

    Args:
        issue_number: The GitHub issue number.
        repo: Repository in owner/repo format.
        author: The GitHub username of the commenter.
        comment_body: The text of the new comment.
        issue_title: The issue title.
        issue_body: The issue body.
        prior_comments: Pre-formatted string of previous comments on the issue.

    Returns:
        Formatted prompt string for the follow-up session.
    """
    prompt = (
        f"Continue the conversation on GitHub issue #{issue_number} on {repo}.\n\n"
        f"A user has posted a follow-up comment after the initial triage was completed. "
        f"Review the issue context and prior comments (which include the triage analysis), "
        f"then respond to the new comment.\n\n"
        f"## Issue #{issue_number}: {issue_title}\n\n"
        f"{issue_body}\n\n"
        f"**Repository:** {repo}\n"
        f"**Issue URL:** https://github.com/{repo}/issues/{issue_number}"
    )

    if prior_comments:
        prompt += f"\n\n## Prior Comments (includes triage analysis)\n{prior_comments}"

    prompt += (
        f"\n\n## New Follow-up Comment from @{author}\n"
        f"{comment_body}\n\n"
        f"Please respond to @{author}'s comment on the issue."
    )

    return prompt


def _write_github_output(key: str, value: str) -> None:
    """Write a key=value pair to GITHUB_OUTPUT for use in subsequent workflow steps."""
    github_output = os.environ.get("GITHUB_OUTPUT", "")
    if github_output:
        with open(github_output, "a") as f:
            if "\n" in value:
                import uuid
                delimiter = f"ghadelimiter_{uuid.uuid4().hex}"
                f.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                f.write(f"{key}={value}\n")


async def cmd_create_session(args: argparse.Namespace) -> None:
    """Create a triage or implement Devin session for a GitHub issue."""
    client = get_devin_client()

    # Read context from file
    with open(args.context_file) as f:
        context = json.load(f)

    # Build prompt and gather config based on stage
    if args.stage == "triage":
        prompt = build_triage_prompt(args.issue, args.repo, context)
        playbook_id = os.environ.get("TRIAGE_PLAYBOOK_ID", "") or None
        acu_limit = int(os.environ.get("ACU_LIMIT_TRIAGE", "25"))
    else:
        prompt = build_implement_prompt(args.issue, args.repo, context)
        playbook_id = os.environ.get("IMPLEMENT_PLAYBOOK_ID", "") or None
        acu_limit = int(os.environ.get("ACU_LIMIT_IMPLEMENT", "50"))

    tags = [
        "backlog-auto",
        f"issue:{args.issue}",
        f"stage:{args.stage}",
        f"repo:{args.repo}",
    ]

    try:
        session = await client.create_session(
            prompt=prompt,
            playbook_id=playbook_id,
            tags=tags,
            max_acu_limit=acu_limit,
        )
    except Exception as exc:
        logger.error("Failed to create %s session for issue #%d: %s", args.stage, args.issue, exc)
        _write_github_output("session_created", "false")
        _write_github_output("session_error", str(exc))
        return

    logger.info(
        "Created %s session %s for issue #%d: %s",
        args.stage,
        session.session_id,
        args.issue,
        session.url,
    )

    # Write outputs for GitHub Actions
    _write_github_output("session_created", "true")
    _write_github_output("session_id", session.session_id)
    _write_github_output("session_url", session.url)


async def cmd_check_active_session(args: argparse.Namespace) -> None:
    """Check if there is an active Devin session for a GitHub issue.

    Writes has_active=true/false and optionally active_session_url to GITHUB_OUTPUT.
    Uses v1 server-side tag filtering to find sessions for this issue.
    """
    client = get_devin_client()
    session = await client.get_active_session_for_issue(args.issue)

    if session:
        logger.info("Active session found for issue #%d: %s (%s)", args.issue, session.session_id, session.url)
        _write_github_output("has_active", "true")
        _write_github_output("active_session_id", session.session_id)
        _write_github_output("active_session_url", session.url)
    else:
        logger.info("No active session for issue #%d", args.issue)
        _write_github_output("has_active", "false")


async def cmd_terminate_active(args: argparse.Namespace) -> None:
    """Terminate the active Devin session for a GitHub issue (if any)."""
    client = get_devin_client()
    session = await client.get_active_session_for_issue(args.issue)

    if session:
        await client.terminate_session(session.session_id)
        logger.info("Terminated session %s for issue #%d", session.session_id, args.issue)
    else:
        logger.info("No active session found for issue #%d", args.issue)


async def cmd_forward_comment(args: argparse.Namespace) -> None:
    """Forward a GitHub comment to the active Devin session for an issue.

    If no active session exists but the issue has a qualifying label
    (devin:triage or devin:triaged), a new follow-up session is created
    with full issue context so that Devin can continue the conversation.
    """
    client = get_devin_client()

    # Read body from file or argument
    if args.body_file:
        body = Path(args.body_file).read_text()
    elif args.body:
        body = args.body
    else:
        logger.error("Either --body or --body-file is required")
        sys.exit(1)

    session = await client.get_active_session_for_issue(args.issue)

    if session:
        message = f"New comment from @{args.author} on GitHub issue #{args.issue}:\n\n{body}"
        await client.send_message(session.session_id, message)
        logger.info("Forwarded comment from @%s to session %s", args.author, session.session_id)
        _write_github_output("comment_handled", "forwarded")
        return

    # No active session — check if the issue qualifies for a follow-up session.
    labels = _parse_labels(args.labels) if getattr(args, "labels", None) else set()
    repo = getattr(args, "repo", "") or ""

    if not labels & _RESUMABLE_LABELS:
        logger.info(
            "No active session for issue #%d and no qualifying labels (%s), comment not forwarded",
            args.issue,
            ", ".join(sorted(labels)) if labels else "none provided",
        )
        _write_github_output("comment_handled", "dropped")
        return

    if not repo:
        logger.error("--repo is required to create a follow-up session")
        _write_github_output("comment_handled", "dropped")
        return

    # Build context for the follow-up session.
    context_file = getattr(args, "context_file", None)
    if context_file:
        with open(context_file) as f:
            context = json.load(f)
        issue_title = context.get("title", "")
        issue_body = context.get("body", "") or ""
        # Exclude the last comment — it is the triggering comment which is
        # already included in the "New Follow-up Comment" section of the prompt.
        all_comments = context.get("comments", [])
        prior_comments = _format_comments(all_comments[:-1] if all_comments else [])
    else:
        issue_title = ""
        issue_body = ""
        prior_comments = ""

    prompt = build_followup_prompt(
        issue_number=args.issue,
        repo=repo,
        author=args.author,
        comment_body=body,
        issue_title=issue_title,
        issue_body=issue_body,
        prior_comments=prior_comments,
    )

    playbook_id = os.environ.get("TRIAGE_PLAYBOOK_ID", "") or None
    # Default must match the workflow fallback in commands.yml (currently 25).
    acu_limit = int(os.environ.get("ACU_LIMIT_TRIAGE", "25"))

    # NOTE: The production path for follow-up session creation is the inline
    # bash in .github/workflows/commands.yml (lines ~164-243).  This Python
    # implementation mirrors it for CLI/test use.  Keep both in sync.
    tags = [
        "backlog-auto",
        f"issue:{args.issue}",
        "stage:followup",
        f"repo:{repo}",
    ]

    try:
        new_session = await client.create_session(
            prompt=prompt,
            playbook_id=playbook_id,
            tags=tags,
            max_acu_limit=acu_limit,
        )
    except Exception as exc:
        logger.error(
            "Failed to create follow-up session for issue #%d: %s", args.issue, exc,
        )
        _write_github_output("comment_handled", "error")
        _write_github_output("session_error", str(exc))
        return

    logger.info(
        "Created follow-up session %s for issue #%d: %s",
        new_session.session_id,
        args.issue,
        new_session.url,
    )
    _write_github_output("comment_handled", "resumed")
    _write_github_output("session_id", new_session.session_id)
    _write_github_output("session_url", new_session.url)


def _parse_labels(labels_str: str) -> set[str]:
    """Parse a comma-separated labels string into a set."""
    if not labels_str:
        return set()
    return {label.strip() for label in labels_str.split(",") if label.strip()}


def main() -> None:
    """CLI entry point with subcommands."""
    parser = argparse.ArgumentParser(description="Devin API helper for GitHub Actions")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create-session
    create_parser = subparsers.add_parser("create-session", help="Create a Devin session")
    create_parser.add_argument("--stage", required=True, choices=["triage", "implement"])
    create_parser.add_argument("--issue", required=True, type=int)
    create_parser.add_argument("--repo", required=True)
    create_parser.add_argument("--context-file", required=True, help="Path to JSON file with issue context")

    # check-active-session
    check_parser = subparsers.add_parser("check-active-session", help="Check if an active session exists for an issue")
    check_parser.add_argument("--issue", required=True, type=int)

    # terminate-active
    terminate_parser = subparsers.add_parser("terminate-active", help="Terminate active session for an issue")
    terminate_parser.add_argument("--issue", required=True, type=int)

    # forward-comment
    forward_parser = subparsers.add_parser("forward-comment", help="Forward comment to active Devin session")
    forward_parser.add_argument("--issue", required=True, type=int)
    forward_parser.add_argument("--author", required=True)
    forward_parser.add_argument("--body", default=None, help="Comment body text")
    forward_parser.add_argument("--body-file", default=None, help="File containing comment body")
    forward_parser.add_argument(
        "--repo", default=None, help="Repository in owner/repo format",
    )
    forward_parser.add_argument(
        "--labels", default=None, help="Comma-separated issue labels",
    )
    forward_parser.add_argument(
        "--context-file", default=None, help="Path to JSON with issue context",
    )

    args = parser.parse_args()

    if args.command == "create-session":
        asyncio.run(cmd_create_session(args))
    elif args.command == "check-active-session":
        asyncio.run(cmd_check_active_session(args))
    elif args.command == "terminate-active":
        asyncio.run(cmd_terminate_active(args))
    elif args.command == "forward-comment":
        asyncio.run(cmd_forward_comment(args))


if __name__ == "__main__":
    main()
