# PRD.md

# Rental App — Product Requirements Document

## 1. Product Overview

Rental App is an internal web application for managing day-to-day rental operations for a kayak and paddleboard business.

The V1 product is designed for operators/managers, not end customers.

The primary objective of V1 is simple:

> Allow an operator to create and manage real Orders from start to finish while keeping customer information, equipment usage, inventory, return, and payment information consistent.

The system should be practical enough to use during normal daily operations.

---

## 2. Product Principles

### 2.1 One transaction, one Order

The system uses one central business object: Order.

“Reservation” and “Walk-in” are business descriptions only.

The UI may use natural-language wording where useful, but the backend does not create different Order types based on whether the selected start time is in the future or the current time.

### 2.2 Operational simplicity

V1 should prioritize:

- fast order creation
- clear current status
- reliable inventory calculation
- simple customer matching
- simple check-in and return
- simple payment handling

V1 should avoid unnecessary workflows and duplicate data entry.

### 2.3 Real-world usability over feature count

The V1 product is considered successful when an operator can use it during actual daily rental operations without needing spreadsheets or parallel manual tracking for the core workflow.

---

## 3. Target Users

### 3.1 Operator / Manager

The V1 user is an internal operator or manager.

The user can:

- log in
- create and edit customers
- create and edit Orders
- manage equipment catalog
- manage operational inventory
- manage boats
- perform Check-in
- perform Return
- manage payment adjustments
- view operational information

### 3.2 Permissions

V1 has no role/permission matrix.

All normal authenticated users have the same functional permissions.

User accounts exist primarily to identify the person performing business-changing actions.

---

## 4. V1 Functional Modules

V1 consists of:

1. Login
2. Dashboard
3. Customer Management
4. Order Management
5. Check-in
6. Return
7. Payment
8. Equipment Management
9. Inventory Management
10. Boat Management
11. Settings
12. Basic Backup / Restore, if implementation time permits

The detailed business rules for these modules are defined in `BUSINESS_RULES.md`.

---

# 5. Login

## 5.1 Goal

Provide basic access control for the internal application.

## 5.2 Requirements

The login page provides:

- username
- password
- login action
- login failure feedback

Authenticated users can access the application.

Inactive users cannot log in.

The System User is not a normal login account.

## 5.3 V1 scope

V1 does not require:

- roles
- permissions
- SSO
- WeChat login
- SMS login
- customer accounts
- password reset workflow

---

# 6. Dashboard

## 6.1 Goal

Provide a quick view of the current operational situation.

The Dashboard should prioritize information that helps the operator run the business today.

## 6.2 V1 information

The Dashboard should provide basic information such as:

- today's Orders
- active Orders
- Orders checked in
- Orders currently using equipment
- Orders completed
- Orders requiring operator attention
- current available inventory for important equipment

The exact visual layout can be determined after selecting the project base.

## 6.3 V1 limitation

The Dashboard does not need advanced analytics.

V1 does not require:

- forecasting
- profit analysis
- customer lifetime value
- utilization forecasting
- AI recommendations
- complex BI dashboards

---

# 7. Customer Management

## 7.1 Goal

Allow operators to maintain reusable customer records and quickly identify returning customers.

## 7.2 Customer information

The UI should support:

- name
- gender
- WeChat nickname
- WeChat ID
- phone

The system also maintains the Customer's unique ID.

## 7.3 Creating a Customer

A standalone Customer must satisfy one of:

- name + phone
- WeChat nickname + WeChat ID

The UI should prevent obviously incomplete Customer records.

## 7.4 Customer matching

When the operator enters one of the customer identity fields, the application should be able to search for possible existing customers using:

- name
- WeChat nickname
- WeChat ID
- phone

The operator confirms the intended customer.

V1 uses simple candidate search.

It does not require:

- fuzzy matching
- pinyin matching
- AI matching
- automatic merge
- ranking/scoring

## 7.5 Order customer snapshot

When an Order is created, relevant Customer information is also stored on the Order as a historical snapshot.

Later Customer profile changes must not silently rewrite historical Order snapshots.

## 7.6 Customer list

The Customer page should allow operators to:

- search customers
- open a customer profile
- view basic customer information
- create a customer
- edit a customer
- start creating an Order for a customer

The exact list/filter UI can be determined during implementation.

---

# 8. Order Management

## 8.1 Goal

Order Management is the central V1 workflow.

