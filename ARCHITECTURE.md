# ARCHITECTURE.md

## 1. 文档目的

本文档定义水上器材租赁管理 App 的技术架构原则、模块边界、数据访问方式、自动任务、部署方式和可替换性要求。

本文档的目标不是锁定某一个具体框架或技术栈，而是确保：

1. 技术实现服务于已经确定的业务规则；
2. V1 保持足够简单，可以快速落地和实际使用；
3. 业务规则集中、清晰、可测试；
4. 前端、后端、数据库之间职责明确；
5. 后续可以替换技术实现，而不需要推翻业务模型；
6. V1 可以运行在本地 Windows 环境，并最终部署到 Synology NAS Docker；
7. 将来如有需要，可以迁移到云端而尽量保留现有数据和业务逻辑。

---

## 2. 架构原则

### 2.1 Business Model First

业务模型优先于具体技术。

以下文档定义业务事实：

- `BUSINESS_RULES.md`
- `PRD.md`
- `ER_MODEL.md`

技术实现必须遵守这些文档。

如果某个框架、ORM、UI 组件库或开源基座的默认设计与业务规则冲突，应调整技术实现，而不是为了迁就技术实现改变已经确认的业务规则。

### 2.2 V1 Simplicity First

V1 的目标是：能够真实处理水上器材租赁业务，而不是建设一个功能尽可能多的平台。

因此 V1 应优先：

- 减少技术层次；
- 减少第三方依赖；
- 减少复杂抽象；
- 减少重复数据；
- 减少不必要的历史记录系统；
- 保持数据库结构容易理解；
- 保持 Docker 部署简单。

### 2.3 Reuse Before Rewrite

项目优先寻找合适的开源项目作为技术基座。

如果已有开源项目已经解决登录、基础 CRUD、数据库访问、表单、Docker、基础 UI、客户管理、订单管理或库存管理，则优先复用，而不是重新开发。

但是：

> 开源基座的现有业务模型不能凌驾于本项目已经确定的业务模型。

必要时应重构或替换不符合本项目业务规则的部分。

### 2.4 Replaceability Over Technology Lock-in

本项目不在架构层面强制绑定某一个具体：

- 前端框架；
- 后端框架；
- ORM；
- UI 组件库；
- API 风格；
- 定时任务库。

这些属于 Implementation Choice。

架构层面只规定模块职责和边界。因此，只要业务接口和数据模型保持稳定，将来可以替换具体技术实现。

---

## 3. 总体逻辑架构

V1 采用简单的 Web Application 架构：

```text
┌──────────────────────────────┐
│          Browser             │
│       Web UI / Frontend      │
└──────────────┬───────────────┘
               │ HTTP / API
               ▼
┌──────────────────────────────┐
│          Backend             │
│                              │
│  API / Application Services  │
│  Business Rules              │
│  Authentication              │
│  Scheduled Operations        │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│         Persistence          │
│                              │
│          SQLite              │
│       Relational Data        │
└──────────────────────────────┘
```

前端和后端可以部署在同一个 Docker Application 中，也可以根据最终选择的开源基座采用前后端分离部署。架构不要求必须采用某一种部署方式。

---

## 4. 前端职责

Frontend 负责：

- 页面展示；
- 用户交互；
- 表单输入；
- 基础客户端校验；
- API 调用；
- 操作结果展示；
- 错误提示；
- Loading 状态；
- Dashboard；
- Customer 页面；
- Order 页面；
- Equipment / Inventory 页面；
- Payment 页面；
- Settings 页面。

Frontend 不负责最终业务判断。

例如库存是否足够、Order 是否允许 Check-in、OrderItem 是否已经锁定、Return 是否有效、Customer 是否满足创建条件、自动归还是否应该执行，都必须由 Backend 作为最终权威判断。

前端可以提前进行校验以改善用户体验，但不能代替后端业务校验。

---

## 5. Backend 职责

Backend 是业务规则的最终权威层。

Backend 负责：

- Authentication；
- Authorization；
- Customer；
- Equipment；
- Inventory；
- Order；
- OrderItem；
- Check-in；
- Return；
- Auto Return；
- Daily Forced Return；
- Payment；
- Boat Assignment；
- Settings；
- 数据验证；
- 数据库事务；
- 状态转换；
- 数据一致性；
- 自动任务；
- 操作人记录。

