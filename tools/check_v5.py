"""Isolated real SQLAlchemy tests. Not live Flask route tests."""
import runpy
from pathlib import Path
from decimal import Decimal
from datetime import date
r=runpy.run_path(str(Path(__file__).with_name('check_demo_week.py')));m=r['m'];db=r['db']
from app.staff_operations import create_table_order,table_state,purchase_lines,cash_summary,ingredient_balance
from app.operations import transition,record_payment,due,BusinessError
user=lambda name:m.User.query.join(m.Role).filter(m.Role.name==name).first()
waiter,chef,cashier=user('waiter'),user('chef'),user('cashier')
items=m.MenuItem.query.filter_by(is_available=True).limit(2).all();table=next(t for t in m.DiningTable.query.all() if table_state(t)[0]=='available')
o=create_table_order(table.id,[str(i.id) for i in items],['2','1'],['Mild spice',''],waiter);db.session.commit();assert len(o.items)==2 and o.items[0].modifiers[0].name=='Note: Mild spice';assert table_state(table)[0]=='occupied';assert o.total==sum(x.unit_price*x.quantity for x in o.items)
assert m.Notification.query.filter_by(user_id=chef.id,message=f'New kitchen order #{o.id} · {table.label}').first()
try: create_table_order(table.id,[str(items[0].id)],['1'],[''],waiter);raise AssertionError('duplicate table accepted')
except BusinessError:db.session.rollback()
transition(o,'preparing',chef);db.session.commit();transition(o,'ready',chef);db.session.commit();assert m.Notification.query.filter_by(user_id=waiter.id,message=f'Order #{o.id} is ready to serve.').first()
method=m.PaymentMethod.query.filter_by(name='Cash / counter').one();value=Decimal(str(o.total));record_payment(o,method,'100',cashier);db.session.commit();assert due(o)==value-100;record_payment(o,method,str(value-100),cashier);db.session.commit();transition(o,'completed',waiter);db.session.commit();assert table_state(table)[0]=='available'
rows=m.Ingredient.query.limit(2).all();lines=purchase_lines([str(i.id) for i in rows],['2','3'],['100','200']);assert len(lines)==2 and sum(l.quantity*l.unit_cost for l in lines)==800
try:purchase_lines([str(rows[0].id)]*2,['1','1'],['1','1']);raise AssertionError('duplicate ingredient accepted')
except BusinessError:pass
for row in m.CashSession.query.filter(m.CashSession.closed_at.is_not(None)).all(): assert cash_summary(row)['variance']==0
for b in m.StockBatch.query.all():assert b.remaining==sum(x.quantity for x in m.StockMovement.query.filter_by(batch_id=b.id).all())>=0
print('PASS V5: multi-dish order, note, totals, occupied-table rejection, kitchen/waiter notifications, split payment, table release, multi-line purchase, duplicate ingredient rejection, closed cash reconciliation, stock ledger')