The operator must be able to create, view, edit, cancel, restore, and complete Orders.

## 8.2 Creating an Order

The operator should be able to enter/select:

### Customer

- existing Customer
- new Customer
- System Customer “游客” where appropriate

### Time

- start date
- start time

The system automatically calculates:

`end_at = start_at + 2 hours`

The operator does not independently edit end time in V1.

### People

- adults
- children

The UI may initialize people counts based on selected equipment, but manually entered values must not later be silently overwritten.

### Items

The operator can add one or more OrderItems.

OrderItems can represent:

- rentable equipment
- additional chargeable SaleItems

For each item, the operator selects:

- item/specification
- quantity

The system obtains the current catalog price and stores it as the OrderItem unit-price snapshot.

### Note

The operator can add a free-text note.

## 8.3 Order creation does not classify Reservation vs Walk-in

The application must not ask the operator to select:

- Reservation
- Walk-in

The operator simply creates an Order and selects its start time.

The system must not create different Order types or processing paths from the selected time.

## 8.4 Order editing

Before Check-in, the operator can:

- edit customer information/reference
- edit start time
- edit people counts
- add/remove OrderItems
- change quantities
- change applicable equipment/specification
- edit notes

Unit prices of existing OrderItems are not manually editable.

After Check-in, OrderItems are locked.

## 8.5 Order status

V1 supports:

- Active
- Cancelled
- No-show
- Completed

The UI should make the current status visually clear.

Terminal Orders are not normally editable.

To modify a terminal Order, the operator must restore it to Active where permitted.

## 8.6 Order search and list

The Order page should support practical operational search/filtering.

At minimum, operators should be able to work with:

- order date
- order number
- customer
- status

The exact filter set can be refined during implementation.

The Order list should make it easy to find today's Orders and Orders requiring action.

---

# 9. Equipment Selection and Capacity Validation

## 9.1 Equipment types

The system supports configurable EquipmentTypes.

Examples:

- Kayak
- Paddleboard

## 9.2 Equipment specifications

The system supports configurable EquipmentSpecs.

Examples:

- Racing Kayak 3-seat
- Racing Kayak 2-seat
- Racing Kayak 1-seat
- Leisure Kayak 3-seat
- Leisure Kayak 2-seat
- Paddleboard

Equipment specifications are managed in Settings.

## 9.3 Initial standard prices

V1 initial catalog:

- Racing kayak: ¥150
- Paddleboard: ¥150
- Leisure kayak: ¥90

Prices are configurable in Settings.

Historical OrderItems retain their original unit-price snapshots.

## 9.4 Capacity validation

The system must validate adult/child counts against the selected equipment.

The core rules are defined in `BUSINESS_RULES.md`.

The application should prevent clearly invalid combinations before the Order can be saved.

---

# 10. Check-in

## 10.1 Goal

Record that the customer has actually started using the rented equipment.

## 10.2 UI

For an eligible active Order, the operator can press:

**Check-in**

The system records:

- current timestamp
- current operator

## 10.3 Effects

Successful Check-in:

- locks OrderItems
- makes OrderItem quantities count against operational inventory
- starts the Auto Return cycle
- allows BoatAssignment if the feature is enabled/used

## 10.4 Restrictions

Check-in must follow the business rules in `BUSINESS_RULES.md`.

In particular:

- Check-in uses current system time.
- Manual Check-in is restricted to the Order's Asia/Shanghai calendar date.
- An effective Return prevents Check-in changes until Return is handled.

## 10.5 Cancel Check-in

The operator can cancel the current Check-in when permitted.

Cancelling Check-in:

- clears Check-in fields
- releases inventory occupation
- unlocks OrderItems
- clears the current Auto Return cycle

---

# 11. Return

## 11.1 Goal

Record the end of the current business activity and release inventory when inventory was actually occupied.

## 11.2 Manual Return after Check-in

For an Order with an effective Check-in, the operator can press:

**Return**

The system:

- records current Return time
- records the operator
- marks the Order Completed
- releases inventory

## 11.3 Direct Return without Check-in

The UI should also allow Return for an active Order that has no Check-in, subject to business rules.

This is useful when the operator knows that the business activity has ended but Check-in was forgotten.

Direct Return without Check-in:

- marks the Order Completed
- records Return
- does not create inventory release because no inventory was occupied

## 11.4 Return cancellation

When permitted, the operator can cancel the current effective Return.