Backend 应尽量避免把核心业务规则散落在多个 API endpoint 中。

推荐结构：

```text
API
 ↓
Application Service
 ↓
Business Rules / Domain Logic
 ↓
Persistence
 ↓
SQLite
```

---

## 6. Application Service

Application Service 负责组织一个完整的业务操作。

例如：

```text
create_order()
update_order()
cancel_order()
check_in_order()
cancel_check_in()
return_order()
cancel_return()
add_order_item()
remove_order_item()
update_inventory()
create_customer()
match_customer()
add_payment_adjustment()
```

Application Service 可以协调多个数据库操作。

例如 Check-in：

```text
Check-in Order
    ↓
Validate Order
    ↓
Validate date/time rules
    ↓
Validate customer / people / equipment rules
    ↓
Create check_in_at
    ↓
Lock OrderItems
    ↓
Start Auto Return cycle
    ↓
Update inventory calculation
    ↓
Record operator
```

这些步骤应作为一个具有事务一致性的业务操作执行。

---

## 7. Business Rules Layer

业务规则是本项目最重要的逻辑层。

业务规则包括但不限于：

### Order

- 所有交易统一使用 Order；
- 不存在 Reservation / Walk-in 两种程序概念；
- 不设置 `order_type`；
- OrderItem 是订单收费明细；
- Order 的 end_at = start_at + 2 小时；
- terminal status 下不能直接编辑；
- 状态只能按照规定的生命周期转换。

### Customer

- Customer 有唯一 ID；
- name / WeChat nickname / WeChat ID / phone 参与匹配；
- Customer 的最小独立创建条件由 BUSINESS_RULES.md 定义；
- 系统游客 Customer 受保护。

### Equipment

- EquipmentType / EquipmentSpec / SaleItem 分开管理；
- EquipmentSpec 保存当前标准价格；
- OrderItem 保存创建时的 unit_price 快照；
- 历史业务数据不能因为目录变化而改变。

### Inventory

库存不是独立保存的 available 数字。

核心计算：

```text
Available Inventory
=
Current Operational Inventory
-
Checked-in and Unreturned Equipment Quantity
```

未来订单不会提前占用库存。

### Check-in

Check-in 不创建独立实体，使用：

```text
orders.check_in_at
orders.check_in_by_user_id
```

记录当前有效 Check-in。

### Return

Return 不创建独立实体，使用：

```text
orders.return_at
orders.return_by_user_id
```

记录当前有效 Return。

### Auto Return

Check-in 时保存当前 Auto Return 周期配置。后续 Settings 改变不影响已经开始的周期。

### Daily Forced Return

每日营业结束时，对仍然 Check-in 且没有有效 Return 的订单执行系统自动 Return。

### Payment

订单收费以 OrderItem 为基础。Payment 不重复记录 OrderItem。

PaymentItem 当前主要用于 `Other`，例如折扣、附加费用、手工调整。

最终金额动态计算，不在 Order 上保存 `total_amount`。

---

## 8. Persistence Layer

Persistence Layer 负责：

- 数据库连接；
- 查询；
- 插入；
- 更新；
- 删除；
- Transaction；
- Migration；
- Index；
- Constraint。

Persistence Layer 不应承担完整业务流程。

例如 Repository 可以负责：

```text
find_order_by_id()
save_order()
find_customer_by_phone()
get_inventory_configuration()
```

但不应该负责完整的：

```text
check_in_order()
```

完整业务操作应由 Application Service 组织。

---

## 9. Database

### 9.1 V1 Database

V1 默认使用：

> SQLite

原因：

- 单店内部管理；
- 用户数量有限；
- 部署简单；
- 不需要额外数据库服务；
- 方便 Docker；
- 方便备份；
- 方便未来迁移。

SQLite 是 V1 的部署选择，不是永久架构锁定。

### 9.2 数据库模型

数据库模型以 `ER_MODEL.md` 为准。

当前核心实体：

```text
users
customers
equipment_types
equipment_specs
sale_items
boats
inventory_configurations
orders
order_items
boat_assignments
payments
payment_items
settings
```

程序中不应额外创建：

```text
reservations
walk_ins
check_ins
returns
actual_usages
order_types
```

