# ER_MODEL.md

# Rental App — Entity Relationship Model

## 1. Purpose

This document defines the V1 logical database model for Rental App.

It translates the business rules and product requirements into persistent data structures.

It defines:
- entities/tables
- important fields
- primary keys and foreign keys
- uniqueness and cardinality
- important database-level constraints
- which business concepts are represented by fields rather than separate entities

`BUSINESS_RULES.md` remains authoritative for business behavior.

---

## 2. Database Conventions

### 2.1 Database
V1 uses SQLite.

### 2.2 Primary keys
All primary keys use UUID values, stored as SQLite `TEXT`.

Primary key column name: `id`.

### 2.3 Foreign keys
Foreign keys use `<entity>_id`, for example:
- `customer_id`
- `order_id`
- `equipment_spec_id`
- `created_by_user_id`

Foreign keys should be indexed where appropriate. Default behavior should be restrictive. Historical business data must not be removed through broad cascading deletes.

### 2.4 Time
Database timestamps are UTC. Business timezone is `Asia/Shanghai`.

Timestamps use ISO 8601 UTC with seconds precision and `Z`.

### 2.5 Money
Money is stored as integer fen. UI displays yuan.

### 2.6 Boolean
Boolean values use `0` / `1`.

### 2.7 Naming
Tables and columns use plural/snake_case:
- `users`
- `customers`
- `orders`
- `order_items`

---

# 3. V1 Entity Overview

Primary entities:

1. `users`
2. `customers`
3. `equipment_types`
4. `equipment_specs`
5. `sale_items`
6. `boats`
7. `inventory_configurations`
8. `orders`
9. `order_items`
10. `boat_assignments`
11. `payments`
12. `payment_items`
13. `settings`

The following are intentionally **not** entities:

- Reservation
- ReservationItem
- Walk-in
- ActualUsage
- ActualUsageItem
- CheckIn
- Return
- ReturnItem
- OrderType

Check-in and Return are represented by fields on `orders`.

---

# 4. users

## Purpose
Stores authenticated operators and the System User.

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK, NOT NULL |
| username | TEXT | UNIQUE, NOT NULL |
| display_name | TEXT | NOT NULL |
| password_hash | TEXT | NOT NULL |
| is_active | INTEGER | NOT NULL, default 1 |
| is_system | INTEGER | NOT NULL, default 0 |
| created_at | TEXT | NOT NULL |
| updated_at | TEXT | NOT NULL |

Rules:
- `username` is unique.
- Exactly one protected System User exists.
- System User has `is_system = 1`.
- System User cannot be deleted or used for normal login.
- Automatic actions reference the System User.

---

# 5. customers

## Purpose
Stores reusable customer profiles.

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| name | TEXT | NULL |
| gender | TEXT | NULL |
| wechat_nickname | TEXT | NULL |
| wechat_id | TEXT | UNIQUE when present |
| phone | TEXT | UNIQUE when present |
| is_system | INTEGER | NOT NULL, default 0 |
| created_by_user_id | TEXT | FK, NOT NULL |
| created_at | TEXT | NOT NULL |
| updated_by_user_id | TEXT | FK, NOT NULL |
| updated_at | TEXT | NOT NULL |

A standalone Customer must satisfy:
- `(name AND phone)`, OR
- `(wechat_nickname AND wechat_id)`

`phone` and `wechat_id` are unique when present.

The protected system customer is `游客` and cannot be deleted or renamed; its phone and WeChat ID are immutable.

---

# 6. equipment_types

## Purpose
Defines broad equipment categories such as Kayak and Paddleboard.

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| name | TEXT | UNIQUE, NOT NULL |
| created_at | TEXT | NOT NULL |
| updated_at | TEXT | NOT NULL |
| created_by_user_id | TEXT | FK, NOT NULL |
| updated_by_user_id | TEXT | FK, NOT NULL |

---

# 7. equipment_specs

## Purpose
Defines specific rentable equipment specifications.

Examples:
- Racing Kayak — 3-seat
- Racing Kayak — 2-seat
- Racing Kayak — 1-seat
- Leisure Kayak — 3-seat
- Leisure Kayak — 2-seat
- Paddleboard

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| equipment_type_id | TEXT | FK, NOT NULL |
| name | TEXT | NOT NULL |
| price | INTEGER | NOT NULL |
| capacity | INTEGER | NULL/NOT NULL according to item capability |
| is_active | INTEGER | NOT NULL, default 1 |
| created_by_user_id | TEXT | FK, NOT NULL |
| created_at | TEXT | NOT NULL |
| updated_by_user_id | TEXT | FK, NOT NULL |
| updated_at | TEXT | NOT NULL |