The exact transition rules are defined in `BUSINESS_RULES.md`.

## 11.5 Return and OrderItems

Once an effective Return exists, OrderItems remain locked.

---

# 12. Auto Return

## 12.1 Goal

Prevent forgotten Returns from leaving inventory occupied indefinitely.

## 12.2 Configuration

Settings contains:

`auto_return_after_minutes`

Default:

`120`

Minimum:

`1`

## 12.3 Check-in snapshot

At Check-in, the current Auto Return setting is copied to the Order.

Later Settings changes do not affect the current Check-in cycle.

## 12.4 Automatic operation

If an eligible Order reaches its Auto Return time without an effective Return:

- the system creates the Return
- records the System User as actor
- releases inventory
- marks the Order Completed

The system also records the Auto Return information required by the business model.

---

# 13. Daily Forced Return

## 13.1 Goal

Provide an end-of-day safety mechanism for Orders that remain checked in without Return.

## 13.2 Schedule

V1 uses the fixed Asia/Shanghai window:

`23:59:01–23:59:59`

## 13.3 Eligibility

Orders with:

- effective Check-in
- no effective Return

are eligible.

## 13.4 Effects

The system:

- creates the current Return
- uses the System User
- releases inventory
- marks the Order Completed
- records that Daily Forced Return occurred

Daily Forced Return is independent from the ordinary Auto Return flag.

---

# 14. Inventory Management

## 14.1 Goal

Show and maintain current operational inventory.

## 14.2 Operational inventory

Inventory represents the quantity currently available for business operations, not necessarily the total physical ownership.

Example:

Physical boats: 20

Boats currently loaned to another club: 5

Operational inventory:

15

The operator may directly set the operational quantity to 15.

V1 does not require recording the reason/history of the change.

## 14.3 Available inventory

Available inventory is calculated from:

`operational inventory - currently occupied quantity`

Occupied quantity comes from effective Check-in without effective Return.

Future Orders do not reduce inventory.

## 14.4 Inventory display

The UI should show enough information for an operator to understand:

- operational inventory
- currently occupied quantity
- available quantity

## 14.5 Inventory shortage

V1 may display a warning when inventory is insufficient.

V1 does not require a hard reservation-style inventory block.

---

# 15. Boat Management

## 15.1 Goal

Provide basic management of individually numbered boats.

## 15.2 Boat information

Each Boat has:

- boat number
- equipment specification
- status

Boat numbers are globally unique.

## 15.3 Boat status

V1 supports:

- Available
- Not Available

Not Available boats cannot be newly assigned.

## 15.4 BoatAssignment

The backend/data model may support BoatAssignment.

However:

> BoatAssignment UI is intentionally outside the V1 primary workflow.

V1 does not need an operator-facing boat assignment workflow.

This allows the project to preserve the data model for later expansion without delaying the first usable release.

---

# 16. Payment

## 16.1 Goal

Provide a simple way to see and adjust the financial amount associated with an Order.

## 16.2 Payment display

Payment should display the Order's current OrderItems directly.

Example:

```text
2-seat Kayak       2 × ¥90 = ¥180
Waterproof Bag     1 × ¥20 = ¥20
--------------------------------
Order Items Total          ¥200
```

The operator should not re-select these items inside Payment.

## 16.3 Other adjustments

Payment provides an “Other” adjustment mechanism for:

- discounts
- surcharges
- refunds
- corrections
- other manual adjustments

Each adjustment should have a note explaining the reason.

## 16.4 Amount calculation

The current amount is calculated from:

`OrderItem charges + Payment adjustment items`

No permanent `Order.total_amount` field is required.

## 16.5 Payment status

V1 does not require a separate stored payment status field.

The UI may display the current payment state based on available payment data.

## 16.6 Payment after completion

Payment adjustments remain possible even when the Order is:

- completed
- cancelled
- no-show

This prevents operational completion and later financial correction from being artificially coupled.

---

# 17. Settings

## 17.1 Goal

Provide one management area for configurable operational data.

## 17.2 Settings should manage

### System settings

- Auto Return duration
- Boat management enabled/disabled

### Equipment

- EquipmentType
- EquipmentSpec
- current standard price
- capacity
- active/inactive state

### Sale Items

- item name
- current price
- active/inactive state

### Inventory

- operational inventory quantity per EquipmentSpec

### Boats

- boat records
- boat numbers
- boat status