除非未来业务需求明确改变并重新修订 ER_MODEL.md。

---

## 10. Database Integrity

数据库约束和业务规则需要分开考虑。

### Database Constraint

适合由数据库保证：

- PK；
- FK；
- UNIQUE；
- NOT NULL；
- 基础 CHECK；
- 数值范围；
- 基础结构一致性。

### Application Business Validation

适合由 Backend 保证：

- Order 状态转换；
- Check-in 条件；
- Return 条件；
- 自动 Return；
- Inventory 计算；
- Customer matching；
- 设备容量组合；
- Payment 业务规则；
- 权限；
- 跨表业务逻辑。

两者可以同时存在。

数据库约束是最后一道防线，Backend 是业务规则的主要实现位置。

---

## 11. Transaction

涉及多个业务状态变化的操作必须尽可能使用数据库 Transaction。

重点包括：

### Check-in

```text
Validate
→ Set Check-in
→ Start Auto Return Cycle
→ Commit
```

### Cancel Check-in

```text
Validate
→ Clear Check-in
→ Clear Auto Return Cycle
→ Commit
```

### Return

```text
Validate
→ Set Return
→ Complete Order
→ Commit
```

### Cancel Return

```text
Validate
→ Restore active
→ Clear current Return
→ Commit
```

### OrderItem modification

如果修改同时影响多个表，应使用 Transaction。

目标是避免出现前半个操作成功、后半个操作失败而导致业务状态不一致。

---

## 12. Inventory Architecture

Inventory 采用“配置总量 + 实时计算占用”的模式。

```text
InventoryConfiguration.total_quantity
                    +
OrderItem
                    +
Order.check_in_at
                    +
Order.return_at
                    ↓
              Available Quantity
```

只有满足：

```text
effective Check-in
AND
no effective Return
```

的 Equipment OrderItem 才占用库存。

SaleItem 不影响 Equipment Inventory。

BoatAssignment 不影响 Inventory Quantity。

---

## 13. Order Lifecycle Architecture

Order 是核心业务实体。

简化生命周期：

```text
              ┌──────────────┐
              │    active    │
              └──────┬───────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
     cancelled    no_show   completed
          ▲          ▲          ▲
          └──────────┴──────────┘
                 restore
```

V1 不允许任意状态跳转。

原则：

```text
active → terminal
terminal → active
```

其中 terminal：

```text
cancelled
no_show
completed
```

实际允许的具体操作必须遵守 BUSINESS_RULES.md。

---

## 14. Check-in Architecture

Check-in 是 Order 的状态数据，不是独立实体。

数据：

```text
check_in_at
check_in_by_user_id
```

Check-in 成功后：

1. Order 记录当前 Check-in；
2. OrderItem 被锁定；
3. Auto Return cycle 开始；
4. Inventory 开始计算对应设备的占用。

取消 Check-in：

1. 清除 Check-in；
2. 清除 Auto Return cycle；
3. 释放库存占用；
4. 解锁 OrderItem。

---

## 15. Return Architecture

Return 是 Order 的当前有效 Return 数据，不是独立实体。

数据：

```text
return_at
return_by_user_id
```

Return 可以来自：

- 人工 Return；
- Ordinary Auto Return；
- Daily Forced Return。

Return 后：

```text
Order → completed
```

并释放对应设备库存。

Return 不删除 BoatAssignment。

---

## 16. Automatic Operations

系统存在两类自动 Return。

### 16.1 Ordinary Auto Return

Check-in 时：

```text
auto_return_at
=
check_in_at
+
auto_return_after_minutes
```

系统任务周期性检查：

```text
check_in exists
AND
no effective return
AND
auto_return_at <= now
AND
auto_return_occurred = 0
```

满足条件后执行自动 Return。

System User 作为操作人。

### 16.2 Daily Forced Return

每日营业结束时：

```text
effective Check-in
AND
no effective Return
```

的订单执行 Daily Forced Return。

它与 Ordinary Auto Return 是两个独立机制。

Daily Forced Return 不改变：

```text
auto_return_occurred
auto_return_at
```

---

## 17. System User

系统必须存在一个受保护的：

> System User

System User 用于记录：

- Ordinary Auto Return；
- Daily Forced Return；
- 其他明确由系统自动执行的业务操作。

System User：

