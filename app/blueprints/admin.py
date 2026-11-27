"""RestroIQ Admin Blueprint: Executive Dashboard, POS, Kitchen KDS, Staff & HR, Analytics & Generic CRUD."""
import csv
from datetime import date, datetime, timedelta
import io
from collections import Counter

from flask import (Blueprint, Response, abort, flash, redirect, render_template, request, url_for)
from sqlalchemy import Boolean, Date, DateTime, Float, Numeric, Integer, String, Text, func, inspect, or_
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from ..admin_navigation import LABELS, NAV
from ..extensions import db
from ..models import (ContactMessage, DiningTable, MenuItem, Order, OrderItem,
                     OrderStatusHistory, Payment, PaymentMethod, Reservation,
                     Review, Role, StaffLeave, StaffMember, StaffPayroll, StaffMessage, User,
                     utcnow)
from ..utils import admin_required, check_csrf, current_user, valid_email, valid_phone

bp = Blueprint("admin", __name__, url_prefix="/admin")
PER_PAGE = 20
PROTECTED = {'roles','permissions','role_permissions','users','staff_members','orders','order_items','order_item_modifiers','order_status_history','payments','stock_batches','stock_movements','purchase_orders','purchase_order_items','audit_logs','attendance_records','cash_sessions','service_requests','reservations','loyalty_transactions','loyalty_accounts'}
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
        elif isinstance(col.type, (Float, Numeric)):
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
                from decimal import Decimal
                values[name] = Decimal(raw) if isinstance(col.type, Numeric) and not isinstance(col.type, Float) else float(raw)
                import math
                if not math.isfinite(values[name]): raise ValueError
            elif f["kind"] == "date":
                values[name] = datetime.strptime(raw, "%Y-%m-%d").date()
            elif f["kind"] == "datetime-local":
                values[name] = datetime.strptime(raw, "%Y-%m-%dT%H:%M")
            else:
                if isinstance(col.type, String) and col.type.length and len(raw) > col.type.length:
                    errors[name] = f"Max {col.type.length} characters."
                values[name] = raw
        except (ValueError, ArithmeticError):
            errors[name] = "Enter a valid value."
            continue
        if name == "email" and "@" not in raw:
            errors[name] = "Enter a valid email address."
        if name in ("price", "extra_price", "fee", "amount", "salary_monthly", "base_salary") and values.get(name, 0) < 0:
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


@bp.app_context_processor
def admin_navigation():
    return {"admin_nav": NAV, "admin_labels": LABELS, "protected_tables": PROTECTED}


def report_data(days):
    now = utcnow()
    start = datetime.combine(now.date() - timedelta(days=days-1), datetime.min.time())
    orders = Order.query.filter(Order.created_at >= start, Order.created_at <= now).all()
    completed = [o for o in orders if o.status == 'completed']
    from ..operations import paid_total
    payments = Payment.query.filter(Payment.status=='paid', Payment.created_at>=start, Payment.created_at<=now).all()
    daily = {start.date()+timedelta(days=i):0.0 for i in range(days)}
    for p in payments: daily[p.created_at.date()] += p.amount
    revenue = sum(p.amount for p in payments)
    popular=Counter()
    for o in completed:
        for line in o.items: popular[line.name] += line.quantity
    peak=max(daily.values(),default=0) or 1
    statuses=Counter(o.status for o in orders)
    return dict(days=days,revenue=revenue,orders=len(orders),average=sum(o.total for o in completed)/len(completed) if completed else 0,active=Order.query.filter(Order.status.in_(['placed','preparing','ready','out_for_delivery'])).count(),completed=len(completed),customers=User.query.join(Role).filter(Role.name=='customer').count(),open_messages=ContactMessage.query.filter_by(is_resolved=False).count(),reservations=Reservation.query.filter(Reservation.reserved_for>=now,Reservation.status=='confirmed').count(),available_items=MenuItem.query.filter_by(is_available=True).count(),bars=[(d.strftime('%d %b'),v,round(v/peak*100)) for d,v in daily.items()],popular=popular.most_common(5),statuses=[(s,statuses[s]) for s in ORDER_STATUSES],today_revenue=daily[now.date()])


def selected_days():
    days = request.args.get("days", 7, type=int)
    return days if days in (7, 14, 30) else 7