## 17.3 Fixed business rules

The following are not ordinary Settings in V1:

- Order duration — fixed at 2 hours
- Daily Forced Return time — fixed at 23:59:01–23:59:59
- database timezone — UTC
- business timezone — Asia/Shanghai

---

# 18. Basic Backup / Restore

## 18.1 Goal

Protect local operational data.

## 18.2 V1 scope

If implementation time permits, V1 should provide a simple reliable backup/restore mechanism appropriate for the selected deployment architecture.

The first implementation should prioritize:

- database integrity
- simple operator workflow
- easy recovery

V1 does not require:

- cloud backup service
- multi-location replication
- versioned backup management
- enterprise disaster recovery

---

# 19. Basic Search and Operational Usability

The application should prioritize fast daily operation.

Important actions should be easy to find:

- create Order
- search Order
- Check-in
- Return
- edit Customer
- view inventory
- view current Orders

The final navigation and UI layout will depend partly on the selected open-source project base.

The product requirements define the behavior, not a fixed visual design.

---

# 20. V1 Non-Goals

The following are explicitly not required for V1:

### Customer-facing functions

- customer self-service booking
- customer account
- online payment
- WeChat authorization
- WeChat mini program
- customer notifications

### Advanced customer functions

- AI customer matching
- fuzzy/pinyin matching
- automatic customer merge
- customer segmentation
- loyalty program
- marketing automation

### Advanced rental functions

- Reservation entity
- ReservationItem
- Walk-in entity/type
- Order type
- ActualUsage entity
- ActualUsageItem
- Check-in entity
- Return entity
- ReturnItem
- complex booking workflows
- automatic boat assignment
- BoatAssignment UI
- overlap conflict engine

### Advanced financial functions

- complex payment allocation
- accounting integration
- invoice management
- payment gateway integration
- multi-currency
- full accounting ledger

### Advanced management functions

- roles and permissions
- multi-store management
- advanced audit log
- inventory adjustment history
- advanced BI
- forecasting
- AI recommendations

---

# 21. V1 Acceptance Criteria

V1 should be considered operationally usable when the following real-world scenarios work correctly.

## Scenario A — Future-time Order

1. Operator logs in.
2. Operator selects or creates a Customer.
3. Operator creates an Order with a future start time.
4. Operator selects equipment/items.
5. System calculates the two-hour end time.
6. Order is saved as Active.
7. The future Order does not reduce current operational inventory.

## Scenario B — Immediate Order

1. Operator creates an Order for a customer who has arrived without a prior booking.
2. Operator selects the current time as the start time.
3. System treats it exactly like any other Order.
4. No Walk-in-specific entity or processing path is created.

## Scenario C — Check-in and Return

1. Operator opens an eligible active Order.
2. Operator presses Check-in.
3. Inventory becomes occupied.
4. OrderItems become locked.
5. Operator later presses Return.
6. Order becomes Completed.
7. Inventory becomes available again.

## Scenario D — Direct Return without Check-in

1. Operator has an active Order without Check-in.
2. Operator confirms the activity has ended.
3. Operator records Return.
4. Order becomes Completed.
5. Inventory does not change because there was no prior inventory occupation.

## Scenario E — Forgotten Return

1. Operator performs Check-in.
2. Inventory becomes occupied.
3. Operator forgets Return.
4. Auto Return eventually occurs.
5. Inventory is released.
6. Order becomes Completed.

## Scenario F — End-of-day safety

1. An Order has Check-in.
2. No effective Return exists.
3. The normal Auto Return has not resolved the situation.
4. Daily Forced Return runs at the end of the day.
5. Inventory is released.
6. Order becomes Completed.

## Scenario G — Payment

1. Order contains equipment/items.
2. Payment page displays those existing OrderItems.
3. Operator does not re-select them.
4. Operator can add an Other adjustment.
5. The final displayed amount reflects OrderItems plus adjustments.

---

# 22. Product Boundary Principle

The V1 product should remain small enough to become usable quickly.

When a proposed feature is not necessary to complete the core workflow:

`Login → Customer → Order → Check-in → Inventory → Return → Payment`

it should normally be deferred until after real-world V1 usage identifies a concrete need.

The product should not introduce a new entity, workflow, or technical dependency merely because that pattern is common in other rental-management systems.

The business model in `BUSINESS_RULES.md` remains authoritative for detailed business constraints.
