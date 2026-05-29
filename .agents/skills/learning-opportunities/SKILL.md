______________________________________________________________________

## name: learning-opportunities description: Facilitates deliberate skill development during AI-assisted coding. Offers interactive learning exercises after architectural work (new files, schema changes, refactors). Use when completing features, making design decisions, or when user asks to understand code better. argument-hint: "[orient]" license: CC-BY-4.0 source: "Adapted from DrCatHicks/learning-opportunities" source_url: "https://github.com/DrCatHicks/learning-opportunities/tree/main/learning-opportunities"

# Learning Opportunities

> Invocation argument: `$ARGUMENTS`

## Purpose

The user wants to build genuine expertise while using AI coding tools, not just ship code. These exercises help break the AI productivity trap where high velocity output and high fluency can lead to missing opportunities for active learning.

## When to offer exercises

Offer an optional 10-15 minute exercise after:

- Creating new files or modules
- Database schema changes
- Architectural decisions or refactors
- Implementing unfamiliar patterns
- Any work where the user asked "why" questions during development

Always ask before starting: "Would you like to do a quick learning exercise on [topic]? About 10-15 minutes."

## When not to offer

- User declined an exercise offer this session
- User has already completed 2 exercises this session

Keep offers brief and non-repetitive.

## Core principle: Pause for input

End your message immediately after the question. Do not generate any further content after the pause point.

After the pause point, do not generate:

- Suggested or example responses
- Hints disguised as encouragement
- Multiple questions in sequence
- Any teaching content

Allowed after the question:

- Content-free reassurance: "(Take your best guess—wrong predictions are useful data.)"
- Escape hatch: "(Or we can skip this one.)"

Pause pattern:

1. Pose a specific question or task.
1. Wait for the user's response.
1. Provide feedback connected to actual behavior.
1. If prediction was wrong, clearly identify what was incorrect and explore the gap.
1. Do not attribute insights the user did not express.

## Exercise types

### Prediction -> Observation -> Reflection

1. Pause with a concrete prediction question.
1. Wait.
1. Walk through actual behavior.
1. Pause for reflection on surprise and match.

### Generation -> Comparison

1. Ask user to sketch approach before showing implementation.
1. Wait.
1. Show actual implementation.
1. Compare and discuss rationale.

### Trace the path

1. Use concrete values.
1. Pause at each decision point.
1. Wait before revealing each step.
1. Continue through full path.

### Debug this

1. Present plausible bug or edge case.
1. Pause: what breaks and why.
1. Wait.
1. Pause: how to fix.
1. Discuss approach.

### Teach it back

1. Ask user to explain a component as if onboarding a new developer.
1. Wait.
1. Provide targeted feedback.

### Retrieval check-in

At start of returning sessions:

1. Ask what they remember about a prior component/scenario.
1. Wait.
1. Fill gaps or confirm.

## Facilitation guidelines

- Ask if they want to engage before starting.
- Honor response time and silence.
- Adjust difficulty dynamically.
- Keep exercises effortful but not frustrating.
- Keep exercises to 10-15 minutes unless user wants deeper work.
- Be direct about errors and non-judgmental in explanation.

## Hands-on exploration defaults

- Prefer directing users to files over pasting large code snippets.
- Use completion-style prompts and fading scaffolding.
- If struggling, increase scaffolding specificity rather than hinting answers.

## Orientation mode (`orient`)

If invoked with `orient`, run a guided repo orientation exercise instead of the default offer flow.

Look for `resources/orientation.md` in this order:

1. `.agents/skills/learning-opportunities/resources/orientation.md`
1. `~/.agents/skills/learning-opportunities/resources/orientation.md`
1. `.codex/skills/learning-opportunities/resources/orientation.md`
1. `~/.codex/skills/learning-opportunities/resources/orientation.md`
1. `.claude/skills/learning-opportunities/resources/orientation.md`
1. `~/.claude/skills/learning-opportunities/resources/orientation.md`

If no orientation file is found, stop and ask the user to generate one first.
