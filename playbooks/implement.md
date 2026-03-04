# Implement GitHub Issue

## Overview
You are implementing a fix or feature for a GitHub issue on the finserv repository.
You have the original issue, triage analysis, implementation plan, and all human
feedback in your prompt context.

Your job ends after creating the PR and swapping the label. You do NOT need to
iterate on reviews or CI — Devin auto-review/auto-fix and the `pr-status.yml`
workflow handle the review lifecycle after you.

## What You Receive
- The full GitHub issue (title, body, labels, URL)
- Triage analysis (recommendation, sizing, services affected) / plan
- All human comments and feedback
- Access to the finserv-demo/finserv codebase

## Disambiguation Phase
Re-read everything. Make sure you understand the full scope before writing code.

1. Review the implementation plan carefully — it is your primary guide
2. Use the Devin MCP to fill remaining gaps:
   - `ask_question` for system-level questions
   - `read_wiki_contents` for architecture understanding
3. If critical ambiguity remains: post a comment on the issue with specific questions,
   then wait for response

### Verification
- Understanding covers the full user intent
- Not taking shortcuts or proposing oversimplified fixes
- Implementation plan reviewed thoroughly

## Implementation Phase
1. Research the codebase to validate/extend the plan:
   - Identify all affected files and modules
   - Use the LSP (goto_definition, goto_references, hover_symbol) to verify types
     and function signatures

2. Create a feature branch: `devin/issue-{number}-{brief-description}`

3. Implement the changes following the plan:
   - Write or update tests for new functionality
   - Ensure all callers/callees are properly updated

4. Run lint checks:
   - Python: `ruff check .` (from repo root)
   - Frontend: `npx eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0`
     (from `web/` directory)

5. Run tests:
   - Python: `pytest services/` (from repo root)
   - Frontend: `npx vitest run` (from `web/` directory)

6. Use `ask_smart_friend` to review your diff:
   - Include the original issue requirements and full diff
   - Ask whether you fully fulfilled the intent and followed best practices
   - Fix any issues found

7. Commit with clear messages: `Fix #{issue_number}: {brief description}`

8. Push and create a PR:
   - Title: `Fix #{issue_number}: {brief description}`
   - Body: link to issue, summary of changes, testing done
   - Include `Closes #{issue_number}` in the PR body

9. Post a comment on the issue with the PR link.

10. **CRITICAL — Label Transition (implement -> pr-in-progress):**
    Immediately after creating the PR, you MUST swap the issue label:

        `devin:implement` -> `devin:pr-in-progress`

    This is NOT optional. This is NOT a suggestion. You MUST perform this label
    swap as soon as the PR is created. Failure to do so will leave the issue
    stuck in the wrong state and break the dashboard. Do NOT skip this step.
    Do NOT use any other label. The ONLY valid transition here is:
    `devin:implement` -> `devin:pr-in-progress`.

11. **Your session is done.** After the label swap, your work is complete.
    Do NOT wait for CI. Do NOT wait for reviews. Do NOT iterate.

    What happens next (automatically, without you):
    - Devin auto-review will review the PR and post inline comments
    - Devin auto-fix will address those review comments and push fixes
    - The `pr-status.yml` workflow monitors review thread resolution and
      automatically swaps `devin:pr-in-progress` -> `devin:pr-ready` when
      all review threads are resolved
    - A human will review and merge (or request further changes)

### Verification
- All affected files and callers/callees updated
- Code follows existing patterns — reuses existing code, follows conventions
- Tests written or updated
- Lint checks pass
- `ask_smart_friend` used for self-review
- PR created with clear description linking to issue
- **Label is now `devin:pr-in-progress`** — confirm this before ending

## Escalation

If you cannot complete the implementation (stuck on a bug, ambiguous requirements,
failing tests you can't fix), swap the label to `devin:escalated`:

    `devin:implement` -> `devin:escalated`

Post a comment on the issue summarizing:
- What's failing
- What you tried
- What you think needs human attention

Do NOT leave a stuck issue in `devin:implement`. Escalate promptly so humans
can unblock it.

## Label Transition Summary

The following are the ONLY valid label transitions during implementation.
Any other transition is WRONG and will break the system:

| When                          | From                    | To                      |
|-------------------------------|-------------------------|-------------------------|
| PR created                    | `devin:implement`       | `devin:pr-in-progress`  |
| Stuck / unrecoverable         | `devin:implement`       | `devin:escalated`       |

All other label transitions (`pr-in-progress` -> `pr-ready`, `pr-ready` -> `done`,
etc.) are handled automatically by the `pr-status.yml` workflow or by humans.
You do NOT perform these transitions.

**There is NO direct path from `devin:implement` to `devin:pr-ready` or `devin:done`.**
You MUST go through `devin:pr-in-progress` first.

## Specifications
- PR must address all requirements from the issue and plan
- Code must pass lint and tests
- Do NOT merge the PR — leave for human verification
- Keep comments terse — write like a human, not an AI

## TODO List Guidance
Only create the TODO list for the current phase. Once you move to the next phase,
create a new TODO list for that phase.

## MCP Tool Reference
### Devin MCP
- `read_wiki_structure`: Parameter: `repoName`
- `read_wiki_contents`: Parameter: `repoName`
- `ask_question`: Parameters: `repoName` and `question`

IMPORTANT: Use only the Devin MCP, NOT the DeepWiki MCP.

## Forbidden Actions
- Do not merge the PR
- Do not skip the self-review phase
- Do not push directly to main
- Do not iterate on review comments or CI failures (auto-review/auto-fix handles this)
- Do not swap to `devin:pr-ready` or `devin:done` — the workflow handles these
- Do not use `devin:pr-opened` — this label no longer exists
