"""All 42 SQLAlchemy models for the Karahi House site, grouped by domain."""
from datetime import datetime, timezone

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


# ---------- Users & accounts ----------
class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    users = db.relationship("User", back_populates="role")


class User(TimestampMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30))
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.relationship("Role", back_populates="users")
    addresses = db.relationship("Address", back_populates="user", cascade="all, delete-orphan")
    orders = db.relationship("Order", back_populates="user")
    reviews = db.relationship("Review", back_populates="user")

    @property
    def is_admin(self):
        return self.role.name == "admin"

    def __str__(self):
        return self.name


class Address(db.Model):
    __tablename__ = "addresses"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    label = db.Column(db.String(30), default="Home")
    street = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(60), default="San Francisco")
    zip_code = db.Column(db.String(10), nullable=False)
    user = db.relationship("User", back_populates="addresses")

    def __str__(self):
        return f"{self.street}, {self.city} {self.zip_code}"


class LoyaltyAccount(db.Model):
    __tablename__ = "loyalty_accounts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    points = db.Column(db.Integer, default=0, nullable=False)
    user = db.relationship("User", backref=db.backref("loyalty", uselist=False))
    transactions = db.relationship("LoyaltyTransaction", back_populates="account", cascade="all, delete-orphan")


class LoyaltyTransaction(TimestampMixin, db.Model):
    __tablename__ = "loyalty_transactions"
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("loyalty_accounts.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    points = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(120))
    account = db.relationship("LoyaltyAccount", back_populates="transactions")


class Notification(TimestampMixin, db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    user = db.relationship("User", backref="notifications")


# ---------- Menu ----------
class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    items = db.relationship("MenuItem", back_populates="category")

    def __str__(self):
        return self.name


class MenuItem(db.Model):
    __tablename__ = "menu_items"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    is_spicy = db.Column(db.Boolean, default=False)
    is_vegetarian = db.Column(db.Boolean, default=False)
    category = db.relationship("Category", back_populates="items")
    images = db.relationship("ItemImage", back_populates="item", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="item")
    nutrition = db.relationship("NutritionInfo", back_populates="item", uselist=False, cascade="all, delete-orphan")
    tags = db.relationship("Tag", secondary="item_tags", back_populates="items")
    allergens = db.relationship("Allergen", secondary="item_allergens", back_populates="items")
    modifier_groups = db.relationship("ModifierGroup", secondary="item_modifier_groups", back_populates="items")
    ingredients = db.relationship("Ingredient", secondary="item_ingredients", back_populates="items")

    @property
    def avg_rating(self):
        rated = [r.rating for r in self.reviews]
        return round(sum(rated) / len(rated), 1) if rated else None

    def __str__(self):
        return self.name


class ItemImage(db.Model):
    __tablename__ = "item_images"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    url = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(150))
    item = db.relationship("MenuItem", back_populates="images")


class NutritionInfo(db.Model):
    __tablename__ = "nutrition_info"
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), unique=True, nullable=False)
    calories = db.Column(db.Integer)
    protein_g = db.Column(db.Float)
    carbs_g = db.Column(db.Float)
    fat_g = db.Column(db.Float)
    item = db.relationship("MenuItem", back_populates="nutrition")


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    items = db.relationship("MenuItem", secondary="item_tags", back_populates="tags")

    def __str__(self):
        return self.name


class ItemTag(db.Model):
    __tablename__ = "item_tags"
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey("tags.id"), primary_key=True)


class Allergen(db.Model):
    __tablename__ = "allergens"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    items = db.relationship("MenuItem", secondary="item_allergens", back_populates="allergens")

    def __str__(self):
        return self.name


class ItemAllergen(db.Model):
    __tablename__ = "item_allergens"
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), primary_key=True)
    allergen_id = db.Column(db.Integer, db.ForeignKey("allergens.id"), primary_key=True)


class Ingredient(db.Model):
    __tablename__ = "ingredients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))
    items = db.relationship("MenuItem", secondary="item_ingredients", back_populates="ingredients")
    supplier = db.relationship("Supplier", back_populates="ingredients")

    def __str__(self):
        return self.name


class ItemIngredient(db.Model):
    __tablename__ = "item_ingredients"
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), primary_key=True)


class Supplier(db.Model):
    __tablename__ = "suppliers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(30))
    ingredients = db.relationship("Ingredient", back_populates="supplier")

    def __str__(self):
        return self.name


class ModifierGroup(db.Model):
    """e.g. 'Spice level' (pick one) or 'Add-ons' (pick many)."""
    __tablename__ = "modifier_groups"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    is_required = db.Column(db.Boolean, default=False)
    allow_multiple = db.Column(db.Boolean, default=False)
    options = db.relationship("ModifierOption", back_populates="group", cascade="all, delete-orphan")
    items = db.relationship("MenuItem", secondary="item_modifier_groups", back_populates="modifier_groups")

    def __str__(self):
        return self.name


