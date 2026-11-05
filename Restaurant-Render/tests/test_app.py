import re

import pytest

from app import create_app
from app.extensions import db
from app.models import MenuItem, Order, Review, User


@pytest.fixture()
def client(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 't.db'}"})
    with app.test_client() as c:
        c.app = app
        yield c


def token(client, url="/menu"):
    html = client.get(url).get_data(as_text=True)
    return re.search(r'name="_csrf" value="([^"]+)"', html).group(1)


def login(client, email, password):
    return client.post("/account/login", data={"email": email, "password": password, "_csrf": token(client, "/account/login")})


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
        order = Order.query.one()
        assert order.discount > 0 and order.total == round(order.subtotal - order.discount, 2)


def test_review_crud(client):
    login(client, "ayesha@example.com", "Customer123")
    t = token(client)
    with client.app.app_context():
        item_id = MenuItem.query.filter_by(name="Seekh Kebab").first().id
    client.post(f"/menu/{item_id}/review", data={"rating": 4, "comment": "Great", "_csrf": t})
    client.post(f"/menu/{item_id}/review", data={"rating": 5, "comment": "Even better", "_csrf": t})  # update
    with client.app.app_context():
        reviews = Review.query.filter_by(item_id=item_id).all()
        assert len(reviews) == 1 and reviews[0].rating == 5
        rid = reviews[0].id
    client.post(f"/review/{rid}/delete", data={"_csrf": t})
    with client.app.app_context():
        assert Review.query.filter_by(item_id=item_id).count() == 0


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
        assert client.get(f"/admin/t/{name}/new").status_code == 200, name


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
