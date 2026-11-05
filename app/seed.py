"""Demo data. Menu items are representative Pakistani karahi-house dishes,
the live store page loads its menu with JavaScript so prices here are placeholders."""
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from .extensions import db
from .models import (Address, Allergen, Category, Combo, ComboItem, Coupon, DeliveryDriver,
                     DeliveryZone, DiningTable, Holiday, Ingredient, ItemImage, LoyaltyAccount,
                     MenuItem, ModifierGroup, ModifierOption, NutritionInfo, OpeningHours,
                     PaymentMethod, Promotion, PromotionItem, Review, Role, StoreInfo, Supplier,
                     Tag, User)

MENU = {
    "Starters": [
        ("Samosa Chaat", "Crisp samosas, chickpeas, yogurt, tamarind and mint chutney.", 8.50, 0, 1, ["Vegetarian"], ["Gluten", "Dairy"]),
        ("Chicken Pakora", "Gram-flour battered chicken, fried golden, with green chutney.", 10.00, 1, 0, ["Popular"], ["Gluten"]),
        ("Papri Chaat", "Crunchy wafers, potato, chickpea, sweet yogurt.", 8.00, 0, 1, ["Vegetarian"], ["Gluten", "Dairy"]),
    ],
    "Karahi": [
        ("Chicken Karahi", "Bone-in chicken wok-cooked with tomato, ginger, green chili. Served for 2.", 19.99, 1, 0, ["Popular", "House special"], []),
        ("Lamb Karahi", "Tender lamb in a rustic tomato and black pepper masala.", 24.99, 1, 0, ["House special"], []),
        ("Paneer Karahi", "Paneer cubes, peppers and onions in karahi masala.", 17.99, 1, 1, ["Vegetarian"], ["Dairy"]),
        ("Peshawari Charsi Karahi", "Minimal-spice Peshawari style: tomato, salt, black pepper, fat.", 26.99, 0, 0, ["House special"], []),
    ],
    "Curries": [
        ("Butter Chicken", "Tandoor chicken in creamy tomato-butter sauce.", 17.50, 0, 0, ["Popular"], ["Dairy", "Nuts"]),
        ("Nihari", "Slow-cooked beef shank stew, finished with ginger and lemon.", 18.99, 1, 0, ["House special"], ["Gluten"]),
        ("Daal Makhani", "Black lentils simmered overnight with butter and cream.", 14.00, 0, 1, ["Vegetarian"], ["Dairy"]),
        ("Chana Masala", "Chickpeas in a tangy onion-tomato masala.", 13.50, 1, 1, ["Vegetarian", "Vegan"], []),
    ],
    "Tandoor & BBQ": [
        ("Chicken Tikka", "Yogurt and spice marinated chicken, charred in the tandoor.", 15.99, 1, 0, ["Popular"], ["Dairy"]),
        ("Seekh Kebab", "Minced beef skewers with herbs and green chili.", 14.99, 1, 0, [], []),
        ("Lamb Chops", "Marinated lamb chops, grilled to order.", 22.99, 1, 0, ["House special"], ["Dairy"]),
    ],
    "Rice": [
        ("Chicken Biryani", "Basmati layered with spiced chicken, served with raita.", 16.99, 1, 0, ["Popular"], ["Dairy"]),
        ("Vegetable Pulao", "Fragrant basmati with seasonal vegetables.", 12.50, 0, 1, ["Vegetarian"], []),
        ("Steamed Basmati", "Plain basmati rice.", 4.00, 0, 1, ["Vegan"], []),
    ],
    "Breads": [
        ("Garlic Naan", "Tandoor-baked, brushed with garlic butter.", 3.75, 0, 1, ["Vegetarian"], ["Gluten", "Dairy"]),
        ("Plain Naan", "Soft, blistered tandoor bread.", 3.00, 0, 1, ["Vegetarian"], ["Gluten", "Dairy"]),
        ("Tandoori Roti", "Whole-wheat flatbread from the tandoor.", 2.75, 0, 1, ["Vegan"], ["Gluten"]),
    ],
    "Drinks & Desserts": [
        ("Mango Lassi", "Yogurt, mango pulp, cardamom.", 5.50, 0, 1, ["Vegetarian"], ["Dairy"]),
        ("Masala Chai", "Black tea simmered with milk, ginger and cardamom.", 3.50, 0, 1, ["Vegetarian"], ["Dairy"]),
        ("Gulab Jamun", "Two milk dumplings in rose-cardamom syrup.", 5.00, 0, 1, ["Vegetarian"], ["Dairy", "Gluten"]),
        ("Kheer", "Rice pudding with pistachio.", 5.50, 0, 1, ["Vegetarian"], ["Dairy", "Nuts"]),
    ],
}

HOURS = {0: ("11:30 AM", "11:30 PM"), 1: ("11:30 AM", "11:30 PM"), 2: ("11:30 AM", "11:30 PM"),
         3: ("11:30 AM", "11:30 PM"), 4: ("11:30 AM", "2:00 AM"), 5: ("11:30 AM", "2:00 AM"),
         6: ("11:30 AM", "11:30 PM")}


