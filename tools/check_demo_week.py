"""Isolated model and demo dataset verification. No Flask dependency or live DB required."""
import sys, types
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, relationship, backref, configure_mappers, scoped_session, sessionmaker
from decimal import Decimal
root=Path(__file__).resolve().parents[1]
pkg=types.ModuleType('app');pkg.__path__=[str(root/'app')];sys.modules['app']=pkg
ext=types.ModuleType('app.extensions'); Base=declarative_base();db=types.SimpleNamespace(Model=Base,relationship=relationship,backref=backref)
for name in ['Column','Integer','String','Text','Boolean','Float','Numeric','Date','DateTime','ForeignKey','UniqueConstraint','CheckConstraint','Table']:setattr(db,name,getattr(sa,name))
ext.db=db;sys.modules['app.extensions']=ext
# Stubs only for isolated seed test; actual application still uses Werkzeug.
try: import werkzeug.security
except ImportError:
    w=types.ModuleType('werkzeug');w.__path__=[];s=types.ModuleType('werkzeug.security');s.generate_password_hash=lambda v:'TEST-ONLY-HASH';sys.modules['werkzeug']=w;sys.modules['werkzeug.security']=s
if 'flask' not in sys.modules:
    try: import flask
    except ImportError:
        f=types.ModuleType('flask');f.abort=f.redirect=f.url_for=lambda *a,**kw:None;sys.modules['flask']=f
import app.models as m
from app.seed import seed_if_empty
from app.access import seed_access
from app.demo_week import seed_week
configure_mappers();engine=sa.create_engine('sqlite:///:memory:')
@sa.event.listens_for(engine,'connect')
def fk(c,r):c.execute('PRAGMA foreign_keys=ON')
Base.metadata.create_all(engine);session=scoped_session(sessionmaker(bind=engine));Base.query=session.query_property();db.session=session
seed_if_empty();seed_access();assert seed_week() is True; assert seed_week() is False
assert m.Order.query.count()==56
assert m.Payment.query.filter_by(status='paid').count()==52
assert len({o.created_at.date() for o in m.Order.query.all()})==7
assert m.StaffMember.query.count()==7
assert all(s.phone and s.salary_monthly>0 and s.user_id for s in m.StaffMember.query.all())
assert m.CashSession.query.count()==7
assert m.PurchaseOrder.query.count()==7
assert m.Reservation.query.count()==26
assert m.StaffMessage.query.count()==13
assert m.ContactMessage.query.count()==12
assert m.User.query.join(m.Role).filter(m.Role.name=='customer').count()==12
for a in m.LoyaltyAccount.query.all():assert a.points==sum(t.points for t in a.transactions)>0
for b in m.StockBatch.query.all():assert b.remaining==sum(x.quantity for x in m.StockMovement.query.filter_by(batch_id=b.id).all())>=0
for o in m.Order.query.all():
    assert abs(o.total-(o.subtotal-o.discount+o.delivery_fee))<.001
    assert abs(o.subtotal-sum(i.quantity*i.unit_price for i in o.items))<.001
    if o.status=='completed':assert abs(o.total-sum(p.amount for p in o.payments if p.status=='paid'))<.001
    assert o.created_at<=m.utcnow()
with engine.connect() as c:assert c.exec_driver_sql('PRAGMA foreign_key_check').fetchall()==[]
for t in Base.metadata.sorted_tables:
    count=session.execute(sa.select(sa.func.count()).select_from(t)).scalar_one();print(f'{t.name}: {count}')
print('PASS: seven days, 56 orders, 52 paid, 7 staff, 26 reservations, 7 purchases, 13 messages, 7 cash sessions, loyalty reconciliation, stock reconciliation, foreign keys, repeat-run guard')
