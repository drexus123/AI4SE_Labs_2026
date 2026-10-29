# Architecture Decision Record: EventTicket Web Application

- **Status:** Proposed
- **Date:** 2026-10-29
- **Scope:** Initial architecture for the EventTicket web application

## Context

EventTicket is intended to provide online discovery and distribution of event
tickets. Clients can register and log in; authenticated users can manage
personal data, favourite categories, pre-sales, and bought tickets. Users can
book pre-sales, buy tickets, and pay online to obtain a ticket code. Managers
can publish events and review the events they proposed. Administrators can add
managers. Users can also regenerate a forgotten password.

The requirements identify three application roles:

- **Client:** visitor who can explore the application and register or log in.
- **User:** authenticated customer who can manage preferences, pre-sales, and
  tickets.
- **Manager:** authenticated event proposer who can insert events and view
  their own proposed events.
- **Admin:** authenticated administrator who can add managers.

The requirements do not specify traffic, availability, latency, deployment
environment, data-retention rules, payment provider, notification provider,
security standards, or operational staffing. These are open decisions and are
not treated as architecture requirements.

## Architectural Problem

The architecture must support:

1. Public event exploration.
2. Registration, login, logout, and forgotten-password recovery.
3. Authorization boundaries between users, managers, and admins.
4. Event creation by managers and event ownership queries.
5. Category preferences and email notifications about related events.
6. Pre-sale booking and ticket purchase.
7. Online payment followed by issuance of a ticket code.
8. Retrieval of a user's pre-sales and purchased tickets.

Pre-sale booking, ticket purchase, and payment are consistency-sensitive
workflows. The authoritative owner of availability, bookings, purchases, and
ticket issuance must prevent two requests from claiming the same inventory.
The exact inventory and expiration rules are not stated and remain open.

## Alternatives Considered

### Alternative A: Modular Monolith

One deployable web application contains explicit modules for identity and
roles, events, preferences and notifications, pre-sales, tickets, payments,
and administration. Modules communicate through internal interfaces and share a
transactional data store. Slow notification delivery and payment callbacks can
be handled as background work while the main request path remains synchronous.

**Request and data flow**

```text
Client
  |
  v
Web application
  +--> Identity and role module
  +--> Event module
  +--> Preference/notification module --> background notification worker
  +--> Pre-sale and ticket module --> authoritative booking/ticket data
  +--> Payment module <--> external payment service (provider unspecified)
  +--> Administration module
```

The pre-sale and ticket module is authoritative for booking, purchase, and
ticket-code issuance. Its operation must be atomic, or use an equivalent
idempotent workflow, so concurrent requests cannot create conflicting claims.
Payment callbacks must be correlated to a purchase and be safe to repeat.

**Strengths**

- Least operational complexity for the stated scope.
- Clear module boundaries without requiring distributed deployment.
- Easier consistency across bookings, purchases, and ticket records.
- Straightforward role authorization in one application boundary.

**Trade-offs**

- Modules share a deployment and may compete for the same resources.
- A failure or deployment can affect the complete application.
- Independent scaling of notifications, event browsing, and purchasing is
  limited until modules are separated.

**Implementation pain points and bottlenecks**

- Preventing overselling during concurrent booking or purchase requests.
- Defining an idempotency strategy for payment callbacks and retried requests.
- Ensuring background notification failures do not make event publication
  appear unsuccessful.
- Keeping module interfaces explicit so the codebase does not become a
  tightly coupled monolith.
- Handling temporary holds and expiry, if the business confirms that such holds
  are required.

**Failure and recovery concerns**

- A failed notification should be retried or surfaced for later processing,
  without duplicating notifications.
- A payment timeout or callback failure must leave the purchase in a
  recoverable state rather than silently issuing or losing a ticket.
- Repeated client requests must not create duplicate bookings or tickets.

**Fit**

Best fit for the currently documented scope because it preserves simple
consistency boundaries while leaving module boundaries explicit for future
extraction.

### Alternative B: Microservices

Separate deployable services own identity, events, ticketing and pre-sales,
payments, notifications, and administration. Each service owns its data and
communicates through APIs or messages.

**Strengths**

- Independent deployment and scaling of high-pressure capabilities.
- Strong ownership boundaries can support future organizational growth.
- Notification and payment integration can fail or scale independently.

**Trade-offs**

- Booking, payment, and ticket issuance become distributed workflows.
- Authentication, authorization, tracing, retries, and service discovery add
  substantial complexity.
- Cross-service queries for personal pages and event views require
  aggregation and partial-failure handling.

**Implementation pain points and bottlenecks**

- Coordinating a reservation or purchase without a distributed transaction.
- Making every command and callback idempotent across retries and duplicate
  messages.
- Reconciling payment success with ticket issuance after partial failure.
- Building reliable aggregation for a user's pre-sales and bought tickets.
- Operating multiple services when no scale or deployment requirement has been
  stated.

**Failure and recovery concerns**

- A partial service outage can produce incomplete pages or pending purchases.
- Messages may be delayed, duplicated, or delivered out of order.
- Recovery requires reconciliation processes and explicit workflow states.

**Fit**

Technically capable, but disproportionate to the currently stated scope unless
independent scaling, organizational boundaries, or availability requirements
are confirmed.

### Alternative C: Serverless and Event-Driven

User-facing capabilities are implemented as independently invoked functions or
managed endpoints. Durable data services store application state, and events
trigger notification, payment processing, and other background work.

**Strengths**

- Background work can be separated naturally from synchronous requests.
- Individual handlers can scale independently.
- Operational infrastructure for invocation and event delivery may be reduced.

