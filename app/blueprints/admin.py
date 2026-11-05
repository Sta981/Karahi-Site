"""Admin panel: dashboard, order workflow, and generic CRUD for every model.

The CRUD views read each model's columns and build the form and validation from
them, so all 47 tables get Create / Read / Update / Delete without 47 copies of
the same code.
"""
from datetime import date, datetime

from flask import (Blueprint, abort, flash, redirect, render_template, request, url_for)
from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, Text, func, inspect
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from ..extensions import db
from ..models import ContactMessage, Order, OrderStatusHistory, User
from ..utils import admin_required, check_csrf

bp = Blueprint("admin", __name__, url_prefix="/admin")
PER_PAGE = 20
ORDER_STATUSES = ["placed", "preparing", "ready", "out_for_delivery", "completed", "cancelled"]


def registry():
    """tablename -> model class, sorted by name."""
    return {m.class_.__tablename__: m.class_ for m in sorted(db.Model.registry.mappers,
                                                             key=lambda m: m.class_.__tablename__)}


def get_model(table):
    return registry().get(table) or abort(404)


def editable_columns(model):
    """Columns shown in forms (skip auto timestamps and auto PKs)."""
    cols = []
    for col in inspect(model).columns:
        if col.name == "created_at":
            continue
        if col.primary_key and not col.foreign_keys:
            continue
        if col.name == "password_hash":
            continue
        cols.append(col)
    return cols


def fk_options(col):
    fk = next(iter(col.foreign_keys))
    target = next(c for c in registry().values() if c.__tablename__ == fk.column.table.name)
    return [(row.id, str(row) if type(row).__str__ is not object.__str__ else f"#{row.id}")
            for row in target.query.limit(300).all()]


def describe_fields(model):
    fields = []
    for col in editable_columns(model):
        kind = "text"
        if col.foreign_keys:
            kind = "select"
        elif isinstance(col.type, Boolean):
            kind = "checkbox"
        elif isinstance(col.type, Integer):
            kind = "number"
        elif isinstance(col.type, Float):
            kind = "float"
        elif isinstance(col.type, Text):
            kind = "textarea"
        elif isinstance(col.type, DateTime):
            kind = "datetime-local"
        elif isinstance(col.type, Date):
            kind = "date"
        required = not col.nullable and col.default is None and not isinstance(col.type, Boolean)
        fields.append({"name": col.name, "kind": kind, "required": required, "col": col,
                       "options": fk_options(col) if kind == "select" else None})
    return fields


def parse_form(model, fields, instance=None):
    """Validate submitted form values. Returns (values, errors)."""
    values, errors = {}, {}
    for f in fields:
        raw, col, name = request.form.get(f["name"], "").strip(), f["col"], f["name"]
        if f["kind"] == "checkbox":
            values[name] = f["name"] in request.form
            continue
        if raw == "":
            if f["required"]:
                errors[name] = "This field is required."
            else:
                values[name] = None
            continue
        try:
            if f["kind"] in ("number", "select"):
                values[name] = int(raw)
            elif f["kind"] == "float":
                values[name] = float(raw)
            elif f["kind"] == "date":
                values[name] = datetime.strptime(raw, "%Y-%m-%d").date()
            elif f["kind"] == "datetime-local":
                values[name] = datetime.strptime(raw, "%Y-%m-%dT%H:%M")
            else:
                if isinstance(col.type, String) and col.type.length and len(raw) > col.type.length:
                    errors[name] = f"Max {col.type.length} characters."
                values[name] = raw
        except ValueError:
            errors[name] = "Enter a valid value."
            continue
        if name == "email" and "@" not in raw:
            errors[name] = "Enter a valid email address."
        if name in ("price", "extra_price", "fee", "amount") and values.get(name, 0) < 0:
            errors[name] = "Cannot be negative."
        if name == "rating" and not 1 <= values.get(name, 0) <= 5:
            errors[name] = "Rating must be 1–5."
        if f["kind"] == "select":
            fk = next(iter(col.foreign_keys))
            target = next(c for c in registry().values() if c.__tablename__ == fk.column.table.name)
            if not db.session.get(target, values[name]):
                errors[name] = "Selected record does not exist."
        if col.unique and name not in errors:
            clash = model.query.filter(getattr(model, name) == values[name]).first()
            if clash and clash is not instance:
                errors[name] = "Must be unique; this value already exists."
    return values, errors


