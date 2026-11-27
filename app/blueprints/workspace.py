"""Role-specific workspaces. Server-side guards apply to every operation."""
from datetime import datetime, date
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash
from ..extensions import db
from ..models import (User, Role, StaffMember, StaffMessage, StaffShift, AttendanceRecord, StaffLeave, StaffPayroll, Notification, ItemIngredient, Order, OrderItem, OrderStatusHistory, Payment, DiningTable, MenuItem, PaymentMethod, Ingredient, Supplier, StockBatch, StockMovement, PurchaseOrder, PurchaseOrderItem, Expense, CashSession, ServiceRequest, ContactMessage, Reservation, utcnow)
from ..access import require, role_name, permitted
from ..utils import current_user, login_required, check_csrf, valid_email
from ..operations import BusinessError, amount, audit, transition, record_payment, due
from sqlalchemy.exc import IntegrityError
from ..staff_operations import table_state, create_table_order, purchase_lines, cash_summary, ingredient_balance
from ..operations import notify_roles, notify_user, paid_total
from werkzeug.security import check_password_hash

bp = Blueprint('workspace', __name__, url_prefix='/workspace')
ACTIVE = ('placed','preparing','ready','out_for_delivery')
DEST = {'owner':'admin.dashboard','manager':'workspace.manager','chef':'workspace.kitchen','waiter':'workspace.waiter','cashier':'workspace.billing','inventory':'workspace.stock','customer':'workspace.customer'}

def finish(endpoint, action):
    try:
        action(); db.session.commit(); flash('Changes saved.', 'success')
    except (BusinessError, IntegrityError, ValueError, KeyError) as exc:
        db.session.rollback(); flash(str(exc) if isinstance(exc,BusinessError) else 'Invalid input or conflicting record. Please review and retry.', 'error')
    return redirect(url_for(endpoint))

def view(kind, **kwargs):
    return render_template('workspace/dashboard.html', kind=kind, **kwargs)

@bp.route('/')
@login_required
def home():
    endpoint = DEST.get(role_name(current_user()))
    if not endpoint: abort(403)
    return redirect(url_for(endpoint))

@bp.route('/manager')
@require('manage')
def manager():
    return view('manager', orders=Order.query.filter(Order.status.in_(ACTIVE)).order_by(Order.id.desc()).all(), staff=StaffMember.query.order_by(StaffMember.name).all(), enquiries=ContactMessage.query.filter_by(is_resolved=False).all(), reservations=Reservation.query.filter(Reservation.status=='confirmed',Reservation.reserved_for>=utcnow()).order_by(Reservation.reserved_for).limit(30).all(), requests=ServiceRequest.query.filter_by(status='open').all(), leaves=StaffLeave.query.filter_by(status='Pending').all())

@bp.route('/employees', methods=['GET','POST'])
@require('manage')
def employees():
    if request.method == 'POST':
        check_csrf()
        def create():
            role = request.form.get('role'); name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
            allowed={'chef','waiter','cashier','inventory'} | ({'manager'} if permitted(current_user(),'owner') else set())
            if role not in allowed or not 2<=len(name)<=80 or not valid_email(email) or len(email)>120 or len(password)<12: raise BusinessError('Use valid employee details, an allowed role and a 12+ character password.')
            phone=request.form.get('phone','').strip(); salary=amount(request.form.get('salary'),minimum='1')
            if not 7<=len(phone)<=30 or not all(c.isdigit() or c in '+- ()' for c in phone): raise BusinessError('Enter a valid employee phone number.')
            u=User(name=name,email=email,phone=phone,password_hash=generate_password_hash(password),role=Role.query.filter_by(name=role).one())
            db.session.add(u); db.session.flush(); db.session.add(StaffMember(user_id=u.id,name=name,email=email,phone=phone,role=role,salary_monthly=float(salary),shift_status='Off Duty',shift_hours_done=0)); audit(current_user(),'employee.created','users',u.id)
        return finish('workspace.employees',create)
    return view('employees',staff=StaffMember.query.order_by(StaffMember.name).all())

@bp.route('/employees/<int:uid>/toggle', methods=['POST'])
@require('manage')
def employee_toggle(uid):
    check_csrf(); u=db.session.get(User,uid) or abort(404)
    if role_name(u) not in ({'chef','waiter','cashier','inventory'} | ({'manager'} if permitted(current_user(),'owner') else set())): abort(403)
    def action():
        u.is_active=not u.is_active; audit(current_user(),'employee.status','users',uid)
    return finish('workspace.employees',action)

