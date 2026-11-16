# Working with the harness

[`00-agents-overview.md`](00-agents-overview.md) covers the mechanism: how a wave uses plan mode, hooks,
and skills together. This page covers the experience: what it's actually like to work with this harness
session to session, and what it standardizes once it's in place.

## How you work: two chats

You work in two kinds of chat. Planning stays a conversation; execution runs in the background and comes
back to you only with questions and a report.

| Chat | Started with | What happens there |
|---|---|---|
| Planning chat | Any session in a repo | Discuss, research and curate `backlog.md` in normal mode. When you are ready to lock in one change ("let's plan wave 12"), the agent enters plan mode, writes the plan and revises it on your feedback. On approval the plan is filed on the [coordination board](05-parallel-waves.md) as `ready` and the chat moves on to the next topic. "Run wave 12 interactively" keeps that wave in the same session instead: it runs in its own worktree and asks you its questions directly. |
| Coordinator chat | `cd ~/Projects && claude --name coordinator`, then `/coordinate` | The one long-lived session that starts `ready` waves as background wave runners (at most two at once), relays a blocked wave's question so you can answer without opening the code, wakes parked waves once the wave they wait for has merged, and answers "what is running" from the board. |

```mermaid
graph TD
  subgraph Human["You"]
    H1["Discuss, research, curate backlog"]
    H2["Approve the plan and its acceptance cases"]
    H3["Answer a blocked question"]
    H4["Read the report in the PR"]
  end

  subgraph Planning["Planning chat"]
    P1["Write the plan<br/>(design-conventions)"]
    P2["File the plan on the board as ready"]
  end

  subgraph Coord["Coordinator chat"]
    C1["Start a wave-runner in the background"]
    C2["Relay the question, pass the answer back"]
    C3["Wake a parked wave"]
  end

  subgraph Wave["Wave runner, own worktree"]
    W1["Specify, Implement, Documentation upkeep"]
    W2["Verification and done check"]
    W3["Integrate and report"]
  end

  H1 --> P1
  P1 -->|"plan mode"| H2
  H2 -->|"keep planning with feedback"| P1
  H2 -->|"approved"| P2
  P2 --> C1
  C1 --> W1
  W1 --> W2
  W2 --> W3
  W1 -.->|"stop condition"| C2
  C2 --> H3
  H3 --> C2
  W3 -->|"merge hold still open"| C3
  C3 --> W3
  W3 -->|"merged, report in the PR"| H4
  H4 -->|"next topic"| H1

  style P1 fill:#55aa77,stroke:#55aa77,stroke-width:2px
  style H2 fill:#5588cc,stroke:#5588cc,stroke-width:2px
  style Planning fill:none,stroke:#5588cc,stroke-width:2px
  style Coord fill:none,stroke:#9966cc,stroke-width:2px
  style Wave fill:none,stroke:#55aa77,stroke-width:2px
```

**What you review** is the plan and its acceptance cases, not the code. An acceptance case says in words
and data what must be true afterwards, so you can check it without reading a diff. After approval the
agent works without asking. A wave lands on `main` only when its done check holds, with the evidence for
each row, and the report in the pull request description tells you what was built, how each acceptance
case was checked and what to look at. Nothing runs past what was approved: a wave stops with one question
when the plan cannot be carried out as written, rather than deciding for itself.

**Blue** marks the plan-mode permission boundary, with the same meaning as in
[`00-agents-overview.md`](00-agents-overview.md): the plan and your approval of it, which can loop through
"keep planning with feedback" as often as needed. **Green** marks a skill genuinely invoked at that step.
Waves are described in [`05-parallel-waves.md`](05-parallel-waves.md).

After a wave merges, three things are normal: go back to discussing or curating the backlog, plan the next
wave, or, once several waves have landed, reach for `ruff-cleanup`. That one is scoped to a whole PR diff
rather than any single wave, to mop up whatever survived the per-edit `ruff-autofix` hook; if it makes
changes, they land as their own commit. Suggest `/clear` after a wave or when switching topic: `backlog.md`,
`docs/history/` and the code carry everything across sessions.

## Two ways a skill activates

A skill's content isn't loaded by default — it only enters context when triggered. These are two
independent entry points, not a choice the agent makes between them — they just happen to land the same
content:

```mermaid
graph TD
  E["Explicit: you type a slash command,<br/>or the agent calls Skill by name"] --> L["Skill content loads fresh"]
  I["Inferred: your message happens<br/>to match a skill's description"] --> L
  L --> W["Agent applies it this turn"]

  style E fill:#1a2a3a,stroke:#5588cc,stroke-width:2px
  style I fill:#1a2a3a,stroke:#5588cc,stroke-width:2px
  style L fill:#55aa77,stroke:#55aa77,stroke-width:2px
```

