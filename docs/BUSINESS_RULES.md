# Rental App — Business Rules

## 1. Purpose and Scope

This document defines the authoritative business rules for the V1 rental management system for kayak and paddleboard operations.

V1 is intended for internal operations staff only. It is designed to manage customers, orders, equipment catalog, inventory, check-in, return, and payment for real daily business use.

This document defines business meaning and business constraints. It does not prescribe a specific frontend library, backend implementation, database ORM, or third-party component.

If another project document conflicts with this document, this document takes precedence.

---

## 2. Core Business Concept: Order

### 2.1 Order is the only order concept

The system has one business entity for a customer transaction: `Order`.

The following are not separate system concepts:

- Reservation
- Walk-in
- Reservation Order
- Walk-in Order
- Order Type

“Reservation” and “Walk-in” are only natural-language descriptions of different business scenarios.

Examples:

- Customer asks in advance for tomorrow at 14:00 → create an Order with `start_at` tomorrow at 14:00.
- Customer arrives without booking and wants to rent now → create an Order with `start_at` set to the current time.
- Customer asks in advance for later today → create an Order.

The system MUST NOT infer an order type from `start_at`.

The system MUST NOT create different processing branches merely because the selected start time is in the past, present, or future.

There is no `order_type`, `reservation_type`, or `walk_in_type`.

---

## 3. User

### 3.1 Purpose

A User identifies the operator who performs a business-changing action.

V1 uses username/password authentication.

### 3.2 Fields

A User contains:

- `id`
- `username` unique
- `display_name`
- `password_hash`
- `is_active`
- `is_system`
- `created_at`
- `updated_at`

### 3.3 Rules

- `username` is unique.
- Normal users use username/password login.
- V1 has no role or permission system.
- All normal users have the same functional permissions.
- The System User always exists.
- The System User has `is_system = 1`.
- The System User cannot be deleted.
- The System User cannot log in through normal authentication.
- Automatic business actions are attributed to the System User.

---

## 4. Customer

### 4.1 Customer identity fields

A Customer may contain:

- `name`
- `gender`
- `wechat_nickname`
- `wechat_id`
- `phone`

### 4.2 Uniqueness

The following are unique when present:

- `phone`
- `wechat_id`

Name and WeChat nickname are not unique.

### 4.3 Minimum valid Customer

A standalone Customer must satisfy at least one of:

- `name` + `phone`
- `wechat_nickname` + `wechat_id`

### 4.4 Customer matching

All four fields participate in customer matching:

- name
- WeChat nickname
- WeChat ID
- phone

V1 uses simple candidate search and operator confirmation.

V1 does NOT require:

- fuzzy matching
- pinyin matching
- AI matching
- automatic customer merging
- ranking/scoring of candidates

Once the operator confirms the intended Customer, the order uses that Customer.

### 4.5 System customer

A system customer named “游客” always exists.

Rules:

- cannot be deleted
- cannot be renamed
- its WeChat ID and phone are immutable
- created by the System User

---

## 5. Equipment Catalog

The equipment catalog is configurable in Settings.

### 5.1 EquipmentType

Represents a broad equipment category, such as:

- Kayak
- Paddleboard

Rules:

- name is unique
- can be created and edited by operators

### 5.2 EquipmentSpec

Represents a specific rentable/chargeable equipment specification.

Examples:

- Racing Kayak — 3-seat
- Racing Kayak — 2-seat
- Racing Kayak — 1-seat
- Leisure Kayak — 3-seat
- Paddleboard

Fields include:

- `id`
- `equipment_type_id`
- `name`
- `price`
- `capacity`
- `is_active`
- creation/update actor and timestamps

Rules:

- price is the current standard price
- historical order prices are stored as OrderItem price snapshots
- operators cannot edit an existing OrderItem's unit price from the Order page
- inactive specifications cannot be used for new orders
- historical references remain valid
- historical business data must not be deleted merely to remove an item from current use

### 5.3 SaleItem

A SaleItem is a separately catalogued chargeable item that is not an EquipmentSpec.

Examples may include:

- waterproof bag
- other small rental/sale extras

Fields include:

- `id`
- `name`
- `price`
- `is_active`
- creation/update actor and timestamps

Rules:

- name is unique
- price is the current standard price
- historical order prices are stored as OrderItem snapshots
- inactive SaleItems cannot be added to new orders
- historical references remain valid

