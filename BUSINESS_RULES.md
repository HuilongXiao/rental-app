# BUSINESS_RULES.md

# Rental App — Business Rules

## 1. Purpose and Scope

This document defines the authoritative business rules for the V1 water-activity equipment rental management system.

The system is an internal management tool for operators of a kayak and paddleboard rental business. It is designed for managing customers, orders, equipment, inventory, check-in, return, and payment.

This document defines business meaning and business constraints. It does not prescribe a specific frontend library, backend implementation, database ORM, or third-party component.

If another project document conflicts with this document, this document takes precedence for business behavior.

---

## 2. Core Business Concept: Order

### 2.1 Order is the only order concept

The system has one business entity for a customer transaction: `Order`.

The following are NOT separate system concepts:

- Reservation
- Walk-in
- Reservation Order
- Walk-in Order
- Order Type

“Reservation” and “Walk-in” are only natural-language descriptions of different business scenarios.

Examples:

- A customer contacts the business in advance and requests tomorrow at 14:00 → create an Order with `start_at` tomorrow at 14:00.
- A customer arrives without a prior booking and wants to use equipment now → create an Order with `start_at` set to the current time.
- A customer makes an advance booking for later today → create an Order.
- A customer asks in advance for a future time → create an Order.

The system MUST NOT infer an order type from `start_at`.

The system MUST NOT create different processing branches merely because the selected start time is in the past, present, or future.

There is no `order_type`, `reservation_type`, or `walk_in_type`.

---

## 3. User

### 3.1 Purpose

A User identifies the operator who performs a business-changing action.

V1 uses simple username/password authentication.

### 3.2 Fields

A User contains:

- `id`
- `username` — unique
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

- price is the current standard price.
- historical order prices are stored as OrderItem price snapshots.
- operators cannot edit an existing OrderItem's unit price from the Order page.
- inactive specifications cannot be used for new orders.
- historical references remain valid.
- historical business data must not be deleted merely to remove an item from current use.

### 5.3 Standard current prices

The initial V1 catalog is:

- Racing kayak: ¥150 / boat
- Paddleboard: ¥150 / board
- Leisure kayak: ¥90 / boat

The actual price used by an order is the EquipmentSpec/SaleItem price at the time the OrderItem is created.

---

## 6. Equipment Capacity Rules

`capacity` means the maximum total number of people allowed on the equipment.

It does NOT mean minimum occupants.

### 6.1 Racing / Leisure kayak — 3-seat

Maximum total: 3 people.

At least 1 adult is required.

Maximum adults: 2.

Examples of valid combinations:

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

V1 treats the paddleboard as a single-spec equipment item. Any additional adult/child restrictions should be configurable or validated only if explicitly defined by the business.

---

## 7. SaleItem

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

- name is unique.
- price is the current standard price.
- historical order prices are stored as OrderItem snapshots.
- inactive SaleItems cannot be added to new orders.
- historical references remain valid.

For V1, normal chargeable products should be represented through OrderItem. Payment should not require the operator to re-select items already present in the Order.

---

## 8. Order

### 8.1 Purpose

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

### 8.2 Core fields

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

### 8.3 Order number

`order_number` is system-generated and unique.

### 8.4 Time rules

- The operator selects `start_at`.
- `end_at` is automatically `start_at + 2 hours`.
- `end_at` is not independently editable in V1.
- Database timestamps are stored in UTC.
- Business time is Asia/Shanghai.
- User-entered local times are converted to UTC for storage.
- Business-date decisions use Asia/Shanghai.

The system does not classify an Order based on whether its start time is before, equal to, or after the current time.

### 8.5 Default people count

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

## 9. Order Status

V1 has exactly four lifecycle statuses:

- `active`
- `cancelled`
- `no_show`
- `completed`

These are the only lifecycle statuses.

### 9.1 Active

An active Order can be edited subject to the rules for check-in and return.

### 9.2 Terminal statuses

The following are terminal statuses:

- cancelled
- no_show
- completed

Terminal Orders are locked for normal editing.

To modify a terminal Order, it must first be restored to `active`, subject to business rules.

### 9.3 Status transitions

Allowed transitions:

- active → cancelled
- active → no_show
- active → completed
- cancelled → active
- no_show → active
- completed → active

Other direct status transitions are not allowed.

### 9.4 Completed does not imply Return

`completed` is simply a terminal business status.

An Order can be completed without having a Check-in or Return record.

Examples:

