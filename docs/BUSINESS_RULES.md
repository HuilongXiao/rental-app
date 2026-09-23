# Rental App — Business Rules

## 1. Purpose and authority

本文档定义 Rental App V1 的权威业务规则。系统是供水上器材租赁业务内部操作员使用的管理系统，主要管理客户、订单、设备目录、运营库存、Check-in、Return 和 Payment。

如果其他项目文档与本文档的业务规则冲突，以本文档为准。本文档不规定具体前端框架、后端框架、ORM 或部署平台。

V1 预计供 2–5 名内部操作员使用。V1 通过 Docker 运行在 Synology NAS 上，并需要通过互联网远程访问。远程访问必须使用 HTTPS 和认证保护。

---

## 2. Order 是唯一交易概念

客户的一次租赁交易只有一个业务实体：`Order`。

以下不是独立的 V1 业务实体或订单类型：

- Reservation
- Walk-in
- Reservation Order
- Walk-in Order
- Order Type

预���和临时到店只是自然语言描述。系统不根据 `start_at` 是过去、现在还是未来来推断订单类型，也不因此建立不同处理流程。

---

## 3. User

User 用于识别执行业务变更的操作员。

字段包括：`id`、`username`、`display_name`、`password_hash`、`is_active`、`is_system`、`created_at`、`updated_at`。

规则：

- `username` 唯一。
- 正常用户使用用户名和密码登录。
- 密码只能保存安全 hash，不能保存明文密码。
- V1 不实现角色和权限矩阵；正常操作员具有相同功能权限。
- System User 必须存在，`is_system = 1`。
- System User 不能删除，不能通过普通登录流程登录。
- 系统自动执行的业务操作使用 System User 作为操作人。

---

## 4. Customer

Customer 可以包含：`name`、`gender`、`wechat_nickname`、`wechat_id`、`phone`。

- `phone` 和 `wechat_id` 在有值时必须唯一。
- `name` 和 `wechat_nickname` 不要求唯一。
- 独立创建 Customer 至少满足 `name + phone` 或 `wechat_nickname + wechat_id`。
- V1 使用简单候选搜索和操作员确认，不要求模糊匹配、拼音匹配、AI 匹配或自动合并。
- 系统客户“游客”必须存在，不能删除或改名，其 phone 和 WeChat ID 不可修改。
- Order 保存客户信息快照。Customer 后续修改不能静默改写历史 Order 快照。

---

## 5. Equipment 目录

### 5.1 EquipmentType

EquipmentType 表示设备大类，例如 Kayak、Paddleboard。名称唯一。

### 5.2 EquipmentSpec

EquipmentSpec 表示具体可租赁设备规格，包含：`equipment_type_id`、`name`、当前 `price`、`capacity`、`is_active` 及创建/更新信息。

- 当前价格以整数分保存。
- 创建 OrderItem 时复制当前价格到 `unit_price`，形成历史价格快照。
- inactive 的 EquipmentSpec 不能加入新订单，但历史 OrderItem 仍可引用。
- 不得为了从当前目录移除项目而删除历史业务数据。
- `capacity` 表示最大总人数，不表示最少人数。

V1 初始目录价格：Racing kayak ¥150、Paddleboard ¥150、Leisure kayak ¥90。价格可以在 Settings 中调整。

### 5.3 Capacity

成人和儿童数量必须是非负数，总人数至少为 1，并满足设备规格的容量和组合规则。

- 3-seat kayak：最多 3 人，至少 1 名成人，最多 2 名成人。
- 2-seat kayak：最多 2 人，至少 1 名成人。
- 1-seat kayak：只能 1 名成人，不能有儿童。
- Paddleboard：V1 不额外规定成人/儿童限制，除非业务明确补充规则。

选择设备时，UI 可以初始化人数；操作员手动修改后，后续设备变更不得静默覆盖手动输入。最终保存和 Check-in 前必须再次校验。

### 5.4 SaleItem