Recommended uniqueness:
`UNIQUE(equipment_type_id, name)`

Rules:
- `price >= 0`
- inactive specs cannot be used for new Orders
- historical OrderItems may reference inactive specs
- `price` is the current catalog price, not a historical order price

---

# 8. sale_items

## Purpose
Stores separately catalogued chargeable extras such as waterproof bags.

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| name | TEXT | UNIQUE, NOT NULL |
| price | INTEGER | NOT NULL |
| is_active | INTEGER | NOT NULL, default 1 |
| created_by_user_id | TEXT | FK, NOT NULL |
| created_at | TEXT | NOT NULL |
| updated_by_user_id | TEXT | FK, NOT NULL |
| updated_at | TEXT | NOT NULL |

Rules:
- `price >= 0`
- inactive SaleItems cannot be added to new Orders
- historical OrderItems may reference inactive SaleItems

---

# 9. boats

## Purpose
Represents individually numbered physical boats.

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| equipment_spec_id | TEXT | FK, NOT NULL |
| boat_number | TEXT | UNIQUE, NOT NULL |
| status | TEXT | NOT NULL, default `available` |
| created_at | TEXT | NOT NULL |
| updated_at | TEXT | NOT NULL |

Allowed status:
- `available`
- `not_available`

A `not_available` boat cannot receive a new BoatAssignment.

---

# 10. inventory_configurations

## Purpose
Stores current operational inventory for each EquipmentSpec.

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| equipment_spec_id | TEXT | FK, UNIQUE, NOT NULL |
| total_quantity | INTEGER | NOT NULL |
| updated_by_user_id | TEXT | FK, NOT NULL |
| updated_at | TEXT | NOT NULL |

Rules:
- one configuration per EquipmentSpec
- `total_quantity >= 0`
- this is current operational inventory, not ownership history
- available quantity is calculated, not stored

---

# 11. orders

## Purpose
Central business entity for every customer transaction.

There is no separate Reservation or Walk-in entity.

## Fields

| Field | Type | Constraints | Description |
|---|---|---|---|
| id | TEXT | PK | UUID |
| order_number | TEXT | UNIQUE, NOT NULL | Human-facing order number |
| customer_id | TEXT | FK, NOT NULL | Customer |
| customer_name | TEXT | NULL | Historical snapshot |
| customer_gender | TEXT | NULL | Historical snapshot |
| customer_wechat_nickname | TEXT | NULL | Historical snapshot |
| customer_wechat_id | TEXT | NULL | Historical snapshot |
| customer_phone | TEXT | NULL | Historical snapshot |
| start_at | TEXT | NOT NULL | UTC |
| end_at | TEXT | NOT NULL | UTC |
| adult_count | INTEGER | NOT NULL | Adults |
| child_count | INTEGER | NOT NULL | Children |
| note | TEXT | NULL | Operator note |
| status | TEXT | NOT NULL, default `active` | Lifecycle status |
| created_at | TEXT | NOT NULL | UTC |
| updated_at | TEXT | NOT NULL | UTC |
| check_in_at | TEXT | NULL | Current Check-in |
| check_in_by_user_id | TEXT | FK, NULL | Check-in actor |
| auto_return_after_minutes | INTEGER | NULL | Check-in snapshot |
| auto_return_at | TEXT | NULL | Auto Return time |
| auto_return_occurred | INTEGER | NOT NULL, default 0 | Auto Return marker |
| return_at | TEXT | NULL | Current effective Return |
| return_by_user_id | TEXT | FK, NULL | Return actor |
| daily_forced_return_occurred | INTEGER | NOT NULL, default 0 | Daily Forced Return marker |
| created_by_user_id | TEXT | FK, NOT NULL | Creator |
| updated_by_user_id | TEXT | FK, NOT NULL | Last updater |

Allowed status:
- `active`
- `cancelled`
- `no_show`
- `completed`

Important constraints:
- `end_at = start_at + 2 hours`
- `end_at > start_at`
- adult/child counts are non-negative
- total people >= 1
- if Check-in exists: `check_in_at >= start_at`
- Check-in must be on the same Asia/Shanghai calendar date as the Order date
- if both Check-in and Return exist: `return_at > check_in_at`
- if Return exists without Check-in: `return_at >= start_at + 1 minute`

