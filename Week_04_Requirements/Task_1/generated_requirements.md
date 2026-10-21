# Refined Software Requirements

## Priority scale

- **Must:** necessary for the basic operation of the system.
- **Should:** important, but the basic system can run without it.
- **Could:** simplifies work or makes use more comfortable, convenient, or efficient.
- **Won't:** not needed for this product or release; retained for traceability.

## Requirements

### REQ-001-F54861: Accessibility and Standards Compliance

**Priority:** Must

Ensure reporting UI and generated HTML outputs meet recognized accessibility standards (for example applicable Section 508/WCAG guidelines) so staff with disabilities can use reporting features. The product must follow standards-based HTML output and provide accessible navigation and forms in the report designer and queue views. Accessibility conformance must be validated during acceptance testing and documented.

**Derived from:** `early_draft_srs_galecia.txt`, `evergreen_reference_2009.txt`, `meeting_minutes/meeting_2009-03-15_minutes.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

### REQ-002-862B80: Background Processing and Queue Isolation

**Priority:** Must

Long-running reports and bulk operations must run in background worker processes or an isolated reporting queue so that OPAC responsiveness and core circulation transactions are not degraded by reporting activity. The system must provide resource controls and priorities for reporting jobs and an administrative view to manage queue health. Default system configuration should protect interactive services from being impacted by scheduled or large ad-hoc reports.

**Derived from:** `early_draft_srs_galecia.txt`, `evergreen_reference_2009.txt`, `interview_sysadmin_2009-05-10.txt`, `meeting_minutes/meeting_2009-07-20_minutes.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

### REQ-003-73D5C2: Canned Reports Library

**Priority:** Should

Provide a library of predefined (canned) reports covering essential operational and governance metrics that staff can run with minimal parameters (for example: date ranges, branch). Canned reports should be discoverable in the reporting UI, parameterizable, and exportable in common formats to support routine operational needs and to reduce ad-hoc query load. The library must be extensible so administrators can add or retire canned reports over time.

**Derived from:** `early_draft_srs_galecia.txt`, `survey_results_2009.txt`

### REQ-004-A36B6F: Deletion Tracking (Audit Logging)

**Priority:** Could

Maintain an audit trail for deletions of items, patrons, and other records that records record type, timestamp, acting user, user's location, and brief reason. Logging of denied deletion attempts is useful for diagnostics but depends on authorization-layer enforcement and may be implemented as a supplemental convenience feature if logging of denial reasons is not available at enforcement points. The audit trail must be queryable and exportable for routine audits and troubleshooting.

**Derived from:** `conversations/conv_pines022_deletions.eml`, `early_draft_srs_galecia.txt`

### REQ-005-A9A29A: Financial Reporting Requirements

**Priority:** Should

Provide financial reporting capabilities that include patron account balances, fines accrued, payments made, and an auditable trail of payments and adjustments. Financial reports must support exportable ledgers with timestamps and conform to common accounting/export formats to support state or external audits. Access to financial data must be role-restricted and auditable.

**Derived from:** `early_draft_srs_galecia.txt`, `email_financial_reports.eml`

### REQ-006-3967B7: In-Transit Items Report

**Priority:** Must

Generate a report listing items that have been in transit longer than a configurable threshold, consolidating transit-to and transit-from data into a single view. The report must be available at branch and system levels and include transit start date, expected arrival, and responsible branch so staff can detect and resolve items lost or stalled in transit. The threshold must be configurable by administrators and included as part of the report metadata.

**Derived from:** `conversations/conv_pines019_020_missing_intransit.eml`, `early_draft_srs_galecia.txt`

### REQ-007-750F35: Inactive Patrons Report

**Priority:** Should

Provide a configurable report of patrons with no circulation or electronic activity within a configurable interval, with options to run at system, home library, and county levels. The report must include mailing addresses and highlight patrons with outstanding fines for targeted outreach and account resolution. The definition of 'electronic activity' must be configurable and documented (examples: OPAC login, digital checkouts, holds placed, renewals).

**Derived from:** `conversations/conv_pines024_inactive_patrons.eml`, `early_draft_srs_galecia.txt`, `interview_sysadmin_2009-05-10.txt`

### REQ-008-27F97D: Item Record Purging Utility

**Priority:** Should