@bp.route('/kitchen')
@require('kitchen')
def kitchen():
    return view('kitchen',orders=Order.query.filter(Order.status.in_(('placed','preparing','ready'))).order_by(Order.created_at).all())

@bp.route('/kitchen/<int:oid>/<target>', methods=['POST'])
@require('kitchen')
def kitchen_status(oid,target):
    check_csrf(); order=db.session.get(Order,oid) or abort(404)
    if target not in ('preparing','ready'): abort(403)
    return finish('workspace.kitchen',lambda:transition(order,target,current_user()))

@bp.route('/waiter',methods=['GET','POST'])
@require('waiter')
def waiter():
    user=current_user()
    if request.method=='POST':
        check_csrf()
        def create():
            create_table_order(request.form.get('table_id',type=int), request.form.getlist('item_id'), request.form.getlist('qty'), request.form.getlist('note'), user)
        return finish('workspace.waiter',create)
    orders=Order.query.filter(Order.status.in_(ACTIVE),Order.waiter_id==user.id).all()
    tables=DiningTable.query.order_by(DiningTable.label).all()
    return view('waiter',orders=orders,tables=tables,table_states={t.id:table_state(t)[0] for t in tables},items=MenuItem.query.filter_by(is_available=True).order_by(MenuItem.name).all())

@bp.route('/waiter/<int:oid>/close',methods=['POST'])
@require('waiter')
def waiter_close(oid):
    check_csrf(); order=Order.query.filter_by(id=oid,waiter_id=current_user().id).first_or_404()
    return finish('workspace.waiter',lambda:transition(order,'completed',current_user()))

@bp.route('/billing',methods=['GET','POST'])
@require('billing')
def billing():
    if request.method=='POST':
        check_csrf()
        def pay():
            order=db.session.get(Order,request.form.get('order_id',type=int) or 0); method=db.session.get(PaymentMethod,request.form.get('method_id',type=int) or 0)
            if not order or not method or not method.is_active: raise BusinessError('Choose a valid order and payment method.')
            record_payment(order,method,request.form.get('amount'),current_user())
        return finish('workspace.billing',pay)
    return view('billing',orders=Order.query.filter(Order.status.in_(ACTIVE)).order_by(Order.id.desc()).all(),methods=PaymentMethod.query.filter_by(is_active=True).all(),due=due,history=Payment.query.filter_by(status='paid').order_by(Payment.created_at.desc()).limit(100).all())

@bp.route('/stock',methods=['GET','POST'])
@require('stock')
def stock():
    if request.method=='POST':
        check_csrf()
        def receive():
            ingredient=db.session.get(Ingredient,request.form.get('ingredient_id',type=int) or 0)
            if not ingredient: raise BusinessError('Select an ingredient.')
            qty=amount(request.form.get('quantity'),'0.001','0.001'); cost=amount(request.form.get('cost')); expiry=date.fromisoformat(request.form['expiry']) if request.form.get('expiry') else None
            if expiry and expiry<date.today(): raise BusinessError('Cannot receive expired stock.')
            batch=StockBatch(ingredient_id=ingredient.id,supplier_id=ingredient.supplier_id,remaining=qty,unit_cost=cost,expires_on=expiry);db.session.add(batch);db.session.flush();db.session.add(StockMovement(batch_id=batch.id,actor_id=current_user().id,quantity=qty,reason='receipt'));audit(current_user(),'stock.received','stock_batches',batch.id)
        return finish('workspace.stock',receive)
    ingredients=Ingredient.query.order_by(Ingredient.name).all(); batches=StockBatch.query.order_by(StockBatch.id.desc()).all()
    return view('stock',ingredients=ingredients,batches=batches,movements=StockMovement.query.order_by(StockMovement.id.desc()).limit(30).all(),today=date.today())

