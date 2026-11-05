from datetime import date, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, session, url_for

from ..extensions import db
from ..models import (Address, CartItem, CartItemModifier, Coupon, CouponUsage, Delivery,
                      DeliveryZone, Favorite, LoyaltyTransaction, MenuItem, ModifierOption,
                      Notification, Order, OrderItem, OrderItemModifier, OrderStatusHistory,
                      Payment, PaymentMethod, Review, ReviewReply)
from ..utils import (check_csrf, current_cart, current_user, login_required, valid_phone, valid_zip)

bp = Blueprint("shop", __name__)


# ---------- Cart ----------
@bp.route("/cart")
def cart_view():
    return render_template("shop/cart.html", cart=current_cart(create=False))


@bp.route("/cart/add/<int:item_id>", methods=["POST"])
def cart_add(item_id):
    check_csrf()
    item = db.session.get(MenuItem, item_id) or abort(404)
    if not item.is_available:
        flash(f"{item.name} is unavailable right now.", "warning")
        return redirect(url_for("main.menu"))
    try:
        qty = int(request.form.get("quantity", 1))
        if not 1 <= qty <= 20:
            raise ValueError
    except ValueError:
        flash("Quantity must be between 1 and 20.", "error")
        return redirect(url_for("main.item_detail", item_id=item.id))

    option_ids = [int(x) for x in request.form.getlist("options") if x.isdigit()]
    options = ModifierOption.query.filter(ModifierOption.id.in_(option_ids)).all() if option_ids else []
    allowed = {g.id: g for g in item.modifier_groups}
    for group in item.modifier_groups:
        picked = [o for o in options if o.group_id == group.id]
        if group.is_required and not picked:
            flash(f"Choose an option for {group.name}.", "error")
            return redirect(url_for("main.item_detail", item_id=item.id))
        if not group.allow_multiple and len(picked) > 1:
            flash(f"Pick only one {group.name.lower()}.", "error")
            return redirect(url_for("main.item_detail", item_id=item.id))
    if any(o.group_id not in allowed for o in options):
        abort(400)

    cart = current_cart()
    line = CartItem(cart=cart, item=item, quantity=qty, note=request.form.get("note", "").strip()[:200])
    line.modifiers = [CartItemModifier(option=o) for o in options]
    db.session.add(line)
    db.session.commit()
    flash(f"Added {qty} × {item.name} to your cart.", "success")
    return redirect(url_for("main.menu"))


@bp.route("/cart/update/<int:line_id>", methods=["POST"])
def cart_update(line_id):
    check_csrf()
    cart = current_cart(create=False) or abort(404)
    line = CartItem.query.filter_by(id=line_id, cart_id=cart.id).first() or abort(404)
    try:
        qty = int(request.form.get("quantity", 1))
        if not 1 <= qty <= 20:
            raise ValueError
        line.quantity = qty
        db.session.commit()
    except ValueError:
        flash("Quantity must be between 1 and 20.", "error")
    return redirect(url_for("shop.cart_view"))


@bp.route("/cart/remove/<int:line_id>", methods=["POST"])
def cart_remove(line_id):
    check_csrf()
    cart = current_cart(create=False) or abort(404)
    line = CartItem.query.filter_by(id=line_id, cart_id=cart.id).first() or abort(404)
    db.session.delete(line)
    db.session.commit()
    flash("Item removed.", "info")
    return redirect(url_for("shop.cart_view"))


# ---------- Checkout ----------
def _discount(coupon_code, subtotal):
    """Return (coupon, discount, error)."""
    if not coupon_code:
        return None, 0.0, None
    coupon = Coupon.query.filter(Coupon.code.ilike(coupon_code), Coupon.is_active.is_(True)).first()
    if not coupon:
        return None, 0.0, "Coupon code not found."
    if coupon.expires_on and coupon.expires_on < date.today():
        return None, 0.0, "That coupon has expired."
    if subtotal < (coupon.min_subtotal or 0):
        return None, 0.0, f"Coupon needs a ${coupon.min_subtotal:.2f} minimum order."
    return coupon, round(subtotal * coupon.percent_off / 100, 2), None


