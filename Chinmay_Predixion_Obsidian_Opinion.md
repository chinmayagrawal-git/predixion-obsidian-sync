# Opinion: Local-First vs. Alternative Memory/Orchestration Stacks

## Context

The brief solves a specific problem: Vaibhav's context is fragmented across
tools, and every interaction starts from a mental reconstruction instead of
a stored state (section 1.1). Obsidian is one way to solve that — not the
only way. Two other approaches solve a version of the same problem:

- **xysq.ai** — cloud memory infrastructure that continuously captures
  context from Gmail, Slack, Notion, Drive, and Calendar, then synthesizes
  across all of them into a memory layer agents can query.
- **A "Hermes" AI-employee setup** — a personal automation stack where an
  AI agent acts as a semi-autonomous employee, with smaller "child agents"
  feeding it external signal (job changes, funding news, event listings),
  and the parent agent writing synthesized output (lead scores, follow-up
  flags) back into tools like HubSpot, Gmail, Notion, and Slack.

Both are real systems solving the same fragmentation problem, architected
differently. Both also conflict with the brief's local-only constraint
(sections 1.3, 9.1).

## Takeaways

1. **Don't adopt Hermes wholesale, and don't use xysq either.** xysq is
   cloud-native by design — not fixable without rebuilding it as something
   else. Hermes is fixable (local model, verified one-directional data
   flow), but once fixed it converges to the same architecture Obsidian
   already specifies. The one genuinely useful piece — child agents pulling
   in external signal — isn't tied to Hermes at all. It's a platform-agnostic
   pattern; the only real ask is looping that signal into the existing
   Obsidian vault, the same one-directional ingestion the sync scripts
   already do.
2. **Markdown-file orchestration is right today, wrong once this scales
   past one founder.** Frontmatter fields already act as a key-value store
   — fine for "show me dormant clients," forever. It breaks on relationship
   queries — "which BD person touched both this prospect and that client" —
   which need semantic similarity (vector store) and entity relationships
   (graph store), neither of which Dataview does. Mem0 is a concrete
   reference for what that next step looks like.

## xysq.ai: not fixable

The cloud dependency isn't an implementation detail on top of the product —
it is the product. There's no version of "make xysq local" that doesn't
mean rebuilding it as something else. Ruled out for this use case.

## Hermes: fixable, but converges to the same architecture

Hermes depends on cloud infrastructure at three points: the model, the
integration layer (HubSpot, Notion, Slack), and synthesized output (lead
scores, dormancy flags) written back into those tools.

The model is the easy fix — open-weight models with real tool-calling (Qwen
2.5 Coder 32B, Kimi K2.6) run locally via Ollama or llama.cpp with credible
accuracy as of 2026.

The write-back dependency is the real constraint, and the model swap alone
doesn't fix it. A local model can still sit behind code that calls a
third-party API to push a lead score — nothing about local inference
prevents that. Fixing it means actively designing and verifying a
one-directional data flow, the same rule Obsidian's design already follows
(section 3.2) — not something that falls out automatically.

Fixed correctly, the result isn't "a local Hermes." It's architecturally
the same shape as the Obsidian vault system already specified.

## The real value-add: the child-agent pattern, not Hermes itself

Child agents that feed external enrichment signal — decision-maker changes,
funding news, event listings — have no equivalent in the current Obsidian
design. The pattern is structurally identical to the existing sync scripts:
one-directional, read-only ingestion into a vault file. It doesn't need
Hermes as a platform — these could run standalone, on any stack, since the
signal source is public, not a private client record.

This maps onto the brief's hunting-vs-farming split (Vault 1 = clients,
Vault 2 = active BD pipeline). The natural extension is a **Vault 3**:
pre-prospect signal radar for accounts not yet in conversation, illustratively
triggered by a decision-maker role change, a funding round, or a relevant
event speaker slot — not a finalized spec, just the shape of the idea.
Concrete signal types need real input from whoever owns BD strategy.

## Scaling past markdown orchestration

Frontmatter-as-key-value-store scales indefinitely for exact-match filters.
It can't answer multi-hop relationship questions across entities — that
needs a different layer.

**Mem0** is the concrete reference for what that layer looks like: a
memory system combining vector storage (semantic, free-form facts), graph
storage (structured entity relationships — "Person Y manages Client X,
who's also connected to Prospect Z," the exact query Dataview can't do),
and key-value storage (exact-match flags and configs). It tracks memory
hierarchically across user, session, and agent levels, and already
integrates with the major agent runtimes (Anthropic, OpenAI, Google).

Not a near-term swap, and not an either/or with Obsidian — the vault stays
the human-readable source of truth; a Mem0-style layer would sit underneath
it once the organization has enough people and entities that "open the
right file" stops being fast enough.

---

Sources: [Mem0 — What Is AI Agent Memory](https://mem0.ai/blog/what-is-ai-agent-memory), [State of AI Agent Memory 2026](https://mem0.ai/blog/state-of-ai-agent-memory-2026)
