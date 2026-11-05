# Karahi Site

A Flask-based restaurant ordering and management application built for **Web Engineering (CSE601330)**. The project demonstrates routing, Jinja2 template inheritance, SQLAlchemy database operations, server-side form validation, sessions and cookies.

## Features

- Responsive restaurant menu with food photographs, categories, search and tag filters
- Dish details with spice choices, add-ons, nutrition, ingredients and allergens
- Customer registration, login, profile, saved addresses and favorites
- Guest and customer carts, quantity updates, and pickup or delivery selection
- Checkout with server-side validation, coupons and delivery-zone fees
- Order confirmation, order history, cancellation and loyalty points
- Customer review creation, editing and deletion
- Table reservations and a contact form
- Admin dashboard, order status management and database record management

## Technology

Python, Flask, Jinja2, Flask-SQLAlchemy, SQLAlchemy, SQLite, HTML, CSS and JavaScript. Render deployments use Gunicorn.

## Run locally on Windows

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

Open **http://127.0.0.1:5000/**. The application creates the SQLite database and sample data automatically on first startup.

For macOS or Linux, use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`.

## Configuration

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session signing key; set a random value when deploying |
| `DATABASE_URL` | Optional database connection URL; defaults to `sqlite:///karahi.db` |

The local SQLite file is stored at `instance/karahi.db`.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@karahihouse.test | Admin12345 |
| Customer | ayesha@example.com | Customer123 |

Admin panel: **/admin/**.

Checkout coupon: **WELCOME10**, giving 10% off eligible orders with a subtotal of at least $20.

Demo delivery ZIP codes: **94109, 94102, 94108, 94133, 94123**.

The checkout is a demonstration and does not charge a real card. Use **Pay at counter** when presenting the project.

## Database

The project defines **47 SQLAlchemy tables**, covering accounts, menu items, ingredients, modifiers, carts, orders, payments, coupons, delivery, reservations, reviews and restaurant information. Foreign keys and ORM relationships connect the application data.

## Project structure

```text
run.py                     Application entry point
requirements.txt           Python dependencies
render.yaml                Render service configuration
app/
  __init__.py              Application factory and shared template context
  extensions.py            SQLAlchemy instance
  models.py                Database models and relationships
  seed.py                  Sample restaurant and account data
  presentation.py          Food image selection
  utils.py                 Authentication, validation, CSRF and cart helpers
  blueprints/
    main.py                Menu, contact, reservations and restaurant pages
    auth.py                Registration, login and logout
    shop.py                Cart, checkout, orders, profiles and reviews
    admin.py               Admin dashboard and record management
  templates/               Jinja2 templates and shared components
  static/                  CSS, JavaScript and local images
tests/test_app.py           Automated application tests
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The supplied tests cover the table minimum, public pages, CSRF rejection, registration validation, cart and checkout, review CRUD, admin access control, admin table/form rendering and tag record CRUD.

## Deploy on Render

See [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for deployment instructions. The build command is `pip install -r requirements.txt` and the start command is:

```bash
gunicorn --workers 1 --threads 2 --bind 0.0.0.0:$PORT run:app
```

SQLite data on a free Render web service is temporary. The seeded menu and demo accounts are recreated when an empty database is initialized.

## Assets

Food photographs are stored locally in `app/static/img/food/`. Asset acknowledgments are recorded in [ASSET_CREDITS.md](ASSET_CREDITS.md).