- staff confirms at the end of the day that the customer actually used the equipment but Check-in/Return was forgotten
- a direct Return is recorded without a prior Check-in

`completed` MUST NOT be interpreted as evidence that `return_at` exists.

---

## 10. OrderItem

OrderItem represents a normal chargeable item within an Order.

V1 does not use ActualUsage or ActualUsageItem.

### 10.1 Core fields

An OrderItem contains:

- `id`
- `order_id`
- item reference
- `quantity`
- `unit_price`
- creation/update actor and timestamps

The item reference must identify the relevant EquipmentSpec or SaleItem according to the final implementation model.

### 10.2 Price snapshot

When an OrderItem is created:

- `unit_price` is copied from the current catalog price.
- `unit_price` becomes the historical price snapshot for that OrderItem.
- operators cannot edit `unit_price` directly from the Order page.

### 10.3 Amount

Line amount is:

`quantity × unit_price`

V1 does not store Order total amount as a permanent field.

### 10.4 Editing rules

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

## 11. Check-in

Check-in is an operation on an Order, NOT a separate database entity.

### 11.1 Fields

The current Check-in state is represented by:

- `check_in_at`
- `check_in_by_user_id`

### 11.2 Rules

- Check-in uses the current system time.
- The operator performing it is recorded.
- V1 has no separate Check-in history entity.
- Re-check-in overwrites the current Check-in timestamp and actor.
- Cancelled Check-in clears the current Check-in fields.
- Manual Check-in is allowed only on the same Asia/Shanghai calendar date as the Order date.
- `check_in_at >= start_at`.
- An effective Return blocks Check-in changes until Return is cancelled/handled.

### 11.3 Effects of Check-in

Successful Check-in:

- locks OrderItems
- starts inventory occupation
- starts the Auto Return cycle
- allows BoatAssignment records to be created if BoatAssignment is used

Check-in is the event that makes an OrderItem count against operational inventory.

---

## 12. Return

Return is an operation on an Order, NOT a separate database entity.

### 12.1 Fields

The current Return state is represented by:

- `return_at`
- `return_by_user_id`

### 12.2 Manual Return after Check-in

If Check-in exists:

- Return must occur after Check-in.
- Return sets the Order to `completed`.
- Inventory occupied by the Check-in is released.

### 12.3 Direct Return without Check-in

A direct Return is allowed.

This means:

- the operator confirms that the business activity has ended
- the Order becomes `completed`
- no inventory release occurs because there was no inventory occupation
- no Check-in is created automatically

For a direct Return without Check-in:

`return_at >= start_at + 1 minute`

### 12.4 Return after end time

Return may occur later than the planned `end_at`.

### 12.5 Return cancellation

Cancelling the current effective Return:

- clears `return_at`
- clears `return_by_user_id`
- resets the current daily forced return marker if applicable
- does not automatically resume a previously invalidated ordinary Auto Return task

If a completed Order had an effective Return, restoring it to active does not automatically remove the historical Auto Return snapshot fields.

---

## 13. Auto Return

Auto Return protects inventory when staff forget to record a Return.

### 13.1 Configuration

Settings contains:

- `auto_return_after_minutes`

Default:

- 120 minutes

Minimum:

- 1 minute

### 13.2 Snapshot behavior

When Check-in occurs:

`auto_return_after_minutes` is copied to the Order.

Later Settings changes do not affect the current Check-in cycle.

### 13.3 Automatic Return

When the scheduled time is reached and the Order still has no effective Return:

- the system creates the current Return
- `return_at` is the scheduled Auto Return time
- `return_by_user_id` is the System User
- the Order becomes `completed`
- inventory is released

The Auto Return operation marks:

- `auto_return_occurred = 1`
- `auto_return_at = actual Auto Return time`

### 13.4 Manual Return before Auto Return

If staff manually Return before the scheduled Auto Return:

- the manual Return becomes the effective Return
- the original scheduled task must not later create another Return

### 13.5 Auto Return followed by human Return

If Auto Return has already occurred and a human later records a Return:

- `auto_return_at` remains the original automatic Return time
- `auto_return_occurred` remains true
- `return_at` becomes the human Return time
- `return_by_user_id` becomes the human operator

### 13.6 Check-in cancellation

Cancelling Check-in clears the current Auto Return cycle:

- `auto_return_after_minutes = NULL`
- `auto_return_occurred = 0`
- `auto_return_at = NULL`

A new Check-in starts a new cycle.

---

## 14. Daily Forced Return

Daily Forced Return is a separate end-of-day inventory safety mechanism.

