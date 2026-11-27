import re

import pytest

from app import create_app
from app.extensions import db
from app.models import MenuItem, Order, Review, User, Cart


@pytest.fixture()
def client(tmp_path):
    app = create_app({"TESTING": True, "DEMO_MODE": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 't.db'}"})
    with app.test_client() as c:
        c.app = app
        yield c


def token(client, url="/menu"):
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="_csrf" value="([^"]+)"', html).group(1)


def login(client, email, password):
    path = "/account/staff-login" if email.endswith("@restroiq.test") or email == "admin@karahihouse.test" else "/account/login"
    return client.post(path, data={"email": email, "password": password, "_csrf": token(client, path)})


def test_table_minimum():
    assert len(db.Model.metadata.tables) >= 40


def test_public_pages(client):
    for url in ("/", "/menu", "/menu?q=karahi", "/about", "/contact", "/reserve", "/account/login", "/account/register", "/cart"):
        assert client.get(url).status_code == 200, url
    assert client.get("/menu/9999").status_code == 404


def test_post_without_csrf_rejected(client):
    assert client.post("/cart/add/1", data={"quantity": 1}).status_code == 400


def test_register_validation_and_success(client):
    t = token(client, "/account/register")
    bad = client.post("/account/register", data={"name": "A", "email": "nope", "password": "short", "confirm": "x", "_csrf": t})
    html = bad.get_data(as_text=True)
    assert "Enter a valid email" in html and "Passwords do not match" in html
    ok = client.post("/account/register", data={"name": "Sam Lee", "email": "sam@example.com", "password": "Strong123", "confirm": "Strong123", "_csrf": t})
    assert ok.status_code == 302  # Post-Redirect-Get
    with client.app.app_context():
        assert User.query.filter_by(email="sam@example.com").first()


def test_cart_checkout_flow(client):
    login(client, "ayesha@example.com", "Customer123")
    with client.app.app_context():
        demo = User.query.filter_by(email="ayesha@example.com").one()
        cart = Cart.query.filter_by(user_id=demo.id).first()
        if cart:
            cart.items.clear()
            db.session.commit()
        item = MenuItem.query.filter_by(name="Chicken Karahi").first()
        spice = item.modifier_groups[0].options[1].id
        item_id = item.id
    t = token(client)
    # required modifier missing -> rejected
    client.post(f"/cart/add/{item_id}", data={"quantity": 1, "_csrf": t})
    assert client.get("/cart").get_data(as_text=True).count("Chicken Karahi") == 0
    r = client.post(f"/cart/add/{item_id}", data={"quantity": 2, "options": spice, "_csrf": t})
    assert r.status_code == 302
    assert "Chicken Karahi" in client.get("/cart").get_data(as_text=True)
    # invalid checkout (no phone / payment)
    bad = client.post("/checkout", data={"name": "A", "phone": "x", "_csrf": t})
    assert "Choose a payment method" in bad.get_data(as_text=True)
    ok = client.post("/checkout", data={"name": "Ayesha Khan", "phone": "415-555-0142", "payment_method": "1",
                                        "coupon": "WELCOME10", "_csrf": t})
    assert ok.status_code == 302
    with client.app.app_context():
        order = Order.query.order_by(Order.id.desc()).first()
        assert order.discount > 0 and order.total == round(order.subtotal - order.discount, 2)


def test_review_crud(client):
    login(client, "ayesha@example.com", "Customer123")
    t = token(client)
    with client.app.app_context():
        item_id = MenuItem.query.filter_by(name="Seekh Kebab").first().id
        demo = User.query.filter_by(email="ayesha@example.com").one()
        for old in Review.query.filter_by(item_id=item_id, user_id=demo.id).all():
            db.session.delete(old)
        db.session.commit()
    client.post(f"/menu/{item_id}/review", data={"rating": 4, "comment": "Great", "_csrf": t})
    client.post(f"/menu/{item_id}/review", data={"rating": 5, "comment": "Even better", "_csrf": t})  # update
    with client.app.app_context():
        reviews = Review.query.filter_by(item_id=item_id, user_id=demo.id).all()
        assert len(reviews) == 1 and reviews[0].rating == 5
        rid = reviews[0].id
    client.post(f"/review/{rid}/delete", data={"_csrf": t})
    with client.app.app_context():
        assert Review.query.filter_by(item_id=item_id, user_id=demo.id).count() == 0


