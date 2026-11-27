"""Synthetic seven-day demonstration only. Never import into a populated business DB."""
from datetime import timedelta, datetime, time
from decimal import Decimal
from werkzeug.security import generate_password_hash
import os
from .extensions import db
from .models import *
from .operations import audit


def seed_week():
    if Coupon.query.filter_by(code='WEEK7').first():
        return False
    if Order.query.first() or StaffMember.query.first():
        return False  # never overwrite an existing V2 demo or business dataset
    now=utcnow(); today=now.date(); first=today-timedelta(days=6)
    def at(day,hour=0,minute=0): return datetime.combine(day,time(hour,minute))
    def phone(i): return f'03XX-000-{i:04d}'  # intentionally non-dialable synthetic number
    def add(obj): db.session.add(obj); return obj
    roles={r.name:r for r in Role.query.all()}
    if 'admin' in roles and not User.query.filter_by(role_id=roles['admin'].id).first():
        db.session.delete(roles['admin'])
    owner=User.query.filter_by(email='admin@karahihouse.test').one(); owner.name='Tahir Abbas'; owner.phone=phone(1)
    if owner.loyalty: db.session.delete(owner.loyalty)
    # The base catalog is priced in USD; this fresh demonstration database is PKR.
    for i in MenuItem.query.all(): i.price=round(i.price*100/50)*50
    for o in ModifierOption.query.all(): o.extra_price=round(o.extra_price*100/50)*50
    for c in Combo.query.all(): c.price=round(c.price*100/50)*50
    for p in PromotionItem.query.all(): p.promo_price=round(p.promo_price*100/50)*50
    for c in Coupon.query.all(): c.min_subtotal=(c.min_subtotal or 0)*100
    store=StoreInfo.query.first(); store.street='Demo Branch, Gulberg'; store.city='Lahore'; store.zip_code='54660'; store.phone=phone(2)
    for h in store.holidays: h.reason='Scheduled restaurant closure'
    for z,(name,zip_) in zip(DeliveryZone.query.order_by(DeliveryZone.id).all(), [('Gulberg','54660'),('DHA','54792'),('Model Town','54700'),('Johar Town','54782'),('Cantt','54810')]): z.name=name; z.zip_code=zip_; z.fee=250
    for s,name in zip(Supplier.query.order_by(Supplier.id).all(),['Punjab Spice Traders','Lahore Fresh Foods']): s.name=name; s.phone=phone(100+s.id)
    for d in DeliveryDriver.query.all(): d.phone=phone(200+d.id)
    method=PaymentMethod.query.filter_by(name='Pay at counter').one(); method.name='Cash / counter'
    other=PaymentMethod.query.filter_by(name='Credit / debit card').one()
    mobile=PaymentMethod.query.filter_by(name='Apple Pay').one(); mobile.name='Bank transfer'
    coupon=add(Coupon(code='WEEK7',percent_off=10,min_subtotal=1500,expires_on=today+timedelta(days=21)))
    menu={i.name:i for i in MenuItem.query.all()}; dishes=list(menu.values())
    promo=add(Promotion(title='Family Dining Deal',description='Enjoy a special price on our signature biryani.',starts_on=first,ends_on=today+timedelta(days=14)))
    promo.items.append(PromotionItem(item=menu['Chicken Biryani'],promo_price=1500))
    combo=add(Combo(name='BBQ Family Platter',price=3450)); combo.items.extend([ComboItem(item=menu['Chicken Tikka'],quantity=1),ComboItem(item=menu['Seekh Kebab'],quantity=1),ComboItem(item=menu['Plain Naan'],quantity=2)])
    # Employees retain the published demo login addresses and passwords.
    staff={}; people={}
    roster=[('manager','Ali Abbas',85000),('chef','Ahmed Raza',65000),('waiter','Tayyab Khan',42000),('cashier','Fatima Noor',48000),('inventory','Eman Malik',52000),('chef','Hassan Bilal',52000),('waiter','Rameesha Ahmed',40000)]
    for idx,(role,name,salary) in enumerate(roster):
        email=f'{role}@restroiq.test' if role not in staff else f'{name.split()[0].lower()}@restroiq.test'
        u=add(User(name=name,email=email,phone=phone(10+idx),role=roles[role],password_hash=generate_password_hash(os.environ.get("DEMO_STAFF_PASSWORD", "DemoStaff123!")),created_at=at(first)-timedelta(days=120)))
        db.session.flush(); p=add(StaffMember(user_id=u.id,name=name,role=role,email=email,phone=u.phone,salary_monthly=salary,shift_status='Off Duty',shift_hours_done=8,shift_hours_total=8,joined_date=first-timedelta(days=120)))
        db.session.flush(); people[email]=p
        if role not in staff: staff[role]=p
        if role!='manager': p.manager_id=staff['manager'].id
        for day in (first+timedelta(days=i) for i in range(7)):
            start=at(day,10); end=at(day,18)
            add(StaffShift(staff_id=p.id,starts_at=start,ends_at=end))
            if end<now: add(AttendanceRecord(staff_id=p.id,clock_in=start,clock_out=end))
            elif start<now: add(AttendanceRecord(staff_id=p.id,clock_in=start)); p.shift_status='On Duty'; p.shift_hours_done=round((now-start).total_seconds()/3600,1)
        month=first.replace(day=1)-timedelta(days=1)
        add(StaffPayroll(staff_id=p.id,month=month.strftime('%B'),year=month.year,base_salary=salary,bonus=1500,deductions=0,net_salary=salary+1500,payment_status='Paid'))
    manager=staff['manager'].user; chef=staff['chef'].user; waiter=staff['waiter'].user; cashier=staff['cashier'].user; inventory=staff['inventory'].user
    add(StaffLeave(staff_id=staff['waiter'].id,leave_type='Casual Leave',start_date=today+timedelta(days=3),end_date=today+timedelta(days=3),reason='Family event',status='Pending'))
    add(StaffLeave(staff_id=staff['chef'].id,leave_type='Annual Leave',start_date=today+timedelta(days=8),end_date=today+timedelta(days=9),reason='Planned leave',status='Approved'))
    names=['Ayesha Khan','Tahir Ali','Ali Hamza','Abbas Shah','Fatima Zahra','Eman Aslam','Rameesha Iqbal','Ahmed Hassan','Tayyab Ali','Bilal Tariq','Zainab Noor','Hira Malik']
    customers=[]; zones=DeliveryZone.query.order_by(DeliveryZone.id).all(); drivers=DeliveryDriver.query.all(); tables=DiningTable.query.order_by(DiningTable.id).all()
    for idx,name in enumerate(names):
        u=User.query.filter_by(email='ayesha@example.com').one() if idx==0 else add(User(name=name,email=f'{name.split()[0].lower()}{idx}@example.test',role=roles['customer'],password_hash=generate_password_hash(os.environ.get("DEMO_CUSTOMER_PASSWORD", "Customer123"))))
        u.name=name; u.phone=phone(30+idx); u.created_at=at(first)-timedelta(days=30)
        if not u.loyalty: u.loyalty=LoyaltyAccount(points=0)
        u.loyalty.points=0; z=zones[idx%len(zones)]
        u.addresses.clear(); u.addresses.append(Address(label='Home',street=f'Demo address {idx+1}, {z.name}',city='Lahore',zip_code=z.zip_code))
        db.session.flush(); customers.append(u)
        add(Favorite(user_id=u.id,item_id=dishes[idx%len(dishes)].id))
        add(Notification(user_id=u.id,message='Welcome to Karahi House. Your loyalty rewards are ready.',is_read=False,created_at=at(first,8)))
    # Remove the legacy base owner's loyalty account safely (no transactions in a fresh DB).
    db.session.flush()
    ingredients=Ingredient.query.order_by(Ingredient.id).all(); batches={}
    for r in ItemIngredient.query.all(): r.quantity=Decimal('0.200')
    for i in ingredients:
        i.reorder_level=Decimal('8'); cost=Decimal(650 if i.name=='Chicken' else 1800 if i.name=='Lamb' else 220)
        b=add(StockBatch(ingredient_id=i.id,supplier_id=i.supplier_id,remaining=Decimal('80'),unit_cost=cost,expires_on=today+timedelta(days=5),created_at=at(first)-timedelta(days=1)))
        db.session.flush(); batches[i.id]=b; add(StockMovement(batch_id=b.id,actor_id=inventory.id,quantity=Decimal('80'),reason='opening stock',created_at=b.created_at))
    db.session.flush()
    # Seven calendar dates through today, with timestamps never in the future.
    cash_by_day={}; completed=[]
    for di in range(7):
        day=first+timedelta(days=di); cash_by_day[day]=Decimal('0')
        for j in range(8):
            when=at(day,10+j,5) if di<6 else now-timedelta(minutes=150-j*10)
            if when.date()!=day: when=at(day)+ (now-at(day))*((j+1)/10) if di==6 else when
            u=customers[(di*8+j)%len(customers)]; item=menu[['Chicken Karahi','Lamb Karahi','Chicken Biryani'][j%3]]; bread=menu['Garlic Naan']; qty=1+j%2
            kind=['dine_in','pickup','delivery'][j%3]; status='completed' if di<6 or j<4 else ['placed','preparing','ready','ready'][j-4]
            sub=round(item.effective_price*qty+bread.price*2,2); disc=round(sub*.1,2) if j%4==0 else 0; fee=250 if kind=='delivery' else 0
            # Active dine-in tickets occupy distinct tables; no duplicate assignment.
            o=add(Order(user_id=u.id,order_type=kind,status=status,customer_name=u.name,customer_phone=u.phone,table_id=tables[j%len(tables)].id if kind=='dine_in' else None,waiter_id=waiter.id if kind=='dine_in' else None,subtotal=sub,discount=disc,delivery_fee=fee,total=sub-disc+fee,coupon_id=coupon.id if disc else None,created_at=when))
            o.items=[OrderItem(item_id=item.id,name=item.name,unit_price=item.effective_price,quantity=qty),OrderItem(item_id=bread.id,name=bread.name,unit_price=bread.price,quantity=2)]; o.items[0].modifiers.append(OrderItemModifier(name='Medium spice',extra_price=0)); db.session.flush()
            if disc: add(CouponUsage(coupon_id=coupon.id,user_id=u.id,order_id=o.id,created_at=when))
            if kind=='delivery': z=zones[j%len(zones)]; o.delivery=Delivery(zone_id=z.id,driver_id=drivers[j%len(drivers)].id,street=f'Demo address, {z.name}',zip_code=z.zip_code)
            steps=['placed','preparing','ready','completed'] if status=='completed' else ['placed','preparing','ready'][:['placed','preparing','ready'].index(status)+1]
            if kind=='delivery' and status=='completed': steps.insert(-1,'out_for_delivery')
            for k,step in enumerate(steps):
                ts=min(when+timedelta(minutes=k*3),now); actor=u if k==0 else chef if step in ('preparing','ready') else waiter
                add(OrderStatusHistory(order_id=o.id,status=step,actor_id=actor.id,created_at=ts))
                if step=='preparing':
                    for line in o.items:
                        for recipe in ItemIngredient.query.filter_by(item_id=line.item_id).all():
                            b=batches[recipe.ingredient_id]; used=recipe.quantity*line.quantity; b.remaining-=used; add(StockMovement(batch_id=b.id,order_id=o.id,actor_id=chef.id,quantity=-used,reason='recipe',created_at=ts))
            if status=='completed':
                paid_at=min(when+timedelta(minutes=8),now); pm=[method,other,mobile][j%3]; add(Payment(order_id=o.id,method_id=pm.id,amount=o.total,status='paid',received_by=cashier.id,created_at=paid_at)); completed.append(o)
                if pm==method: cash_by_day[day]+=Decimal(str(o.total))
                points=max(1,int(o.total//100)); u.loyalty.points+=points; add(LoyaltyTransaction(account_id=u.loyalty.id,order_id=o.id,points=points,reason='Completed paid order',created_at=paid_at))
            else: add(Payment(order_id=o.id,method_id=method.id,amount=o.total,status='pending',created_at=when))
            add(AuditLog(actor_id=waiter.id,action='order.demo_created',entity='orders',entity_id=o.id,created_at=when))
        if di<6: add(CashSession(cashier_id=cashier.id,opened_at=at(day,9),closed_at=at(day,23),opening_balance=Decimal('5000'),closing_balance=Decimal('5000')+cash_by_day[day]))
        add(Expense(recorded_by=owner.id,category=['Utilities','Cleaning','Packaging'][di%3],description='Demo daily operating cost',amount=Decimal(1200+di*150),created_at=min(at(day,9),now)))
        ing=ingredients[di%len(ingredients)]; po=add(PurchaseOrder(supplier_id=ing.supplier_id,requested_by=inventory.id,status='received' if di<5 else 'approved' if di==5 else 'draft',created_at=min(at(day,8),now)))
        po.lines.append(PurchaseOrderItem(ingredient_id=ing.id,quantity=Decimal('12'),unit_cost=batches[ing.id].unit_cost)); db.session.flush()
        if po.status=='received':
            b=add(StockBatch(ingredient_id=ing.id,supplier_id=ing.supplier_id,remaining=Decimal('12'),unit_cost=batches[ing.id].unit_cost,expires_on=today+timedelta(days=6),created_at=po.created_at)); db.session.flush(); add(StockMovement(batch_id=b.id,actor_id=inventory.id,quantity=Decimal('12'),reason='purchase',created_at=po.created_at))
        # Past bookings and future bookings occupy unique table/time slots.
        for j in range(2):
            u=customers[(di*2+j)%len(customers)]; t=tables[2+j]; start=at(day,18+j*2)
            add(Reservation(table_id=t.id,user_id=u.id,guest_name=u.name,guest_phone=u.phone,party_size=4,reserved_for=start,ends_at=start+timedelta(hours=2),status='completed' if start+timedelta(hours=2)<now else 'confirmed',created_at=min(at(day,8),now)))
    add(CashSession(cashier_id=cashier.id,opened_at=at(today),opening_balance=Decimal('5000')))
    for j,u in enumerate(customers):
        start=at(today+timedelta(days=1+j//4),17+(j%4)*1); t=tables[2+j%4]
        add(Reservation(table_id=t.id,user_id=u.id,guest_name=u.name,guest_phone=u.phone,party_size=min(4,t.seats),reserved_for=start,ends_at=start+timedelta(hours=2),status='confirmed',created_at=now))
        add(ContactMessage(user_id=u.id,assigned_to=manager.id,name=u.name,email=u.email,department=['management','kitchen','service','reservations'][j%4],message=['Could you arrange a family table?','Please confirm the mild spice option.','Can we request a high chair?','Is a birthday booking possible?'][j%4],is_resolved=j%3==0,created_at=now-timedelta(hours=j)))
        add(ServiceRequest(customer_id=u.id,assigned_to=manager.id,body='Please confirm my dining preferences.',status='resolved' if j%3==0 else 'open',created_at=now-timedelta(minutes=j*10)))
        rev=add(Review(user_id=u.id,item_id=completed[j].items[0].item_id if completed[j].user_id==u.id else menu['Chicken Karahi'].id,rating=4+j%2,comment=['Excellent food and friendly service.','Enjoyed the karahi and fresh naan.'][j%2],created_at=now-timedelta(hours=j)))
        db.session.flush(); add(ReviewReply(review_id=rev.id,user_id=manager.id,body='Thank you for dining with us!',created_at=now))
        c=add(Cart(user_id=u.id)); c.items.append(CartItem(item_id=menu['Chicken Karahi'].id,quantity=1)); c.items[0].modifiers.append(CartItemModifier(option_id=ModifierOption.query.filter_by(name='Medium').one().id))
    for idx,p in enumerate(people.values()):
        sender=owner if p.user_id==manager.id else manager
        add(StaffMessage(staff_id=p.id,sender_id=sender.id,subject=['Weekly operations review','Kitchen preparation checklist','Evening service plan','Till reconciliation','Supplier delivery update','Kitchen prep schedule','Table service briefing'][idx],body='Please review the assigned tasks for this week and confirm readiness.',reply='Confirmed, tasks reviewed.' if idx%2 else None,replied_at=now if idx%2 else None,created_at=now-timedelta(hours=idx+1)))
        if p.user_id!=manager.id: add(StaffMessage(staff_id=staff['manager'].id,sender_id=p.user_id,subject=f'{p.role.title()} status update',body='Daily checklist completed; please review the latest activity.',created_at=now-timedelta(minutes=idx*15)))
    for u in (owner, manager, chef, waiter, cashier, inventory):
        add(Notification(user_id=u.id,message="Demo operations: review your latest work queue and team messages.",is_read=False,created_at=now))
    db.session.commit(); return True
