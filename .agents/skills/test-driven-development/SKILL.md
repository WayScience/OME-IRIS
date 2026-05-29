______________________________________________________________________

## name: test-driven-development description: Drives development with tests first. Use when implementing logic, fixing bugs, or changing behavior that must be proven.

# Test-Driven Development

## Overview

Write a failing test before writing code that makes it pass. For bug fixes, reproduce the bug with a test first. Tests are proof.

## When to use

- Implementing new behavior
- Fixing bugs (prove-it pattern)
- Refactoring behavior with regression risk

## Red-Green-Refactor

1. Define expected behavior first.
1. Write a failing test (RED).
1. Implement the smallest change to pass (GREEN).
1. Clean up without changing behavior (REFACTOR).
1. Re-run tests after each meaningful change.

## Prove-it pattern for bugs

1. Reproduce the bug with a test.
1. Confirm the test fails.
1. Implement the fix.
1. Confirm the test passes.
1. Run broader tests to check for regressions.

## Rules

- Prefer state/output assertions over implementation-detail assertions.
- Keep tests descriptive and behavior-focused.
- Avoid skipping tests to make the suite pass.
- Do not run the same command repeatedly without code changes in between.

## Suggested commands

- Targeted: `uv run --frozen pytest tests/test_main.py -q`
- Full: `uv run --frozen pytest`