For V1, ordinary chargeable products should be represented through `OrderItem` and not require re-selection inside Payment.

---

## 6. Equipment Capacity Rules

`capacity` means the maximum total number of people allowed on the equipment.

It does NOT mean minimum occupants.

### 6.1 Racing / Leisure kayak — 3-seat

Maximum total: 3 people.

At least 1 adult is required.

Maximum adults: 2.

Valid examples:

- 2 adults + 1 child
- 1 adult + 2 children
- 2 adults
- 1 adult + 1 child
- 1 adult

Invalid examples:

- 3 adults
- 0 adults
- more than 3 total people

### 6.2 Racing / Leisure kayak — 2-seat

Maximum total: 2 people.

Valid combinations:

- 2 adults
- 1 adult + 1 child
- 1 adult

Invalid:

- 2 children
- 3 or more people
- 0 adults

### 6.3 Racing / Leisure kayak — 1-seat

Only one adult is allowed.

Valid:

- 1 adult

Invalid:

- any child
- more than one person
- zero adults

### 6.4 Paddleboard

V1 treats the paddleboard as a single-spec equipment item. Any additional adult/child restrictions are only enforced if explicitly defined by business rules.

---

## 7. Order

### 7.1 Purpose

Order is the central business entity.

An Order records:

- customer
- requested/selected start time
- end time
- people count
- ordered items
- operational status
- check-in information
- return information
- payment relationship
- business actors

### 7.2 Core fields

An Order contains:

- `id`
- `order_number`
- `customer_id`
- customer snapshot fields
- `start_at`
- `end_at`
- `adult_count`
- `child_count`
- `note`
- `status`
- `created_at`
- `updated_at`
- `created_by_user_id`
- `updated_by_user_id`
- `check_in_at`
- `check_in_by_user_id`
- `auto_return_after_minutes`
- `auto_return_at`
- `auto_return_occurred`
- `return_at`
- `return_by_user_id`
- `daily_forced_return_occurred`

### 7.3 Order number

`order_number` is system-generated and unique.

### 7.4 Time rules

- The operator selects `start_at`.
- `end_at` is automatically `start_at + 2 hours`.
- `end_at` is not independently editable in V1.
- Database timestamps are stored in UTC.
- Business time is Asia/Shanghai.
- User-entered local times are converted to UTC for storage.
- Business-date decisions use Asia/Shanghai.

The system does not classify an Order based on whether its start time is before, equal to, or after the current time.

### 7.5 Default people count

When equipment is selected, the UI may initialize people counts as follows:

- 2 adults for racing 3-seat
- 2 adults for racing 2-seat
- 2 adults for leisure 3-seat
- 2 adults for leisure 2-seat
- 1 adult for racing 1-seat
- 1 adult for leisure 1-seat
- 1 adult for paddleboard
- children default to 0

Once the operator manually edits adult/child counts, later equipment changes MUST NOT automatically overwrite the operator's manually entered counts.

The final combination must still satisfy applicable equipment capacity rules.

---

## 8. Order Status

V1 has exactly four lifecycle statuses:

- `active`
- `cancelled`
- `no_show`
- `completed`

These are the only lifecycle statuses.

### 8.1 Active

An active Order can be edited subject to the rules for check-in and return.

### 8.2 Terminal statuses

The following are terminal statuses:

- `cancelled`
- `no_show`
- `completed`

Terminal Orders are locked for normal editing.

To modify a terminal Order, it must first be restored to `active`, subject to business rules.

### 8.3 Status transitions

Allowed transitions:

- active → cancelled
- active → no_show
- active → completed
- cancelled → active
- no_show → active
- completed → active

Other direct status transitions are not allowed.

### 8.4 Completed does not imply Return

`completed` is simply a terminal business status.

An Order can be completed without having a Check-in or Return record.

Examples:

- staff confirms at the end of the day that the customer actually used the equipment but Check-in/Return was forgotten
- a direct Return is recorded without a prior Check-in

`completed` MUST NOT be interpreted as evidence that `return_at` exists.

---

## 9. OrderItem

OrderItem represents a normal chargeable item within an Order.

### 9.1 Core fields

An OrderItem contains:

- `id`
- `order_id`
- item reference
- `quantity`
- `unit_price`
- creation/update actor and timestamps