Provide tools and reports to identify item records eligible for purging based on configurable criteria (for example: status='missing' for N months, marked for discard), and to perform safe batch status changes or purge workflows with an approval step. The utility must include safeguards such as preview lists, an approval/confirmation workflow, and audit logging of actions taken. This reduces catalog clutter while preserving reviewability of deletions.

**Derived from:** `conversations/conv_pines021_item_purging.eml`, `early_draft_srs_galecia.txt`

### REQ-009-47D1A2: Item Transfer Utility — Advanced Features

**Priority:** Should

Provide additional transfer features such as previewing transfer results before commit, undo/rollback of recent transfers when feasible, transfer history and audit logging, configurable notification/alerts, printable labels/pull sheets, and configurable revert rules (for example: revert after N days if not received). These features are valuable for operational convenience and error recovery but are not required for the baseline release; implementations must document edge cases (e.g., what happens if destination constraints prevent a revert).

**Derived from:** `conversations/conv_pines018_item_transfer.eml`, `early_draft_srs_galecia.txt`

### REQ-010-D03DCD: Item Transfer Utility — Core

**Priority:** Must

Provide core batch transfer functionality that lets staff query candidate items, select items manually or via saved queries, and perform bulk updates to item home-location and holding-location fields. The utility must generate pull lists for physical transfer and update the live item-location records so availability and search results reflect the transfer. This baseline functionality must be robust and auditable so inventory is accurate after transfers.

**Derived from:** `conversations/conv_pines018_item_transfer.eml`, `early_draft_srs_galecia.txt`, `interview_sysadmin_2009-05-10.txt`

### REQ-011-251935: Last Copy Report

**Priority:** Must

Provide a 'last copy' report that reliably identifies item records which represent the only copy of a bibliographic work in the system before any purge or deletion action is allowed. The report must surface bibliographic and item-level details to support cataloging review and must be designated CRITICAL in workflows that perform automated or bulk deletions. This requirement is necessary to prevent accidental loss of unique holdings.

**Derived from:** `conversations/conv_pines021_item_purging.eml`, `early_draft_srs_galecia.txt`, `interview_cataloging_2009-05-08.txt`

### REQ-012-4941F5: Material Volume Report

**Priority:** Should

Provide a report showing material volume at a branch or system 'point in time', including counts for new acquisitions, items checked in (on shelf), and items checked out (in circulation). The report must support breakdowns by configurable categories (for example: holds, adult fiction, board books) and allow administrators to define and save custom category mappings. The report must document which timestamp defines the 'point in time' (e.g., acquisition_date vs. last-checked-in timestamp) so consumers can interpret counts consistently.

**Derived from:** `conversations/conv_pines014_material_volume.eml`, `early_draft_srs_galecia.txt`

### REQ-013-B6DCFF: Missing and Damaged Items Report

**Priority:** Should

Provide reports of missing and damaged items at branch and system level that list item identifiers, condition notes, and status history. The report must support filtering by branch, date range, and item type and provide aggregates to help identify loss or damage patterns. These reports assist staff in targeting preservation, security, and staffing responses.

**Derived from:** `conversations/conv_pines019_020_missing_intransit.eml`, `early_draft_srs_galecia.txt`

### REQ-014-4804B2: Patron Characteristics Reporting

**Priority:** Should

Allow queries and reports to be limited or grouped by patron attributes (for example: age range, ZIP code, county, home branch, patron type, preferred language) and permit combinations of demographic filters. The query tool must support inclusion of null or missing values where appropriate and produce aggregated results usable for program planning and outreach. Access to sensitive demographic fields must respect privacy policies and permissions.

**Derived from:** `conversations/conv_pines023_patron_characteristics.eml`, `early_draft_srs_galecia.txt`, `survey_results_2009.txt`

### REQ-015-268D14: Query Tool (Ad-hoc Builder)

**Priority:** Should

Provide an interactive query builder that can query all record types, let staff select fields and values, support Boolean operators, and allow saved and reusable queries. The tool must be usable by non-technical staff, show which query selections produced which rows in results (query → result traceability), and include options to include null/blank values in results. Integration points must exist so saved queries can feed templates and canned reports.

**Derived from:** `early_draft_srs_galecia.txt`, `evergreen_reference_2009.txt`, `survey_results_2009.txt`

### REQ-016-1A3DF8: Report Features and Interface — Queueing, Scheduling, and Visibility

**Priority:** Should

