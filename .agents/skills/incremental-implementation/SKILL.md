______________________________________________________________________

## name: incremental-implementation description: Delivers changes in thin, verifiable slices. Use when a task spans multiple files or feels too large for one safe change.

# Incremental Implementation

## Overview

Build in small vertical slices: implement, test, verify, then continue. Each increment should keep the project in a working state.

## When to use

- Multi-file features
- Refactors with risk
- Any task where scope is likely to expand

## Increment cycle

1. Implement the smallest complete slice.
1. Run relevant tests and checks.
1. Verify behavior manually if needed.
1. Commit or checkpoint.
1. Move to the next slice.

## Rules

- Scope discipline: do only what the current slice requires.
- Keep each increment reversible.
- Avoid broad cleanups mixed with feature work.
- Use safe defaults and feature flags when partial work must merge.

## Verification

- `uv run --frozen pytest`
- `pre-commit run --all-files`
