______________________________________________________________________

## name: ci-cd-and-automation description: Keeps delivery workflows automated and repeatable. Use when adding checks, changing pipelines, or improving contributor onboarding.

# CI/CD and Automation

## Overview

Prefer one-command local pipelines and CI parity so contributors can validate changes quickly and consistently.

## Rules

- If a check is required in CI, provide an easy local path to run it.
- Keep commands discoverable in Poe tasks instead of ad-hoc docs only.
- Prefer stable defaults and explicit failure signals.

## Project convention

- Maintain a complete local pipeline task: `uv run --frozen poe pipeline`
- Keep focused tasks for:
  - `uv run --frozen poe test`
  - `uv run --frozen poe lint`

## Change checklist

1. Update `pyproject.toml` Poe tasks when checks change.
1. Keep GitHub Actions and local tasks aligned.
1. Verify full local pipeline before completion.

## Verification

- `uv run --frozen poe pipeline`
