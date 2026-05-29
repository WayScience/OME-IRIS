______________________________________________________________________

## name: code-review-and-quality description: Runs a multi-axis quality review before merge. Use after implementation and before considering work complete.

# Code Review and Quality

## Overview

Every non-trivial change should be reviewed across correctness, readability, architecture, security, and performance.

## Five-axis review

1. Correctness: does behavior match requirements and edge cases?
1. Readability: is intent clear and maintainable?
1. Architecture: are boundaries and abstractions appropriate?
1. Security: are inputs validated and risky paths handled safely?
1. Performance: any obvious regressions or expensive paths?

## Rules

- Fix critical issues before completion.
- Keep feedback actionable and specific.
- Prefer smaller, reviewable changes over large diffs.
- Approve when the change clearly improves code health, even if not perfect.

## Quality gates

- Tests pass for changed behavior.
- Lint/type checks pass.
- No known high-severity defects remain.

## Suggested commands

- `uv run --frozen pytest`
- `pre-commit run --all-files`