@bp.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = current_cart(create=False)
    if not cart or not cart.items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("main.menu"))
    user = current_user()
    order_type = session.get("order_type", "pickup")
    form, errors = {}, {}
    if request.method == "GET" and user:
        form = {"name": user.name, "phone": user.phone or ""}
    if request.method == "POST":
        check_csrf()
        form = {k: request.form.get(k, "").strip() for k in
                ("name", "phone", "street", "zip_code", "coupon", "payment_method")}
        if len(form["name"]) < 2:
            errors["name"] = "Enter your name."
        if not valid_phone(form["phone"]):
            errors["phone"] = "Enter a valid phone number."
        zone, fee = None, 0.0
        if order_type == "delivery":
            if len(form["street"]) < 5:
                errors["street"] = "Enter your street address."
            if not valid_zip(form["zip_code"]):
                errors["zip_code"] = "Enter a 5-digit ZIP code."
            else:
                zone = DeliveryZone.query.filter_by(zip_code=form["zip_code"]).first()
                if not zone:
                    errors["zip_code"] = "We don't deliver to that ZIP yet. Choose pickup instead."
                else:
                    fee = zone.fee
        method = db.session.get(PaymentMethod, int(form["payment_method"])) if form["payment_method"].isdigit() else None
        if not method or not method.is_active:
            errors["payment_method"] = "Choose a payment method."
        coupon, discount, coupon_error = _discount(form["coupon"], cart.subtotal)
        if coupon_error:
            errors["coupon"] = coupon_error

        if not errors:
            total = round(cart.subtotal - discount + fee, 2)
            order = Order(user_id=user.id if user else None, coupon=coupon, order_type=order_type,
                          customer_name=form["name"], customer_phone=form["phone"],
                          subtotal=cart.subtotal, discount=discount, delivery_fee=fee, total=total)
            for line in cart.items:
                oi = OrderItem(item_id=line.item_id, name=line.item.name,
                               unit_price=line.unit_price, quantity=line.quantity)
                oi.modifiers = [OrderItemModifier(name=m.option.name, extra_price=m.option.extra_price)
                                for m in line.modifiers]
                order.items.append(oi)
            order.history.append(OrderStatusHistory(status="placed"))
            order.payment = Payment(method=method, amount=total,
                                    status="paid" if method.name != "Pay at counter" else "pending")
            if order_type == "delivery":
                order.delivery = Delivery(zone=zone, street=form["street"], zip_code=form["zip_code"])
            db.session.add(order)
            db.session.flush()
            if coupon:
                db.session.add(CouponUsage(coupon=coupon, user_id=order.user_id, order_id=order.id))
            if user and user.loyalty:
                earned = int(total)
                user.loyalty.points += earned
                db.session.add(LoyaltyTransaction(account=user.loyalty, order_id=order.id,
                                                  points=earned, reason=f"Order #{order.id}"))
                db.session.add(Notification(user_id=user.id, message=f"Order #{order.id} placed. +{earned} points."))
            db.session.delete(cart)
            db.session.commit()
            flash("Order placed. We're firing up the karahi.", "success")
            return redirect(url_for("shop.order_detail", order_id=order.id, token=_token(order)))
    coupon, discount, _ = _discount(form.get("coupon", ""), cart.subtotal)
    return render_template("shop/checkout.html", cart=cart, form=form, errors=errors, order_type=order_type,
                           methods=PaymentMethod.query.filter_by(is_active=True).all())


def _token(order):
    """Lets guest customers view their own confirmation page."""
    return f"{order.id * 7919 + 13:x}"


# ---------- Orders ----------
@bp.route("/orders")
@login_required
def orders():
    mine = Order.query.filter_by(user_id=current_user().id).order_by(Order.created_at.desc()).all()
    return render_template("shop/orders.html", orders=mine)


@bp.route("/orders/<int:order_id>")
def order_detail(order_id):
    order = db.session.get(Order, order_id) or abort(404)
    user = current_user()
    owns = user and (order.user_id == user.id or user.is_admin)
    if not owns and request.args.get("token") != _token(order):
        abort(404)
    return render_template("shop/order_detail.html", order=order)


@bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def order_cancel(order_id):
    check_csrf()
    order = Order.query.filter_by(id=order_id, user_id=current_user().id).first() or abort(404)
    if order.status != "placed":
        flash("This order is already being prepared and can't be cancelled.", "warning")
    else:
        order.status = "cancelled"
        order.history.append(OrderStatusHistory(status="cancelled"))
        db.session.commit()
        flash("Order cancelled.", "info")
    return redirect(url_for("shop.order_detail", order_id=order.id))