SaleItem 是不属于 EquipmentSpec、但可以收费的额外项目，例如 waterproof bag。它有名称、当前价格和 active 状态。它不占用设备库存。

---

## 6. Order

Order 至少记录：客户及快照、`start_at`、自动计算的 `end_at`、成人/儿童人数、OrderItems、状态、操作人、Check-in、Return、Auto Return 和 Daily Forced Return 的当前字段。

- `order_number` 系统生成且唯一。
- `end_at = start_at + 2 hours`，操作员不能独立编辑 `end_at`。
- 数据库存储 UTC 时间，业务日期使用 `Asia/Shanghai`。
- 金额使用整数分。

### 6.1 状态

V1 只有以下四种 Order lifecycle status：

- `active`
- `cancelled`
- `no_show`
- `completed`

允许的状态转换：

- `active → cancelled`
- `active → no_show`
- `active → completed`
- `cancelled → active`
- `no_show → active`
- `completed → active`

`checked_in`、`returned`、`auto_returned`、`using`、`reserved`、`walk_in` 不是 status 值。`completed` 不代表一定存在 Return；直接完成和系统自动完成都是允许的业务结果。

Terminal Order 正常情况下不可编辑。如需修改，必须先按照规则恢复为 active。

### 6.2 OrderItem

OrderItem 表示普通收费项目，必须恰好引用一个 EquipmentSpec 或一个 SaleItem。

- `quantity >= 1`。
- `unit_price` 是创建时的价格快照，不能在 Order 页面直接修改。
- 行金额为 `quantity × unit_price`。
- Check-in 后 OrderItems 锁定。
- 如需在 Check-in 后修改，必须在允许的情况下取消当前 Check-in，再修改并重新 Check-in。
- 有效 Return 后 OrderItems 仍保持锁定。

---

## 7. Business date、Check-in 和 Return

业务时区为 `Asia/Shanghai`。系统比较订单业务日期和当前业务日期：

- 订单日期早于今天：不允许 Check-in 和 Return，不显示相关按钮。
- 订单日期等于今天：在其他规则允许时可以显示并执行相关操作。
- 订单日期晚于今天：不允许 Check-in 和 Return，不显示相关按钮。

隐藏按钮不是唯一保护；后端必须再次拒绝不符合日期规则的请求。

### 7.1 Check-in

Check-in 不是独立实体，由当前订单字段表示：

- `check_in_at`
- `check_in_by_user_id`

规则：

- 时间由操作员按下按钮时系统自动取得，操作员不能输入时间。
- `check_in_at >= start_at`。
- 只能对当天订单执行。
- 有效 Return 存在时，不能直接改变 Check-in，必须先按规则处理 Return。
- 成功后锁定 OrderItems、开始占用库存并开始 Auto Return 周期。
- 取消 Check-in 会清除当前 Check-in、释放库存、清除当前 Auto Return 周期并在允许时解锁 OrderItems。
- V1 不记录 Check-in 历史。

### 7.2 Return

Return 不是独立实体，由当前订单字段表示：

- `return_at`
- `return_by_user_id`

规则：

- 时间由操作员执行 Return 时系统自动取得，操作员不能输入时间。
- 有 Check-in 时，`return_at > check_in_at`。
- 没有 Check-in 的直接 Return 允许执行，但 `return_at >= start_at + 1 minute`。
- Return 后订单变为 `completed`，实际占用的库存被释放。
- 没有 Check-in 的直接 Return 不改变库存，因为此前没有库存占用。
- Return 只能对当天订单执行；过去日期和未来日期订单不显示 Return 按钮，后端也必须拒绝。
- 允许的 Return 修正必须是事务一致的业务操作。

V1 不设置“客户是否仍在使用设备”的字段。

---

## 8. Auto Return

Auto Return 是防止操作员繁忙时库存长期被占用的库存保护机制，不是客户实际使用状态记录，也不代表客户一定在该时刻停止使用。

Check-in 时：