def test_admin_requires_role(client):
    assert client.get("/admin/").status_code == 302
    login(client, "ayesha@example.com", "Customer123")
    assert client.get("/admin/").status_code == 403


def test_admin_crud_every_table(client):
    login(client, "admin@karahihouse.test", "Admin12345")
    assert client.get("/admin/").status_code == 200
    with client.app.app_context():
        tables = list(db.Model.metadata.tables)
    for name in tables:
        assert client.get(f"/admin/t/{name}").status_code == 200, name
        from app.blueprints.admin import PROTECTED
        assert client.get(f"/admin/t/{name}/new").status_code == (403 if name in PROTECTED else 200), name


def test_admin_create_edit_delete(client):
    login(client, "admin@karahihouse.test", "Admin12345")
    t = token(client, "/admin/t/tags/new")
    client.post("/admin/t/tags/new", data={"name": "Chef pick", "_csrf": t})
    dup = client.post("/admin/t/tags/new", data={"name": "Chef pick", "_csrf": t})
    assert "Must be unique" in dup.get_data(as_text=True)
    from app.models import Tag
    with client.app.app_context():
        tag_id = Tag.query.filter_by(name="Chef pick").one().id
    client.post(f"/admin/t/tags/edit?id={tag_id}", data={"name": "Staff pick", "_csrf": t})
    with client.app.app_context():
        assert db.session.get(Tag, tag_id).name == "Staff pick"
    client.post("/admin/t/tags/delete", data={"id": tag_id, "_csrf": t})
    with client.app.app_context():
        assert db.session.get(Tag, tag_id) is None


def test_admin_edit_pages_render_including_composite_keys(client):
    login(client, "admin@karahihouse.test", "Admin12345")
    assert client.get("/admin/t/menu_items/edit?id=1").status_code == 200
    assert client.get("/admin/t/item_tags/edit?item_id=1&tag_id=1").status_code in (200, 404)
    page = client.get("/admin/t/item_tags").get_data(as_text=True)
    assert "Edit" in page