- 不允许普通登录；
- 不允许删除；
- `is_system = 1`。

这样所有业务变化都可以追溯到一个 User。

---

## 18. Authentication

V1 使用：

> Username + Password

认证职责属于 Backend。

密码必须以安全的 password hash 存储，不得保存明文密码。

V1 不要求：

- 微信登录；
- 手机验证码登录；
- OAuth；
- 多因素认证；
- 复杂 RBAC。

V1 所有正常用户采用相同业务权限模型。

未来如果需要角色权限，可在不改变核心业务实体的情况下扩展。

---

## 19. Time Architecture

数据库统一使用：

> UTC

业务时区：

> Asia/Shanghai

规则：

- DB timestamp 使用 UTC；
- API 内部使用明确的时间格式；
- 前端根据 Asia/Shanghai 展示业务时间；
- 所有“今天”“当天”“23:59”等业务概念按照 Asia/Shanghai 判断。

这样可以降低未来迁移到云端后的时区问题。

---

## 20. Money Architecture

数据库金额统一使用：

> INTEGER fen

例如：

```text
150 元 = 15000
90 元 = 9000
```

Frontend 显示：

```text
¥150.00
```

Backend / Database 使用：

```text
15000
```

避免使用浮点数存储货币。

---

## 21. API Boundary

Frontend 与 Backend 之间通过 API 通信。

API 应表达业务操作，而不是简单暴露数据库 CRUD。

例如推荐：

```text
POST /orders
POST /orders/{id}/check-in
POST /orders/{id}/cancel-check-in
POST /orders/{id}/return
POST /orders/{id}/cancel-return
POST /orders/{id}/restore
```

而不是让前端直接：

```text
UPDATE orders SET check_in_at = ...
```

API 是业务边界。

具体 URL 风格可以根据最终选择的开源基座调整。

---

## 22. Customer Matching

Customer matching V1 保持简单。

流程：

```text
Operator enters one identity field
            ↓
Backend searches other identity fields
            ↓
Candidate customers returned
            ↓
Operator confirms
            ↓
Customer profile selected
```

V1 不要求：

- AI matching；
- fuzzy matching；
- pinyin matching；
- complicated ranking；
- automatic merge。

最终 Customer 选择权属于操作员。

---

## 23. Equipment Architecture

Equipment 分成：

### EquipmentType

例如：

```text
Racing Kayak
Leisure Kayak
Paddleboard
```

### EquipmentSpec

例如：

```text
Racing Kayak / 3-seat
Racing Kayak / 2-seat
Racing Kayak / 1-seat
```

EquipmentSpec 保存：

- 当前标准价格；
- capacity；
- active 状态。

OrderItem 保存创建时的：

```text
unit_price
```

因此未来修改标准价格不会修改历史订单金额。

---

## 24. SaleItem Architecture

SaleItem 是可收费的额外商品。

例如：

```text
Waterproof Bag
```

SaleItem 不影响 Equipment Inventory。

它可以和 EquipmentSpec 一起成为 OrderItem。

因此：

```text
Order
 ├── OrderItem: Racing Kayak
 ├── OrderItem: Waterproof Bag
 └── PaymentItem: Other adjustment
```

---

## 25. Boat Architecture

Boat 是可选的具体设备实例。

例如：

```text
Boat #001
Boat #002
Boat #003
```

BoatAssignment：

```text
OrderItem
   ↓
BoatAssignment
   ↓
Boat
```

V1：

- 不强制分配 Boat；
- 不自动分配；
- 不检查 Boat 时间重叠；
- `not_available` 的 Boat 不允许新的 assignment；
- 已有 assignment 不因为状态改变而自动删除。

BoatAssignment UI 可以晚于核心订单流程实现。

---

## 26. Settings Architecture

Settings 是管理中心，不是一个巨大的 JSON 配置表。

主要配置对象分别存储：

```text
settings
equipment_types
equipment_specs
sale_items
inventory_configurations
boats
```

Settings Core 保存真正的系统级配置，例如：

```text
auto_return_after_minutes
boat_management_enabled
```

EquipmentSpec 的价格、SaleItem 的价格、Inventory 数量不放入 settings JSON。

---

## 27. Frontend Page Structure

V1 页面建议包括：

