# Agent Guide

This repository includes local agent guidance in `.agents/skills/`.

## Where agent guidance lives

- Root guide: `AGENTS.md`
- Skills directory: `.agents/skills/`
- Skill directories:
  - `.agents/skills/test-driven-development/SKILL.md`
  - `.agents/skills/incremental-implementation/SKILL.md`
  - `.agents/skills/code-review-and-quality/SKILL.md`
  - `.agents/skills/ci-cd-and-automation/SKILL.md`
  - `.agents/skills/debugging-and-error-recovery/SKILL.md`
  - `.agents/skills/learning-opportunities/SKILL.md`

## How to use these skills

- Load relevant skill(s) before making edits.
- Prefer small changes with frequent validation.
- Keep work aligned with this project's `pyproject.toml`, CI workflows, and pre-commit hooks.

## Default execution order

1. Apply `test-driven-development` when behavior changes.
1. Apply `incremental-implementation` for multi-file or higher-risk changes.
1. Apply `code-review-and-quality` as the final quality gate before completion.
1. Apply `ci-cd-and-automation` when changing checks, tasks, or pipelines.
1. Apply `debugging-and-error-recovery` when tests, CI, or runtime behavior fails unexpectedly.
1. Optionally apply `learning-opportunities` for 10-15 minute learning exercises after design-heavy work.

## Local commands

- Run tests: `uv run --frozen pytest`
- Run lint/format hooks: `pre-commit run --all-files`
- Run type checks via pre-commit hook: `pre-commit run ty --all-files`
- Run full local pipeline: `uv run --frozen poe pipeline`

## Scope expectations

- These instructions are project-local.
- If team standards evolve, update these files in-place.
