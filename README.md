# RestroIQ V4 — Unified Premium Experience

Flask restaurant operations project for Web Engineering (CSE601330), by Syed Tahir Ali Shah. This is a development build, not a production-certified system. See `docs/IMPLEMENTATION_STATUS.md` before submitting.

## Start a separate demonstration database (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:RESTRO_DEMO='1'
$env:DATABASE_URL='sqlite:///restroiq_demo_v4.db'
$env:SECRET_KEY=(& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))")
.\.venv\Scripts\python.exe run.py
```

Open http://127.0.0.1:5000/. Keep the same secret key between restarts for session and guest confirmation links. Demo mode seeds fictional records into a fresh database; do not enable it against a real database. Existing V1 databases need a separate migration and must not be overwritten. The app checks for missing legacy columns and refuses those schemas.

For Linux/macOS use `python3 -m venv .venv`, `.venv/bin/python -m pip install -r requirements.txt`, `export RESTRO_DEMO=1`, `export DATABASE_URL=sqlite:///restroiq_demo_v4.db`, `export SECRET_KEY=$(.venv/bin/python -c 'import secrets; print(secrets.token_hex(32))')`, and `.venv/bin/python run.py`.

## V4 customer-facing redesign

The menu, dish detail, customer account, reservations, Visit Us, cart, checkout, order history, order details and profile use one premium design system. Discover More scrolls within the homepage. The cart drawer uses server-rendered contents with a full-page fallback. See `docs/PREMIUM_V4.md` for changes and verification limitations. All V3 management modules and the seven-day seed remain included.

## Seven-day synthetic dataset

Use a **fresh** database filename. The app inserts the dataset once at first startup; restarting does not duplicate it. If `restroiq_demo_v4.db` already contains older records, choose a different unused filename. All 63 tables have records. PKR prices, Lahore delivery zones, fictional Pakistani names, and deliberately masked/non-dialable phone numbers are included. The sample dates cover the seven UTC calendar dates ending on the first run date. Upcoming reservations and scheduled activities extend beyond this date. Demo passwords are documented here only; no existing password/hash is displayed in the app. No real messages, payments or calls are sent.

## Demonstration users (not production credentials)

| Role | Email | Password | Login |
|---|---|---|---|
| Owner | admin@karahihouse.test | Admin12345 | /account/staff-login |
| Manager | manager@restroiq.test | DemoStaff123! | /account/staff-login |
| Chef | chef@restroiq.test | DemoStaff123! | /account/staff-login |
| Waiter | waiter@restroiq.test | DemoStaff123! | /account/staff-login |
| Cashier | cashier@restroiq.test | DemoStaff123! | /account/staff-login |
| Inventory officer | inventory@restroiq.test | DemoStaff123! | /account/staff-login |
| Customer | ayesha@example.com | Customer123 | /account/login |

Owner has the executive dashboard and data directory. Other staff access their own workspace; management can open operational modules. Customers have a separate public website and account area. Roles are assigned server-side.

## Blank development database

Do not set RESTRO_DEMO. Use a new DATABASE_URL and a persistent secret. Run `python -m flask --app app:create_app create-owner` to create the initial owner; populate store details, tables, menu, ingredients, recipe quantities and payment methods using owner reference-data controls. For HTTPS set COOKIE_SECURE=1. Do not expose demo credentials publicly.

## Suggested demonstration

1. Sign in as owner; open executive dashboard and database directory. Open people and access to create staff.
2. Sign in as waiter; submit a table order for Chicken Karahi.
3. Sign in as chef; start preparation and mark ready. Demo recipe quantities and stock are synthetic.
4. Sign in as inventory officer; inspect the stock ledger.
5. Sign in as cashier; record actual received payment for the order (partial or full). No payment gateway is integrated.
6. Sign in as the same waiter; close the ready, paid order. Check the owner report.
7. Demonstrate customer registration, service request and manager resolution; test forbidden direct routes.

## Tests and documentation

`python -m pytest -q` (requires the dependencies above). `python tools/check_schema.py` runs a separate actual SQLAlchemy/SQLite model and transaction check, without Flask. Run `python tools/check_demo_week.py` for isolated SQLite seed checks. See `docs/DEMO_V3.md` and `docs/DEMO_DATA_TEST_RESULTS.txt` for the current scope and results; `IMPLEMENTATION_STATUS.md` describes the previous foundation milestone. Existing frontend assets and template references are credited in ASSET_CREDITS.md.

## Latest release
See [V5 release notes](docs/V5_RELEASE.md) for setup, staff operations, verification and limitations.