def seed_if_empty():
    if Role.query.first():
        return
    admin_role, customer_role = Role(name="admin"), Role(name="customer")
    db.session.add_all([admin_role, customer_role])

    admin = User(name="Karahi Admin", email="admin@karahihouse.test", role=admin_role,
                 password_hash=generate_password_hash("Admin12345"))
    diner = User(name="Ayesha Khan", email="ayesha@example.com", phone="415-555-0142", role=customer_role,
                 password_hash=generate_password_hash("Customer123"))
    admin.loyalty, diner.loyalty = LoyaltyAccount(points=0), LoyaltyAccount(points=120)
    diner.addresses.append(Address(label="Home", street="500 Hyde Street", zip_code="94109"))
    db.session.add_all([admin, diner])

    store = StoreInfo(name="Karahi House", street="1409 Polk Street", city="San Francisco",
                      zip_code="94109", phone="+923104327543")
    for day, (opens, closes) in HOURS.items():
        store.hours.append(OpeningHours(weekday=day, opens=opens, closes=closes))
    store.holidays.append(Holiday(on_date=date(date.today().year, 12, 25), reason="Christmas Day"))
    for i, seats in enumerate([2, 2, 4, 4, 4, 6, 6, 8], start=1):
        store.tables.append(DiningTable(label=f"T{i}", seats=seats))
    db.session.add(store)

    tags = {n: Tag(name=n) for n in ["Popular", "House special", "Vegetarian", "Vegan"]}
    allergens = {n: Allergen(name=n) for n in ["Gluten", "Dairy", "Nuts"]}
    db.session.add_all(list(tags.values()) + list(allergens.values()))

    spice = ModifierGroup(name="Spice level", is_required=True, allow_multiple=False)
    for name in ("Mild", "Medium", "Hot", "Desi hot"):
        spice.options.append(ModifierOption(name=name, extra_price=0))
    extras = ModifierGroup(name="Add-ons", is_required=False, allow_multiple=True)
    for name, price in (("Extra raita", 1.50), ("Side salad", 2.50), ("Extra naan", 3.00)):
        extras.options.append(ModifierOption(name=name, extra_price=price))
    db.session.add_all([spice, extras])

    market = Supplier(name="Bay Spice Traders", phone="415-555-0110")
    fresh = Supplier(name="Mission Fresh Produce", phone="415-555-0177")
    db.session.add_all([market, fresh])
    ingredients = {n: Ingredient(name=n, supplier=s) for n, s in
                   [("Chicken", fresh), ("Lamb", fresh), ("Tomato", fresh), ("Ginger", fresh),
                    ("Green chili", fresh), ("Basmati rice", market), ("Garam masala", market)]}
    db.session.add_all(ingredients.values())

    items = {}
    for order, (cat_name, rows) in enumerate(MENU.items()):
        cat = Category(name=cat_name, slug=cat_name.lower().replace(" & ", "-").replace(" ", "-"), sort_order=order)
        db.session.add(cat)
        for name, desc, price, spicy, veg, tag_names, allergen_names in rows:
            item = MenuItem(category=cat, name=name, description=desc, price=price,
                            is_spicy=bool(spicy), is_vegetarian=bool(veg))
            item.tags = [tags[t] for t in tag_names]
            item.allergens = [allergens[a] for a in allergen_names]
            item.images.append(ItemImage(url=f"/static/img/{cat.slug}.svg", alt_text=name))
            item.nutrition = NutritionInfo(calories=int(price * 32), protein_g=round(price, 1),
                                           carbs_g=round(price * 1.8, 1), fat_g=round(price * 1.1, 1))
            if cat_name in ("Karahi", "Curries", "Tandoor & BBQ", "Rice"):
                item.modifier_groups = [spice, extras]
            if cat_name == "Karahi":
                item.ingredients = [ingredients["Tomato"], ingredients["Ginger"], ingredients["Green chili"]]
            db.session.add(item)
            items[name] = item
    items["Chicken Karahi"].ingredients.append(ingredients["Chicken"])
    items["Lamb Karahi"].ingredients.append(ingredients["Lamb"])
    items["Chicken Biryani"].ingredients = [ingredients["Chicken"], ingredients["Basmati rice"],
                                            ingredients["Garam masala"]]

    combo = Combo(name="Karahi for Two", price=34.99)
    for n in ("Chicken Karahi", "Garlic Naan", "Steamed Basmati"):
        combo.items.append(ComboItem(item=items[n], quantity=2 if n == "Garlic Naan" else 1))
    db.session.add(combo)

    promo = Promotion(title="Weekend Karahi Deal", description="Lamb Karahi at a special price, Fri to Sun.",
                      starts_on=date.today(), ends_on=date.today() + timedelta(days=365))
    promo.items.append(PromotionItem(item=items["Lamb Karahi"], promo_price=21.99))
    db.session.add(promo)

    db.session.add_all([PaymentMethod(name="Credit / debit card"), PaymentMethod(name="Pay at counter"),
                        PaymentMethod(name="Apple Pay")])
    db.session.add_all([Coupon(code="WELCOME10", percent_off=10, min_subtotal=20,
                               expires_on=date.today() + timedelta(days=365)),
                        Coupon(code="EXPIRED5", percent_off=5, expires_on=date(2020, 1, 1))])
    for name, zip_code, fee in [("Polk Gulch", "94109", 2.99), ("Tenderloin", "94102", 3.99),
                                ("Nob Hill", "94108", 3.99), ("Russian Hill", "94133", 4.49),
                                ("Marina", "94123", 4.99)]:
        db.session.add(DeliveryZone(name=name, zip_code=zip_code, fee=fee))
    db.session.add_all([DeliveryDriver(name="Bilal Ahmed", phone="415-555-0190"),
                        DeliveryDriver(name="Sara Malik", phone="415-555-0191")])
    db.session.flush()
    for n, rating, text in [("Chicken Karahi", 5, "Proper dhaba flavor. Order it hot."),
                            ("Chicken Biryani", 4, "Generous portion, good raita.")]:
        db.session.add(Review(user_id=diner.id, item_id=items[n].id, rating=rating, comment=text))
    db.session.commit()
