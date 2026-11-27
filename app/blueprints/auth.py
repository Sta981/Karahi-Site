from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import LoyaltyAccount, Role, User, StaffMember, StaffMessage, utcnow
from ..utils import check_csrf, safe_next, valid_email, valid_phone, current_user, login_required
from flask import abort

bp = Blueprint("auth", __name__, url_prefix="/account")


@bp.route("/register", methods=["GET", "POST"])
def register():
    form, errors = {}, {}
    if current_user():
        return redirect(url_for("workspace.home"))
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
    return login_form(False)

@bp.route("/staff-login", methods=["GET", "POST"])
def staff_login():
    return login_form(True)

def login_form(staff_portal):
    error, email = None, ""
    if request.method == "POST":
        check_csrf()
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.is_active and (user.role.name != "customer") == staff_portal and check_password_hash(user.password_hash, request.form.get("password", "")):
            guest_cart_key = session.get("cart_key")
            order_type = session.get("order_type")
            session.clear()
            session["user_id"] = user.id
            if guest_cart_key and not staff_portal:
                session["cart_key"] = guest_cart_key
            if order_type:
                session["order_type"] = order_type
            from ..utils import current_cart
            current_cart(create=False)
            flash(f"Welcome back, {user.name.split()[0]}.", "success")
            return redirect(url_for("workspace.home"))
        error = "Email or password is incorrect."
    return render_template("auth/staff_login.html" if staff_portal else "auth/login.html", error=error, email=email)


@bp.route("/logout", methods=["POST"])
def logout():
    check_csrf()
    session.clear()
    flash("You're logged out.", "info")
    return redirect(url_for("main.home"))


@bp.route("/staff-inbox", methods=["GET", "POST"])
@login_required
def staff_inbox():
    staff = StaffMember.query.filter_by(user_id=current_user().id).first()
    from ..access import permitted
    if not staff or not permitted(current_user(),"team"):
        abort(403)
    if request.method == "POST":
        check_csrf()
        message = StaffMessage.query.filter_by(id=request.form.get("message_id", type=int), staff_id=staff.id).first_or_404()
        reply = request.form.get("reply", "").strip()
        if message.reply or not 1 <= len(reply) <= 2000:
            flash("Reply must be 1–2000 characters and can only be sent once.", "error")
        else:
            message.reply, message.replied_at = reply, utcnow()
            db.session.commit()
            flash("Reply saved for management.", "success")
        return redirect(url_for("auth.staff_inbox"))
    return render_template("auth/staff_inbox.html", staff=staff, messages=StaffMessage.query.filter_by(staff_id=staff.id).order_by(StaffMessage.created_at.desc()).all())
