# Karahi House (Flask)

Online ordering site for a karahi restaurant, modeled on the Karahi House store on Hey Eats
(https://app.heyeats.shop/store/karahi-house/shop). Built for **Web Engineering (CSE601330)**, Weeks 5-8:
routing, Jinja2 templates, SQLAlchemy CRUD, forms, sessions and cookies.

The live store loads its menu with JavaScript, so the dishes and prices in `app/seed.py` are
representative placeholders. Address, phone and opening hours come from the store page.

## Features

- Menu with categories, search, tag filter, limited-time promotion, dish pages with modifiers
  (spice level, add-ons), nutrition, allergens and reviews
- Pick up / Delivery toggle (kept in the session and in a 30-day cookie)
- Cart (guest or logged in, merged on login), checkout with server-side validation, delivery-zone
  fees, coupons, payment method, loyalty points, order history and cancel
- Accounts: register, login, profile, saved addresses (create/delete), favorites
- Reviews: create, update, delete; admin replies
- Table reservations, contact form
- Admin panel (`/admin`): dashboard, order status workflow, and Create / Read / Update / Delete for
  **every table** through one generic, validated CRUD view

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Open http://127.0.0.1:5000. The SQLite database (`instance/karahi.db`) is created and seeded on first run.

Optional environment variables (see `.env.example`): `SECRET_KEY`, `DATABASE_URL`.
Set a real `SECRET_KEY` outside development.

## Seed accounts

| Role     | Email                    | Password     |
|----------|--------------------------|--------------|
| Admin    | admin@karahihouse.test   | Admin12345   |
| Customer | ayesha@example.com       | Customer123  |

Coupon to try at checkout: `WELCOME10` (10% off orders over $20).
Delivery ZIPs: 94109, 94102, 94108, 94133, 94123.

To reset the data, stop the app and delete `instance/karahi.db`.

## Tests

```bash
pytest
```

Covers the 40-table minimum, every public page, CSRF rejection, registration validation, the cart and
checkout flow, review CRUD, admin access control, and admin CRUD on every table.

## Project structure

```
run.py                     entry point
app/
  __init__.py              application factory, error handlers, context
  extensions.py            SQLAlchemy instance
  models.py                47 models (tables) and relationships
  utils.py                 auth guards, CSRF, validators, cart lookup
  seed.py                  demo data
  blueprints/
    main.py                home, menu, dish page, about, contact, reserve, order type
    auth.py                register, login, logout
    shop.py                cart, checkout, orders, profile, favorites, reviews
    admin.py               dashboard, order status, generic CRUD for all tables
  templates/               base.html + extends/blocks, macros in partials/
  static/                  css, js, category images
tests/test_app.py
```

## Database (47 tables)

Users and accounts: roles, users, addresses, loyalty_accounts, loyalty_transactions, notifications.
Menu: categories, menu_items, item_images, nutrition_info, tags, item_tags, allergens, item_allergens,
ingredients, item_ingredients, suppliers, modifier_groups, modifier_options, item_modifier_groups,
combos, combo_items.
Cart and orders: carts, cart_items, cart_item_modifiers, orders, order_items, order_item_modifiers,
order_status_history, payment_methods, payments, coupons, coupon_usages, promotions, promotion_items.
Delivery: delivery_zones, delivery_drivers, deliveries.
Store and engagement: store_info, opening_hours, holidays, dining_tables, reservations, reviews,
review_replies, favorites, contact_messages.

## Security notes

- Passwords hashed with Werkzeug; session cookie is HttpOnly and SameSite=Lax
- CSRF token required on every POST
- Post-Redirect-Get after every successful form submission, with flash messages
- Login redirects only to same-site paths; users can only touch their own cart, addresses and reviews

## Credits

Course material: Flask, Flask-SQLAlchemy and Jinja2 documentation patterns. Restaurant details
from the public Karahi House store page.

## Reference-style presentation

The storefront uses the reference's white/cream palette, dark buttons, restaurant logo and food
banner, horizontal category navigation, two-column menu cards and a mobile menu. Home and `/menu`
share inherited Jinja templates. Search, tag filtering, dish modifiers, cart, checkout, reservations,
accounts and the admin panel continue to use the existing Flask routes and database.

Food photographs are stored locally in `app/static/img/food/`; their original labels and source
pages are recorded in `sources.json` in that folder. Reference restaurant photos are supplemented
by the sources listed there for starters, lamb chops, chai and gulab jamun. Some photographs show
related dishes as representative images for the existing sample menu. Dishes and prices remain
the project's demo data, rather than the reference's complete live catalogue.

`app/presentation.py` replaces the original seeded category illustrations at display time and
preserves custom images saved by an administrator. No database migration or additional runtime
dependency is needed. The schema remains 47 tables and the supplied Flask rubric is unchanged.

Design verification: `python artifacts/verify_design.py` (requires Playwright in the verification
environment and the Flask server on port 5000). Current screenshots and browser results are in
`artifacts/redesign/`. The earlier technical audit in `artifacts/rubric-review.md` records backend
issues separately; a visual redesign does not resolve those findings.
