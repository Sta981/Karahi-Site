# Database dictionary

| Table | Column | Type | Required | Key / reference |
|---|---|---|---|---|
| addresses | id | INTEGER | Yes | PK |
| addresses | user_id | INTEGER | Yes | users.id |
| addresses | label | VARCHAR(30) | No |  |
| addresses | street | VARCHAR(150) | Yes |  |
| addresses | city | VARCHAR(60) | No |  |
| addresses | zip_code | VARCHAR(10) | Yes |  |
| allergens | id | INTEGER | Yes | PK |
| allergens | name | VARCHAR(40) | Yes | Unique |
| attendance_records | id | INTEGER | Yes | PK |
| attendance_records | staff_id | INTEGER | Yes | staff_members.id |
| attendance_records | clock_in | DATETIME | Yes |  |
| attendance_records | clock_out | DATETIME | No |  |
| audit_logs | id | INTEGER | Yes | PK |
| audit_logs | actor_id | INTEGER | Yes | users.id |
| audit_logs | action | VARCHAR(80) | Yes |  |
| audit_logs | entity | VARCHAR(80) | Yes |  |
| audit_logs | entity_id | INTEGER | Yes |  |
| audit_logs | created_at | DATETIME | Yes |  |
| cart_item_modifiers | id | INTEGER | Yes | PK |
| cart_item_modifiers | cart_item_id | INTEGER | Yes | cart_items.id |
| cart_item_modifiers | option_id | INTEGER | Yes | modifier_options.id |
| cart_items | id | INTEGER | Yes | PK |
| cart_items | cart_id | INTEGER | Yes | carts.id |
| cart_items | item_id | INTEGER | Yes | menu_items.id |
| cart_items | quantity | INTEGER | Yes |  |
| cart_items | note | VARCHAR(200) | No |  |
| carts | id | INTEGER | Yes | PK |
| carts | user_id | INTEGER | No | users.id |
| carts | session_key | VARCHAR(64) | No |  |
| carts | created_at | DATETIME | Yes |  |
| cash_sessions | id | INTEGER | Yes | PK |
| cash_sessions | cashier_id | INTEGER | Yes | users.id |
| cash_sessions | opened_at | DATETIME | Yes |  |
| cash_sessions | closed_at | DATETIME | No |  |
| cash_sessions | opening_balance | NUMERIC(12, 2) | Yes |  |
| cash_sessions | closing_balance | NUMERIC(12, 2) | No |  |
| categories | id | INTEGER | Yes | PK |
| categories | name | VARCHAR(60) | Yes | Unique |
| categories | slug | VARCHAR(60) | Yes | Unique |
| categories | sort_order | INTEGER | No |  |
| combo_items | id | INTEGER | Yes | PK |
| combo_items | combo_id | INTEGER | Yes | combos.id |
| combo_items | item_id | INTEGER | Yes | menu_items.id |
| combo_items | quantity | INTEGER | Yes |  |
| combos | id | INTEGER | Yes | PK |
| combos | name | VARCHAR(80) | Yes |  |
| combos | price | FLOAT | Yes |  |
| contact_messages | id | INTEGER | Yes | PK |
| contact_messages | name | VARCHAR(80) | Yes |  |
| contact_messages | email | VARCHAR(120) | Yes |  |
| contact_messages | message | TEXT | Yes |  |
| contact_messages | user_id | INTEGER | No | users.id |
| contact_messages | assigned_to | INTEGER | No | users.id |
| contact_messages | department | VARCHAR(30) | Yes |  |
| contact_messages | is_resolved | BOOLEAN | No |  |
| contact_messages | created_at | DATETIME | Yes |  |
| coupon_usages | id | INTEGER | Yes | PK |
| coupon_usages | coupon_id | INTEGER | Yes | coupons.id |
| coupon_usages | user_id | INTEGER | No | users.id |
| coupon_usages | order_id | INTEGER | No | orders.id |
| coupon_usages | created_at | DATETIME | Yes |  |
| coupons | id | INTEGER | Yes | PK |
| coupons | code | VARCHAR(30) | Yes | Unique |
| coupons | percent_off | INTEGER | Yes |  |
| coupons | min_subtotal | FLOAT | No |  |
| coupons | expires_on | DATE | No |  |
| coupons | is_active | BOOLEAN | No |  |
| deliveries | id | INTEGER | Yes | PK |
| deliveries | order_id | INTEGER | Yes | Unique; orders.id |
| deliveries | zone_id | INTEGER | No | delivery_zones.id |
| deliveries | driver_id | INTEGER | No | delivery_drivers.id |
| deliveries | street | VARCHAR(150) | Yes |  |
| deliveries | zip_code | VARCHAR(10) | Yes |  |
| delivery_drivers | id | INTEGER | Yes | PK |
| delivery_drivers | name | VARCHAR(80) | Yes |  |
| delivery_drivers | phone | VARCHAR(30) | No |  |
| delivery_zones | id | INTEGER | Yes | PK |
| delivery_zones | name | VARCHAR(60) | Yes |  |
| delivery_zones | zip_code | VARCHAR(10) | Yes | Unique |
| delivery_zones | fee | FLOAT | Yes |  |
| dining_tables | id | INTEGER | Yes | PK |
| dining_tables | store_id | INTEGER | Yes | store_info.id |
| dining_tables | label | VARCHAR(20) | Yes |  |
| dining_tables | seats | INTEGER | Yes |  |
| expenses | id | INTEGER | Yes | PK |
| expenses | recorded_by | INTEGER | Yes | users.id |
| expenses | category | VARCHAR(60) | Yes |  |
| expenses | description | VARCHAR(200) | Yes |  |
| expenses | amount | NUMERIC(12, 2) | Yes |  |
| expenses | created_at | DATETIME | Yes |  |
| favorites | id | INTEGER | Yes | PK |
| favorites | user_id | INTEGER | Yes | users.id |
| favorites | item_id | INTEGER | Yes | menu_items.id |
| holidays | id | INTEGER | Yes | PK |
| holidays | store_id | INTEGER | Yes | store_info.id |
| holidays | on_date | DATE | Yes |  |
| holidays | reason | VARCHAR(100) | No |  |
| ingredients | id | INTEGER | Yes | PK |
| ingredients | name | VARCHAR(60) | Yes | Unique |
| ingredients | supplier_id | INTEGER | No | suppliers.id |
| ingredients | unit | VARCHAR(16) | Yes |  |
| ingredients | reorder_level | NUMERIC(12, 3) | Yes |  |
| item_allergens | id | INTEGER | Yes | PK |
| item_allergens | item_id | INTEGER | Yes | menu_items.id |
| item_allergens | allergen_id | INTEGER | Yes | allergens.id |
| item_images | id | INTEGER | Yes | PK |
| item_images | item_id | INTEGER | Yes | menu_items.id |
| item_images | url | VARCHAR(255) | Yes |  |
| item_images | alt_text | VARCHAR(150) | No |  |
| item_ingredients | id | INTEGER | Yes | PK |
| item_ingredients | item_id | INTEGER | Yes | menu_items.id |
| item_ingredients | ingredient_id | INTEGER | Yes | ingredients.id |
| item_ingredients | quantity | NUMERIC(12, 3) | Yes |  |
| item_modifier_groups | id | INTEGER | Yes | PK |
| item_modifier_groups | item_id | INTEGER | Yes | menu_items.id |
| item_modifier_groups | group_id | INTEGER | Yes | modifier_groups.id |
| item_tags | id | INTEGER | Yes | PK |
| item_tags | item_id | INTEGER | Yes | menu_items.id |
| item_tags | tag_id | INTEGER | Yes | tags.id |
| loyalty_accounts | id | INTEGER | Yes | PK |
| loyalty_accounts | user_id | INTEGER | Yes | Unique; users.id |
| loyalty_accounts | points | INTEGER | Yes |  |
| loyalty_transactions | id | INTEGER | Yes | PK |
| loyalty_transactions | account_id | INTEGER | Yes | loyalty_accounts.id |
| loyalty_transactions | order_id | INTEGER | No | orders.id |
| loyalty_transactions | points | INTEGER | Yes |  |
| loyalty_transactions | reason | VARCHAR(120) | No |  |
| loyalty_transactions | created_at | DATETIME | Yes |  |
| menu_items | id | INTEGER | Yes | PK |
| menu_items | category_id | INTEGER | Yes | categories.id |
| menu_items | name | VARCHAR(100) | Yes |  |
| menu_items | description | TEXT | No |  |
| menu_items | price | FLOAT | Yes |  |
| menu_items | is_available | BOOLEAN | No |  |
| menu_items | is_spicy | BOOLEAN | No |  |
| menu_items | is_vegetarian | BOOLEAN | No |  |
| modifier_groups | id | INTEGER | Yes | PK |
| modifier_groups | name | VARCHAR(60) | Yes |  |
| modifier_groups | is_required | BOOLEAN | No |  |
| modifier_groups | allow_multiple | BOOLEAN | No |  |
| modifier_options | id | INTEGER | Yes | PK |
| modifier_options | group_id | INTEGER | Yes | modifier_groups.id |
| modifier_options | name | VARCHAR(60) | Yes |  |
| modifier_options | extra_price | FLOAT | No |  |
| notifications | id | INTEGER | Yes | PK |
| notifications | user_id | INTEGER | Yes | users.id |
| notifications | message | VARCHAR(255) | Yes |  |
| notifications | is_read | BOOLEAN | No |  |
| notifications | created_at | DATETIME | Yes |  |
| nutrition_info | id | INTEGER | Yes | PK |
| nutrition_info | item_id | INTEGER | Yes | Unique; menu_items.id |
| nutrition_info | calories | INTEGER | No |  |
| nutrition_info | protein_g | FLOAT | No |  |
| nutrition_info | carbs_g | FLOAT | No |  |
| nutrition_info | fat_g | FLOAT | No |  |
| opening_hours | id | INTEGER | Yes | PK |
| opening_hours | store_id | INTEGER | Yes | store_info.id |
| opening_hours | weekday | INTEGER | Yes |  |
| opening_hours | opens | VARCHAR(8) | Yes |  |
| opening_hours | closes | VARCHAR(8) | Yes |  |
| order_item_modifiers | id | INTEGER | Yes | PK |
| order_item_modifiers | order_item_id | INTEGER | Yes | order_items.id |
| order_item_modifiers | name | VARCHAR(60) | Yes |  |
| order_item_modifiers | extra_price | FLOAT | No |  |
| order_items | id | INTEGER | Yes | PK |
| order_items | order_id | INTEGER | Yes | orders.id |
| order_items | item_id | INTEGER | No | menu_items.id |
| order_items | name | VARCHAR(100) | Yes |  |
| order_items | unit_price | FLOAT | Yes |  |
| order_items | quantity | INTEGER | Yes |  |
| order_status_history | id | INTEGER | Yes | PK |
| order_status_history | order_id | INTEGER | Yes | orders.id |
| order_status_history | status | VARCHAR(20) | Yes |  |
| order_status_history | actor_id | INTEGER | No | users.id |
| order_status_history | created_at | DATETIME | Yes |  |
| orders | id | INTEGER | Yes | PK |
| orders | user_id | INTEGER | No | users.id |
| orders | coupon_id | INTEGER | No | coupons.id |
| orders | table_id | INTEGER | No | dining_tables.id |
| orders | waiter_id | INTEGER | No | users.id |
| orders | order_type | VARCHAR(10) | Yes |  |
| orders | status | VARCHAR(20) | Yes |  |
| orders | customer_name | VARCHAR(80) | Yes |  |
| orders | customer_phone | VARCHAR(30) | Yes |  |
| orders | subtotal | FLOAT | Yes |  |
| orders | discount | FLOAT | No |  |
| orders | delivery_fee | FLOAT | No |  |
| orders | total | FLOAT | Yes |  |
| orders | created_at | DATETIME | Yes |  |
| payment_methods | id | INTEGER | Yes | PK |
| payment_methods | name | VARCHAR(40) | Yes | Unique |
| payment_methods | is_active | BOOLEAN | No |  |
| payments | id | INTEGER | Yes | PK |
| payments | order_id | INTEGER | Yes | orders.id |
| payments | method_id | INTEGER | Yes | payment_methods.id |
| payments | amount | FLOAT | Yes |  |
| payments | status | VARCHAR(20) | No |  |
| payments | received_by | INTEGER | No | users.id |
| payments | created_at | DATETIME | Yes |  |
| permissions | id | INTEGER | Yes | PK |
| permissions | code | VARCHAR(64) | Yes | Unique |
| promotion_items | id | INTEGER | Yes | PK |
| promotion_items | promotion_id | INTEGER | Yes | promotions.id |
| promotion_items | item_id | INTEGER | Yes | menu_items.id |
| promotion_items | promo_price | FLOAT | Yes |  |
| promotions | id | INTEGER | Yes | PK |
| promotions | title | VARCHAR(100) | Yes |  |
| promotions | description | TEXT | No |  |
| promotions | starts_on | DATE | No |  |
| promotions | ends_on | DATE | No |  |
| purchase_order_items | id | INTEGER | Yes | PK |
| purchase_order_items | purchase_id | INTEGER | Yes | purchase_orders.id |
| purchase_order_items | ingredient_id | INTEGER | Yes | ingredients.id |
| purchase_order_items | quantity | NUMERIC(12, 3) | Yes |  |
| purchase_order_items | unit_cost | NUMERIC(12, 2) | Yes |  |
| purchase_orders | id | INTEGER | Yes | PK |
| purchase_orders | supplier_id | INTEGER | Yes | suppliers.id |
| purchase_orders | requested_by | INTEGER | Yes | users.id |
| purchase_orders | status | VARCHAR(20) | Yes |  |
| purchase_orders | created_at | DATETIME | Yes |  |
| reservations | id | INTEGER | Yes | PK |
| reservations | table_id | INTEGER | Yes | dining_tables.id |
| reservations | user_id | INTEGER | No | users.id |
| reservations | guest_name | VARCHAR(80) | Yes |  |
| reservations | guest_phone | VARCHAR(30) | Yes |  |
| reservations | party_size | INTEGER | Yes |  |
| reservations | reserved_for | DATETIME | Yes |  |
| reservations | ends_at | DATETIME | No |  |
| reservations | status | VARCHAR(20) | Yes |  |
| reservations | created_at | DATETIME | Yes |  |
| review_replies | id | INTEGER | Yes | PK |
| review_replies | review_id | INTEGER | Yes | reviews.id |
| review_replies | user_id | INTEGER | Yes | users.id |
| review_replies | body | TEXT | Yes |  |
| review_replies | created_at | DATETIME | Yes |  |
| reviews | id | INTEGER | Yes | PK |
| reviews | user_id | INTEGER | Yes | users.id |
| reviews | item_id | INTEGER | Yes | menu_items.id |
| reviews | rating | INTEGER | Yes |  |
| reviews | comment | TEXT | No |  |
| reviews | created_at | DATETIME | Yes |  |
| role_permissions | id | INTEGER | Yes | PK |
| role_permissions | role_id | INTEGER | Yes | roles.id |
| role_permissions | permission_id | INTEGER | Yes | permissions.id |
| roles | id | INTEGER | Yes | PK |
| roles | name | VARCHAR(30) | Yes | Unique |
| service_requests | id | INTEGER | Yes | PK |
| service_requests | customer_id | INTEGER | Yes | users.id |
| service_requests | order_id | INTEGER | No | orders.id |
| service_requests | assigned_to | INTEGER | No | users.id |
| service_requests | body | VARCHAR(500) | Yes |  |
| service_requests | status | VARCHAR(20) | Yes |  |
| service_requests | created_at | DATETIME | Yes |  |
| staff_leaves | id | INTEGER | Yes | PK |
| staff_leaves | staff_id | INTEGER | Yes | staff_members.id |
| staff_leaves | leave_type | VARCHAR(40) | No |  |
| staff_leaves | start_date | DATE | Yes |  |
| staff_leaves | end_date | DATE | Yes |  |
| staff_leaves | reason | TEXT | Yes |  |
| staff_leaves | status | VARCHAR(20) | No |  |
| staff_leaves | created_at | DATETIME | Yes |  |
| staff_members | id | INTEGER | Yes | PK |
| staff_members | user_id | INTEGER | No | Unique; users.id |
| staff_members | name | VARCHAR(80) | Yes |  |
| staff_members | role | VARCHAR(50) | Yes |  |
| staff_members | phone | VARCHAR(30) | No |  |
| staff_members | email | VARCHAR(120) | No |  |
| staff_members | salary_monthly | FLOAT | No |  |
| staff_members | manager_id | INTEGER | No | staff_members.id |
| staff_members | shift_status | VARCHAR(20) | No |  |
| staff_members | shift_hours_done | FLOAT | No |  |
| staff_members | shift_hours_total | FLOAT | No |  |
| staff_members | avatar_url | VARCHAR(255) | No |  |
| staff_members | joined_date | DATE | No |  |
| staff_members | created_at | DATETIME | Yes |  |
| staff_messages | id | INTEGER | Yes | PK |
| staff_messages | staff_id | INTEGER | Yes | staff_members.id |
| staff_messages | sender_id | INTEGER | Yes | users.id |
| staff_messages | subject | VARCHAR(120) | Yes |  |
| staff_messages | body | TEXT | Yes |  |
| staff_messages | reply | TEXT | No |  |
| staff_messages | replied_at | DATETIME | No |  |
| staff_messages | created_at | DATETIME | Yes |  |
| staff_payrolls | id | INTEGER | Yes | PK |
| staff_payrolls | staff_id | INTEGER | Yes | staff_members.id |
| staff_payrolls | month | VARCHAR(20) | Yes |  |
| staff_payrolls | year | INTEGER | Yes |  |
| staff_payrolls | base_salary | FLOAT | Yes |  |
| staff_payrolls | bonus | FLOAT | No |  |
| staff_payrolls | deductions | FLOAT | No |  |
| staff_payrolls | net_salary | FLOAT | Yes |  |
| staff_payrolls | payment_status | VARCHAR(20) | No |  |
| staff_payrolls | created_at | DATETIME | Yes |  |
| staff_shifts | id | INTEGER | Yes | PK |
| staff_shifts | staff_id | INTEGER | Yes | staff_members.id |
| staff_shifts | starts_at | DATETIME | Yes |  |
| staff_shifts | ends_at | DATETIME | Yes |  |
| stock_batches | id | INTEGER | Yes | PK |
| stock_batches | ingredient_id | INTEGER | Yes | ingredients.id |
| stock_batches | supplier_id | INTEGER | No | suppliers.id |
| stock_batches | remaining | NUMERIC(12, 3) | Yes |  |
| stock_batches | unit_cost | NUMERIC(12, 2) | Yes |  |
| stock_batches | expires_on | DATE | No |  |
| stock_batches | created_at | DATETIME | Yes |  |
| stock_movements | id | INTEGER | Yes | PK |
| stock_movements | batch_id | INTEGER | Yes | stock_batches.id |
| stock_movements | order_id | INTEGER | No | orders.id |
| stock_movements | actor_id | INTEGER | Yes | users.id |
| stock_movements | quantity | NUMERIC(12, 3) | Yes |  |
| stock_movements | reason | VARCHAR(30) | Yes |  |
| stock_movements | created_at | DATETIME | Yes |  |
| store_info | id | INTEGER | Yes | PK |
| store_info | name | VARCHAR(80) | Yes |  |
| store_info | street | VARCHAR(150) | Yes |  |
| store_info | city | VARCHAR(60) | Yes |  |
| store_info | zip_code | VARCHAR(10) | Yes |  |
| store_info | phone | VARCHAR(30) | Yes |  |
| suppliers | id | INTEGER | Yes | PK |
| suppliers | name | VARCHAR(80) | Yes |  |
| suppliers | phone | VARCHAR(30) | No |  |
| tags | id | INTEGER | Yes | PK |
| tags | name | VARCHAR(40) | Yes | Unique |
| users | id | INTEGER | Yes | PK |
| users | role_id | INTEGER | Yes | roles.id |
| users | name | VARCHAR(80) | Yes |  |
| users | email | VARCHAR(120) | Yes | Unique |
| users | phone | VARCHAR(30) | No |  |
| users | is_active | BOOLEAN | Yes |  |
| users | password_hash | VARCHAR(256) | Yes |  |
| users | created_at | DATETIME | Yes |  |