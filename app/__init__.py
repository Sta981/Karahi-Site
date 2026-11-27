import os
from datetime import datetime, timezone

from flask import Flask, session
from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def sqlite_foreign_keys(connection, _):
    import sqlite3
    if isinstance(connection, sqlite3.Connection):
        connection.execute("PRAGMA foreign_keys=ON")

from .extensions import db


def create_app(config=None):
    app = Flask(__name__)
    db_url = os.environ.get("DATABASE_URL", "sqlite:///restroiq_demo_v5.db" if os.environ.get("RESTRO_DEMO") == "1" else "sqlite:///restroiq_v2.db")
    if db_url and db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or os.urandom(32).hex(),
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE") == "1",
        DEMO_MODE=os.environ.get("RESTRO_DEMO") == "1",
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)

    # Public Render demo credentials must be private, never the local defaults.
    if os.environ.get("RENDER") and app.config["DEMO_MODE"]:
        secrets = [os.environ.get(k, "") for k in ("DEMO_OWNER_PASSWORD", "DEMO_STAFF_PASSWORD", "DEMO_CUSTOMER_PASSWORD")]
        if any(len(p) < 12 or p in {"Admin12345", "DemoStaff123!", "Customer123"} for p in secrets) or len(set(secrets)) != 3:
            raise RuntimeError("Set three different DEMO_*_PASSWORD variables of at least 12 characters in Render.")
        if not os.environ.get("SECRET_KEY"):
            raise RuntimeError("Set SECRET_KEY in Render.")

    db.init_app(app)

    from .blueprints.admin import bp as admin_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.main import bp as main_bp
    from .blueprints.shop import bp as shop_bp
    from .blueprints.workspace import bp as workspace_bp

    for blueprint in (main_bp, auth_bp, shop_bp, admin_bp, workspace_bp):
        app.register_blueprint(blueprint)

    from .utils import csrf_token, current_cart, current_user, store_status

    # a Jinja global (not just context) so imported macros can call it too
    app.jinja_env.globals["csrf_token"] = csrf_token
    from .access import permitted, role_name
    app.jinja_env.globals.update(permitted=permitted, role_name=role_name)
    from .presentation import menu_image
    app.jinja_env.globals["menu_image"] = menu_image

    @app.context_processor
    def inject_globals():
        from flask import request
        from .models import StoreInfo, StaffMember, Notification
        order_type = session.get("order_type")
        if not order_type:
            cookie_pref = request.cookies.get("preferred_order_type")
            if cookie_pref in ("delivery", "pickup"):
                order_type = cookie_pref
                session["order_type"] = order_type
            else:
                order_type = "pickup"
        return {
            "current_user": current_user(),
            "unread_notifications": Notification.query.filter_by(user_id=current_user().id,is_read=False).count() if current_user() else 0,
            "staff_profile": StaffMember.query.filter_by(user_id=current_user().id).first() if current_user() else None,
            "cart": current_cart(create=False),
            "store": StoreInfo.query.first(),
            "store_status": store_status(),
            "year": datetime.now(timezone.utc).year,
            "order_type": order_type,
            "currency_code": app.config.get("CURRENCY_CODE", "USD"),
            "currency_symbol": "Rs. " if app.config.get("CURRENCY_CODE") == "PKR" else "$",
            "demo_mode": app.config["DEMO_MODE"],
        }

    @app.errorhandler(404)
    def not_found(_):
        from flask import render_template
        return render_template("error.html", code=404, message="That page isn't on our menu."), 404

    @app.errorhandler(403)
    def forbidden(_):
        from flask import render_template
        return render_template("error.html", code=403, message="You don't have access to this page."), 403

    with app.app_context():
        # Never silently modify a legacy database. Use a fresh database for V2.
        existing = inspect(db.engine)
        for name in existing.get_table_names():
            if name in db.metadata.tables:
                expected = set(db.metadata.tables[name].columns.keys())
                found = {c['name'] for c in existing.get_columns(name)}
                if expected - found:
                    raise RuntimeError(f"Legacy schema detected in {name}; back up and use a new database for Foundation V2.")
        db.create_all()
        from .access import seed_access, seed_demo_staff
        from .models import Role, User, Coupon
        if not app.config['DEMO_MODE'] and Coupon.query.filter_by(code='WEEK7').first():
            raise RuntimeError('This is a synthetic demo database. Set RESTRO_DEMO=1 for local demonstration, or use a separate production database.')
        if app.config['DEMO_MODE'] and not Role.query.first():
            from .seed import seed_if_empty
            seed_if_empty()
        seed_access()
        if app.config['DEMO_MODE']:
            from .demo_week import seed_week
            from .models import MenuItem
            if not MenuItem.query.first():
                raise RuntimeError("The selected demo database has no menu catalog. Back it up and use a fresh database filename with RESTRO_DEMO=1; existing data has not been overwritten.")
            seed_week()
            from .models import Coupon
            if Coupon.query.filter_by(code="WEEK7").first():
                app.config["CURRENCY_CODE"] = "PKR"
            else:
                seed_demo_staff()

    app.jinja_env.globals["currency_symbol"] = "Rs. " if app.config.get("CURRENCY_CODE") == "PKR" else "$"
    app.jinja_env.globals["currency_code"] = app.config.get("CURRENCY_CODE", "USD")

    @app.cli.command('create-owner')
    def create_owner():
        import click
        from werkzeug.security import generate_password_hash
        from .models import User, Role
        from .utils import valid_email
        if User.query.join(Role).filter(Role.name == 'owner').first():
            raise click.ClickException('An owner already exists.')
        email = click.prompt('Owner email').strip().lower()
        name = click.prompt('Owner name').strip()
        password = click.prompt('Password', hide_input=True, confirmation_prompt=True)
        if not valid_email(email) or not 2 <= len(name) <= 80 or len(password) < 12:
            raise click.ClickException('Valid email, name and password of 12+ characters required.')
        db.session.add(User(name=name,email=email,password_hash=generate_password_hash(password),role=Role.query.filter_by(name='owner').one()))
        db.session.commit()
        click.echo('Owner created.')

    return app
