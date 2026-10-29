# EventTicket Architecture Discussion Notes

## Source reviewed

- Requirements source: `data/EventTicket.txt`
- Scope constraint: proposals are based only on the stated system description and user stories.

## Requirements summary

The system is a web application for event management, event proposals, event discovery, and online ticket distribution. Clients can visit the application, register, log in, explore events, and recover a forgotten password. Authenticated users can manage personal data, favourite categories, related email notifications, pre-sale bookings, bought tickets, online payments, and ticket codes. Managers can view their proposed events and insert new events. Administrators can add managers. Clients, users, managers, and administrators can log out.

## Initial architecture proposals

1. **Modular monolith**
   - One deployable web application with explicit modules for identity and roles, events, favourites and notifications, pre-sales, ticket purchases and payments, and administration.
   - Shared persistence and in-process module calls simplify consistency and initial delivery.

2. **Microservices**
   - Independently deployable services organized around capabilities such as identity, events, notifications, pre-sales, ticketing/payments, and administration.
   - Service boundaries and asynchronous communication can support independent scaling, but introduce distributed consistency and operational complexity.

3. **Serverless event-driven architecture**
   - HTTP/API entry points invoke functions for user actions, while durable storage and an event bus/queue connect workflows such as event publication, category notifications, pre-sale booking, payment processing, and ticket-code issuance.
   - Elastic operation and managed infrastructure are advantages, while workflow coordination, debugging, and transactional boundaries are challenges.

## Discussion record

### Proposal 1: Modular monolith

#### Shape

Use one web application and one deployable system, divided internally into modules:

- identity, registration, login, logout, roles, and password regeneration;
- event discovery and event management;
- user favourites and email notifications;
- pre-sale bookings;
- ticket purchases, online payment, and ticket codes;
- administration, including adding managers.

The modules would have explicit interfaces even though they run in the same process and can initially use a shared database.

#### Strengths

- The user stories can be implemented with straightforward request/response flows.
- Login, role checks, event ownership, booking, purchase, payment state, and ticket-code issuance can be coordinated without network calls between internal modules.
- A shared transaction boundary makes it easier to prevent inconsistent states, such as recording a ticket purchase without its corresponding ticket code.
- One deployable application is simpler to test, operate, monitor, and deploy than multiple services.
- Internal module boundaries preserve a possible future path to extraction if a capability later needs independent scaling.

#### Trade-offs and hurdles

- The application is still one deployment unit, so a change or failure in one module can affect the whole system.
- Shared persistence can create coupling: careless queries or direct table access may blur ownership between modules.
- Notification delivery should not block an event or favourite-category request; it needs a reliable background mechanism, even inside a monolith.
- Payment processing must represent intermediate and failed states explicitly. The requirements say users pay online and receive a ticket code, but they do not specify a payment provider or recovery policy, so those details remain design decisions rather than assumptions.
- Concurrency needs attention for ticket buying and pre-sale booking. The implementation must protect the relevant availability and purchase records from duplicate or conflicting operations, although the requirements do not state capacity rules.
- Role-based behavior must be enforced on the server for users, managers, and administrators, not only hidden in the interface.

#### Main bottlenecks

The shared database and the single runtime are the likely scaling bottlenecks. Email notifications and payment interactions are also operational boundaries: they can be slow or unavailable and therefore should be isolated from the user request through durable status handling and retryable background work. These are implementation concerns derived from the required notification and payment behaviors; the requirements do not prescribe a particular infrastructure.

#### Best fit

This is the lowest-complexity starting point when the goal is to deliver all stated user stories consistently while keeping the system understandable. Its main risk is allowing the internal modules to become tightly coupled, making later separation difficult.

#### Discussion point: preventing simultaneous ticket buying

The requirements do not explicitly define ticket capacity, temporary reservations, or a reservation-clock duration. If the business decision is that a ticket becomes unavailable while one user is completing payment, the monolith can implement a ticket-hold state with an expiration timestamp. A purchase attempt would atomically claim an available ticket (or availability record), set the hold expiry, and allow only the holder to complete payment. A later request would reject an active hold; an expired hold could be released by a scheduled cleanup or by checking expiry during the next booking or purchase request. Successful payment would convert the hold to a purchased state, while a failed or abandoned payment would make it available again.

