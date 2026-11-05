from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import LoyaltyAccount, Role, User
from ..utils import check_csrf, safe_next, valid_email, valid_phone

bp = Blueprint("auth", __name__, url_prefix="/account")


@bp.route("/register", methods=["GET", "POST"])
def register():
    form, errors = {}, {}
    if request.method == "POST":
        check_csrf()
        form = {k: request.form.get(k, "").strip() for k in ("name", "email", "phone")}
        password, confirm = request.form.get("password", ""), request.form.get("confirm", "")
        if len(form["name"]) < 2:
            errors["name"] = "Enter your full name."
        if not valid_email(form["email"]):
            errors["email"] = "Enter a valid email address."
        elif User.query.filter_by(email=form["email"].lower()).first():
            errors["email"] = "An account with this email already exists."
        if form["phone"] and not valid_phone(form["phone"]):
            errors["phone"] = "Phone may contain digits, spaces, +, - and brackets only."
        if len(password) < 8 or password.isalpha() or password.isdigit():
            errors["password"] = "Use 8+ characters with letters and numbers."
        if password != confirm:
            errors["confirm"] = "Passwords do not match."
        if not errors:
            role = Role.query.filter_by(name="customer").first()
            user = User(name=form["name"], email=form["email"].lower(), phone=form["phone"],
                        password_hash=generate_password_hash(password), role=role)
            user.loyalty = LoyaltyAccount(points=0)
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Welcome to Karahi House! Your account is ready.", "success")
            return redirect(url_for("main.menu"))
    return render_template("auth/register.html", form=form, errors=errors)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error, email = None, ""
    if request.method == "POST":
        check_csrf()
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, request.form.get("password", "")):
            session.clear()
            session["user_id"] = user.id
            flash(f"Welcome back, {user.name.split()[0]}.", "success")
            return redirect(safe_next(request.args.get("next")) or url_for("main.menu"))
        error = "Email or password is incorrect."
    return render_template("auth/login.html", error=error, email=email)


@bp.route("/logout", methods=["POST"])
def logout():
    check_csrf()
    session.clear()
    flash("You're logged out.", "info")
    return redirect(url_for("main.home"))