Check-in state is the pair:
- `check_in_at`
- `check_in_by_user_id`

Return state is the pair:
- `return_at`
- `return_by_user_id`

Auto Return invariants:
- `auto_return_occurred = 0` ↔ `auto_return_at IS NULL`
- `auto_return_occurred = 1` ↔ `auto_return_at IS NOT NULL`
- when occurred, `auto_return_at > check_in_at`
- current Return cannot precede Auto Return time

`daily_forced_return_occurred` identifies that the current effective Return was produced by the daily end-of-day mechanism.

---

# 12. order_items

## Purpose
Stores normal chargeable items belonging to an Order.

An OrderItem can represent either:
- an EquipmentSpec
- a SaleItem

This keeps normal chargeable items in one place and prevents Payment from duplicating item selection.

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| order_id | TEXT | FK, NOT NULL |
| equipment_spec_id | TEXT | FK, NULL |
| sale_item_id | TEXT | FK, NULL |
| quantity | INTEGER | NOT NULL |
| unit_price | INTEGER | NOT NULL |
| created_by_user_id | TEXT | FK, NOT NULL |
| created_at | TEXT | NOT NULL |
| updated_by_user_id | TEXT | FK, NOT NULL |
| updated_at | TEXT | NOT NULL |

Business invariant:

`exactly one of equipment_spec_id and sale_item_id is non-NULL`

Other constraints:
- `quantity >= 1`
- `unit_price >= 0`

`unit_price` is copied from the catalog at creation and becomes the historical price snapshot.

Line amount is calculated:
`quantity × unit_price`

No separate `amount` field is required.

Only OrderItems referencing EquipmentSpec affect equipment inventory.

OrderItems are editable before effective Check-in and locked after effective Check-in. Effective Return also leaves them locked.

---

# 13. boat_assignments

## Purpose
Optional assignment of an individual Boat to an OrderItem.

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| order_item_id | TEXT | FK, NOT NULL |
| boat_id | TEXT | FK, NOT NULL |
| created_by_user_id | TEXT | FK, NOT NULL |
| created_at | TEXT | NOT NULL |

Rules:
- assignment only after Check-in
- no assignment before Check-in
- assignment does not affect inventory
- assignment count does not have to equal OrderItem quantity
- no V1 overlap validation
- same Boat may appear on overlapping assignments
- `not_available` Boat cannot receive a new assignment

V1 does not require a BoatAssignment UI.

---

# 14. payments

## Purpose
Payment container associated with an Order.

## Cardinality
`orders 1 : 0..1 payments`

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| order_id | TEXT | FK, UNIQUE, NOT NULL |

V1 does not store:
- permanent payment total
- payment status
- payment method as an authoritative financial field
- duplicate equipment/payment allocation data

Current amount is derived from OrderItems plus PaymentItems.

---

# 15. payment_items

## Purpose
Stores manual financial adjustments that are not normal OrderItems.

Examples:
- discount
- surcharge
- refund
- correction
- other

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| payment_id | TEXT | FK, NOT NULL |
| type | TEXT | NOT NULL |
| item_name | TEXT | NOT NULL |
| quantity | INTEGER | NOT NULL |
| unit_price | INTEGER | NOT NULL |
| amount | INTEGER | NOT NULL |
| note | TEXT | NULL / required for `other` |
| created_by_user_id | TEXT | FK, NOT NULL |
| created_at | TEXT | NOT NULL |

V1 primarily uses `type = other`.

Constraints:
- `quantity != 0`
- `unit_price >= 0`
- `amount != 0`
- `amount = quantity × unit_price`
- `type = other` requires a note
- PaymentItems are immutable after creation

Corrections are represented by new PaymentItems.

---

# 16. settings

## Purpose
Stores true system-wide operational settings.

Settings is not a generic JSON/key-value dump.

## Fields

| Field | Type | Constraints |
|---|---|---|
| id | TEXT | PK |
| auto_return_after_minutes | INTEGER | NOT NULL, default 120 |
| boat_management_enabled | INTEGER | NOT NULL, default 1 |
| updated_by_user_id | TEXT | FK, NOT NULL |
| updated_at | TEXT | NOT NULL |

Rules:
- one active Settings row is expected
- `auto_return_after_minutes >= 1`

Equipment prices, SaleItem prices, inventory quantities, Order duration, and Daily Forced Return schedule do not belong in this table.

---

# 17. Entity Relationships

## 17.1 Customer → Order
`customers 1 : N orders`

Each Order has exactly one Customer.

