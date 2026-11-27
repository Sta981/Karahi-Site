# Demo V3 — scope and verification

A fresh local demonstration database is required. Existing databases are not overwritten or merged. The seven-day data is synthetic and relative to first initialization. Phone numbers are deliberately masked (not dialable). Demo payments are simulated historical records, not actual transactions. Demo mode must not be deployed publicly. PKR applies to the fresh seven-day demo database; legacy amounts are not converted.

## Changes
- 56 orders (52 completed and paid, four active); 26 reservations including upcoming bookings; seven purchase orders; seven cash sessions; 12 customers and seven linked employees; payroll, shifts, leave, messages, offers, customer enquiries, loyalty and supporting records.
- Sidebar navigation scroll and expanded groups saved in per-tab session storage; independently scrollable sidebar nav on desktop. Browser testing still pending.
- Cashier payment history; manager inbox link and named reservations; chef board lane counts; employee onboarding requires contact and salary; customer account displays points; loyalty accrual on validated order completion. Password hashes remain excluded from generic account tables. No password-reset workflow added.
- Discover More links to the homepage story. Full customer-facing visual overhaul remains pending.

## Verification
`tools/check_demo_week.py` ran against actual SQLAlchemy/SQLite using a Flask-independent test harness with a test-only password-hashing stub because Flask/Werkzeug are unavailable. Verified repeat-run protection, 7 dates, counts, loyalty/stock reconciliation, order totals, paid totals and foreign keys. `tools/check_schema.py` verified model creation, mappings and selected order/stock/payment transitions. All Python and Jinja syntax parsed and JavaScript passed Node syntax checks. Full Flask integration, login, browser, mobile, sidebar behavior and new live loyalty workflow not end-to-end tested. No claims of production readiness. Existing tests adjusted for seeded carts and reviews but not run here.