The exact clock duration, whether holds apply to pre-sales, and the behavior when payment is interrupted are not specified in `EventTicket.txt`; they must be decided rather than assumed. The architectural benefit of the monolith is that the claim, expiry check, and state transition can be protected by one database transaction, reducing the race window between two buyers.

### Proposal 2: Microservices

#### Shape

Split the application into independently deployable services aligned with the stated capabilities:

- identity and access for registration, login, logout, roles, and password regeneration;
- event service for event discovery and manager event proposals;
- user-preferences and notification service for favourite categories and email notifications;
- reservation or pre-sale service;
- ticket and payment service for purchases, payment state, and ticket codes;
- administration service for adding managers.

The web client would call an API gateway or equivalent entry point. Services would communicate synchronously for queries and commands where an immediate result is needed and asynchronously for work such as sending category notifications or reacting to completed payment.

#### Strengths

- Each capability can be deployed and scaled independently.
- Failures or load in notifications need not directly take down event browsing or ticket purchase endpoints.
- Service ownership can enforce clearer boundaries than a shared module, especially around manager-owned events and user-owned purchases.
- The ticket/payment capability can be optimized separately because buying and payment have stricter consistency needs than event browsing.

#### Trade-offs and hurdles

- A user action may cross several services, so failures can occur after only part of the workflow has completed.
- Avoiding a duplicate purchase requires idempotent commands and a clear owner for ticket availability; a shared database transaction across services should not be assumed.
- A ticket hold with an expiry clock would belong to the ticket/reservation service. It would need an atomic claim there, an expiry mechanism, and a reliable hand-off to payment. Payment completion and ticket-code issuance may require a saga-like workflow rather than one transaction.
- User pages aggregate data from several services, increasing latency and creating partial-result decisions that the requirements do not specify.
- Authentication and role checks must work consistently across services; the requirements name roles but do not specify a token or session technology.
- Deployment, service discovery, logging, monitoring, retries, versioned APIs, and data ownership add substantial operational work.

#### Main bottlenecks

The central bottleneck is distributed consistency around ticket availability, holds, payment, and ticket-code issuance. A notification event can be retried safely only if consumers are idempotent. Network latency and cross-service aggregation can also affect personal pages and event workflows.

#### Best fit

This architecture is more suitable when independent scaling or independent team ownership is important enough to justify the operational cost. For the stated requirements alone, it is more complex than necessary unless growth or isolation needs are established separately.

#### Discussion point: complexity versus very high traffic

The microservices approach is indeed likely too complex as a default for the stated requirements. The requirements do not state traffic volume, so high traffic is a hypothetical stress case rather than a documented constraint.

If many clients browse the event list at once, event discovery is primarily a read concern and could be scaled separately from ticket purchase. Ticket buying is different: the ticket or reservation owner must serialize or atomically coordinate claims for the same limited availability. Adding more service instances does not remove that consistency requirement. The payment workflow also needs idempotent retries so a repeated request cannot create multiple purchases or ticket codes.

Therefore microservices may help isolate event browsing, notifications, and ticket/payment workloads under high traffic, but the ticket service remains a correctness bottleneck. A modular monolith with independently scalable deployment resources or a separately extracted reservation component may address the pressure with less complexity. The decision should be driven by an explicitly required traffic or availability target, which `EventTicket.txt` does not provide.

### Proposal 3: Serverless event-driven architecture

#### Shape

Use HTTP/API entry points and function-based handlers for the user stories, with managed persistent storage and a durable event or queue mechanism for asynchronous workflows. Functions could cover identity and roles, event operations, user preferences, pre-sales, ticket holds and purchases, payment callbacks, administration, and password regeneration.

The synchronous path would handle actions needing an immediate response, such as browsing events or requesting a ticket purchase. Events would connect longer workflows: a favourite-category change can lead to notification work; an event publication can lead to matching notifications; a successful payment can lead to ticket-code issuance; and an expired hold can trigger release processing.

#### Strengths

- Functions can scale independently for bursts without keeping a full application runtime running.
- Notification delivery and other slow work can be decoupled from the request that initiated it.
- Event-driven workflows make payment completion, ticket-code creation, and expired-hold processing explicit stages.
- Managed infrastructure can reduce the amount of server maintenance required.