Provide a user-facing report/query designer and a reporting UI that supports scheduling, saving templates, and visibility into the report queue (status, owner, priority, start/completion times). The system must allow users to see their own queued jobs and provide administrators with visibility into all queued and running jobs so long-running reports can be managed and prioritized. The UI must offer the ability to cancel queued/running reports and to view basic run history.

**Derived from:** `early_draft_srs_galecia.txt`, `email_report_features.eml`, `meeting_minutes/meeting_2009-07-20_minutes.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

### REQ-017-3B84C4: Report Output Formats and Scheduling

**Priority:** Should

Support export of report results in standard formats (CSV, Excel-compatible files, and HTML) and support scheduling of recurring reports with email or shared-location delivery. The system must also allow report runs to be canceled and must include metadata about the run (parameters used, timestamp, user). These capabilities must be documented in the administrative guide.

**Derived from:** `early_draft_srs_galecia.txt`, `evergreen_reference_2009.txt`, `meeting_minutes/meeting_2009-03-15_minutes.txt`

### REQ-018-165B10: Report Permissions, Template Editing, and Cloning

**Priority:** Should

Provide fine-grained permissions for report creation, editing, scheduling and template cloning so that administrators can control who may view, run, or modify canned or ad-hoc reports. Templates must be clonable so staff can start from an existing template and customize parameters without altering the canonical template. Permission changes and template edits must be auditable.

**Derived from:** `early_draft_srs_galecia.txt`, `email_report_features.eml`, `meeting_tech_subcommittee_2009-06-30.txt`

### REQ-019-62529E: Shelf Space Report

**Priority:** Should

Provide a report comparing percentage of total circulations, percentage of collection, and an estimated percentage of shelf space by genre/format at branch and system levels. Because shelf-space is not directly tracked, the report must offer configurable estimation methods (for example: sum of item physical-dimension metadata where available, or an item-count proxy by format/genre) and must indicate which proxy/algorithm was used for a given run. Report consumers must be able to compare branch-level values to system averages to support reallocation decisions.

**Derived from:** `conversations/conv_pines016_shelf_space.eml`, `early_draft_srs_galecia.txt`

### REQ-020-407E46: Staff Login Streamlining

**Priority:** Could

Support optional streamlined staff authentication methods (for example card-swipe or single-sign-on) at workstation level while preserving individual accountability in audit logs; traditional username/password must remain available. The streamlined option must be configurable per workstation and must not permit shared or anonymous logins that would compromise auditability. Implementation must include an administrative configuration to enable/disable streamlined login per terminal.

**Derived from:** `early_draft_srs_galecia.txt`, `email_staff_login.eml`, `interview_sysadmin_2009-05-10.txt`

### REQ-021-D54DC2: System Capacity Interface

**Priority:** Should

Provide a visual interface that displays capacity metrics for all branches with a high-level overview and the ability to drill down to individual-branch detail. The interface must support sorting and filtering (region, library type, current load) and present trend data over configurable time windows so managers can observe growth or shrinkage. Data displayed must be exportable for further analysis.

**Derived from:** `conversations/conv_pines015_capacity_interface.eml`, `early_draft_srs_galecia.txt`

### REQ-022-3B2AA6: Won't: Separate Reporting Database or Historical Warehouse (Initial Release)

**Priority:** Won't

For the initial release, the project will not include a separate reporting-only database or a historical reporting warehouse; reporting will use live operational data and scheduled exports. Multiple sources identify historical/snapshot reporting as valuable for trend analysis and compliance, but building and maintaining a separate warehouse is an architectural effort that will delay initial delivery and is therefore deferred to a future release. The decision and tradeoffs must be documented, and specific historical reporting needs should be collected for prioritization in subsequent releases.

**Derived from:** `early_draft_srs_galecia.txt`, `evergreen_reference_2009.txt`, `meeting_tech_subcommittee_2009-06-30.txt`

## Discarded or Blacklisted

- Original 'Won't Need for Current Release' candidate (simple assertion that no separate reporting database will be included) was flagged as contradictory to multiple source documents that explicitly call out the need for a historical reporting warehouse or snapshots. Several meeting notes, the Evergreen reference, and the tech-subcommittee files identify historical reporting as an identified gap; discarding the unqualified original candidate preserves traceability. The revised Won't requirement is retained in the requirements list but rewritten to acknowledge the conflict and to defer the warehouse as an explicit scope decision rather than deny its future necessity.
