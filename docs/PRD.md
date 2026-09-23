# Rental App — 产品需求文档（PRD）

## 1. 产品概述

Rental App 是供皮划艇、桨板等水上器材租赁业务内部操作员使用的 Web 管理系统。V1 预计供 2–5 名工作人员使用，不提供客户自助预订。

V1 的核心目标是让操作员能够完成：

```text
登录 → 客户 → Order → Check-in → 库存占用 → Return → Payment
```

系统需要在日常运营中替代核心 Excel 或纸面记录。

## 2. 产品原则

- 一次交易只有一个 `Order`。
- Reservation 和 Walk-in 只是自然语言描述，不是订单类型或独立实体。
- 后端是业务规则的最终权威，前端校验不能替代后端校验。
- 优先保证日常操作简单、数据一致和容易恢复。
- V1 不因为其他租赁软件常见某项功能就引入额外实体或流程。

## 3. 用户和权限

V1 用户是内部操作员/管理人员。

用户可以：

- 登录；
- 创建和编辑 Customer；
- 创建、查询、编辑和处理 Order；
- 管理 EquipmentSpec、SaleItem 和运营库存；
- 执行 Check-in、Return 和允许的修正；
- 查看和调整 Payment 金额明细；
- 查看 Dashboard 和运营信息。

V1 不实现角色权限矩阵。所有正常登录用户拥有相同功能权限。System User 只用于自动操作，不能普通登录。

## 4. V1 功能模块

1. Login
2. Dashboard
3. Customer Management
4. Order Management
5. Check-in
6. Return
7. Payment
8. Equipment Management
9. Inventory Management
10. Settings
11. 基础 Backup / Restore（如果不会明显延迟核心功能）

V1 不包含 Boat 和 BoatAssignment。

## 5. Login

登录页面需要：

- username；
- password；
- 登录按钮；
- 登录失败提示。

inactive 用户不能登录。密码必须以安全 hash 保存，不能保存明文。

V1 不需要：角色、复杂权限、SSO、微信登录、短信登录、客户账号、密码找回流程。

## 6. Dashboard

Dashboard 优先显示当天运营信息：

- 今天的订单；
- active、checked-in、completed 订单数量；
- 需要操作员关注的订单；
- 各 EquipmentSpec 的运营库存、已占用数量和可用数量；
- Auto Return 或 Daily Forced Return 相关提示；
- 当天 Payment 金额汇总（如果实现不会增加不必要复杂度）。

V1 不需要预测、利润分析、客户生命周期、复杂 BI 或 AI 推荐。

## 7. Customer Management

Customer 页面支持：

- 搜索 Customer；
- 查看和编辑 Customer；
- 创建 Customer；
- 从 Customer 开始创建 Order。

支持字段：name、gender、WeChat nickname、WeChat ID、phone。独立 Customer 必须满足 `name + phone` 或 `wechat_nickname + wechat_id`。

搜索采用简单候选搜索，由操作员确认最终 Customer。不需要模糊匹配、拼音匹配、AI 匹配或自动合并。

创建 Order 时保存 Customer 快照，后续 Customer 资料变化不能静默修改历史 Order 快照。

## 8. Order Management

### 8.1 创建 Order

操作员可以选择或填写：

- existing Customer、new Customer 或系统客户“游客”；
- start date；
- start time；
- adults；
- children；
- 一个或多个 OrderItem；
- note。

系统自动计算：

```text
end_at = start_at + 2 hours
```

操作员不能独立编辑 `end_at`。OrderItem 可以是 EquipmentSpec 或 SaleItem。创建时复制当前目录价格作为 `unit_price` 快照。

### 8.2 Order 编辑

有效 Check-in 之前可以：

- 修改客户引用；
- 修改 start time；
- 修改成人/儿童人数；
- 添加、删除和修改 OrderItem 数量；
- 更换适用 EquipmentSpec 或 SaleItem；
- 修改 note。

不能直接编辑已有 OrderItem 的历史 `unit_price`。Check-in 后 OrderItems 锁定；如需修改，必须在允许时取消 Check-in，再修改并重新 Check-in。有效 Return 后仍保持锁定。

### 8.3 Status

V1 只有：`active`、`cancelled`、`no_show`、`completed`。

Terminal Order 默认不可编辑，允许的修改必须先恢复为 active。`checked_in`、`returned`、`auto_returned`、`using` 不是 Order status。

### 8.4 搜索和列表

Order 页面至少支持按以下条件查询：

- 订单业务日期；
- order number；
- Customer；
- status。

列表应优先让操作员快速找到今天的订单和需要处理的订单。

## 9. Check-in 和 Return 的日期规则

业务时区为 `Asia/Shanghai`。

- 过去日期订单：不显示 Check-in/Return 按钮，后端拒绝相关请求。
- 当天订单：在其他业务规则允许时显示并允许操作。
- 未来日期订单：不显示 Check-in/Return 按钮，后端拒绝相关请求。

Check-in 和 Return 的时间均由系统在按钮操作时自动取得，操作员不能输入时间。

## 10. Check-in

当天且符合条件的 active Order 显示 Check-in 操作。

成功 Check-in 后：

- 保存当前时间和操作员；
- 锁定 OrderItems；
- 使 EquipmentSpec OrderItems 占用库存；
- 保存当前 Auto Return 配置快照；
- 启动 Auto Return 周期。

如果可用库存为 0 或预计变成负数，系统必须显示清晰警告，但 V1 不强制阻止 Check-in。操作员确认后仍可完成。

