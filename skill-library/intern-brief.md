# /intern-brief

## Purpose
Generate a task brief for an intern that's specific enough to execute without follow-up clarification, scaled to intern-level context (per the doc's section 2.4 — intern output quality is bottlenecked by context quality, not capability).

## Context
You are writing a task brief for an intern at Predixion AI. The intern has general engineering/ops capability but no deep institutional context — they need the brief to substitute for the 20 minutes of verbal context a senior person would normally give.

## Input Required
- Task description (what needs to get done)
- Relevant background (client/product context, why this task matters now, any prior related work)
- Deadline
- Who reviews/signs off on completion

## Output Format
- **Context:** 2-3 sentences — why this task exists, what it's for, who's downstream of it
- **Deliverable:** one explicit sentence stating exactly what "done" produces (a file, a working script, a sign-off, etc.) — not a vague goal
- **Acceptance criteria:** a checklist, each item independently verifiable (not "make it good," but "X works when given Y input")
- **Deadline:** explicit date, not "soon" or "this week"
- **Escalation path:** who to ping if blocked, and what counts as a blocker worth escalating vs. something to push through alone

## Constraints
- Never assume institutional knowledge the intern wouldn't have (client history, internal acronyms, prior decisions) — spell it out or link to where it's documented
- Acceptance criteria must be testable by someone other than the brief's author, not just "looks right to me"
- If the input doesn't specify a deadline or reviewer, flag that as missing rather than inventing one
