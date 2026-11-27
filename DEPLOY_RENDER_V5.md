# Render V5 classroom deployment

Use Python web service, repository root containing run.py, build `pip install -r requirements.txt`, start `gunicorn --workers 1 --threads 2 --bind 0.0.0.0:$PORT run:app`.

Set RESTRO_DEMO=1, COOKIE_SECURE=1, SECRET_KEY (random), DATABASE_URL=sqlite:///restroiq_render_v5.db, and distinct DEMO_OWNER_PASSWORD, DEMO_STAFF_PASSWORD, DEMO_CUSTOMER_PASSWORD values (12+ characters). Do not commit secrets. Local demo defaults remain available outside Render. Passwords apply when the database is seeded, not to existing accounts. Use a fresh database; back up existing records first. SQLite on Render free is ephemeral. For persistence, use a fresh PostgreSQL database and set DATABASE_URL to its internal URL; PostgreSQL has not been runtime-tested in this package. All sample data is synthetic, not suitable for production. The application and public demo accounts have not undergone a complete security review. Do not collect real customer details or payment data.

Static Python syntax and ZIP integrity verified; live deployment not performed.