### 14.1 Timing

V1 uses the fixed Asia/Shanghai window:

`23:59:01–23:59:59`

### 14.2 Eligibility

An Order is eligible if:

- it has an effective Check-in
- it has no effective Return

### 14.3 Effects

Daily Forced Return:

- creates the current Return
- uses the System User
- releases occupied inventory
- sets `daily_forced_return_occurred = 1`
- does not change ordinary Auto Return fields

### 14.4 Cancellation

Cancelling the effective Daily Forced Return:

- clears the current Return fields
- resets `daily_forced_return_occurred = 0`

If a new Check-in occurs, the daily forced return marker is reset.

---

## 15. Inventory

### 15.1 Meaning of inventory quantity

V1 inventory represents **current operational inventory**, not total physical ownership.

Example:

If the business physically owns 20 boats but 5 are currently lent to another club, the operator may change operational inventory to 15.

V1 does not need to record why the quantity changed.

### 15.2 Inventory configuration

Each EquipmentSpec has one InventoryConfiguration containing:

- `equipment_spec_id`
- `total_quantity`
- `updated_by_user_id`
- `updated_at`

### 15.3 Available inventory

Available inventory is calculated:

`available = total operational inventory - currently occupied quantity`

Occupied quantity consists only of OrderItem quantities belonging to Orders that:

- have an effective Check-in
- do not have an effective Return

Future Orders do not reduce available inventory.

### 15.4 Inventory release

Inventory is released when:

- an effective Return occurs
- an effective Check-in is cancelled

Direct Return without Check-in does not change inventory.

### 15.5 Inventory shortage

V1 may warn the operator when an operation would result in insufficient inventory.

V1 does not require a hard inventory reservation block.

### 15.6 Inventory minimum

`total_quantity` cannot be negative and cannot be lower than current occupied quantity.

V1 does not maintain an inventory transaction/history table.

---

## 16. Boat

Boat management is optional through Settings.

A Boat represents an individually numbered physical boat.

Fields include:

- `id`
- `equipment_spec_id`
- `boat_number`
- `status`
- `created_at`
- `updated_at`

### 16.1 Boat number

`boat_number` is globally unique.

### 16.2 Boat status

V1 uses:

- `available`
- `not_available`

`not_available` prevents new assignment.

Existing historical/current assignments are not automatically deleted.

### 16.3 BoatAssignment

BoatAssignment is a supporting data structure, not a V1 primary workflow.

Rules:

- assignment belongs to an OrderItem
- assignment is only created after Check-in
- no assignment before Check-in
- assignment count does not have to equal OrderItem quantity
- no automatic assignment
- V1 does not require overlap/conflict validation
- the same Boat may appear on overlapping Orders
- Return does not automatically delete the assignment
- a wrong assignment can be corrected by deleting the incorrect record and creating the correct one

V1 does not require a BoatAssignment UI.

---

## 17. Payment

### 17.1 Payment purpose

Payment records the current financial state associated with an Order.

V1 does not duplicate OrderItem selection in Payment.

The Payment UI displays the Order's current normal chargeable items and their calculated amounts.

### 17.2 Normal order charges

Normal charges come directly from OrderItems:

`SUM(quantity × unit_price)`

The operator does not re-select Kayaks, Paddleboards, waterproof bags, or other OrderItems inside Payment.

### 17.3 Other adjustments

Payment may contain additional adjustment records for cases such as:

- discount
- surcharge
- refund
- correction
- other manual adjustment

These are represented by PaymentItem records of type `other`.

### 17.4 PaymentItem

A PaymentItem contains:

- `id`
- `payment_id`
- `type`
- `item_name`
- `quantity`
- `unit_price`
- `amount`
- `note`
- actor and timestamp

For `other`:

- `sale_item_id` is NULL
- `item_name` is “其他”
- `note` is mandatory
- `unit_price >= 0`
- `quantity != 0`
- `amount != 0`
- `amount = quantity × unit_price`

Positive values represent charges.

Negative values represent refunds/deductions.

### 17.5 Immutability

PaymentItem records are immutable after creation.

Corrections are made by adding a new adjustment rather than editing the historical PaymentItem.

### 17.6 Final amount

Current received/final amount is dynamically calculated:

`SUM(current OrderItem charges) + SUM(current PaymentItem adjustments)`

The final Order amount is not stored as a separate authoritative field.

### 17.7 Payment status

V1 does not store a separate payment status field.

The application can derive/display payment state from the current Payment data.

