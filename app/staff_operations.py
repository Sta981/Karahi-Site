"""Small, reusable operations for staff workspaces; caller owns transaction."""
from datetime import timedelta
from decimal import Decimal
from .extensions import db
from .models import (Order, OrderItem, OrderItemModifier, OrderStatusHistory, MenuItem, DiningTable,
                     Reservation, Ingredient, PurchaseOrderItem, Payment, PaymentMethod, StockBatch, utcnow)
from .operations import BusinessError, amount, audit
ACTIVE = ('placed', 'preparing', 'ready', 'out_for_delivery')


def table_state(table, now=None):
    now = now or utcnow()
    order = Order.query.filter(Order.table_id == table.id, Order.status.in_(ACTIVE)).first()
    reservation = Reservation.query.filter(Reservation.table_id == table.id, Reservation.status == 'confirmed',
        Reservation.reserved_for < now + timedelta(hours=2)).order_by(Reservation.reserved_for).all()
    reserved = next((r for r in reservation if (r.ends_at or r.reserved_for + timedelta(hours=2)) > now), None)
    return ('occupied', order) if order else ('reserved', reserved) if reserved else ('available', None)


def create_table_order(table_id, ids, quantities, notes, actor):
    if not 1 <= len(ids) <= 20 or len(ids) != len(quantities) or len(notes) != len(ids):
        raise BusinessError('Add between 1 and 20 complete dish lines.')
    table = db.session.get(DiningTable, table_id)
    if not table: raise BusinessError('Choose a table.')
    DiningTable.query.filter_by(id=table.id).update({DiningTable.seats: DiningTable.seats}, synchronize_session=False)
    if table_state(table)[0] != 'available': raise BusinessError('Table occupied or reserved within the next two hours.')
    order = Order(table_id=table.id, waiter_id=actor.id, order_type='dine_in', status='placed', customer_name=f'Table {table.label}', customer_phone='', subtotal=0, discount=0, delivery_fee=0, total=0)
    total=Decimal('0.00')
    for raw_id, raw_qty, raw_note in zip(ids, quantities, notes):
        item=db.session.get(MenuItem, int(raw_id)); qty=int(raw_qty); note=raw_note.strip()
        if not item or not item.is_available or not 1<=qty<=50 or len(note)>54:
            raise BusinessError('Use available dishes, quantities 1–50, and notes up to 54 characters.')
        price=amount(item.effective_price); total+=price*qty
        line=OrderItem(item_id=item.id,name=item.name,unit_price=float(price),quantity=qty)
        if note: line.modifiers.append(OrderItemModifier(name='Note: '+note,extra_price=0))
        order.items.append(line)
    order.subtotal=order.total=float(total)
    order.history.append(OrderStatusHistory(status='placed',actor_id=actor.id))
    db.session.add(order);db.session.flush();audit(actor,'order.created','orders',order.id)
    from .operations import notify_roles
    notify_roles(('chef',),f'New kitchen order #{order.id} · {table.label}')
    return order


def purchase_lines(ids, quantities, costs):
    if not 1<=len(ids)<=20 or len(ids)!=len(quantities) or len(ids)!=len(costs):
        raise BusinessError('Add between 1 and 20 complete ingredient lines.')
    seen=set(); rows=[]
    for raw, q, c in zip(ids,quantities,costs):
        iid=int(raw)
        if iid in seen or not db.session.get(Ingredient,iid): raise BusinessError('Choose distinct, valid ingredients.')
        seen.add(iid);rows.append(PurchaseOrderItem(ingredient_id=iid,quantity=amount(q,'0.001','0.001'),unit_cost=amount(c)))
    return rows


def cash_summary(row):
    q=Payment.query.join(PaymentMethod).filter(Payment.received_by==row.cashier_id,Payment.status=='paid',Payment.created_at>=row.opened_at)
    if row.closed_at: q=q.filter(Payment.created_at<=row.closed_at)
    cash=sum((amount(p.amount) for p in q.all() if 'cash' in p.method.name.lower() or p.method.name.lower()=='pay at counter'),Decimal('0.00'))
    expected=row.opening_balance+cash
    return dict(cash=cash,expected=expected,variance=(row.closing_balance-expected) if row.closing_balance is not None else None)


def ingredient_balance(ingredient, today):
    rows=StockBatch.query.filter_by(ingredient_id=ingredient.id).all()
    return sum((b.remaining for b in rows if not b.expires_on or b.expires_on>=today),Decimal('0'))