- **Explicit** — you type `/wave`, `/ruff-cleanup`, or the agent calls the Skill tool directly by name.
- **Inferred** — the agent recognizes your message matches a skill's `description` and loads it without
  being asked by name.

Neither path is "more official" than the other — both land the same content. What matters more the
longer a session runs is *re-invoking* a skill at the moment its content is actually needed, rather than
working from a memory of having read it earlier in the conversation — see `CLAUDE.md`'s "Skill freshness"
note for why.

## Keeping the harness itself current

Skills solve their freshness problem by being invoked fresh each time — the section above. `CLAUDE.md` and
`instructions.md` are different: they're baked into every session's initial context via the `@import`
chain, so there's a standing risk of a session's belief about them going stale mid-session, two ways —
ordinary context compaction can summarize them away, and editing them directly (as this session did,
repeatedly) doesn't automatically refresh what's already in context. `reinject-instructions.py` covers
both:

```mermaid
graph TD
  C["Context compaction happens"] --> R["reinject-instructions.py<br/>re-injects CLAUDE.md and instructions.md"]
  E["CLAUDE.md or instructions.md<br/>edited directly"] --> R
  R --> F["Session's understanding of the<br/>core conventions stays current"]

  style R fill:#cc8844,stroke:#cc8844,stroke-width:2px
```

Same underlying problem "Skill freshness" names for skills, solved differently here because these two
files don't have an explicit invocation mechanism to lean on — they're supposed to just always be there.

## How skills compound

Some skills stand alone; others explicitly build on one another. This is a structural view, not a
sequence — it shows what each skill *reaches for*, not when you'd run it:

```mermaid
graph TD
  wave["wave"] -.->|"Plan phase"| dc["design-conventions"]
  wave -.->|"Documentation update"| doccv["doc-conventions"]
  wave -.->|"Implement, automatic"| autofix["ruff-autofix hook"]
  wave -.->|"Implement, briefs"| impl["implementer-contract"]
  sweep["doc-sweep"] -.->|"preloads"| doccv
  cleanup["ruff-cleanup"] -.->|"cleans up what survives"| autofix
  cleanup -.->|"runs the same test command as"| wave

  style dc fill:#55aa77,stroke:#55aa77,stroke-width:2px
  style doccv fill:#55aa77,stroke:#55aa77,stroke-width:2px
  style autofix fill:#cc8844,stroke:#cc8844,stroke-width:2px
  style impl fill:#55aa77,stroke:#55aa77,stroke-width:2px
```

`wave` is the hub: it reaches into four others in the course of a single run.
`doc-sweep` piggybacks on `doc-conventions` rather than redefining documentation rules of its own.
`ruff-cleanup` has two relationships that aren't about invoking anything: it picks up *after* whatever
the `ruff-autofix` hook already fixed, and it runs the same repo test command a wave's Verification phase
does. `sdk-release` and `design-conventions` itself don't reach for anything further — they're
leaves in this graph, not hubs.

## What actually gets standardized, and how

| Concern | Standardized via | Enforcement |
|---|---|---|
| Lint/formatting fixes | `ruff-cleanup`'s `RULES.md` | Skill (judgment) + `ruff-autofix` hook (mechanical, safe fixes only) |
| Design/architecture principles | `design-conventions` | Skill (judgment), invoked fresh at Plan phase |
| Documentation conventions | `doc-conventions` | Skill, auto-loaded on every markdown edit |
| Workflow/process (waves, planning, integration) | `instructions.md` + `wave` + `coordinate` | Always-loaded prose + skills |
| What "done" means for a wave | Acceptance cases, `test-author`, the done check | Frozen tests plus a table of evidence |
| Parallel waves not colliding | Coordination board and `coordination-guard.py` | Hook blocks a push or PR completion that breaks a lock or hold |
| Dependency/changelog discipline | Hooks | Mechanical, can't be skipped by forgetting |

Each row is deliberately backed by a different kind of mechanism — see `00-agents-overview.md`'s "why
this one" table for the same reasoning applied to a single wave's phases.

## Aspirational: the same pattern for a team

Today this is one person's `~/.claude/` symlink setup — nothing here is currently shared with anyone
else. But nothing about the *pattern* is single-user-only. A team could each point their own
`~/.claude/skills` and `~/.claude/agents` at one shared repo (or each keep their own clone of it) and get
the same shared `RULES.md`, `design-conventions`, and hooks — the same lint fixes, the same architectural
principles, the same dependency discipline — without forcing everyone onto one shared `CLAUDE.md`. That
last part matters: `03-cross-repo-distribution.md`'s Gotcha 2 already keeps colleague-shared repos
independent for exactly this reason — personal working style and shared team standards are different
things, and this harness's distribution model already separates them (global skills/hooks, per-repo or
per-person conventions on top).

This is a description of what the pattern *could* support, not a claim that it's happening — see
[`03-cross-repo-distribution.md`](03-cross-repo-distribution.md) for how the current, personal-only
distribution actually works.
