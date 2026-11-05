import os
from datetime import datetime, timezone

from flask import Flask, session

from .extensions import db


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///karahi.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)

    db.init_app(app)

    from .blueprints.admin import bp as admin_bp
    from .blueprints.auth import bp as auth_bp
    from .blueprints.main import bp as main_bp
    from .blueprints.shop import bp as shop_bp

    for blueprint in (main_bp, auth_bp, shop_bp, admin_bp):
        app.register_blueprint(blueprint)

    from .utils import csrf_token, current_cart, current_user, store_status

    # a Jinja global (not just context) so imported macros can call it too
    app.jinja_env.globals["csrf_token"] = csrf_token
    from .presentation import menu_image
    app.jinja_env.globals["menu_image"] = menu_image

    @app.context_processor
    def inject_globals():
        from .models import StoreInfo
        return {
            "current_user": current_user(),
            "cart": current_cart(create=False),
            "store": StoreInfo.query.first(),
            "store_status": store_status(),
            "year": datetime.now(timezone.utc).year,
            "order_type": session.get("order_type", "pickup"),
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
        db.create_all()
        from .seed import seed_if_empty
        seed_if_empty()

    return app
