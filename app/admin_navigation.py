"""RestroIQ Enterprise Navigation Structure.
Every model and operational view has a categorized, accessible destination.
"""
NAV = [
    ('Workspace', 'Overview', '◈', [
        ('Dashboard Overview', '@dashboard'),
        ('Sales & Analytics', '@analytics'),
        ('Staff & Operations', '@staff'),
        ('Data Directory', '@directory')
    ]),
    ('Operations', 'Order Management', '▤', [
        ('POS Order Workspace', '@orders'),
        ('Orders (Master Table)', 'orders'),
        ('Order Items', 'order_items'),
        ('Order Customizations', 'order_item_modifiers'),
        ('Order Status History', 'order_status_history'),
        ('Shopping Carts', 'carts'),
        ('Cart Items', 'cart_items'),
        ('Cart Options', 'cart_item_modifiers')
    ]),
    ('Operations', 'Kitchen & KDS', '♨', [
        ('Kitchen Display Board', '@kitchen'),
        ('Dish Ingredients', 'item_ingredients'),
        ('Raw Materials / Ingredients', 'ingredients')
    ]),
    ('Operations', 'Tables & Bookings', '▦', [
        ('Table Reservations Board', '@tables'),
        ('Dining Tables Floorplan', 'dining_tables'),
        ('Reservations Records', 'reservations')
    ]),
    ('Operations', 'Delivery & Logistics', '↗', [
        ('Active Deliveries', 'deliveries'),
        ('Delivery Zones & Fees', 'delivery_zones'),
        ('Delivery Drivers', 'delivery_drivers')
    ]),
    ('Staff & HR', 'Team & Payroll', '👥', [
        ('Staff Hub & Shifts', '@staff'),
        ('Team messages', '@staff_messages'),
        ('Staff Profiles & Roles', 'staff_members'),
        ('Leave Requests & Approvals', 'staff_leaves'),
        ('Salaries & Payroll Records', 'staff_payrolls')
    ]),
    ('Catalog', 'Menu Management', '☷', [
        ('Menu Items (Dishes)', 'menu_items'),
        ('Categories', 'categories'),
        ('Food Photography', 'item_images'),
        ('Nutrition & Calorie Info', 'nutrition_info'),
        ('Dietary Tags', 'tags'),
        ('Item Tags Mapping', 'item_tags'),
        ('Allergens', 'allergens'),
        ('Item Allergens Mapping', 'item_allergens')
    ]),
    ('Catalog', 'Customization & Combos', '⊕', [
        ('Modifier Groups', 'modifier_groups'),
        ('Modifier Options', 'modifier_options'),
        ('Item Modifier Links', 'item_modifier_groups'),
        ('Meal Combos', 'combos'),
        ('Combo Items', 'combo_items')
    ]),
    ('Catalog', 'Procurement & Supply', '▧', [
        ('Suppliers & Vendors', 'suppliers'),
        ('Ingredient Inventory', 'ingredients'),
        ('Item Recipe Links', 'item_ingredients')
    ]),
    ('Business', 'Finance & Billing', '◉', [
        ('Revenue Intelligence', '@analytics'),
        ('Payment Transactions', 'payments'),
        ('Payment Methods', 'payment_methods')
    ]),
    ('Business', 'Discounts & Growth', '✦', [
        ('Special Promotions', 'promotions'),
        ('Promotion Items', 'promotion_items'),
        ('Coupons & Vouchers', 'coupons'),
        ('Coupon Redemption Logs', 'coupon_usages')
    ]),
    ('Business', 'Customers & Loyalty', '♙', [
        ('Customer Accounts', 'users'),
        ('Delivery Addresses', 'addresses'),
        ('Loyalty Accounts', 'loyalty_accounts'),
        ('Loyalty Points Activity', 'loyalty_transactions'),
        ('Customer Favorites', 'favorites'),
        ('In-App Notifications', 'notifications')
    ]),
    ('Business', 'Feedback & Support', '✉', [
        ('Customer Reviews', 'reviews'),
        ('Management Replies', 'review_replies'),
        ('Contact Inquiry Inbox', 'contact_messages')
    ]),
    ('Administration', 'Store Configuration', '⚙', [
        ('Store Information', 'store_info'),
        ('Operating Hours', 'opening_hours'),
        ('Holidays & Closures', 'holidays')
    ]),
    ('Administration', 'Security & Access', '⊙', [
        ('User Accounts & Passwords', 'users'),
        ('Security Roles & Permissions', 'roles')
    ])
]

LABELS = {target: label for _, _, _, links in NAV for label, target in links if not target.startswith('@')}