# ---------- RestroIQ Executive Dashboard ----------
@bp.route("/")
@admin_required
def dashboard():
    stats=report_data(selected_days())
    recent=Order.query.order_by(Order.created_at.desc()).limit(8).all()
    return render_template('admin/dashboard.html',stats=stats,recent=recent,staff_on_duty=StaffMember.query.filter_by(shift_status='On Duty').limit(8).all(),statuses=ORDER_STATUSES)


# ---------- Staff & HR Management Hub ----------
@bp.route("/staff", methods=["GET", "POST"])
@admin_required
def staff():
    if request.method == "POST":
        check_csrf()
        form_type = request.form.get("form_type")
        if form_type == "new_staff":
            name = request.form.get("name", "").strip()
            role = request.form.get("role", "").strip()
            phone = request.form.get("phone", "").strip()
            email = request.form.get("email", "").strip()
            try:
                salary = float(request.form.get("salary", 2500) or 2500)
            except ValueError:
                salary = -1
            if name and len(name) <= 80 and role and len(role) <= 50 and 0 <= salary < 100000000 and (not email or valid_email(email)) and (not phone or valid_phone(phone)):
                sm = StaffMember(name=name, role=role, phone=phone, email=email,
                                 salary_monthly=salary, shift_status="On Duty",
                                 shift_hours_done=0.0, shift_hours_total=10.0)
                db.session.add(sm)
                db.session.commit()
                flash(f"Staff member {name} added successfully.", "success")
            else:
                flash("Enter valid staff details and a non-negative salary.", "error")
        elif form_type == "new_leave":
            staff_id = int(request.form.get("staff_id", 0))
            l_type = request.form.get("leave_type", "Sick Leave")
            s_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d").date()
            e_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d").date()
            reason = request.form.get("reason", "").strip()
            if staff_id and reason:
                sl = StaffLeave(staff_id=staff_id, leave_type=l_type, start_date=s_date,
                                end_date=e_date, reason=reason, status="Pending")
                db.session.add(sl)
                db.session.commit()
                flash("Leave request submitted for review.", "success")
        return redirect(url_for("admin.staff"))

    all_staff = StaffMember.query.order_by(StaffMember.name).all()
    leaves = StaffLeave.query.order_by(StaffLeave.created_at.desc()).all()
    payrolls = StaffPayroll.query.order_by(StaffPayroll.created_at.desc()).limit(15).all()
    
    total_payroll = sum(s.salary_monthly for s in all_staff)
    on_duty_count = sum(1 for s in all_staff if s.shift_status == "On Duty")
    on_leave_count = sum(1 for s in all_staff if s.shift_status == "Off Duty")
    pending_leaves = sum(1 for l in leaves if l.status == "Pending")

    return render_template("admin/staff.html",
                           all_staff=all_staff,
                           leaves=leaves,
                           payrolls=payrolls,
                           total_payroll=total_payroll,
                           on_duty_count=on_duty_count,
                           on_leave_count=on_leave_count,
                           pending_leaves=pending_leaves)


@bp.route("/staff/leave/<int:leave_id>/<string:action>", methods=["POST"])
@admin_required
def leave_action(leave_id, action):
    check_csrf()
    leave = db.session.get(StaffLeave, leave_id) or abort(404)
    if action == "approve":
        leave.status = "Approved"
        leave.staff.shift_status = "Off Duty"
        flash(f"Leave for {leave.staff.name} approved.", "success")
    elif action == "reject":
        leave.status = "Rejected"
        flash(f"Leave for {leave.staff.name} rejected.", "info")
    db.session.commit()
    return redirect(url_for("admin.staff"))


@bp.route("/staff/shift/<int:staff_id>/<string:status>", methods=["POST"])
@admin_required
def staff_shift(staff_id, status):
    check_csrf()
    sm = db.session.get(StaffMember, staff_id) or abort(404)
    if status in ("On Duty", "Off Duty", "On Break"):
        sm.shift_status = status
        db.session.commit()
        flash(f"{sm.name}'s status changed to {status}.", "success")
    return redirect(url_for("admin.staff"))