Payment remains adjustable even after the Order reaches a terminal status.

---

## 18. Order and Customer Snapshot

An Order stores a snapshot of customer information in addition to its `customer_id`.

This preserves the customer information that was associated with the Order at the time it was created.

Changing the Customer profile later must not silently rewrite historical Order snapshots.

---

## 19. Actor Tracking

Every business-changing action must identify the User responsible for it.

Typical actor fields include:

- `created_by_user_id`
- `updated_by_user_id`
- `check_in_by_user_id`
- `return_by_user_id`

Automatic operations use the System User.

V1 does not require a separate audit-log entity, but the actor fields above are part of the business model.

---

## 20. Data Integrity Rules

### 20.1 IDs

All primary keys use UUID values.

### 20.2 Money

Money is stored as integer fen.

UI displays yuan.

### 20.3 Time

Database timestamps are UTC.

Business timezone is Asia/Shanghai.

UTC timestamps use ISO 8601 with `Z` and seconds precision.

### 20.4 Nullability

NULL means nonexistent, unknown, or not applicable.

NOT NULL means required.

Defaults are used only where they have explicit business meaning.

### 20.5 Foreign keys

Foreign keys must reference valid records.

Historical business records must not be deleted to bypass business rules.

### 20.6 Historical catalog data

If an EquipmentSpec or SaleItem is no longer offered:

- deactivate it
- do not delete historical references merely to remove it from the current catalog

### 20.7 Quantity

OrderItem quantity must be at least 1.

Inventory quantity must not be negative.

### 20.8 People

Adult and child counts must be non-negative.

Total people must be at least 1.

Equipment-specific capacity/composition rules are enforced at the business layer.

### 20.9 Order timing

`end_at > start_at`

`end_at = start_at + 2 hours`

If Check-in exists:

`check_in_at >= start_at`

and Check-in must be on the same Asia/Shanghai calendar date as the Order date.

If both Check-in and Return exist:

`return_at > check_in_at`

If Return exists without Check-in:

`return_at >= start_at + 1 minute`

### 20.10 Auto Return invariants

If `auto_return_occurred = 0`:

`auto_return_at IS NULL`

If `auto_return_occurred = 1`:

`auto_return_at IS NOT NULL`

When an Auto Return has occurred:

`auto_return_at > check_in_at`

and the current Return must not precede the Auto Return time.

### 20.11 Check-in / Return pairing

Check-in state is represented by the pair:

- `check_in_at`
- `check_in_by_user_id`

Return state is represented by the pair:

- `return_at`
- `return_by_user_id`

The two fields in each pair should remain logically consistent.

### 20.12 Effective Return and completion

An effective Return always results in:

`status = completed`

However:

`status = completed`

does NOT require an effective Return.

### 20.13 Inventory occupation

Only an effective Check-in without an effective Return causes OrderItem quantity to occupy inventory.

### 20.14 BoatAssignment

BoatAssignment does not affect inventory calculations.

---

## 21. Business State vs. Technical Implementation

The following concepts are business rules, not requirements to create separate software entities or services:

- Check-in
- Return
- Auto Return
- Daily Forced Return
- Reservation
- Walk-in

Implementation may represent these concepts using Order fields, service methods, scheduled jobs, or other technical structures.

The implementation must preserve the business behavior defined in this document.

---

## 22. V1 Explicit Boundaries

The following are intentionally outside the V1 business model:

- Reservation entity
- ReservationItem entity
- Walk-in entity/type
- Order type
- ActualUsage entity
- ActualUsageItem entity
- CheckIn entity
- Return entity
- ReturnItem entity
- Check-in history entity
- Return history entity
- multi-role permission model
- online customer self-booking
- WeChat login/integration
- multi-store management
- advanced customer matching
- automatic customer merge
- advanced analytics
- inventory adjustment history
- BoatAssignment UI
- complex payment allocation workflow
- full accounting/finance module

These may be considered in future versions, but V1 implementation must not introduce them merely because they are common patterns in rental software.

---

## 23. Guiding Principle

The V1 system should prefer a small number of clear concepts over a large number of specialized entities.

In particular:

> One customer transaction is one Order.

> Reservation and Walk-in describe how people talk about an Order; they do not define different Order types.

> Check-in and Return describe operations on an Order; they do not require separate business entities.

> Inventory reflects current operational availability, not ownership history.

> Payment should complement OrderItems, not duplicate them.

> Technical implementation may change as the project adopts a suitable open-source base or reusable components, provided the business rules in this document remain intact.