```text
Login
│
├── Dashboard
│
├── Orders
│   ├── Order List
│   ├── Create Order
│   └── Order Detail
│
├── Customers
│   ├── Customer List
│   └── Customer Detail
│
├── Equipment / Inventory
│
├── Payment
│
└── Settings
    ├── Equipment Types
    ├── Equipment Specs
    ├── Sale Items
    ├── Inventory
    ├── Boats
    └── System Settings
```

具体页面名称和导航结构可以根据最终开源基座调整。

---

## 28. Error Handling

Backend 应返回可理解的业务错误。

例如：

```text
ORDER_NOT_FOUND
ORDER_NOT_ACTIVE
CHECK_IN_NOT_ALLOWED
RETURN_NOT_ALLOWED
RETURN_ALREADY_EXISTS
ORDER_ITEM_LOCKED
CUSTOMER_NOT_FOUND
INVALID_CUSTOMER
INVALID_PEOPLE_COMPOSITION
INVENTORY_SHORTAGE
BOAT_NOT_AVAILABLE
PAYMENT_ITEM_INVALID
```

Frontend 将这些错误转换为用户可理解的中文提示。

不应直接把数据库异常原文显示给操作员。

---

## 29. Logging

系统至少应记录：

- Application Error；
- Authentication Error；
- Scheduled Task Error；
- Database Error；
- Critical Business Operation Error。

业务操作本身通过 User 字段记录：

```text
created_by_user_id
updated_by_user_id
check_in_by_user_id
return_by_user_id
```

自动操作使用：

```text
System User
```

V1 不要求建立完整的 Audit Log Event Store。

---

## 30. Testing Architecture

测试重点应放在业务规则，而不是单纯页面截图测试。

优先测试：

### Customer

- 创建条件；
- UNIQUE；
- matching；
- System Customer 保护。

### Order

- 创建；
- 编辑；
- 状态转换；
- terminal lock。

### OrderItem

- EquipmentSpec；
- SaleItem；
- unit_price snapshot；
- Check-in 后锁定；
- Return 后锁定。

### Capacity

- 成人/儿童人数；
- 各 EquipmentSpec 容量规则。

### Inventory

- 未 Check-in 不占库存；
- Check-in 占库存；
- Return 释放库存；
- Cancel Check-in 释放库存；
- SaleItem 不占库存。

### Check-in / Return

- 时间规则；
- 状态规则；
- Return > Check-in；
- 无 Check-in 的直接 Return。

### Auto Return

- schedule；
- snapshot；
- cancel cycle；
- duplicate prevention。

### Daily Forced Return

- 当日结束处理；
- Inventory release；
- System User；
- 与 Ordinary Auto Return 独立。

---

## 31. Backup and Recovery

由于 V1 使用 SQLite，数据库文件应作为重要业务资产保护。

至少需要：

```text
SQLite database
+
application configuration
```

可备份。

V1 应尽量提供简单可靠的数据库备份方式。

推荐：

```text
regular SQLite backup
→
NAS backup location
```

未来可以扩展：

- scheduled backup；
- backup retention；
- cloud backup；
- point-in-time recovery。

---

## 32. Docker Deployment

V1 最终目标是在 Synology NAS Container Manager 中运行。

目标结构可以是：

```text
Synology NAS
│
└── Container Manager
      │
      └── Rental App
           ├── Web / Backend
           └── SQLite data volume
```

数据库文件必须位于持久化 Volume，而不是只存在于 Container Writable Layer。

例如逻辑上：

```text
/app/data
```

映射到 NAS：

```text
/volume1/docker/rental-app/data
```

具体路径根据最终 Docker 配置确定。

---

## 33. Local Development

开发环境：

```text
Windows
    ↓
Git repository
    ↓
Local development server
    ↓
Browser
```

推荐保持：

```text
GitHub = source of truth
```

本地环境用于：

- 开发；
- 测试；
- 数据模型验证；
- UI 调整。

NAS 用于：

- 实际部署；
- 实际业务使用。

---

## 34. Git Workflow

建议：

```text
main
  ↑
development / feature branch
```

V1 阶段不需要复杂 Git Flow。

重要原则：

1. 每完成一个可工作的功能就提交；
2. 不要一次修改几十个不相关模块；
3. 每次 commit 尽量对应一个明确目的；
4. 保持可以回退；
5. 大规模修改前先备份或建立 branch。