The item reference must identify the relevant EquipmentSpec or SaleItem according to the final implementation model.

### 9.2 Price snapshot

When an OrderItem is created:

- `unit_price` is copied from the current catalog price
- `unit_price` becomes the historical price snapshot for that OrderItem
- operators cannot edit `unit_price` directly from the Order page

### 9.3 Amount

Line amount is:

`quantity × unit_price`

V1 does not store Order total amount as a permanent field.

### 9.4 Editing rules

Before Check-in:

- equipment/item can be added
- equipment/item can be removed
- quantity can be changed
- applicable catalog item can be changed

After Check-in:

- OrderItems are locked.

To change an OrderItem after Check-in:

1. cancel the current Check-in
2. modify the OrderItem
3. Check-in again

An effective Return also keeps the OrderItem locked.

---

## 10. Check-in

Check-in is an operation on an Order, not a separate database entity.

### 10.1 Fields

The current Check-in state is represented by:

- `check_in_at`
- `check_in_by_user_id`

### 10.2 Rules

- Check-in uses the current system time
- The operator performing it is recorded
- V1 has no separate Check-in history entity
- Re-check-in overwrites the current Check-in timestamp and actor
- Cancelled Check-in clears the current Check-in fields
- Manual Check-in is allowed only on the same Asia/Shanghai calendar date as the Order date
- `check_in_at >= start_at`
- An effective Return blocks Check-in changes until Return is cancelled/handled

### 10.3 Effects of Check-in

Successful Check-in:

- locks OrderItems
- starts inventory occupation
- starts the Auto Return cycle

Check-in is the event that makes an OrderItem count against operational inventory.

---

## 11. Return

Return is an operation on an Order, not a separate database entity.

### 11.1 Fields

The current Return state is represented by:

- `return_at`
- `return_by_user_id`

### 11.2 Manual Return after Check-in

If Check-in exists:

- Return must occur after Check-in.
- Return sets the Order to `completed`.
- Inventory occupied by the Check-in is released.

### 11.3 Direct Return without Check-in

A direct Return is allowed.

This means:

- the operator confirms that the business activity has ended
- the Order becomes `completed`
- no inventory release occurs because there was no inventory occupation
- no Check-in is created automatically

For a direct Return without Check-in:

`return_at >= start_at + 1 minute`

### 11.4 Return after end time

Return may occur later than the planned `end_at`.

### 11.5 Return cancellation

Cancelling the current effective Return:

- clears `return_at`
- clears `return_by_user_id`
- resets the current daily forced return marker if applicable
- does not automatically resume a previously invalidated ordinary Auto Return task

If a completed Order had an effective Return, restoring it to active does not automatically remove the historical Auto Return snapshot fields.

---

## 12. Auto Return

Auto Return protects inventory when staff forget to record a Return.

### 12.1 Configuration

Settings contains:

- `auto_return_after_minutes`

Default:

- 120 minutes

Minimum:

- 1 minute

### 12.2 Snapshot behavior

When Check-in occurs:

`auto_return_after_minutes` is copied to the Order.

Later Settings changes do not affect the current Check-in cycle.

### 12.3 Automatic Return

When the scheduled time is reached and the Order still has no effective Return:

- the system creates the current Return
- `return_at` is the scheduled Auto Return time
- `return_by_user_id` is the System User
- the Order becomes `completed`
- inventory is released

The Auto Return operation marks:

- `auto_return_occurred = 1`
- `auto_return_at = actual Auto Return time`

### 12.4 Manual Return before Auto Return

If staff manually Return before the scheduled Auto Return:

- the manual Return becomes the effective Return
- the original scheduled task must not later create another Return

### 12.5 Auto Return followed by human Return

If Auto Return has already occurred and a human later records a Return:

- `auto_return_at` remains the original automatic Return time
- `auto_return_occurred` remains true
- `return_at` becomes the human Return time
- `return_by_user_id` becomes the human operator

### 12.6 Check-in cancellation

Cancelling Check-in clears the current Auto Return cycle:

- `auto_return_after_minutes = NULL`
- `auto_return_occurred = 0`
- `auto_return_at = NULL`

A new Check-in starts a new cycle.

---

## 13. Daily Forced Return

Daily Forced Return is a separate end-of-day inventory safety mechanism.

### 13.1 Timing

V1 uses the fixed Asia/Shanghai window:

`23:59:01–23:59:59`

