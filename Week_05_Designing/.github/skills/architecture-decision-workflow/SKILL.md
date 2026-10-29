---
name: architecture-decision-workflow
description: 'Propose software architectures from explicit requirements, compare alternatives, facilitate trade-off discussion, select an architecture, and create an Architecture Decision Record (ADR). Use for requirements analysis, architectural proposals, architecture comparison, ADR creation, or iterative architecture review.'
argument-hint: 'Provide the requirements source and any existing architecture notes or constraints.'
user-invocable: true
disable-model-invocation: false
---

# Architecture Decision Workflow

## Purpose

Turn explicit software requirements into a reasoned architecture decision. The workflow produces:

- a requirements-grounded summary;
- three materially different architecture proposals;
- a discussion of strengths, trade-offs, bottlenecks, and implementation pain points;
- a selected architecture with documented rationale;
- an informative ADR with comparison tables and a text-based architectural diagram;
- a concise record of discussion and revisions when the user requests continuous notes.

## Grounding rules

1. Read the supplied requirements before proposing architecture.
2. Use only facts stated in the requirements and the user's confirmed decisions.
3. Label missing information as an open decision; do not invent traffic targets, providers, technologies, capacities, timing values, or quality attributes.
4. Distinguish required behavior from implementation suggestions.
5. Preserve unresolved constraints in the ADR instead of silently choosing defaults.

## Procedure

### 1. Inspect the inputs

- Locate and read the requirements source.
- Read any existing architecture notes, prior ADRs, or decision records.
- Identify actors, capabilities, workflows, data ownership, external interactions, and explicit constraints.
- Record omissions that could materially affect the architecture.

If the user requests notes, create a separate Markdown notes file before beginning the discussion. Keep it as a structured summary rather than a verbatim transcript.

### 2. Establish the architectural problem

Summarize:

- the system purpose;
- the main user roles and required capabilities;
- synchronous user-facing workflows;
- asynchronous or slow work;
- consistency-sensitive operations;
- explicit and missing non-functional requirements.

Do not treat hypothetical concerns as requirements. Mark them as scenarios to evaluate.

### 3. Propose three alternatives

Choose three genuinely different shapes appropriate to the requirements. For each proposal document:

- structural shape and responsibility boundaries;
- request and data-flow behavior;
- strengths;
- trade-offs;
- low-level implementation hurdles;
- likely bottlenecks;
- failure and recovery concerns;
- suitability for the documented scope.

When relevant, cover monolith or modular monolith, microservices, and serverless/event-driven designs, but choose alternatives based on the actual problem rather than using a fixed list mechanically.

### 4. Discuss alternatives interactively

Present one architecture at a time and ask the user to confirm understanding or raise concerns. Explain concrete scenarios, especially:

- concurrent writes and race conditions;
- reservation or temporary-hold expiry;
- payment and external interaction failures;
- duplicate messages or retries;
- authorization and role boundaries;
- aggregation and partial failure;
- scaling pressure and bottlenecks.

When the user gives feedback, update the discussion notes and adjust the comparison. Do not convert an unresolved question into a requirement without confirmation.

### 5. Select and justify a decision

Prefer the least complex architecture that satisfies the stated requirements unless an explicit quality target justifies additional complexity. Explain:

- why the selected architecture fits;
- why each alternative was not selected initially;
- which conditions would trigger reconsideration;
- what boundaries should remain explicit for future evolution.

For consistency-sensitive operations, identify the authoritative owner and the atomicity or idempotency strategy at an architectural level without inventing technology-specific details.

### 6. Create the ADR

Use [the ADR template](./assets/adr-template.md). The ADR should include:

- title, status, date, and scope;
- context and requirements summary;
- decision;
- module or component boundaries;
- consequences, benefits, costs, and risks;
- a dedicated low-level implementation pain-points section;
- a comparison table across all evaluated architectures;
- a separate architectural trade-off matrix when useful;
- a Mermaid or equivalent text-based architecture diagram;
- alternatives considered;
- deliberately unresolved requirements and decisions;
- review or migration triggers.

For asynchronous work, make the diagram explicit. Show the main request path separately from queues, events, workers, callbacks, or background processing. Explain the notation.

### 7. Review and revise

Inspect the generated ADR for:

- unsupported assumptions;
- missing alternatives or trade-offs;
- unclear decision rationale;
- omitted concurrency, retry, or failure behavior;
- diagrams that hide asynchronous work;
- tables that repeat rather than clarify the decision;
- unresolved requirements presented as settled facts.

Apply user feedback iteratively and record each substantive revision in the discussion notes.

## Completion checklist

- [ ] Requirements and prior notes were read.
- [ ] Scope is grounded only in supplied information and confirmed decisions.
- [ ] Three distinct architectures were proposed.
- [ ] Each alternative includes benefits, trade-offs, hurdles, bottlenecks, and fit.
- [ ] The user had an opportunity to discuss each proposal.
- [ ] The selected architecture and rejection rationale are explicit.
- [ ] Concurrency and race conditions are documented where relevant.
- [ ] Retry, failure, and asynchronous flows are documented where relevant.
- [ ] The ADR contains at least one comparison table.
- [ ] The ADR contains a readable architecture diagram.
- [ ] Open decisions are clearly labeled.
- [ ] Discussion notes were updated throughout the workflow when requested.