#### Trade-offs and hurdles

- Function invocations and event delivery can be retried or arrive more than once, so every state transition and notification consumer needs an idempotency strategy.
- A ticket hold still needs an authoritative atomic store. The hold record must include an expiry time, and the purchase function must conditionally claim only an available or expired record.
- A timer or delayed event must release expired holds, but the system must also check expiry during a purchase attempt because delayed processing may not happen exactly at the expiry moment.
- Payment is an external or separately managed step in this design. The requirements say online payment and a ticket code are needed, but do not specify payment integration or failure behavior; those must be designed explicitly.
- Debugging a workflow across functions, queues, retries, and state changes is harder than tracing an in-process request.
- Cold starts, function-duration limits, event ordering, eventual consistency, and provider-specific behavior can complicate user-facing flows.
- Personal pages may need to aggregate records from several stores or materialized views, and the requirements do not define how partial or delayed data should be displayed.

#### Main bottlenecks

The ticket reservation store and payment state machine remain the correctness-critical bottlenecks. The event bus or queue can also become a source of delay or duplicate work, although retries and idempotent handlers can make processing reliable. Serverless elasticity does not remove the need for strict conditional writes around ticket availability.

#### Best fit

This architecture fits workloads with irregular bursts and workflows that naturally continue asynchronously, especially notifications and payment follow-up. It is less attractive if the application needs simple end-to-end debugging, predictable low latency, or strong multi-step transactional behavior without adding substantial workflow machinery.

#### Plain-language explanation and ticket-buying flow

In this proposal, there is no continuously running application server responsible for every action. Instead, a request activates a small function for one job, and the function finishes. For work that does not need to finish before the response, the function publishes an event or places a message on a queue. Another function later consumes that message.

A possible ticket flow is:

1. The client asks to buy a ticket.
2. A purchase function checks the ticket state and atomically creates a temporary hold with an expiry time. If another active hold or purchase exists, it rejects the request.
3. The client completes online payment. Payment completion is represented as a separate event or callback.
4. A payment-handling function verifies the payment result and changes the hold to purchased, using an idempotency key so a retry cannot create a second purchase.
5. A ticket-code function handles the purchase event and creates or exposes the ticket code.
6. If payment fails or the hold expires, a release function makes the ticket available again. The purchase function must also check the expiry directly because a delayed timer is not a sufficient guarantee.

The same pattern can be used for email notifications: the user action records the favourite category and emits a notification-related event; a notification function later finds matching events and sends email. This keeps email delays or retries out of the main request.

The architecture is therefore a collection of short handlers connected by stored state and messages. Its elasticity is useful for bursts, but the ticket state store remains the authority for preventing two clients from claiming the same ticket. The requirements do not prescribe a cloud provider, function runtime, queue, timer, payment provider, or hold duration; these are unresolved implementation choices.

## Closing comparison

| Architecture | Main advantage for EventTicket | Main cost or risk |
|---|---|---|
| Modular monolith | Simplest consistency and operation for the stated user stories; ticket holds and purchases can share a transaction boundary. | Shared runtime and database can become bottlenecks or create coupling. |
| Microservices | Independent scaling and isolation for identity, events, notifications, reservations, and ticket/payment capabilities. | Distributed consistency, especially for ticket holds and payment, plus substantial operational complexity. |
| Serverless event-driven | Elastic execution and natural separation of asynchronous notifications, payment follow-up, code issuance, and hold release. | Retry/idempotency requirements, workflow debugging, delayed events, and more complex state coordination. |

No traffic, availability, ticket-capacity, payment-provider, or temporary-hold duration targets are stated. Therefore, the modular monolith is the least-complex default for the documented requirements, with an explicit ticket/reservation boundary and an atomic expiring hold if that business rule is adopted. Microservices or serverless become stronger candidates only when additional operational constraints justify their complexity.

## Discussion complete

The user asked about simultaneous ticket buying and temporary holds, challenged microservices complexity under hypothetical high traffic, and requested a plain-language explanation of the serverless flow. These concerns and responses are recorded above.
