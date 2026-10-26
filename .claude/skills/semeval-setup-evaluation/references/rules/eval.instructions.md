---
description: Check the evaluation impact of every change to how the LLM agent behaves.
applyTo: "**"
---

# Evaluation is part of every change to how the agent behaves

A change to a prompt, a tool, the workflow, a routing rule or anything else that changes
how the agent behaves, and every fix of a bug in its behaviour, is not done until its
evaluation impact is checked, the way a change to deterministic code is not done without
its unit test. Load the `semeval-maintain` skill for it. `evaluation/coverage.md` lists
what the evaluation covers and what to update for each kind of change.

The project's `.env` holds keys. Never open, print or search it, not even for the names it
sets: `.env.example` lists the names, and a command that needs the values reads the file
itself (`uv run --env-file .env …`) and names any variable that is missing.