# ---------- Kitchen Display Board (KDS) ----------
@bp.route("/kitchen")
@admin_required
def kitchen():
    active_orders = Order.query.filter(Order.status.in_(["placed", "preparing", "ready"]))\
        .order_by(Order.created_at.asc()).all()
    lanes = {s: [o for o in active_orders if o.status == s] for s in ["placed", "preparing", "ready"]}
    return render_template("admin/kitchen.html", stages=lanes.items())


# ---------- Table Bookings & Floorplan ----------
@bp.route("/tables")
@admin_required
def tables():
    now = utcnow()
    upcoming = Reservation.query.filter(Reservation.reserved_for >= now)\
        .order_by(Reservation.reserved_for.asc()).all()
    all_tables = DiningTable.query.order_by(DiningTable.seats.asc()).all()
    return render_template("admin/tables.html", reservations=upcoming, tables=all_tables)


# ---------- POS Order Workspace ----------
@bp.route("/orders")
@admin_required
def orders():
    status = request.args.get("status", "")
    query = Order.query
    if status in ORDER_STATUSES:
        query = query.filter_by(status=status)
    q = request.args.get("q", "").strip()[:100]
    if q:
        query = query.filter(or_(Order.customer_name.ilike(f"%{q}%"), Order.customer_phone.ilike(f"%{q}%")))
    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=max(1, request.args.get("page", 1, type=int)), per_page=20, error_out=False
    )
    return render_template("admin/orders.html", pagination=pagination, recent=pagination.items,
                           statuses=ORDER_STATUSES, selected=status, q=q)


@bp.route("/orders/export")
@admin_required
def export_orders():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Order ID", "Created UTC", "Customer", "Phone", "Type", "Status", "Subtotal", "Discount", "Total"])
    for o in Order.query.order_by(Order.created_at.desc()).all():
        writer.writerow([o.id, o.created_at.isoformat(), o.customer_name, o.customer_phone,
                         o.order_type, o.status, o.subtotal, o.discount, o.total])
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=restroiq-orders.csv"})


# ---------- Sales & Revenue Intelligence ----------
@bp.route("/analytics")
@admin_required
def analytics():
    return render_template("admin/analytics.html", stats=report_data(selected_days()))


# ---------- Data Directory (All 50 Tables) ----------
@bp.route("/directory")
@admin_required
def directory():
    counts = {name: model.query.count() for name, model in registry().items()}
    return render_template("admin/directory.html", tables=sorted(counts.items()))


@bp.route("/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def order_status(order_id):
    check_csrf()
    order = db.session.get(Order, order_id) or abort(404)
    status = request.form.get("status")
    if status not in ORDER_STATUSES:
        abort(400)
    from ..operations import transition, BusinessError
    try:
        transition(order,status,current_user()); db.session.commit(); flash('Order updated.','success')
    except BusinessError as exc:
        db.session.rollback(); flash(str(exc),'error')
    return redirect(url_for('admin.orders'))


# ---------- Generic CRUD for All 50 Tables ----------
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
    if table in PROTECTED: abort(403)
    model = get_model(table)
    fields = describe_fields(model)
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
    if table in PROTECTED: abort(403)
    model = get_model(table)
    obj = row_key(model, request.args)
    fields = [f for f in describe_fields(model) if not f["col"].primary_key]
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
    if table in PROTECTED: abort(403)
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


@bp.route("/staff/messages", methods=["GET", "POST"])
@admin_required
def staff_messages():
    if request.method == "POST":
        check_csrf()
        staff = db.session.get(StaffMember, request.form.get("staff_id", type=int) or 0)
        subject, body = request.form.get("subject", "").strip(), request.form.get("body", "").strip()
        if not staff or not staff.user_id or not 1 <= len(subject) <= 120 or not 1 <= len(body) <= 2000:
            flash("Select a staff member with a linked account and enter a valid subject and message.", "error")
        else:
            db.session.add(StaffMessage(staff_id=staff.id, sender_id=current_user().id, subject=subject, body=body))
            db.session.commit()
            flash("Message delivered to the staff inbox.", "success")
        return redirect(url_for("admin.staff_messages"))
    staff = StaffMember.query.order_by(StaffMember.name).all()
    return render_template("admin/staff_messages.html", staff=staff, selected=request.args.get("staff_id", type=int), messages=StaffMessage.query.order_by(StaffMessage.created_at.desc()).limit(100).all())