@bp.route('/team',methods=['GET','POST'])
@require('team')
def team():
    user=current_user(); profile=StaffMember.query.filter_by(user_id=user.id).first()
    if request.method=='POST':
        check_csrf()
        def send():
            staff=db.session.get(StaffMember,request.form.get('staff_id',type=int) or 0); subject=request.form.get('subject','').strip(); body=request.form.get('body','').strip()
            if not staff or not staff.user or not staff.user.is_active or not 1<=len(subject)<=120 or not 1<=len(body)<=2000: raise BusinessError('Select an active colleague and enter a message.')
            db.session.add(StaffMessage(staff_id=staff.id,sender_id=user.id,subject=subject,body=body));notify_user(staff.user_id,f'New team message: {subject}')
        return finish('workspace.team',send)
    return view('team',staff=StaffMember.query.filter(StaffMember.user_id.is_not(None)).all(), sent=StaffMessage.query.filter_by(sender_id=user.id).order_by(StaffMessage.id.desc()).all(),received=StaffMessage.query.filter_by(staff_id=profile.id).order_by(StaffMessage.id.desc()).all() if profile else [],profile=profile)

@bp.route('/attendance',methods=['POST'])
@require('team')
def attendance():
    check_csrf(); staff=StaffMember.query.filter_by(user_id=current_user().id).first_or_404()
    def clock():
        StaffMember.query.filter_by(id=staff.id).update({StaffMember.id:StaffMember.id},synchronize_session=False)
        row=AttendanceRecord.query.filter_by(staff_id=staff.id,clock_out=None).first()
        if request.form.get('action')=='in' and not row: db.session.add(AttendanceRecord(staff_id=staff.id));staff.shift_status='On Duty'
        elif request.form.get('action')=='out' and row: row.clock_out=utcnow();staff.shift_status='Off Duty'
        else: raise BusinessError('Invalid attendance transition.')
    return finish('workspace.team',clock)

@bp.route('/customer',methods=['GET','POST'])
@require('customer')
def customer():
    user=current_user()
    if request.method=='POST':
        check_csrf()
        def service():
            body=request.form.get('body','').strip(); oid=request.form.get('order_id',type=int)
            if not 1<=len(body)<=500 or (oid and not Order.query.filter_by(id=oid,user_id=user.id).first()): raise BusinessError('Enter a message for your own order.')
            db.session.add(ServiceRequest(customer_id=user.id,order_id=oid,body=body));notify_roles(('manager',), 'New customer service request.')
        return finish('workspace.customer',service)
    return render_template('workspace/customer.html',orders=Order.query.filter_by(user_id=user.id).order_by(Order.id.desc()).all(), reservations=Reservation.query.filter_by(user_id=user.id).all(),requests=ServiceRequest.query.filter_by(customer_id=user.id).all())

@bp.route('/requests/<int:rid>/resolve',methods=['POST'])
@require('manage')
def resolve(rid):
    check_csrf(); row=db.session.get(ServiceRequest,rid) or abort(404)
    def action(): row.status='resolved';row.assigned_to=current_user().id;audit(current_user(),'service.resolved','service_requests',rid)
    return finish('workspace.manager',action)

@bp.route('/purchases',methods=['GET','POST'])
@require('stock')
def purchases():
    if request.method=='POST':
        check_csrf()
        def create():
            supplier=db.session.get(Supplier,request.form.get('supplier_id',type=int) or 0)
            if not supplier: raise BusinessError('Select a supplier.')
            p=PurchaseOrder(supplier_id=supplier.id,requested_by=current_user().id)
            p.lines.extend(purchase_lines(request.form.getlist('ingredient_id'),request.form.getlist('quantity'),request.form.getlist('cost')))
            db.session.add(p);db.session.flush();audit(current_user(),'purchase.created','purchase_orders',p.id)
            notify_roles(('owner','manager'),f'Purchase order #{p.id} awaits approval.')
        return finish('workspace.purchases',create)
    return view('purchases',purchases=PurchaseOrder.query.order_by(PurchaseOrder.id.desc()).all(),suppliers=Supplier.query.all(),ingredients=Ingredient.query.all())