# ---------- Profile & addresses ----------
@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user, errors = current_user(), {}
    if request.method == "POST":
        check_csrf()
        name, phone = request.form.get("name", "").strip(), request.form.get("phone", "").strip()
        if len(name) < 2:
            errors["name"] = "Enter your name."
        if phone and not valid_phone(phone):
            errors["phone"] = "Enter a valid phone number."
        if not errors:
            user.name, user.phone = name, phone
            db.session.commit()
            flash("Profile updated.", "success")
            return redirect(url_for("shop.profile"))
    return render_template("shop/profile.html", user=user, errors=errors,
                           favorites=Favorite.query.filter_by(user_id=user.id).all())


@bp.route("/profile/addresses", methods=["POST"])
@login_required
def address_add():
    check_csrf()
    street, zip_code = request.form.get("street", "").strip(), request.form.get("zip_code", "").strip()
    if len(street) < 5 or not valid_zip(zip_code):
        flash("Enter a street address and a 5-digit ZIP code.", "error")
    else:
        db.session.add(Address(user_id=current_user().id, street=street, zip_code=zip_code,
                               label=request.form.get("label", "Home").strip()[:30] or "Home"))
        db.session.commit()
        flash("Address saved.", "success")
    return redirect(url_for("shop.profile"))


@bp.route("/profile/addresses/<int:address_id>/delete", methods=["POST"])
@login_required
def address_delete(address_id):
    check_csrf()
    addr = Address.query.filter_by(id=address_id, user_id=current_user().id).first() or abort(404)
    db.session.delete(addr)
    db.session.commit()
    flash("Address removed.", "info")
    return redirect(url_for("shop.profile"))


# ---------- Favorites ----------
@bp.route("/favorite/<int:item_id>", methods=["POST"])
@login_required
def favorite_toggle(item_id):
    check_csrf()
    db.session.get(MenuItem, item_id) or abort(404)
    uid = current_user().id
    fav = Favorite.query.filter_by(user_id=uid, item_id=item_id).first()
    if fav:
        db.session.delete(fav)
        flash("Removed from favorites.", "info")
    else:
        db.session.add(Favorite(user_id=uid, item_id=item_id))
        flash("Saved to favorites.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("main.menu"))


# ---------- Reviews (create / update / delete) ----------
def _review_form():
    try:
        rating = int(request.form.get("rating", 0))
    except ValueError:
        rating = 0
    comment = request.form.get("comment", "").strip()
    error = None
    if not 1 <= rating <= 5:
        error = "Choose a rating from 1 to 5."
    elif len(comment) > 1000:
        error = "Keep your comment under 1000 characters."
    return rating, comment, error


@bp.route("/menu/<int:item_id>/review", methods=["POST"])
@login_required
def review_save(item_id):
    check_csrf()
    item = db.session.get(MenuItem, item_id) or abort(404)
    user = current_user()
    rating, comment, error = _review_form()
    if error:
        flash(error, "error")
    else:
        review = Review.query.filter_by(user_id=user.id, item_id=item.id).first()
        if review:
            review.rating, review.comment = rating, comment
            flash("Review updated.", "success")
        else:
            db.session.add(Review(user_id=user.id, item_id=item.id, rating=rating, comment=comment))
            flash("Thanks for the review.", "success")
        db.session.commit()
    return redirect(url_for("main.item_detail", item_id=item.id))


@bp.route("/review/<int:review_id>/delete", methods=["POST"])
@login_required
def review_delete(review_id):
    check_csrf()
    review = db.session.get(Review, review_id) or abort(404)
    user = current_user()
    if review.user_id != user.id and not user.is_admin:
        abort(403)
    item_id = review.item_id
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted.", "info")
    return redirect(url_for("main.item_detail", item_id=item_id))


@bp.route("/review/<int:review_id>/reply", methods=["POST"])
@login_required
def review_reply(review_id):
    check_csrf()
    review = db.session.get(Review, review_id) or abort(404)
    body = request.form.get("body", "").strip()
    if len(body) < 2:
        flash("Write a reply first.", "error")
    else:
        db.session.add(ReviewReply(review_id=review.id, user_id=current_user().id, body=body[:500]))
        db.session.commit()
        flash("Reply posted.", "success")
    return redirect(url_for("main.item_detail", item_id=review.item_id))
