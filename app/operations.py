"""Transactional restaurant operations shared by the management interfaces."""
from datetime import date
from sqlalchemy import or_
from decimal import Decimal, InvalidOperation
from .extensions import db
from .models import (AuditLog, Order, OrderStatusHistory, Payment, ItemIngredient, StockBatch, StockMovement, LoyaltyAccount, LoyaltyTransaction, Notification, Role, User, utcnow)

class BusinessError(ValueError):
    pass

def amount(raw, scale='0.01', minimum=0):
    try:
        value = Decimal(str(raw)).quantize(Decimal(scale))
        if not value.is_finite() or value < Decimal(str(minimum)) or value > Decimal('99999999'):
            raise ValueError
        return value
    except (InvalidOperation, ValueError, TypeError):
        raise BusinessError('Enter a valid non-negative amount.')

def audit(actor, action, entity, entity_id):
    db.session.add(AuditLog(actor_id=actor.id, action=action, entity=entity, entity_id=entity_id))

def notify_user(uid, message):
    if uid and db.session.get(User, uid):
        db.session.add(Notification(user_id=uid, message=message[:255], is_read=False))


def notify_roles(roles, message):
    for user in User.query.join(Role).filter(Role.name.in_(roles), User.is_active.is_(True)).all():
        notify_user(user.id, message)


def paid_total(order):
    return sum((amount(p.amount) for p in order.payments if p.status == 'paid'), Decimal('0.00'))

def due(order):
    return max(Decimal('0.00'), amount(order.total)-paid_total(order))

def consume_recipe(order, actor):
    needs = {}
    for line in order.items:
        if not line.item_id:
            continue
        for recipe in ItemIngredient.query.filter_by(item_id=line.item_id).all():
            if recipe.quantity > 0:
                needs[recipe.ingredient_id] = needs.get(recipe.ingredient_id, Decimal('0')) + recipe.quantity * line.quantity
    for ingredient, needed in sorted(needs.items()):
        batches = StockBatch.query.filter(StockBatch.ingredient_id == ingredient, StockBatch.remaining > 0,
            or_(StockBatch.expires_on.is_(None), StockBatch.expires_on >= date.today())).order_by(StockBatch.expires_on.asc().nulls_last(), StockBatch.id).all()
        for batch in batches:
            take = min(needed, batch.remaining)
            if take <= 0: continue
            changed = StockBatch.query.filter(StockBatch.id == batch.id, StockBatch.remaining >= take).update({StockBatch.remaining: StockBatch.remaining-take}, synchronize_session=False)
            if changed != 1: raise BusinessError('Stock changed. Retry the operation.')
            db.session.add(StockMovement(batch_id=batch.id, order_id=order.id, actor_id=actor.id, quantity=-take, reason='recipe'))
            needed -= take
            if needed == 0: break
        if needed > 0: raise BusinessError('Insufficient unexpired stock for this recipe.')

def transition(order, target, actor):
    allowed = {'placed': {'preparing','cancelled'}, 'preparing': {'ready'}, 'ready': {'completed','out_for_delivery'}, 'out_for_delivery': {'completed'}}
    old = order.status
    if target not in allowed.get(old, set()): raise BusinessError('That order transition is not allowed.')
    if target == 'cancelled' and paid_total(order) > 0: raise BusinessError('Paid orders require a refund process before cancellation.')
    if target == 'completed' and due(order) > 0: raise BusinessError('Payment must be recorded before closing the order.')
    changed = Order.query.filter_by(id=order.id, status=old).update({'status':target}, synchronize_session=False)
    if changed != 1: raise BusinessError('Order changed. Refresh and try again.')
    if target == 'preparing': consume_recipe(order, actor)
    if target == 'completed' and order.user and order.user.role.name == 'customer':
        account = order.user.loyalty
        if account and not LoyaltyTransaction.query.filter_by(order_id=order.id, reason='Completed paid order').first():
            points = max(1, int(amount(order.total) // Decimal('100')))
            LoyaltyAccount.query.filter_by(id=account.id).update({LoyaltyAccount.points: LoyaltyAccount.points + points}, synchronize_session=False)
            db.session.add(LoyaltyTransaction(account_id=account.id, order_id=order.id, points=points, reason='Completed paid order'))
    db.session.add(OrderStatusHistory(order_id=order.id, status=target, actor_id=actor.id))
    audit(actor, 'order.'+target, 'orders', order.id)
    if target == 'ready':
        notify_user(order.waiter_id, f'Order #{order.id} is ready to serve.')
        notify_roles(('cashier',), f'Order #{order.id} is ready for billing.')
    if target in ('preparing','ready','completed','out_for_delivery'):
        notify_user(order.user_id, f'Order #{order.id}: {target.replace("_", " ")}.')

def record_payment(order, method, raw, actor):
    # Serialize payment writes by acquiring the order row; SQLite serializes writes.
    Order.query.filter_by(id=order.id).update({Order.status:Order.status}, synchronize_session=False)
    db.session.expire(order, ['payments','status'])
    value = amount(raw, minimum='0.01')
    if order.status in ('cancelled','completed') or value > due(order): raise BusinessError('Payment exceeds outstanding balance or order is closed.')
    pending = next((p for p in order.payments if p.status == 'pending'), None)
    if pending and value == due(order):
        pending.method_id, pending.amount, pending.status, pending.received_by = method.id, float(value), 'paid', actor.id
        pending.created_at = utcnow()
    else:
        db.session.add(Payment(order_id=order.id, method_id=method.id, amount=float(value), status='paid', received_by=actor.id))
    audit(actor, 'payment.recorded', 'orders', order.id)
    notify_user(order.waiter_id, f'Payment recorded for order #{order.id}: {value}.')
    notify_user(order.user_id, f'Payment recorded for order #{order.id}: {value}.')
