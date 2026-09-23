# V1 Final Spec

## 1. Project Name

Rental App

## 2. Purpose

A simple internal web app for daily rental operations of kayak and paddleboard equipment. V1 targets internal staff and focuses on the real operational workflow: customer → order → check-in → inventory → return → payment.

## 3. Core Principles

- Business model first.
- V1 is intentionally small and practical.
- One transaction = one `Order`.
- Reservation / Walk-in are not separate entities.
- Frontend validation is helpful but cannot replace backend rules.
- Backend is the single source of truth for business validation.
- SQLite is the default V1 database.
- Business timezone: `Asia/Shanghai`.
- Database timezone: `UTC`.
- Money is stored as integer fen.

## 4. V1 Scope

### Included

- Login
- Customer management
- Order management
- Equipment catalog
- SaleItem catalog
- Inventory configuration and real-time calculation
- Check-in
- Return
- Auto Return
- Daily Forced Return
- Payment calculation
- Payment “Other” adjustments
- Dashboard basics
- Settings basics
- Backup / Restore if time allows

### Excluded

- Boat / BoatAssignment
- Reservation entity
- Walk-in entity
- Order type system
- customer self-service
- online payment
- WeChat login
- roles and permissions
- multi-store support
- advanced accounting
- payment status tracking
- payment method tracking
- payment channel tracking
- AI matching
- fuzzy/pinyin matching
- inventory transaction history
- advanced BI

## 5. Core Data Model

### users

- id
- username
- display_name
- password_hash
- is_active
- is_system
- created_at
- updated_at

System User exists and is protected.

### customers

- id
- name
- gender
- wechat_nickname
- wechat_id
- phone
- created_by_user_id
- updated_by_user_id
- created_at
- updated_at

Requirements:

- at least one of `name + phone` or `wechat_nickname + wechat_id` to create a standalone customer
- `phone` unique if present
- `wechat_id` unique if present
- customer snapshot is stored on each Order

### equipment_types

- id
- name
- created_by_user_id
- updated_by_user_id
- created_at
- updated_at

### equipment_specs

- id
- equipment_type_id
- name
- price
- capacity
- is_active
- created_by_user_id
- updated_by_user_id
- created_at
- updated_at

### sale_items

- id
- name
- price
- is_active
- created_by_user_id
- updated_by_user_id
- created_at
- updated_at

### inventory_configurations

- id
- equipment_spec_id
- total_quantity
- updated_by_user_id
- updated_at

### orders

- id
- order_number
- customer_id
- customer snapshot fields
- start_at
- end_at
- adult_count
- child_count
- note
- status
- check_in_at
- check_in_by_user_id
- auto_return_after_minutes
- auto_return_at
- auto_return_occurred
- return_at
- return_by_user_id
- daily_forced_return_occurred
- created_by_user_id
- updated_by_user_id
- created_at
- updated_at

Allowed statuses:

- active
- cancelled
- no_show
- completed

### order_items

- id
- order_id
- equipment_spec_id or sale_item_id
- quantity
- unit_price
- created_by_user_id
- updated_by_user_id
- created_at
- updated_at

Rules:

- `unit_price` is a snapshot at creation time
- `quantity >= 1`
- one item reference only
- OrderItems are locked after Check-in

### payments

- id
- order_id

No payment status fields. No payment method fields. No paid/received amount tracking fields.

### payment_items

- id
- payment_id
- quantity
- unit_amount
- amount
- note
- created_by_user_id
- created_at

Rules:

- “Other” is the only adjustment type in V1
- no subcategories
- `note` is required
- `quantity != 0`
- `unit_amount >= 0`
- `amount = quantity × unit_amount`
- positive values increase final amount
- negative values reduce final amount
- immutable after creation

## 6. Payment Formula

Order amount is computed as:

```text
SUM(order_items.quantity × order_items.unit_price)
+
SUM(payment_items.amount)
```

This is the authoritative final amount for the order.

The system does not store a permanent `order.total_amount` field.