**Trade-offs**

- The architecture still requires careful ownership of booking and ticket
  state.
- Eventual consistency complicates personal pages and purchase status.
- Cold starts, execution limits, provider coupling, and observability are open
  concerns.
- Distributed retries and duplicate event delivery are central design issues.

**Implementation pain points and bottlenecks**

- Enforcing atomic inventory claims across independently invoked handlers.
- Designing idempotency keys for commands, payment callbacks, and events.
- Representing pending, paid, failed, and reconciled purchase states.
- Debugging a workflow that crosses functions, queues, and external services.
- Aggregating data for user pages when updates arrive asynchronously.

**Failure and recovery concerns**

- A failed event consumer must be retried without issuing duplicate tickets.
- A payment callback may arrive more than once or after a timeout.
- Poison messages require explicit isolation and operational recovery.
- Eventual consistency can temporarily show stale booking or ticket data.

**Fit**

Suitable if the requirements later establish significant asynchronous
processing or independently variable workloads. The supplied requirements do
not establish those conditions.

## Decision

Select **Alternative A: Modular Monolith** for the initial architecture.

This is the least complex architecture that directly supports the documented
features and role boundaries. It keeps consistency-sensitive booking,
purchase, and ticket issuance under one authoritative application boundary,
while still separating responsibilities into explicit modules. It also permits
notifications and payment callbacks to be processed asynchronously without
requiring every feature to become a distributed service.

Microservices and serverless/event-driven designs are not selected initially
because their distributed coordination, retry, aggregation, and operational
costs are not justified by any confirmed quality target in the requirements.

## Component Boundaries

The initial application should preserve these logical boundaries:

| Module | Responsibility |
|---|---|
| Identity and access | Registration, login, logout, password recovery, roles, and authorization |
| Events | Public event discovery, manager event creation, and manager-owned event listing |
| User profile and preferences | Personal data and favourite categories |
| Pre-sales and ticketing | Pre-sale bookings, purchases, ticket inventory, and ticket codes |
| Payments | Payment initiation, payment result handling, and purchase correlation |
| Notifications | Category-based email notification requests and delivery status |
| Administration | Admin management of manager accounts |

The pre-sales and ticketing module owns the authoritative state for
availability, bookings, purchases, and ticket codes. Commands that change this
state must be atomic or idempotent at the architectural boundary. Payment
results must be associated with a purchase and safely repeatable.

## Consequences

### Benefits

- Lower initial deployment and operational complexity.
- Easier implementation of role-based access and shared user workflows.
- Stronger consistency for ticket-related operations.
- Explicit module boundaries provide a path toward later service extraction.

### Costs

- All modules initially share a release and runtime boundary.
- A shared data store can create contention as usage grows.
- Background processing still needs durable status, retries, and monitoring.
- The architecture does not provide independently scalable services by
  default.

### Risks and mitigations

| Risk | Mitigation |
|---|---|
| Concurrent requests oversell tickets | Keep inventory ownership in the ticketing module and make the state change atomic |
| Duplicate payment callbacks issue duplicate tickets | Correlate callbacks to a purchase and make handling idempotent |
| Notification failure blocks event publication | Separate notification work from the synchronous publication path |
| Module coupling grows over time | Enforce module interfaces and ownership of data changes |
| Requirements remain incomplete | Track the open decisions below before finalizing implementation details |

## Trade-Off Matrix

Scores are qualitative and relative to the requirements supplied; they are not
performance measurements.

| Criterion | Modular monolith | Microservices | Serverless/event-driven |
|---|---:|---:|---:|
| Initial implementation simplicity | High | Low | Medium |
| Booking consistency simplicity | High | Low | Low |
| Independent scaling | Medium | High | High |
| Operational simplicity | High | Low | Medium |
| Natural asynchronous processing | Medium | High | High |
| Fit for stated scope | High | Medium | Medium |

## Deliberately Unresolved Requirements and Decisions

The following must be confirmed before implementation is finalized:

- Whether pre-sales reserve inventory temporarily, and the expiry behavior.
- Ticket capacity and inventory rules for each event.
- Whether a purchase is finalized before or after payment confirmation.
- Payment provider, callback protocol, refund behavior, and payment failure
  handling.
- Email provider, notification timing, unsubscribe behavior, and retry policy.
- Required password recovery verification and account-security rules.
- Exact permissions for users, managers, and admins.
- Whether event editing, cancellation, refunds, and ticket cancellation are
  required.
- Data-retention, privacy, audit, and regulatory requirements.
- Availability, performance, traffic, scaling, and deployment targets.
- Required ticket-code format and whether codes must be single-use.

## Reconsideration and Migration Triggers

Reconsider the decision if confirmed requirements establish any of the
following:

- Independent scaling or deployment of a module is required.
- Availability or isolation targets require separate failure domains.
- Notification or payment processing becomes a large, independently operated
  workload.
- A team or organizational boundary requires separate service ownership.
- Measured contention in the shared runtime or data store prevents the system
  from meeting confirmed targets.

If migration is needed, extract the notification or payment boundary first
only after its interfaces, event semantics, retry policy, and ownership are
explicit. Preserve the ticketing module as the authoritative owner until
cross-service consistency and reconciliation are proven.

## Discussion and Revision Record

No user feedback or architecture preference was supplied with the
requirements. The alternatives and selection above are therefore a proposed
initial decision, not a confirmed final choice. This record should be revised
after stakeholders review the three alternatives and answer the unresolved
decisions.

