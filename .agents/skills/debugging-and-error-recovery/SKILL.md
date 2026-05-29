______________________________________________________________________

## name: debugging-and-error-recovery description: Systematic debugging workflow for failing tests, CI breakages, and runtime errors. Use when behavior is unexpected or a check fails.

# Debugging and Error Recovery

## Overview

Use a disciplined triage loop: reproduce, localize, reduce, fix, and guard against regressions.

## When to use

- CI failures
- Test regressions
- Runtime exceptions
- Template rendering or environment issues

## Workflow

1. Reproduce the issue with the smallest reliable command.
1. Localize failure to a file, function, or boundary.
1. Reduce to the minimal failing case.
1. Implement the smallest safe fix.
1. Add or update tests to prevent recurrence.
1. Re-run relevant checks, then broader validation.

## Rules

- Do not patch blindly without reproducing.
- Prefer evidence from logs, traces, and failing assertions.
- Keep recovery changes scoped; avoid unrelated refactors.
- If root cause is uncertain, state assumptions and verify them.

## Suggested commands

- Targeted tests: `uv run --frozen pytest tests/<target> -q`
- Full tests: `uv run --frozen pytest`
- Full quality gate: `uv run --frozen poe pipeline`
