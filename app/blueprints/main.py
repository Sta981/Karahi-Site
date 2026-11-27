from datetime import date, datetime, timedelta

from sqlalchemy import or_

from flask import (Blueprint, abort, flash, make_response, redirect, render_template, request,
                   session, url_for)

from ..extensions import db
from ..models import (Category, ContactMessage, DiningTable, MenuItem, OpeningHours, Promotion,
                      Reservation, Review, Tag)
from ..utils import check_csrf, current_user, safe_next, valid_email, valid_phone

bp = Blueprint("main", __name__)
DEPARTMENTS = [("management", "Restaurant manager", "Events, complaints and feedback"), ("kitchen", "Chef & kitchen", "Dietary requirements and menu questions"), ("service", "Waiters & service", "Table service and dining requests"), ("reservations", "Reservations team", "Bookings and special occasions")]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@bp.route("/")
def home():
    return menu_page("main/home.html")


@bp.route("/menu")
def menu():
    return menu_page("main/menu.html")


def menu_page(template):
    """The home and menu routes share one server-rendered storefront."""
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag", type=int)
    query = MenuItem.query.filter_by(is_available=True)
    if q:
        query = query.filter(MenuItem.name.ilike(f"%{q}%") | MenuItem.description.ilike(f"%{q}%"))
    if tag:
        query = query.filter(MenuItem.tags.any(Tag.id == tag))
    items = query.all()
    categories = [(c, [i for i in items if i.category_id == c.id])
                  for c in Category.query.order_by(Category.sort_order).all()]
    categories = [(c, its) for c, its in categories if its]
    today = date.today()
    promos = Promotion.query.filter(or_(Promotion.starts_on.is_(None), Promotion.starts_on <= today), or_(Promotion.ends_on.is_(None), Promotion.ends_on >= today)).all()
    return render_template(template, categories=categories, promos=promos,
                           tags=Tag.query.order_by(Tag.name).all(), q=q, active_tag=tag,
                           count=len(items), storefront=True)


@bp.route("/menu/<int:item_id>")
def item_detail(item_id):
    item = db.session.get(MenuItem, item_id) or abort(404)
    user = current_user()
    my_review = next((r for r in item.reviews if user and r.user_id == user.id), None)
    return render_template("main/item.html", item=item, my_review=my_review)


@bp.route("/order-type", methods=["POST"])
def set_order_type():
    """Remember delivery/pickup in the session and in a long-lived cookie."""
    check_csrf()
    choice = request.form.get("order_type")
    if choice not in ("delivery", "pickup"):
        abort(400)
    session["order_type"] = choice
    resp = make_response(redirect(safe_next(request.form.get("next")) or url_for("main.menu")))
    resp.set_cookie("preferred_order_type", choice, max_age=60 * 60 * 24 * 30, samesite="Lax")
    return resp


@bp.route("/about")
def about():
    hours = OpeningHours.query.order_by(OpeningHours.weekday).all()
    return render_template("main/about.html", hours=hours, days=DAYS)


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    form, errors = {}, {}
    if request.method == "POST":
        check_csrf()
        form = {k: request.form.get(k, "").strip() for k in ("name", "email", "message")}
        form["department"] = request.form.get("department", "management")
        if form["department"] not in {d[0] for d in DEPARTMENTS}:
            errors["department"] = "Choose a valid department."
        if not 2 <= len(form["name"]) <= 80:
            errors["name"] = "Tell us your name."
        if not valid_email(form["email"]) or len(form["email"]) > 120:
            errors["email"] = "Enter a valid email address."
        if not 10 <= len(form["message"]) <= 2000:
            errors["message"] = "Write between 10 and 2000 characters."
        if not errors:
            label = next(d[1] for d in DEPARTMENTS if d[0] == form["department"])
            db.session.add(ContactMessage(name=form["name"], email=form["email"], message=form["message"], department=form["department"], user_id=current_user().id if current_user() else None))
            from ..operations import notify_roles
            notify_roles(("manager",), "New customer enquiry.")
            db.session.commit()
            flash("Your enquiry has been saved for the restaurant team.", "success")
            return redirect(url_for("main.contact"))
    return render_template("main/contact.html", form=form, errors=errors, departments=DEPARTMENTS)


@bp.route("/reserve", methods=["GET", "POST"])
def reserve():
    user = current_user()
    form, errors = ({"guest_name": user.name, "guest_phone": user.phone or ""} if user else {}), {}
    if request.method == "POST":
        check_csrf()
        form = {k: request.form.get(k, "").strip() for k in ("guest_name", "guest_phone", "party_size", "when")}
        if len(form["guest_name"]) < 2:
            errors["guest_name"] = "Enter a name for the booking."
        if not valid_phone(form["guest_phone"]):
            errors["guest_phone"] = "Enter a valid phone number."
        try:
            size = int(form["party_size"])
            if not 1 <= size <= 12:
                raise ValueError
        except ValueError:
            size = 0
            errors["party_size"] = "Party size must be between 1 and 12."
        try:
            when = datetime.strptime(form["when"], "%Y-%m-%dT%H:%M")
            if when <= datetime.now():
                errors["when"] = "Pick a time in the future."
        except ValueError:
            when = None
            errors["when"] = "Pick a date and time."
        table = None
        if not errors:
            for candidate in DiningTable.query.filter(DiningTable.seats >= size).order_by(DiningTable.seats).all():
                DiningTable.query.filter_by(id=candidate.id).update({DiningTable.seats: DiningTable.seats}, synchronize_session=False)
                clash = Reservation.query.filter(Reservation.table_id == candidate.id, Reservation.status != "cancelled", Reservation.reserved_for < when + timedelta(hours=2), Reservation.ends_at > when).first()
                if not clash:
                    table = candidate
                    break
            if not table:
                errors["when"] = "No table free for that time. Try another slot."
        if not errors:
            user = current_user()
            booking = Reservation(table=table, user_id=user.id if user else None,
                                  guest_name=form["guest_name"], guest_phone=form["guest_phone"],
                                  party_size=size, reserved_for=when, ends_at=when + timedelta(hours=2))
            db.session.add(booking)
            from ..operations import notify_roles
            notify_roles(("manager",), "New confirmed table reservation.")
            db.session.commit()
            flash(f"Reservation KH-{booking.id} confirmed for {size} on {when:%a %b %d at %I:%M %p}.", "success")
            return redirect(url_for("main.reserve"))
    return render_template("main/reserve.html", form=form, errors=errors)