---

## 35. Open-source Base Integration

选定 GitHub 基座后，应先进行：

```text
License Check
        ↓
Technology Stack Check
        ↓
Database / Data Model Check
        ↓
Module Structure Check
        ↓
Docker Check
        ↓
Security Check
        ↓
Business Fit Check
```

不要因为项目 UI 看起来漂亮就直接采用。

尤其需要检查：

- License；
- 是否允许修改和商业/内部使用；
- 是否有明显安全问题；
- 是否已经停止维护；
- 是否存在大量不必要功能；
- 是否很难替换原有业务模型；
- 是否有过度复杂的数据库结构。

---

## 36. Architecture Adaptation Strategy

选定基座后，不要求完全保留它原来的结构。

可以采用：

```text
Existing Base
     ↓
Identify reusable modules
     ↓
Keep useful infrastructure
     ↓
Replace conflicting business logic
     ↓
Align database model
     ↓
Align UI with PRD
```

优先保留：

- authentication infrastructure；
- Docker；
- frontend shell；
- UI components；
- database connection infrastructure；
- common utilities；
- testing infrastructure。

必要时替换：

- reservation model；
- rental lifecycle；
- inventory logic；
- payment model；
- customer model；
- order state machine。

---

## 37. Technology Decisions vs Architecture Requirements

以下属于 Architecture Requirement：

- Business rules must be enforced by Backend；
- Database must preserve historical order prices；
- Order is the central transaction entity；
- Reservation / Walk-in are not separate program concepts；
- Inventory must be derived from effective Check-in / Return state；
- Check-in and Return are not separate entities；
- automatic actions use System User；
- DB timestamps use UTC；
- business timezone is Asia/Shanghai；
- money uses integer fen；
- data must be persistent in Docker；
- historical business data cannot be bypassed by deletion；
- application should remain replaceable and portable.

以下属于 Implementation Choice：

- React / Vue / other frontend framework；
- FastAPI / Node.js / other backend framework；
- Prisma / SQLAlchemy / other ORM；
- Tailwind / another CSS system；
- REST / another API style；
- SQLite library；
- task scheduler implementation；
- specific component library。

Implementation Choice 可以随着选定的开源基座调整。

---

## 38. Future Cloud Migration

V1 不需要提前建设云架构。

但是应避免：

- 把 NAS 路径写死进业务代码；
- 把 SQLite API 暴露给 Frontend；
- 把业务逻辑写进 UI；
- 把业务规则写死在数据库文件操作中；
- 依赖只能在 Synology 上运行的逻辑。

未来迁移到云端时，目标结构可以演变为：

```text
Browser
   ↓
Cloud Frontend
   ↓
Application Backend
   ↓
PostgreSQL / other relational DB
```

核心业务模型尽量保持：

```text
Customer
Equipment
Order
OrderItem
Inventory
Payment
Boat
User
```

不需要因为部署环境改变而重新设计整个业务系统。

---

## 39. V1 Architecture Scope

V1 必须优先保证：

```text
Login
Customer
Equipment
Inventory
Order
OrderItem
Check-in
Return
Auto Return
Daily Forced Return
Payment
Basic Dashboard
Settings
Docker Deployment
```

V1 暂不要求：

- 多门店；
- SaaS；
- 微信授权；
- 手机验证码；
- RBAC；
- 复杂审计系统；
- 在线客户自助预约；
- 在线支付；
- 复杂报表；
- BoatAssignment 完整 UI；
- AI customer matching；
- 云端同步。

这些功能应进入未来增强范围，而不是阻碍 V1。

---

## 40. Final Architecture Principle

本项目最重要的架构原则：

> **技术服务于业务，业务模型保持稳定，具体技术实现保持可替换。**

开发过程中应始终优先回答：

1. 这是否符合 BUSINESS_RULES.md？
2. 这是否符合 PRD.md？
3. 这是否符合 ER_MODEL.md？
4. 是否真的属于 V1？
5. 是否可以复用现有开源代码？
6. 是否增加了不必要的复杂度？
7. 是否会影响未来数据迁移？

如果某个技术方案无法同时满足这些要求，应优先重新评估技术方案，而不是改变已经确认的核心业务规则。