### 13.2 Eligibility

An Order is eligible if:

- it has an effective Check-in
- it has no effective Return

### 13.3 Effects

Daily Forced Return:

- creates the current Return
- uses the System User
- releases occupied inventory
- sets `daily_forced_return_occurred = 1`
- does not change ordinary Auto Return fields

### 13.4 Cancellation

Cancelling the effective Daily Forced Return:

- clears the current Return fields
- resets `daily_forced_return_occurred = 0`

If a new Check-in occurs, the daily forced return marker is reset.

---

## 14. Inventory

### 14.1 Meaning of inventory quantity

V1 inventory represents current operational inventory, not total physical ownership.

Example:

If the business physically owns 20 boats but 5 are currently lent to another club, the operator may change operational inventory to 15.

V1 does not need to record why the quantity changed.

### 14.2 Inventory configuration

Each EquipmentSpec has one InventoryConfiguration containing:

- `equipment_spec_id`
- `total_quantity`
- `updated_by_user_id`
- `updated_at`

### 14.3 Available inventory

Available inventory is calculated:

`available = total operational inventory - currently occupied quantity`

Occupied quantity consists only of OrderItem quantities belonging to Orders that:

- have an effective Check-in
- do not have an effective Return

Future Orders do not reduce available inventory.

### 14.4 Inventory release

Inventory is released when:

- an effective Return occurs
- an effective Check-in is cancelled

Direct Return without Check-in does not change inventory.

### 14.5 Inventory shortage

V1 may warn the operator when an operation would result in insufficient inventory.

V1 does not require a hard inventory reservation block.

### 14.6 Inventory minimum

`total_quantity` cannot be negative and cannot be lower than current occupied quantity.

V1 does not maintain an inventory transaction/history table.

---

## 15. Payment

### 15.1 Payment purpose

Payment records the current financial state associated with an Order.

V1 does not duplicate OrderItem selection in Payment.

The Payment UI displays the Order's current normal chargeable items and their calculated amounts.

### 15.2 Normal order charges

Normal charges come directly from OrderItems:

`SUM(quantity × unit_price)`

The operator does not re-select equipment or SaleItems inside Payment.

### 15.3 Other adjustments

Payment may contain additional adjustment records for cases such as:

- discount
- surcharge
- refund
- correction
- temporary charge
- other manual adjustment

These are represented by PaymentItem records as “other”.

### 15.4 PaymentItem model

A PaymentItem contains:

- `id`
- `payment_id`
- `quantity`
- `unit_amount`
- `amount`
- `note`
- actor and timestamp

The system does not create subcategories for “other”.

A note is mandatory to explain why the adjustment exists.

Rules:

- `quantity != 0`
- `unit_amount >= 0`
- `amount = quantity × unit_amount`
- positive values increase the final amount
- negative values decrease the final amount
- PaymentItem records are immutable after creation

Corrections are made by adding a new adjustment rather than editing the historical PaymentItem.

### 15.5 Final amount

Current received/final amount is dynamically calculated:

`SUM(current OrderItem charges) + SUM(current PaymentItem adjustments)`

The final Order amount is not stored as a separate authoritative field.

### 15.6 Payment status

V1 does not store a separate payment status field.

The application can derive/display payment state from the current Payment data.

Payment remains adjustable even after the Order reaches a terminal status.

### 15.7 “Other” semantics

“Other” is not a separate business category in the system. It is simply a PaymentItem adjustment with a required note.

Examples of business reasons stored in `note`:

- refund
- discount
- temporary fee
- surcharge
- correction
- manual adjustment

The system does not need separate classification or extra fields beyond `quantity`, `unit_amount`, `amount`, `note`, and actor/timestamp metadata.

---

## 16. Order and Customer Snapshot

An Order stores a snapshot of customer information in addition to its `customer_id`.

This preserves the customer information associated with the Order at the time it was created.

Changing the Customer profile later must not silently rewrite historical Order snapshots.

---

## 17. Actor Tracking

Every business-changing action must identify the User responsible for it.

Typical actor fields include:

- `created_by_user_id`
- `updated_by_user_id`
- `check_in_by_user_id`
- `return_by_user_id`

Automatic operations use the System User.

V1 does not require a separate audit-log entity, but the actor fields above are part of the business model.

---

## 18. Data Integrity Rules

### 18.1 IDs