class ModifierOption(db.Model):
    __tablename__ = "modifier_options"
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("modifier_groups.id"), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    extra_price = db.Column(db.Float, default=0)
    group = db.relationship("ModifierGroup", back_populates="options")

    def __str__(self):
        return self.name


class ItemModifierGroup(db.Model):
    __tablename__ = "item_modifier_groups"
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("modifier_groups.id"), primary_key=True)


class Combo(db.Model):
    __tablename__ = "combos"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    items = db.relationship("ComboItem", back_populates="combo", cascade="all, delete-orphan")

    def __str__(self):
        return self.name


class ComboItem(db.Model):
    __tablename__ = "combo_items"
    id = db.Column(db.Integer, primary_key=True)
    combo_id = db.Column(db.Integer, db.ForeignKey("combos.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    combo = db.relationship("Combo", back_populates="items")
    item = db.relationship("MenuItem")


# ---------- Cart ----------
class Cart(TimestampMixin, db.Model):
    __tablename__ = "carts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    session_key = db.Column(db.String(64), index=True)
    items = db.relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

    @property
    def subtotal(self):
        return round(sum(i.line_total for i in self.items), 2)

    @property
    def count(self):
        return sum(i.quantity for i in self.items)


class CartItem(db.Model):
    __tablename__ = "cart_items"
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey("carts.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    note = db.Column(db.String(200))
    cart = db.relationship("Cart", back_populates="items")
    item = db.relationship("MenuItem")
    modifiers = db.relationship("CartItemModifier", back_populates="cart_item", cascade="all, delete-orphan")

    @property
    def unit_price(self):
        return self.item.price + sum(m.option.extra_price or 0 for m in self.modifiers)

    @property
    def line_total(self):
        return round(self.unit_price * self.quantity, 2)


class CartItemModifier(db.Model):
    __tablename__ = "cart_item_modifiers"
    id = db.Column(db.Integer, primary_key=True)
    cart_item_id = db.Column(db.Integer, db.ForeignKey("cart_items.id"), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey("modifier_options.id"), nullable=False)
    cart_item = db.relationship("CartItem", back_populates="modifiers")
    option = db.relationship("ModifierOption")


# ---------- Orders & payments ----------
class Order(TimestampMixin, db.Model):
    __tablename__ = "orders"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    coupon_id = db.Column(db.Integer, db.ForeignKey("coupons.id"))
    order_type = db.Column(db.String(10), nullable=False)  # delivery | pickup
    status = db.Column(db.String(20), default="placed", nullable=False)
    customer_name = db.Column(db.String(80), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    delivery_fee = db.Column(db.Float, default=0)
    total = db.Column(db.Float, nullable=False)
    user = db.relationship("User", back_populates="orders")
    coupon = db.relationship("Coupon")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    history = db.relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    payment = db.relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    delivery = db.relationship("Delivery", back_populates="order", uselist=False, cascade="all, delete-orphan")


class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    name = db.Column(db.String(100), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order = db.relationship("Order", back_populates="items")
    item = db.relationship("MenuItem")
    modifiers = db.relationship("OrderItemModifier", back_populates="order_item", cascade="all, delete-orphan")


class OrderItemModifier(db.Model):
    __tablename__ = "order_item_modifiers"
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey("order_items.id"), nullable=False)
    name = db.Column(db.String(60), nullable=False)
    extra_price = db.Column(db.Float, default=0)
    order_item = db.relationship("OrderItem", back_populates="modifiers")


class OrderStatusHistory(TimestampMixin, db.Model):
    __tablename__ = "order_status_history"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    order = db.relationship("Order", back_populates="history")


class PaymentMethod(db.Model):
    __tablename__ = "payment_methods"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    def __str__(self):
        return self.name


class Payment(TimestampMixin, db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True, nullable=False)
    method_id = db.Column(db.Integer, db.ForeignKey("payment_methods.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="pending")
    order = db.relationship("Order", back_populates="payment")
    method = db.relationship("PaymentMethod")


class Coupon(db.Model):
    __tablename__ = "coupons"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    percent_off = db.Column(db.Integer, nullable=False)
    min_subtotal = db.Column(db.Float, default=0)
    expires_on = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    usages = db.relationship("CouponUsage", back_populates="coupon", cascade="all, delete-orphan")

    def __str__(self):
        return self.code


class CouponUsage(TimestampMixin, db.Model):
    __tablename__ = "coupon_usages"
    id = db.Column(db.Integer, primary_key=True)
    coupon_id = db.Column(db.Integer, db.ForeignKey("coupons.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    coupon = db.relationship("Coupon", back_populates="usages")


class Promotion(db.Model):
    """Limited-time offer shown on the menu page."""
    __tablename__ = "promotions"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    starts_on = db.Column(db.Date)
    ends_on = db.Column(db.Date)
    items = db.relationship("PromotionItem", back_populates="promotion", cascade="all, delete-orphan")

    def __str__(self):
        return self.title


class PromotionItem(db.Model):
    __tablename__ = "promotion_items"
    id = db.Column(db.Integer, primary_key=True)
    promotion_id = db.Column(db.Integer, db.ForeignKey("promotions.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    promo_price = db.Column(db.Float, nullable=False)
    promotion = db.relationship("Promotion", back_populates="items")
    item = db.relationship("MenuItem")


# ---------- Delivery ----------
class DeliveryZone(db.Model):
    __tablename__ = "delivery_zones"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(60), nullable=False)
    zip_code = db.Column(db.String(10), unique=True, nullable=False)
    fee = db.Column(db.Float, default=0, nullable=False)
    deliveries = db.relationship("Delivery", back_populates="zone")

    def __str__(self):
        return f"{self.name} ({self.zip_code})"


class DeliveryDriver(db.Model):
    __tablename__ = "delivery_drivers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(30))
    deliveries = db.relationship("Delivery", back_populates="driver")

    def __str__(self):
        return self.name


class Delivery(db.Model):
    __tablename__ = "deliveries"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), unique=True, nullable=False)
    zone_id = db.Column(db.Integer, db.ForeignKey("delivery_zones.id"))
    driver_id = db.Column(db.Integer, db.ForeignKey("delivery_drivers.id"))
    street = db.Column(db.String(150), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    order = db.relationship("Order", back_populates="delivery")
    zone = db.relationship("DeliveryZone", back_populates="deliveries")
    driver = db.relationship("DeliveryDriver", back_populates="deliveries")


# ---------- Store, reviews, reservations ----------
class StoreInfo(db.Model):
    __tablename__ = "store_info"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    street = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(60), nullable=False)
    zip_code = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    hours = db.relationship("OpeningHours", back_populates="store", cascade="all, delete-orphan")
    holidays = db.relationship("Holiday", back_populates="store", cascade="all, delete-orphan")
    tables = db.relationship("DiningTable", back_populates="store", cascade="all, delete-orphan")

    def __str__(self):
        return self.name


class OpeningHours(db.Model):
    __tablename__ = "opening_hours"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("store_info.id"), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 0 = Monday
    opens = db.Column(db.String(8), nullable=False)
    closes = db.Column(db.String(8), nullable=False)
    store = db.relationship("StoreInfo", back_populates="hours")


class Holiday(db.Model):
    __tablename__ = "holidays"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("store_info.id"), nullable=False)
    on_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(100))
    store = db.relationship("StoreInfo", back_populates="holidays")


class DiningTable(db.Model):
    __tablename__ = "dining_tables"
    id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer, db.ForeignKey("store_info.id"), nullable=False)
    label = db.Column(db.String(20), nullable=False)
    seats = db.Column(db.Integer, nullable=False)
    store = db.relationship("StoreInfo", back_populates="tables")
    reservations = db.relationship("Reservation", back_populates="table")

    def __str__(self):
        return f"{self.label} ({self.seats} seats)"


class Reservation(TimestampMixin, db.Model):
    __tablename__ = "reservations"
    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey("dining_tables.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    guest_name = db.Column(db.String(80), nullable=False)
    guest_phone = db.Column(db.String(30), nullable=False)
    party_size = db.Column(db.Integer, nullable=False)
    reserved_for = db.Column(db.DateTime, nullable=False)
    table = db.relationship("DiningTable", back_populates="reservations")
    user = db.relationship("User", backref="reservations")


class Review(TimestampMixin, db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    user = db.relationship("User", back_populates="reviews")
    item = db.relationship("MenuItem", back_populates="reviews")
    replies = db.relationship("ReviewReply", back_populates="review", cascade="all, delete-orphan")


class ReviewReply(TimestampMixin, db.Model):
    __tablename__ = "review_replies"
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    review = db.relationship("Review", back_populates="replies")
    user = db.relationship("User")


class Favorite(db.Model):
    __tablename__ = "favorites"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("user_id", "item_id"),)
    user = db.relationship("User", backref="favorites")
    item = db.relationship("MenuItem")


class ContactMessage(TimestampMixin, db.Model):
    __tablename__ = "contact_messages"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
