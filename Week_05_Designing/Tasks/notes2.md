# EventTicket Task 2 Discussion Notes

## Session scope

- Task: create and iteratively inspect an Architecture Decision Record (ADR).
- Source of architectural decisions: [notes.md](./notes.md), created during Task 1.
- Scope constraint: do not introduce requirements or implementation facts that were not established in Task 1.

## Initial review

Task 1 evaluated three architectures:

1. Modular monolith
2. Microservices
3. Serverless event-driven architecture

The selected direction is a modular monolith because it provides the simplest consistency model and operational approach for the stated user stories. Its modules are identity and roles, events, favourites and notifications, pre-sales, ticket purchases/payments/ticket codes, and administration.

## Important recorded constraints

- The requirements do not state traffic, availability, ticket-capacity, payment-provider, or temporary-hold-duration targets.
- Simultaneous ticket buying requires an authoritative ticket or availability record and an atomic claim if temporary holds are adopted.
- A possible hold has an expiry timestamp; active holds block competing purchases, successful payment changes the hold to purchased, and failed or expired holds become available again.
- The exact hold duration, whether holds apply to pre-sales, and interrupted-payment behavior remain decisions for a later requirements discussion.
- Email notification and payment work should not unnecessarily block the main request; reliable background handling was discussed without selecting a particular technology.

## ADR drafting record

- Initial ADR includes standard sections: status, context, decision, consequences, alternatives, constraints, and follow-up decisions.
- Added an architecture comparison table to make the trade-offs inspectable.
- Added a Mermaid component/data-flow diagram for the selected modular monolith.
- Revised the Mermaid diagram to show a background work queue, email worker, payment-confirmation worker, and ticket-code worker. Dashed arrows distinguish asynchronous work from the main request and state path.
- Added a separate architectural trade-off matrix covering simplicity versus scaling, transaction consistency versus service isolation, synchronous versus background work, temporary reservation safety, and future extraction.
- Added a low-level implementation pain-points table covering concurrent holds, expiry races, duplicate payment confirmations, code-issuance retries, failed payments, and notification failures.
- Inspection found and corrected two draft issues: the comparison table was initially omitted from the ADR, and the context incorrectly called the four listed roles “three role levels.”
- The ADR deliberately avoids naming a cloud provider, payment provider, programming language, database product, queue product, or numeric hold duration.

## Review status

The ADR was revised in response to feedback. The current version explicitly visualizes asynchronous background work, documents low-level concurrency and retry pain points, and contains both an architecture comparison table and a separate architectural trade-off matrix.