All primary keys use UUID values.

### 18.2 Money

Money is stored as integer fen.

UI displays yuan.

### 18.3 Time

Database timestamps are UTC.

Business timezone is Asia/Shanghai.

UTC timestamps use ISO 8601 with `Z` and seconds precision.

### 18.4 Nullability

NULL means nonexistent, unknown, or not applicable.

NOT NULL means required.

Defaults are used only where they have explicit business meaning.

### 18.5 Foreign keys

Foreign keys must reference valid records.

Historical business records must not be deleted to bypass business rules.

### 18.6 Historical catalog data

If an EquipmentSpec or SaleItem is no longer offered:

- deactivate it
- do not delete historical references merely to remove it from the current catalog

### 18.7 Quantity

OrderItem quantity must be at least 1.

Inventory quantity must not be negative.

### 18.8 People

Adult and child counts must be non-negative.

Total people must be at least 1.

Equipment-specific capacity/composition rules are enforced at the business layer.

### 18.9 Order timing

`end_at > start_at`

`end_at = start_at + 2 hours`

If Check-in exists:

`check_in_at >= start_at`

and Check-in must be on the same Asia/Shanghai calendar date as the Order date.

If both Check-in and Return exist:

`return_at > check_in_at`

If Return exists without Check-in:

`return_at >= start_at + 1 minute`

### 18.10 Auto Return invariants

If `auto_return_occurred = 0`:

`auto_return_at IS NULL`

If `auto_return_occurred = 1`:

`auto_return_at IS NOT NULL`

When an Auto Return has occurred:

`auto_return_at > check_in_at`

and the current Return must not precede the Auto Return time.

### 18.11 Check-in / Return pairing

Check-in state is represented by the pair:

- `check_in_at`
- `check_in_by_user_id`

Return state is represented by the pair:

- `return_at`
- `return_by_user_id`

---

## 19. Non-goals for V1

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
- Boat and BoatAssignment
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

## 20. Acceptance Criteria

V1 should be considered operationally usable when the following work correctly.

### Scenario A — Future-time Order

1. Operator logs in.
2. Operator selects or creates a Customer.
3. Operator creates an Order with a future start time.
4. Operator selects equipment/items.
5. System calculates the two-hour end time.
6. Order is saved as Active.
7. The future Order does not reduce current operational inventory.

### Scenario B — Immediate Order

1. Operator creates an Order for a customer who has arrived without a prior booking.
2. Operator selects the current time as the start time.
3. System treats it exactly like any other Order.
4. No Walk-in-specific entity or processing path is created.

### Scenario C — Check-in and Return

1. Operator opens an eligible active Order.
2. Operator presses Check-in.
3. Inventory becomes occupied.
4. OrderItems become locked.
5. Operator later presses Return.
6. Order becomes Completed.
7. Inventory becomes available again.

### Scenario D — Direct Return without Check-in

1. Operator has an active Order without Check-in.
2. Operator confirms the activity has ended.
3. Operator records Return.
4. Order becomes Completed.
5. Inventory does not change because there was no prior inventory occupation.

### Scenario E — Forgotten Return

1. Operator performs Check-in.
2. Inventory becomes occupied.
3. Operator forgets Return.
4. Auto Return eventually occurs.
5. Inventory is released.
6. Order becomes Completed.

### Scenario F — End-of-day safety

1. An Order has Check-in.
2. No effective Return exists.
3. The normal Auto Return has not resolved the situation.
4. Daily Forced Return runs at the end of the day.
5. Inventory is released.
6. Order becomes Completed.

### Scenario G — Payment

1. Order contains equipment/items.
2. Payment page displays those existing OrderItems.
3. Operator does not re-select them.
4. Operator can add an “Other” adjustment.
5. Multiple “Other” adjustments can exist in the same Payment.
6. Each “Other” has a note describing why it exists.
7. The final displayed amount reflects OrderItems plus adjustment items.

---

## 21. Product Boundary Principle

The V1 product should remain small enough to become usable quickly.

When a proposed feature is not necessary to complete the core workflow:

`Login → Customer → Order → Check-in → Inventory → Return → Payment`

it should normally be deferred until after real-world V1 usage identifies a concrete need.

The product should not introduce a new entity, workflow, or technical dependency merely because that pattern is common in other rental-management systems.

The business model in this document remains authoritative for business constraints.
