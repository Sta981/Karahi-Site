# V4 — Unified Premium Experience

Based on Demo V3. No model changes or management template changes. The 63-table schema and seven-day seed generator are unchanged. Use a new demo database for a clean demonstration, or retain a backed-up, compatible V3 database if you want to preserve its records.

## Changes
- Homepage: explicit View menu and same-page Discover more anchor.
- Menu: premium hero, photo-led dish cards, active promotions, search, dietary filter, category navigation, pickup/delivery selector. The legacy store-header component is no longer used on the menu. Displayed dish prices now use the same effective price as cart totals.
- Dish details: matching image, typography, controls, modifier options, favourites, reviews and add-to-bag form.
- Customer overview: personalized welcome, real loyalty balance, order and reservation summaries, cards, account tabs and service requests.
- Reservation: three-step progressively enhanced form, prefilled customer details, real server-side checks and a confirmation reference. Without JavaScript the entire form remains usable. This does not offer a live availability calendar or selectable floor plan.
- Visit Us: address, hours, closures, food gallery, contact and reservation links. No invented restaurant interior photographs, directions or map; location and phone are fictional in demo mode.
- Cart: accessible dialog preview, opens after successful add (server redirect), full-page editing fallback, checkout link. Not an AJAX checkout.
- Checkout: structured sections, payment preference and clear pending-payment notice. No live payment gateway.
- Orders: photo-led order cards, current status and recorded progress; refresh to get updated status. No push notifications or reorder implementation in V4.
- Profile: account navigation, profile form, address CRUD and saved dish cards.
- Shared premium stylesheet and scripts: responsive layouts, scroll anchors, hero entrance animation, hover motion, sliding bag, reduced-motion support. Existing customer login/register split-screen branding retained.
- New Flask integration regression tests added (unexecuted in this environment).

## Verification
`tools/check_premium_pages.py` executed using actual seeded SQLAlchemy objects and Jinja StrictUndefined, then rendered the resulting static HTML in Chromium with local assets inlined. 15 templates passed render checks. All 15 pages checked at 1440px and 390px for document horizontal overflow; link target/anchor, native bag dialog opening and Escape closure, booking step navigation and preview checked. No JavaScript exceptions in these checks. All 63 demo tables remain populated; seed count and reconciliation checks passed. See PREMIUM_V4_TEST_RESULTS.txt.

Flask and Flask-SQLAlchemy are not installed and package download was unavailable. Full Flask route/authentication/POST integration tests have not run; the browser check is a static seeded-template check, not an end-to-end test or assurance of live navigation. Browser navigation to localhost was blocked in this environment. Run `python -m pytest -q` on a machine with requirements installed. No production or real payment data used. Remaining V3 backend limitations still apply.