A Customer can have many Orders.

Order also stores customer identity snapshots.

## 17.2 EquipmentType → EquipmentSpec
`equipment_types 1 : N equipment_specs`

## 17.3 EquipmentSpec → InventoryConfiguration
`equipment_specs 1 : 1 inventory_configurations`

## 17.4 EquipmentSpec → Boat
`equipment_specs 1 : N boats`

## 17.5 Order → OrderItem
`orders 1 : N order_items`

## 17.6 EquipmentSpec → OrderItem
`equipment_specs 1 : N order_items`

## 17.7 SaleItem → OrderItem
`sale_items 1 : N order_items`

An OrderItem references exactly one of the two item types.

## 17.8 OrderItem → BoatAssignment
`order_items 1 : N boat_assignments`

## 17.9 Boat → BoatAssignment
`boats 1 : N boat_assignments`

V1 does not require overlap validation.

## 17.10 Order → Payment
`orders 1 : 0..1 payments`

## 17.11 Payment → PaymentItem
`payments 1 : N payment_items`

---

# 18. Inventory Calculation

Inventory does not store `available_quantity`.

For an EquipmentSpec:

`occupied_quantity = SUM(OrderItem.quantity)`

where the OrderItem:
1. references that EquipmentSpec
2. belongs to an Order with effective Check-in
3. belongs to an Order without effective Return

Then:

`available_quantity = total_quantity - occupied_quantity`

Future Orders do not occupy inventory.

Cancelling Check-in removes the Order from occupied inventory.

Effective Return removes the Order from occupied inventory.

Direct Return without Check-in does not release inventory because no inventory was previously occupied.

---

# 19. Order State Representation

V1 intentionally represents several operational concepts through Order fields instead of additional tables.

### Check-in
- `check_in_at`
- `check_in_by_user_id`

### Return
- `return_at`
- `return_by_user_id`

### Auto Return
- `auto_return_after_minutes`
- `auto_return_at`
- `auto_return_occurred`

### Daily Forced Return
- `daily_forced_return_occurred`

Therefore V1 does not introduce:
- `check_ins`
- `returns`
- `return_items`

---

# 20. Status and State Separation

Order `status` contains only:
- `active`
- `cancelled`
- `no_show`
- `completed`

These must NOT become status values:
- checked_in
- returned
- auto_returned
- reserved
- walk_in
- using
- pending_payment

They are represented by fields, derived conditions, or future UI concepts.

---

# 21. Deletion and Historical Integrity

Historical business data must be preserved.

When an EquipmentSpec or SaleItem is no longer offered:
- set `is_active = 0`
- retain historical references

Orders, OrderItems, Payments, PaymentItems, and historical actor references must not be deleted merely to bypass business state rules.

Broad cascading deletes must not erase historical business data.

---

# 22. Database Constraints vs Business Validation

## Prefer database-level constraints for:
- primary keys
- foreign keys
- unique order number
- unique username
- unique phone/WeChat ID when present
- unique boat number
- unique EquipmentSpec name within EquipmentType
- non-negative standard prices
- positive OrderItem quantity
- valid enum/status values where practical
- basic structural relationships

## Prefer business-layer validation for:
- adult/child composition
- same-business-date Check-in
- Return timing
- status transitions
- inventory shortage warnings
- OrderItem locking
- Auto Return scheduling
- Daily Forced Return eligibility
- customer matching
- direct Return without Check-in

---

# 23. V1 Entities Explicitly Excluded

Do not introduce these tables merely because they are common in other rental systems:

```text
reservations
reservation_items
walk_ins
actual_usages
actual_usage_items
check_ins
returns
return_items
order_types
```

Their required concepts are already represented by the V1 model.

---

# 24. Future Evolution

Future features may add capabilities such as:
- richer BoatAssignment workflow
- inventory adjustment history
- audit log
- roles and permissions
- online customer booking
- multi-store
- richer payment features
- customer merge/history
- cloud deployment

Future additions must preserve the historical meaning of existing V1 Orders and OrderItems.

---

# 25. Implementation Independence

This document defines the logical data model, not a mandatory code folder structure or ORM.

The eventual open-source base may use:
- a different ORM
- different frontend libraries
- different internal module names
- different code organization

Those implementation details may be adapted.

However, adopting an existing project must not automatically introduce Reservation, ActualUsage, CheckIn, Return, or OrderType entities simply because the base project uses them.

The persistent business meaning defined here must remain intact unless the business model is explicitly changed.
