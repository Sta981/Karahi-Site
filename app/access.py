"""Central authorization; the role is never selected by the login form."""
from functools import wraps
from flask import abort, redirect, url_for
import os
from .extensions import db
from .models import Role, Permission, RolePermission, StaffMember, User

ROLE_PERMISSIONS = {
    'owner': {'owner', 'manage', 'kitchen', 'waiter', 'billing', 'stock', 'team'},
    'manager': {'manage', 'kitchen', 'waiter', 'billing', 'stock', 'team'},
    'chef': {'kitchen', 'team'}, 'waiter': {'waiter', 'team'},
    'cashier': {'billing', 'team'}, 'inventory': {'stock', 'team'}, 'customer': {'customer'},
}

def role_name(user):
    return 'owner' if user.role.name == 'admin' else user.role.name

def permitted(user, code):
    if not user or not user.is_active:
        return False
    if role_name(user) not in ROLE_PERMISSIONS or code not in ROLE_PERMISSIONS[role_name(user)]:
        return False
    return db.session.query(RolePermission.id).join(Permission).filter(
        RolePermission.role_id == user.role_id, Permission.code == code).first() is not None

def require(code):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            from .utils import current_user
            user = current_user()
            if not user:
                return redirect(url_for('auth.staff_login' if code != 'customer' else 'auth.login'))
            if not permitted(user, code):
                abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator

def seed_access():
    for name, codes in ROLE_PERMISSIONS.items():
        role = Role.query.filter_by(name=name).first()
        if not role:
            role = Role(name=name); db.session.add(role); db.session.flush()
        for code in codes:
            permission = Permission.query.filter_by(code=code).first()
            if not permission:
                permission = Permission(code=code); db.session.add(permission); db.session.flush()
            if not RolePermission.query.filter_by(role_id=role.id, permission_id=permission.id).first():
                db.session.add(RolePermission(role_id=role.id, permission_id=permission.id))
    legacy = Role.query.filter_by(name='admin').first()
    if legacy:
        owner = Role.query.filter_by(name='owner').first()
        User.query.filter_by(role_id=legacy.id).update({'role_id': owner.id})
    db.session.commit()

def seed_demo_staff():
    from werkzeug.security import generate_password_hash
    for name in ('manager','chef','waiter','cashier','inventory'):
        email = f'{name}@restroiq.test'
        if User.query.filter_by(email=email).first():
            continue
        u = User(name=f'Demo {name.title()}', email=email, role=Role.query.filter_by(name=name).one(), password_hash=generate_password_hash(os.environ.get("DEMO_STAFF_PASSWORD", "DemoStaff123!")))
        db.session.add(u); db.session.flush()
        db.session.add(StaffMember(user_id=u.id, name=u.name, email=email, role=name, salary_monthly=0, shift_status='Off Duty', shift_hours_done=0))
    db.session.commit()

    # Clearly labelled synthetic ingredient quantities for the demonstration database only.
    from .models import ItemIngredient, Ingredient, StockBatch, StockMovement
    from decimal import Decimal
    from datetime import date, timedelta
    if not StockBatch.query.first():
        actor=User.query.join(Role).filter(Role.name=='owner').first()
        if actor:
            for recipe in ItemIngredient.query.all():
                recipe.quantity=Decimal('0.200')
            for ingredient in Ingredient.query.all():
                batch=StockBatch(ingredient_id=ingredient.id,supplier_id=ingredient.supplier_id,remaining=Decimal('25'),unit_cost=Decimal('5'),expires_on=date.today()+timedelta(days=7))
                db.session.add(batch);db.session.flush();db.session.add(StockMovement(batch_id=batch.id,actor_id=actor.id,quantity=Decimal('25'),reason='demo opening stock'))
            db.session.commit()
