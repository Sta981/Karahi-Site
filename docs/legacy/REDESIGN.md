# Karahi House / RestroIQ — brand and team communication upgrade

This version is based on the supplied Restaurant.zip. It preserves the existing Flask routes, SQLAlchemy models, admin dashboard and navigation, and adds a staff_messages table (51 tables based on the supplied 50-table database). No production database is included in the distribution. The original archive remains untouched.

## Run locally
Use Python version compatible with the existing dependencies. Create and activate a virtual environment, install requirements, then run `python run.py`. See README.md for setup and existing demo credentials. If pinned dependencies cannot be resolved, verify available versions before changing requirements. Use `pytest -q` before submission. Do not deploy the demo credentials or default development secret publicly.

## What changed
- Original vector restaurant and RestroIQ marks, editorial homepage, animated hero, responsive cards, accessible reduced-motion behavior.
- Split-screen login and registration; password visibility toggle; role-based default login destinations.
- Department-specific contact form: department label saved with message in the management contact inbox. This is not email delivery or live customer-to-staff chat.
- Admin staff directory call/email shortcuts (where a number or email exists), private staff message compose and reply history.
- For internal communication: create a non-admin user through registration or authorized account management, then link that user to exactly one employee using Admin > Staff Profiles & Roles. Use a fresh test account, not a real customer's account. Sign in as admin and send a message from Team messages, then sign in as the linked employee and open Staff inbox. Staff can read only their linked profile's messages and reply once. Only admins can send through the management workspace. Existing staff records are not automatically assigned logins.
- Added regression tests for staff communication and departmental enquiries.

## Verification and limitations
Python compile and Jinja syntax parsing passed, as did JavaScript syntax checking. Fixture templates for homepage, login and contact rendered using menu data from the supplied database. Flask and Flask-SQLAlchemy were unavailable, and package installation failed. Full runtime tests and visual browser checks could not be completed. Do not represent this release as production-ready or fully tested. Original US currency and location remain unchanged. Existing cart, checkout, order and admin views retain their structure with shared brand styling; no complete redesign of every admin screen was performed.