@bp.route("/")
@admin_required
def dashboard():
    stats = {
        "orders": Order.query.count(),
        "revenue": db.session.query(func.coalesce(func.sum(Order.total), 0)).filter(
            Order.status != "cancelled").scalar(),
        "customers": User.query.count(),
        "open_messages": ContactMessage.query.filter_by(is_resolved=False).count(),
    }
    recent = Order.query.order_by(Order.created_at.desc()).limit(8).all()
    tables = [(name, model.query.count()) for name, model in registry().items()]
    return render_template("admin/dashboard.html", stats=stats, recent=recent, tables=tables,
                           statuses=ORDER_STATUSES)


@bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def order_status(order_id):
    check_csrf()
    order = db.session.get(Order, order_id) or abort(404)
    status = request.form.get("status")
    if status not in ORDER_STATUSES:
        abort(400)
    if status != order.status:
        order.status = status
        order.history.append(OrderStatusHistory(status=status))
        db.session.commit()
        flash(f"Order #{order.id} is now {status.replace('_', ' ')}.", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))


# ---------- Generic CRUD ----------
@bp.route("/t/<table>")
@admin_required
def list_rows(table):
    model = get_model(table)
    page = request.args.get("page", 1, type=int)
    pk = inspect(model).primary_key
    pagination = model.query.order_by(*pk).paginate(page=page, per_page=PER_PAGE, error_out=False)
    cols = [c.name for c in inspect(model).columns if c.name != "password_hash"][:7]
    return render_template("admin/list.html", table=table, cols=cols, pagination=pagination,
                           pk_names=[c.name for c in pk])


def row_key(model, args):
    """Composite-key aware lookup from query-string values."""
    pk_cols = inspect(model).primary_key
    try:
        ident = tuple(int(args.get(c.name)) for c in pk_cols)
    except (TypeError, ValueError):
        abort(404)
    return db.session.get(model, ident if len(ident) > 1 else ident[0]) or abort(404)


@bp.route("/t/<table>/new", methods=["GET", "POST"])
@admin_required
def create_row(table):
    model = get_model(table)
    fields = describe_fields(model)
    # association tables have FK primary keys, so those columns are included in `fields`
    errors, values = {}, {}
    if request.method == "POST":
        check_csrf()
        values, errors = parse_form(model, fields)
        password = request.form.get("password", "")
        if model is User and len(password) < 8:
            errors["password"] = "Password needs at least 8 characters."
        if not errors:
            obj = model(**values)
            if model is User:
                obj.password_hash = generate_password_hash(password)
            db.session.add(obj)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Could not save: that combination already exists or breaks a constraint.", "error")
            else:
                flash("Record created.", "success")
                return redirect(url_for("admin.list_rows", table=table))
    return render_template("admin/form.html", table=table, fields=fields, errors=errors,
                           values=values or {}, obj=None, is_user=model is User, mode="Create")


@bp.route("/t/<table>/edit", methods=["GET", "POST"])
@admin_required
def edit_row(table):
    model = get_model(table)
    obj = row_key(model, request.args)
    fields = [f for f in describe_fields(model) if not f["col"].primary_key]  # keys are fixed once created
    errors = {}
    if request.method == "POST":
        check_csrf()
        values, errors = parse_form(model, fields, instance=obj)
        password = request.form.get("password", "")
        if model is User and password and len(password) < 8:
            errors["password"] = "Password needs at least 8 characters."
        if not errors:
            for key, val in values.items():
                setattr(obj, key, val)
            if model is User and password:
                obj.password_hash = generate_password_hash(password)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                flash("Could not save: constraint violated.", "error")
            else:
                flash("Record updated.", "success")
                return redirect(url_for("admin.list_rows", table=table))
    return render_template("admin/form.html", table=table, fields=fields, errors=errors,
                           values={f["name"]: getattr(obj, f["name"]) for f in fields}, obj=obj,
                           is_user=model is User, mode="Edit")


@bp.route("/t/<table>/delete", methods=["POST"])
@admin_required
def delete_row(table):
    check_csrf()
    model = get_model(table)
    obj = row_key(model, request.form)
    db.session.delete(obj)
    try:
        db.session.commit()
        flash("Record deleted.", "info")
    except IntegrityError:
        db.session.rollback()
        flash("Can't delete: other records still depend on this one.", "error")
    return redirect(url_for("admin.list_rows", table=table))