- 将当前 `auto_return_after_minutes` 复制到 Order；
- 计算本次 `auto_return_at`；
- 开始库存占用。

到期时，如果没有有效 Return，系统执行 Auto Return：

- 订单变为 `completed`；
- 释放库存；
- 使用 System User；
- 设置 Auto Return 相关标记和时间。

如果客户实际使用时间超过 Auto Return，操作员可以执行允许的人工 Return 更新/修正操作，使用当前系统时间记录操作员的 Return。该操作必须按实现约定清除或更新当前 Auto Return 时间标记，并作为单一事务处理。V1 不增加客户实际使用字段。

如果操作员在 Auto Return 前人工 Return，Auto Return 任务不得随后重复创建 Return。

---

## 9. Daily Forced Return

Daily Forced Return 是防止跨午夜订单长期占用库存的技术安全机制，不是客户流程的核心业务要求。

每天 Asia/Shanghai 的 `23:59:01–23:59:59` 处理仍有有效 Check-in 且没有有效 Return 的订单：

- 使用 System User 记录 Return；
- 释放库存；
- 将订单设为 completed；
- 设置 `daily_forced_return_occurred`。

它与普通 Auto Return 独立，不应被解释为客户实际停止使用的精确事实。V1 不保存客户实际使用状态字段。

---

## 10. Inventory

Inventory 表示当前运营库存，不是物理所有权历史。每个 EquipmentSpec 有一个库存配置 `total_quantity`。

```text
available_quantity = total_quantity - occupied_quantity
```

`occupied_quantity` 只统计属于有效 Check-in 且没有有效 Return 的 EquipmentSpec OrderItem。未来订单不会占用库存。

库存不足规则：

- 可用库存为 0 或 Check-in 后会小于 0 时，必须显示清晰警告。
- V1 不强制阻止 Check-in；操作员确认后仍可完成。
- `total_quantity` 不得为负数。
- V1 不要求保存库存调整历史。

---

## 11. Payment

Payment 用于记录订单的应收金额计算和人工调整明细，不记录实际付款状态或付款渠道。

V1 不记录：

- 已付款/未付款；
- 现金、微信、支付宝、银行卡等支付方式；
- 客户支付账户信息。

最终金额可由明细计算：

```text
final_amount = SUM(OrderItem.quantity × OrderItem.unit_price)
             + SUM(PaymentItem.amount)
```

最终金额必须能够按订单查询并用于后续统计分析。可以动态计算，也可以保存可重建的缓存；Order 的独立总金额不能取代明细作为唯一权威数据。

PaymentItem 用于折扣、附加费、退款、修正等人工调整：

- `amount = quantity × unit_price`；
- 正数表示增加，负数表示退款或扣减；
- 人工 adjustment 必须填写 note；
- PaymentItem 创建后不可修改；
- 更正必须新增 PaymentItem；
- completed、cancelled、no-show 订单仍可添加 Payment adjustment。

---

## 12. Actor、ID 和历史完整性

每个业务变更必须记录操作人。自动操作使用 System User。所有主键使用 UUID。金额使用整数分。数据库时间使用 UTC，业务日期使用 Asia/Shanghai。

EquipmentSpec、SaleItem 停用时使用 `is_active = 0`，不得删除历史引用。Orders、OrderItems、Payments、PaymentItems 和操作人引用不得为了绕过业务规则而删除。

V1 不要求独立 audit log，但核心表必须保留创建、更新及关键操作人字段。

---

## 13. V1 明确排除的内容

V1 不包含：

- Boat、BoatAssignment 和具体船号管理；
- 客户自助预订、客户账号、在线支付、微信登录或小程序；
- 角色权限、多个门店、复杂会计、支付网关；
- 预约冲突引擎；
- Check-in、Return、ActualUsage 的独立历史表；
- 客户实际使用状态字段；
- 库存调整历史和完整 audit log。

Boat/BoatAssignment 可以在 V2 根据真实使用情况重新设计。