取消 Check-in（在允许时）：

- 清除当前 Check-in 字段；
- 释放库存占用；
- 清除当前 Auto Return 周期；
- 恢复 OrderItems 可编辑状态。

## 11. Return

当天订单在符合条件时显示 Return 操作。

### 11.1 有 Check-in 的 Return

系统记录当前时间和操作员，将 Order 标记为 completed，并释放库存。

### 11.2 没有 Check-in 的直接 Return

允许操作员对符合条件的 active Order 直接 Return：

- 标记为 completed；
- 记录 Return；
- 不产生库存释放，因为此前没有库存占用；
- Return 时间至少为 `start_at + 1 minute`。

Return 不能对过去日期或未来日期订单执行。

### 11.3 Auto Return 后的人工修正

Auto Return 后，操作员可以执行允许的人工 Return 更新/修正。系统使用当前操作时间记录操作员的 Return，并按照业务规则更新 Auto Return 字段。这个操作必须保持订单和库存数据一致。

V1 不设置“客户是否仍在使用设备”字段。

## 12. Auto Return 和 Daily Forced Return

### 12.1 Auto Return

Auto Return 是防止操作员忘记 Return 导致库存长期占用的保护机制，不表示客户一定在该时刻停止使用。

Check-in 时复制 `auto_return_after_minutes`。到期且没有有效 Return 时，系统使用 System User 执行 Auto Return、释放库存并完成 Order。

### 12.2 Daily Forced Return

Daily Forced Return 是防止跨午夜长期占用库存的技术安全机制。每天 Asia/Shanghai 的 `23:59:01–23:59:59` 处理仍有有效 Check-in 且无有效 Return 的订单：使用 System User、记录 Return、释放库存、完成 Order，并记录 Daily Forced Return 标记。

它与普通 Auto Return 独立，不代表客户实际停止使用的精确时刻。

## 13. Inventory

Inventory 页面显示：

- operational inventory；
- currently occupied quantity；
- available quantity。

```text
available = operational inventory - currently occupied quantity
```

只有有效 Check-in 且无有效 Return 的 EquipmentSpec OrderItem 占用库存。未来 Order 不占用库存。V1 不要求库存调整历史，也不强制库存不足时阻止 Check-in。

## 14. Payment

Payment 页面直接展示当前 OrderItems，不让���作员重新选择已经存在的项目。

最终金额为：

```text
final_amount = SUM(OrderItem.quantity × OrderItem.unit_price)
             + SUM(PaymentItem.amount)
```

Payment 必须能够显示和查询最终金额及 adjustment 明细，用于后续统计分析。

V1 不记录：

- 是否已付款或未付款；
- 支付方式；
- 现金、微信、支付宝、银行卡等支付渠道。

Payment adjustment 可以是折扣、附加费、退款或更正，必须填写说明。PaymentItem 创建后不可修改，更正通过新增 adjustment 完成。completed、cancelled、no-show 订单仍可添加 adjustment。

## 15. Settings

Settings 管理：

- Auto Return duration；
- EquipmentType；
- EquipmentSpec、价格、capacity、active 状态；
- SaleItem、价格、active 状态；
- 每种 EquipmentSpec 的 operational inventory。

以下规则固定，不作为普通 Settings：

- Order duration：2 hours；
- Daily Forced Return：23:59:01–23:59:59；
- database timezone：UTC；
- business timezone：Asia/Shanghai。

## 16. Backup / Restore

如果实现，优先保证 SQLite 数据库完整性、简单操作和可恢复性。V1 不要求云备份、多地点复制、企业级灾难恢复或复杂版本管理。

## 17. V1 非目标

- 客户自助预订、客户账号、在线支付、微信登录、小程序和通知；
- Boat、BoatAssignment、具体船号管理；
- Reservation、Walk-in、ActualUsage、独立 Check-in/Return 历史实体；
- 角色权限、多门店、复杂会计、支付网关；
- 预约冲突引擎、自动船只分配；
- 库存调整历史、完整 audit log、高级 BI、预测和 AI 推荐。

## 18. V1 验收场景

1. 创建未来 Order，未来订单不占用库存，也不显示 Check-in/Return。
2. 创建当天 Order，可以在规则允许时 Check-in 和 Return。
3. 过去日期 Order 不显示相关按钮，后端也拒绝请求。
4. Check-in 使用系统当前时间，OrderItems 锁定，库存被占用。
5. 库存不足时显示警告，但确认后 Check-in 成功。
6. 有 Check-in 的人工 Return 释放库存并完成 Order。
7. 没有 Check-in 的直接 Return 不改变库存。
8. 忘记 Return 时 Auto Return 释放库存并完成 Order。
9. 跨午夜订单由 Daily Forced Return 处理。
10. Auto Return 后人工修正可以记录当前操作时间，不增加客户使用状态字段。
11. Payment 显示 OrderItems、adjustment 明细和最终金额。
12. Payment adjustment 在终止状态订单上仍可添加。
13. V1 不包含 Boat 或 BoatAssignment。

## 19. 产品边界

V1 应保持足够小，以便尽快在真实业务中使用。任何不直接服务于以下流程的新增实体、工作流或技术依赖，都应优先延期：

```text
Login → Customer → Order → Check-in → Inventory → Return → Payment
```

详细业务约束以 `BUSINESS_RULES.md` 为准，数据结构以 `ER_MODEL.md` 为准，技术实现边界以 `ARCHITECTURE.md` 为准。