def test_restroiq_admin_dashboard(client):
    login(client, "admin@karahihouse.test", "Admin12345")
    res = client.get("/admin/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Restroq" in html or "RestroIQ" in html
    assert "Staff currently on duty" in html
    assert "Recorded Payments" in html
    assert "Business performance" in html


def test_restroiq_staff_and_leaves(client):
    login(client, "admin@karahihouse.test", "Admin12345")
    res = client.get("/admin/staff")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Staff Roster" in html or "Leave Management" in html
    
    # Test leave approval
    t = token(client, "/admin/staff")
    res = client.post("/admin/staff/leave/1/approve", data={"_csrf": t}, follow_redirects=True)
    assert res.status_code == 200
    with client.app.app_context():
        from app.models import StaffLeave
        leave = db.session.get(StaffLeave, 1)
        assert leave.status == "Approved"


def test_restroiq_kds_orders_analytics(client):
    login(client, "admin@karahihouse.test", "Admin12345")
    assert client.get("/admin/kitchen").status_code == 200
    assert client.get("/admin/orders").status_code == 200
    assert client.get("/admin/tables").status_code == 200
    assert client.get("/admin/analytics").status_code == 200
    assert client.get("/admin/directory").status_code == 200


def test_customer_home_luxury_showcase(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Made with fire" in html
    assert "Chicken Karahi" in html
    assert "Karahi House" in html



def test_staff_message_permissions_and_reply(client):
    from app.models import StaffMember, StaffMessage
    with client.app.app_context():
        employee = User.query.filter_by(email='chef@restroiq.test').first()
        staff = StaffMember.query.filter_by(user_id=employee.id).one()
        staff_id = staff.id
    login(client, 'admin@karahihouse.test', 'Admin12345')
    assert client.post('/admin/staff/messages', data={'staff_id': staff_id, 'subject': 'Service briefing', 'body': 'Prepare table five.', '_csrf': token(client, '/admin/staff/messages')}).status_code == 302
    with client.app.app_context():
        msg_id = StaffMessage.query.filter_by(subject='Service briefing').first().id
    login(client, 'chef@restroiq.test', 'DemoStaff123!')
    assert b'Service briefing' in client.get('/account/staff-inbox').data
    assert client.get('/admin/staff/messages').status_code == 403
    assert client.post('/account/staff-inbox', data={'message_id': msg_id, 'reply': 'Confirmed.', '_csrf': token(client, '/account/staff-inbox')}).status_code == 302
    with client.app.app_context():
        assert db.session.get(StaffMessage, msg_id).reply == 'Confirmed.'
    login(client, 'admin@karahihouse.test', 'Admin12345')
    assert b'Confirmed.' in client.get('/admin/staff/messages').data


def test_department_enquiry(client):
    from app.models import ContactMessage
    result = client.post('/contact', data={'name':'Test Guest','email':'test@example.com','department':'kitchen','message':'Please confirm allergy information.', '_csrf':token(client,'/contact')})
    assert result.status_code == 302
    with client.app.app_context():
        assert ContactMessage.query.filter_by(email='test@example.com').first().department == 'kitchen'

@pytest.mark.parametrize('role,path,denied',[
    ('manager','manager','/admin/'),('chef','kitchen','/workspace/billing'),
    ('waiter','waiter','/workspace/stock'),('cashier','billing','/workspace/employees'),
    ('inventory','stock','/workspace/kitchen')])
def test_staff_role_boundaries(client,role,path,denied):
    assert login(client,role+'@restroiq.test','DemoStaff123!').status_code==302
    assert client.get('/workspace/'+path).status_code==200
    assert client.get(denied).status_code==403


def test_customer_cannot_use_staff_login(client):
    path='/account/staff-login'
    r=client.post(path,data={'email':'ayesha@example.com','password':'Customer123','_csrf':token(client,path)})
    assert r.status_code==200
    assert client.get('/workspace/kitchen').status_code==302


def test_employee_cannot_escalate_role(client):
    login(client,'manager@restroiq.test','DemoStaff123!')
    path='/workspace/employees'
    client.post(path,data={'role':'owner','name':'Malicious','email':'test@local.test','password':'Password12345!','_csrf':token(client,path)})
    with client.app.app_context():
        assert User.query.filter_by(email='test@local.test').first() is None


def test_v4_shared_public_design(client):
    for path in ('/', '/menu', '/reserve', '/about', '/contact', '/cart'):
        html = client.get(path).get_data(as_text=True)
        assert 'css/premium.css' in html, path
        assert 'id="bag-drawer"' in html, path
    home = client.get('/').get_data(as_text=True)
    assert 'href="#discover"' in home and 'id="discover"' in home
    menu = client.get('/menu').get_data(as_text=True)
    assert 'premium-dish' in menu and 'store-banner' not in menu
    assert 'data-book-step="2"' in client.get('/reserve').get_data(as_text=True)


def test_v4_customer_account_design(client):
    assert login(client, 'ayesha@example.com', 'Customer123').status_code == 302
    for path in ('/workspace/customer', '/orders', '/profile'):
        response = client.get(path)
        assert response.status_code == 200
        assert 'account-nav' in response.get_data(as_text=True)
    assert 'Loyalty points' in client.get('/workspace/customer').get_data(as_text=True)