@bp.route('/purchases/<int:pid>/<action>',methods=['POST'])
@require('stock')
def purchase_action(pid,action):
    check_csrf(); p=db.session.get(PurchaseOrder,pid) or abort(404)
    if action=='approve' and not permitted(current_user(),'manage'): abort(403)
    if action not in ('approve','receive'): abort(400)
    def perform():
        old,new=('draft','approved') if action=='approve' else ('approved','received')
        if PurchaseOrder.query.filter_by(id=pid,status=old).update({'status':new},synchronize_session=False)!=1: raise BusinessError('Purchase has already moved to a different state.')
        if action=='receive':
            expiry=date.fromisoformat(request.form['expiry']) if request.form.get('expiry') else None
            if expiry and expiry<date.today(): raise BusinessError('Cannot receive expired stock.')
            for line in p.lines:
                b=StockBatch(ingredient_id=line.ingredient_id,supplier_id=p.supplier_id,remaining=line.quantity,unit_cost=line.unit_cost,expires_on=expiry);db.session.add(b);db.session.flush();db.session.add(StockMovement(batch_id=b.id,actor_id=current_user().id,quantity=line.quantity,reason='purchase'))
        audit(current_user(),'purchase.'+new,'purchase_orders',pid)
    return finish('workspace.purchases',perform)

@bp.route('/cash-register',methods=['GET','POST'])
@require('billing')
def cash_register():
    user=current_user()
    if request.method=='POST':
        check_csrf()
        def change():
            User.query.filter_by(id=user.id).update({User.id:User.id},synchronize_session=False)
            row=CashSession.query.filter_by(cashier_id=user.id,closed_at=None).first(); value=amount(request.form.get('balance'))
            if request.form.get('action')=='open' and not row: db.session.add(CashSession(cashier_id=user.id,opening_balance=value))
            elif request.form.get('action')=='close' and row: row.closed_at=utcnow();row.closing_balance=value
            else: raise BusinessError('Invalid cash session action.')
        return finish('workspace.cash_register',change)
    sessions=CashSession.query.filter_by(cashier_id=user.id).order_by(CashSession.id.desc()).limit(30).all()
    return view('cash_register',active=next((r for r in sessions if not r.closed_at),None),sessions=sessions,summaries={r.id:cash_summary(r) for r in sessions})

@bp.route('/shifts',methods=['GET','POST'])
@require('manage')
def shifts():
    if request.method=='POST':
        check_csrf()
        def schedule():
            staff=db.session.get(StaffMember,request.form.get('staff_id',type=int) or 0)
            if not staff or not staff.user or not staff.user.is_active: raise BusinessError('Select an active employee.')
            start=datetime.fromisoformat(request.form['starts_at']);end=datetime.fromisoformat(request.form['ends_at'])
            if end<=start or start.tzinfo or end.tzinfo: raise BusinessError('Enter a valid local shift interval.')
            StaffMember.query.filter_by(id=staff.id).update({StaffMember.id:StaffMember.id},synchronize_session=False)
            if StaffShift.query.filter(StaffShift.staff_id==staff.id,StaffShift.starts_at<end,StaffShift.ends_at>start).first(): raise BusinessError('Employee already has a shift in this interval.')
            row=StaffShift(staff_id=staff.id,starts_at=start,ends_at=end);db.session.add(row);db.session.flush();audit(current_user(),'shift.scheduled','staff_shifts',row.id)
        return finish('workspace.shifts',schedule)
    return view('shifts',staff=StaffMember.query.all(),shifts=StaffShift.query.order_by(StaffShift.starts_at.desc()).limit(100).all())

@bp.route('/expenses',methods=['GET','POST'])
@require('owner')
def expenses():
    if request.method=='POST':
        check_csrf()
        def create():
            category=request.form.get('category','').strip();description=request.form.get('description','').strip()
            if not 1<=len(category)<=60 or not 1<=len(description)<=200: raise BusinessError('Enter category and description.')
            row=Expense(recorded_by=current_user().id,category=category,description=description,amount=amount(request.form.get('amount'),minimum='0.01'));db.session.add(row);db.session.flush();audit(current_user(),'expense.recorded','expenses',row.id)
        return finish('workspace.expenses',create)
    rows=Expense.query.order_by(Expense.id.desc()).limit(100).all()
    return view('expenses',expenses=rows)


@bp.route('/kitchen/history')
@require('kitchen')
def kitchen_history():
    return view('history', orders=Order.query.filter(Order.status.in_(('completed','out_for_delivery'))).order_by(Order.id.desc()).limit(100).all())

@bp.route('/waiter/history')
@require('waiter')
def waiter_history():
    return view('history',orders=Order.query.filter(Order.waiter_id==current_user().id,Order.status.in_(('completed','cancelled'))).order_by(Order.id.desc()).limit(100).all())

