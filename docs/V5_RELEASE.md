# RestroIQ V5 — Professional Operations Edition

Based on V4.1. No new tables, schema migrations or destructive database changes. The public visual templates and menu catalog are unchanged. For a fresh demonstration use `start_demo.ps1` or set `RESTRO_DEMO=1` and `DATABASE_URL=sqlite:///restroiq_demo_v5.db` before running `python run.py`. Demo credentials unchanged; never deploy demo credentials publicly.

## Changes
- Owner: large Operations card removed; normal navigation link and database-backed notification indicator. Existing sidebar scroll state script retained.
- Waiter: table availability tiles (not an architectural floor plan), multi-item orders, quantities, zero-price kitchen notes, server-side price and availability checks, own closed-order history. Reserved tables within two hours cannot be used for new walk-in orders; reservation check-in is not implemented.
- Chef: elapsed-since-order timer and 25-minute warning, 30-second page refresh when visible and not interacting with a form or in fullscreen, fullscreen control, ticket history, recipe and unexpired ingredient balances. No real-time socket or audio alerts.
- Cashier: print-ready payment receipt, existing partial/split payments, per-cash-session expected cash and counted variance; no automatic refund gateway or full accounting ledger.
- Inventory: multi-line purchase drafts; existing approval and receiving workflow retained.
- Staff: personal profile, own payroll, shifts, attendance and leave records, leave request and manager review, password change requiring current password. Existing messaging remains available.
- Notifications: per-user unread list and mark-all-read; events for new orders, order transitions, payments, staff messages, purchasing, leave requests/decisions, online reservations and enquiries. Text notices only, not push notifications or universal search.

## Tests and limits
`tools/check_v5.py` executes real SQLAlchemy services with isolated seeded SQLite records. `tools/check_v5_pages.py` renders staff pages with real seeded records using Jinja, then checks Chromium at 1440 and 390px. These are not Flask route tests. Flask and Flask-SQLAlchemy could not be installed in the review environment. Run `pytest` in the installed local environment and manually verify all seven logins, authorization and submissions before showing the project. Manager leave approval was added after the initial browser run; syntax checked only. No refund processing, live push updates, full cashier reconciliation including non-sales cash movements, or comprehensive concurrency testing is claimed. Existing generic owner CRUD and legacy routes still require a full security and integrity review. Do not run demo seeding on production data.