The system does not track “already paid” or “received amount.”

## 7. Order Lifecycle

- `active`
- `cancelled`
- `no_show`
- `completed`

Allowed transitions:

- active → cancelled
- active → no_show
- active → completed
- cancelled → active
- no_show → active
- completed → active

No other direct transitions are allowed.

## 8. Order Timing Rules

- `end_at = start_at + 2 hours`
- `end_at` is not independently editable in V1
- `check_in_at >= start_at`
- `return_at > check_in_at` when both exist
- direct return without check-in must satisfy `return_at >= start_at + 1 minute`
- business timezone: `Asia/Shanghai`
- database timestamps stored in `UTC`

## 9. Check-in and Return

### Check-in

Check-in is an operation on an `Order`, not a dedicated entity.

When check-in succeeds:

- record `check_in_at`
- record `check_in_by_user_id`
- lock OrderItems
- begin operational inventory occupation
- start Auto Return cycle

### Return

Return is also an operation on an `Order`, not a dedicated entity.

When return succeeds:

- record `return_at`
- record `return_by_user_id`
- set status to `completed`
- release occupied inventory

Direct Return without Check-in is allowed under business rules.

## 10. Auto Return and Daily Forced Return

### Auto Return

- Check-in copies `auto_return_after_minutes` to the Order
- later settings changes do not affect the active cycle
- when due and no effective return exists, system performs return using System User
- same end result: completed order + inventory released

### Daily Forced Return

- runs at fixed `Asia/Shanghai` time window `23:59:01–23:59:59`
- applies to orders with effective Check-in and no effective Return
- uses System User
- releases inventory
- sets Order to completed

Daily Forced Return is separate from ordinary Auto Return.

## 11. Inventory Rules

Inventory represents operational inventory, not physical ownership.

```text
available = total operational inventory - occupied quantity
```

Occupied quantity includes only OrderItems belonging to Orders that:

- have effective Check-in
- do not have effective Return

Future orders do not reserve inventory early.

Inventory shortage may trigger a warning, but V1 does not require a hard block.

## 12. Customer Matching

Simple match-confirm strategy only:

- operator enters a field
- backend searches likely matches
- operator confirms the correct customer

No fuzzy, pinyin, AI, or automatic merge logic required.

## 13. Payment “Other” Rule

“Other” is a single PaymentItem adjustment type with a required note.

It is not a SaleItem.

It is not a templated business category.

It is simply used to represent an extra amount with explanation, such as:

- refund
- discount
- temporary charge
- surcharge
- correction
- manual adjustment

The operator writes the reason in `note`.

A Payment may contain multiple “Other” adjustments.

## 14. Settings

Settings manages:

- Auto Return duration
- EquipmentType
- EquipmentSpec
- SaleItem
- Inventory config
- current catalog prices
- activation flags

Order duration, timezone, and Daily Forced Return timing are fixed business rules, not normal settings.

## 15. Authentication

- username + password
- password stored as hash
- inactive users cannot log in
- System User cannot log in via normal flow

## 16. Non-functional Requirements

- SQLite for V1
- Docker-friendly deployment
- simple backup/restore if time permits
- secure local deployment and external access via reverse proxy / HTTPS
- minimal dependencies

## 17. Acceptance Checklist

The project is ready for implementation when the following scenarios are satisfied:

- future order does not reserve inventory
- immediate order works without reservation vs walk-in types
- check-in locks items and begins inventory occupation
- return releases inventory and completes the order
- direct return without check-in works
- auto return executes and completes overdue orders
- daily forced return runs once at end-of-day
- payment amount is computed from order items plus other adjustments
- multiple “Other” entries are allowed in one payment
- note is mandatory for each “Other”
- boat/boat assignment is not part of V1

## 18. Implementation Boundary

This spec must be treated as the final baseline for building the first usable V1 version. Detailed technical choices (framework, API style, ORM, UI library) may vary as long as they do not conflict with the rules above.