@bp.route('/kitchen/recipes')
@require('kitchen')
def recipes():
    items=MenuItem.query.order_by(MenuItem.name).all()
    ingredients={i.id:i for i in Ingredient.query.all()}
    return view('recipes',items=items,recipes=ItemIngredient.query.all(),ingredients=ingredients,balances={i.id:ingredient_balance(i,date.today()) for i in ingredients.values()})

@bp.route('/floor')
@require('waiter')
def floor():
    tables=DiningTable.query.order_by(DiningTable.label).all()
    return view('floor',tables=tables,table_states={t.id:table_state(t)[0] for t in tables})

@bp.route('/billing/receipt/<int:pid>')
@require('billing')
def receipt(pid):
    payment=Payment.query.filter_by(id=pid,status='paid').first_or_404()
    return render_template('workspace/receipt.html',payment=payment,paid=paid_total(payment.order),balance=due(payment.order))

@bp.route('/notifications',methods=['GET','POST'])
@login_required
def notifications():
    user=current_user()
    if role_name(user)=='customer': abort(403)
    if request.method=='POST':
        check_csrf()
        def mark():
            Notification.query.filter_by(user_id=user.id,is_read=False).update({'is_read':True})
        return finish('workspace.notifications',mark)
    return view('notifications',notifications=Notification.query.filter_by(user_id=user.id).order_by(Notification.id.desc()).limit(100).all())

@bp.route('/my-workspace',methods=['GET','POST'])
@require('team')
def personal():
    user=current_user(); staff=StaffMember.query.filter_by(user_id=user.id).first()
    if request.method=='POST':
        check_csrf()
        def action():
            if request.form.get('action')=='password':
                new=request.form.get('new_password','')
                if not check_password_hash(user.password_hash,request.form.get('old_password','')) or not 12<=len(new)<=128: raise BusinessError('Enter your current password and a new password of 12–128 characters.')
                user.password_hash=generate_password_hash(new);audit(user,'password.changed','users',user.id)
            else:
                if not staff: raise BusinessError('A linked employee profile is required.')
                start=date.fromisoformat(request.form['start']);end=date.fromisoformat(request.form['end']);reason=request.form.get('reason','').strip()
                leave_type=request.form.get('leave_type')
                if start<date.today() or end<start or (end-start).days>30 or not 1<=len(reason)<=500 or leave_type not in ('Sick Leave','Casual Leave','Annual Leave','Emergency'): raise BusinessError('Enter valid leave dates and reason.')
                if StaffLeave.query.filter(StaffLeave.staff_id==staff.id,StaffLeave.status.in_(('Pending','Approved')),StaffLeave.start_date<=end,StaffLeave.end_date>=start).first(): raise BusinessError('Overlapping leave request.')
                db.session.add(StaffLeave(staff_id=staff.id,leave_type=leave_type,start_date=start,end_date=end,reason=reason,status='Pending'));notify_roles(('manager',),f'Leave request from {staff.name}.')
        return finish('workspace.personal',action)
    sid=staff.id if staff else None
    return view('personal',profile=staff,shifts=StaffShift.query.filter_by(staff_id=sid).order_by(StaffShift.starts_at.desc()).limit(30).all() if sid else [],attendance=AttendanceRecord.query.filter_by(staff_id=sid).order_by(AttendanceRecord.clock_in.desc()).limit(30).all() if sid else [],leaves=StaffLeave.query.filter_by(staff_id=sid).order_by(StaffLeave.id.desc()).all() if sid else [],payroll=StaffPayroll.query.filter_by(staff_id=sid).order_by(StaffPayroll.id.desc()).all() if sid else [])


@bp.route('/leave/<int:lid>/<decision>',methods=['POST'])
@require('manage')
def decide_leave(lid,decision):
    check_csrf(); row=db.session.get(StaffLeave,lid) or abort(404)
    if decision not in ('approve','reject'): abort(400)
    if row.staff.user_id==current_user().id or (row.staff.user and role_name(row.staff.user) in ('owner','manager') and not permitted(current_user(),'owner')): abort(403)
    def action():
        status='Approved' if decision=='approve' else 'Rejected'
        if StaffLeave.query.filter_by(id=lid,status='Pending').update({'status':status},synchronize_session=False)!=1: raise BusinessError('Leave has already been reviewed.')
        audit(current_user(),'leave.'+decision,'staff_leaves',lid);notify_user(row.staff.user_id,f'Your leave request was {status.lower()}.')
    return finish('workspace.manager',action)
