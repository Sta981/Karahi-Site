import sys,types,importlib.util
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy.orm import declarative_base,relationship,backref,configure_mappers,sessionmaker
root=Path.cwd();pkg=types.ModuleType('app');pkg.__path__=[str(root/'app')];sys.modules['app']=pkg
ext=types.ModuleType('app.extensions'); Base=declarative_base(); db=types.SimpleNamespace(Model=Base,relationship=relationship,backref=backref)
for name in ['Column','Integer','String','Text','Boolean','Float','Numeric','Date','DateTime','ForeignKey','UniqueConstraint','CheckConstraint','Table']:
 setattr(db,name,getattr(sa,name))
ext.db=db;sys.modules['app.extensions']=ext
import app.models as m
configure_mappers();engine=sa.create_engine('sqlite:///:memory:')
@sa.event.listens_for(engine,'connect')
def fk(c,r):c.execute('PRAGMA foreign_keys=ON')
Base.metadata.create_all(engine); db.session=sessionmaker(bind=engine)();Base.query=db.session.query_property() if hasattr(db.session,'query_property') else None
# scoped_session supplies Flask-like query property for domain services
from sqlalchemy.orm import scoped_session
session=scoped_session(sessionmaker(bind=engine)); Base.query=session.query_property();db.session=session
from app.operations import transition,record_payment,due,BusinessError
from decimal import Decimal
r=m.Role(name='owner');u=m.User(name='Test',email='test@local.test',password_hash='test',role=r);cat=m.Category(name='Food',slug='food');item=m.MenuItem(name='Dish',category=cat,price=10);ing=m.Ingredient(name='Chicken');method=m.PaymentMethod(name='Cash');session.add_all([u,item,ing,method]);session.flush();session.add(m.ItemIngredient(item_id=item.id,ingredient_id=ing.id,quantity=Decimal('0.5')));batch=m.StockBatch(ingredient_id=ing.id,remaining=Decimal('5'),unit_cost=Decimal('3'));o=m.Order(order_type='pickup',status='placed',customer_name='Guest',customer_phone='',subtotal=20,total=20);o.items.append(m.OrderItem(item_id=item.id,name='Dish',unit_price=10,quantity=2));session.add_all([o,batch]);session.commit();
transition(o,'preparing',u);session.commit();assert batch.remaining==Decimal('4');assert m.StockMovement.query.count()==1
try:transition(o,'preparing',u);raise AssertionError('duplicate transition accepted')
except BusinessError:session.rollback()
transition(o,'ready',u);session.commit()
try:transition(o,'completed',u);raise AssertionError('unpaid order closed')
except BusinessError:session.rollback()
record_payment(o,method,'7',u);session.commit();assert due(o)==Decimal('13')
try:record_payment(o,method,'14',u);raise AssertionError('overpayment accepted')
except BusinessError:session.rollback()
record_payment(o,method,'13',u);session.commit();assert due(o)==0;transition(o,'completed',u);session.commit();assert o.status=='completed'
# relationship graph
metadata=Base.metadata;tables=metadata.tables; edges=[(t.name,fk.column.table.name) for t in tables.values() for fk in t.foreign_keys];seen={'users'}
while True:
 new=seen|{b for a,b in edges if a in seen}|{a for a,b in edges if b in seen}
 if new==seen:break
 seen=new
print(f'{len(tables)} models, {len(edges)} FK declarations, {len(seen)} connected tables; mappers, SQLite DDL, recipe deduction, duplicate transition rejection, unpaid close rejection, partial payment, overpayment rejection, paid close PASS')
# export exact column-level Mermaid ERD and data dictionary
lines=['# Detailed database ERD','','Generated from actual SQLAlchemy model metadata. Mermaid supports zoom/rendering in compatible Markdown viewers. Each relationship is derived from a foreign key; unique FKs are one-to-one at most.','','```mermaid','erDiagram']
for t in sorted(tables.values(),key=lambda x:x.name):
 lines.append('    '+t.name+' {')
 for col in t.columns:
  kind=type(col.type).__name__.lower(); flags=','.join(x for x in ['PK' if col.primary_key else '', 'FK' if col.foreign_keys else '', 'UK' if col.unique else ''] if x)
  lines.append(f'        {kind} {col.name}'+(f' {flags}' if flags else ''))
 lines.append('    }')
for t in sorted(tables.values(),key=lambda x:x.name):
 for fk in sorted(t.foreign_keys,key=lambda f:f.parent.name):
  c=fk.parent;lines.append(f'    {fk.column.table.name} {"|o" if c.nullable else "||"}--{"o|" if c.unique else "o{"} {t.name} : {c.name}')
lines.append('```');(root/'docs/ERD.md').write_text('\n'.join(lines))
lines=['# Database dictionary','','| Table | Column | Type | Required | Key / reference |','|---|---|---|---|---|']
for t in sorted(tables.values(),key=lambda x:x.name):
 for c in t.columns:
  refs=', '.join(f.target_fullname for f in c.foreign_keys); flags='; '.join(x for x in ['PK' if c.primary_key else '', 'Unique' if c.unique else '',refs] if x)
  lines.append(f'| {t.name} | {c.name} | {c.type} | {"No" if c.nullable else "Yes"} | {flags} |')
(root/'docs/DATABASE_DICTIONARY.md').write_text('\n'.join(lines))
