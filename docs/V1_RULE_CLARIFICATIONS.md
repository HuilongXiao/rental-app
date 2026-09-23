# Rental App — V1 规则确认与文档修订说明

> 本文件记录在审查 `BUSINESS_RULES.md`、`PRD.md`、`ER_MODEL.md` 和 `ARCHITECTURE.md` 后确认的 V1 规则。
>
> 如果本文件与旧文档中的内容发生冲突，在本次文档正式修订完成前，以本文件中的确认内容为准。原有文档暂时保留，待你审阅完整修改方案后再统一更新。

## 1. V1 的部署方式和使用人员

- V1 是供内部操作员和管理人员使用的系统。
- 预计有 2–5 名已登录的操作员使用。
- V1 以 Docker 形式运行在 Synology NAS 上。
- 操作员需要通过互联网远程访问系统。
- 远程访问必须使用 HTTPS 和安全的访问控制。不能把未认证的 HTTP 容器直接暴露到互联网。
- 未来会迁移到更加稳定可靠的云端环境。
- 近期迁移后仍然主要供内部员工使用，客户在线预订不属于下一阶段的直接目标。

## 2. V1 的 Payment 范围

Payment **不记录**：

- 订单是否已经付款或仍未付款；
- 支付方式；
- 现金、微信支付、支付宝、银行卡或其他收款渠道。

Payment **需要记录**订单的金额计算结果及调整明细：

```text
最终金额 = SUM(OrderItem.quantity × OrderItem.unit_price)
         + SUM(PaymentItem.amount)
```

最终金额必须能够被查询，以便今后的运营统计和数据分析。最终金额可以根据明细动态计算，而不必作为唯一权威金额单独保存。如果为了报表性能而保存缓存金额，该金额只能作为缓存，必须能够与明细保持一致。

Payment adjustment 在订单 completed、cancelled 或 no-show 后仍然可以添加。调整明细创建后不可修改；如需更正，应新增一条调整明细。每一条人工调整都必须填写说明。

## 3. Business date 以及 Check-in / Return 的可用规则

业务时区为 `Asia/Shanghai`。

系统需要将订单的业务日期与当前业务日期进行比较：

- **过去日期的订单**：如果订单日期早于今天，不允许 Check-in 和 Return，并且不显示对应按钮。
- **当天订单**：如果订单日期是今天，在其他业务规则允许的情况下，可以显示 Check-in 和 Return 按钮。
- **未来日期的订单**：如果订单日期晚于今天，不允许 Check-in 和 Return，并且不显示对应按钮。

这既是前端 UI 规则，也是后端的权限和业务校验规则。不能只依靠隐藏按钮来保护系统。

Check-in 始终使用操作员按下 Check-in 按钮那一刻由系统取得的当前时间。操作员不能手动输入过去或未来的 Check-in 时间。

Return 始终使用操作员按下 Return 按钮，或执行允许的人工修正操作时由系统取得的当前时间。操作员不能手动输入过去或未来的 Return 时间。

以下时间规则仍然有效：

- Check-in 不能早于 `start_at`。
- 已经 Check-in 后执行 Return 时，Return 时间必须晚于 Check-in 时间。
- 没有 Check-in 的直接 Return，时间必须至少晚于 `start_at` 一分钟。

## 4. 库存不足时的处理方式

V1 中库存不足只产生警告，不强制阻止操作。

如果可用库存为零，或者执行 Check-in 后计算出的库存会小于零，系统必须向操作员显示清晰的警告；但是操作员确认后仍然可以继续完成 Check-in。后端仍然必须准确计算和显示最终的运营库存状态。

这个规则同时适用于普通人工 Check-in 以及其他具有同等效果的操作流程。

## 5. Auto Return

Auto Return 是一种库存保护机制。它表示系统为了运营管理目的，认为约定的使用时间已经结束；它不表示客户实际上一定已经停止使用设备。

V1 不增加“客户是否仍在使用设备”这个字段。

Check-in 时：

- 将当前设置中的 Auto Return 时长复制到订单；
- 计算本次 Auto Return 的计划时间；
- 当前 Check-in 开始占用库存。

当计划时间到达且订单仍然没有有效 Return 时，系统可以执行 Auto Return：

- 订单变成 completed；
- 释放库存占用；
- 使用 System User 作为执行者；
- 记录 Auto Return 标记和时间。

如果客户实际使用设备的时间超过了 Auto Return 时间，操作员可以使用允许的人工 Return 修正/更新操作。该操作使用操作员执行操作时的当前时间作为新的 Return 时间，并按照最终实现规则清除或更新当前 Auto Return 时间标记。

这个修正操作必须作为一个具有事务一致性的完整业务操作执行，确保订单状态、Return 字段、Auto Return 字段和库存计算不会互相矛盾。

## 6. Daily Forced Return

Daily Forced Return 是一种技术安全机制，不是客户使用流程中的核心业务要求。

它在 Asia/Shanghai 时区每天以下时间窗口运行：

```text
23:59:01–23:59:59
```

它处理仍然存在有效 Check-in、但没有有效 Return 的订单，包括可能跨午夜仍占用库存的订单。它需要：

- 使用 System User 记录 Return；
- 释放库存；
- 将订单标记为 completed；
- 记录 Daily Forced Return 已经发生。

Daily Forced Return 与普通 Auto Return 是两个独立机制。Daily Forced Return 不应被理解为客户恰好在该时间停止使用设备的事实。V1 仍然不保存单独的“客户实际使用状态”字段。

## 7. Boat 范围

Boat 和 BoatAssignment 从 V1 实现范围中移除。

V1 只按照 EquipmentSpec 和数量管理设备，不需要：

- 单独编号的船只记录；
- BoatAssignment 记录；
- Boat assignment UI；
- 单船可用状态；
- 船只时间重叠校验。

在 V1 实际使用后，如果确认确实需要管理具体船号，可以在 V2 重新设计 Boat 和 BoatAssignment。它们不应增加 V1 的数据表、页面、API 或定时任务。

## 8. V1 数据模型的影响

V1 的核心数据范围包括：

- users；
- customers；
- equipment types 和 equipment specs；
- sale items；
- 运营库存配置；
- orders；
- order items；
- payments 和不可变的 payment adjustments；
- system settings。

V1 不应仅仅因为其他租赁系统通常具有这些表，就增加以下实体：

- `check_ins`；
- `returns`；
- `actual_usages`；
- `reservations`；
- `walk_ins`；
- `order_types`。

Order 可以继续保留用于表示当前 Check-in、Return、Auto Return 和 Daily Forced Return 状态的字段。这些字段只表示当前运营状态。V1 不提供完整的历史事件审计，也不提供单独的客户实际使用状态字段。

## 9. 面向云端迁移的边界

V1 的业务模型不能依赖 Synology 专用 API 或固定的 NAS 文件路径。以下部分应该保持可替换：

- Docker 部署方式；
- 数据库连接和 migration 层；
- authentication 实现；
- scheduled job 执行器；
- backup 保存位置；
- web server 和 reverse proxy 配置。

SQLite 仍然适合初始的单店 V1，前提是数据库文件保存在持久化存储中，并且已经实际测试过 backup 和 restore。未来将应用和数据迁移到云端时，主要应当是基础设施和数据存储实现的变化，而不是改变 Order、库存、Return 或 Payment 明细的业务含义。

## 10. V1 测试计划必须增加的场景

至少需要测试以下情况：

1. 过去日期的订单没有 Check-in 和 Return 操作，后端请求也会被拒绝。
2. 未来日期的订单没有 Check-in 和 Return 操作，后端请求也会被拒绝。
3. 当天订单执行 Check-in 时，使用服务器取得的当前业务时间。
4. 当天订单执行 Return 时，使用服务器取得的当前时间。
5. 可用库存为零时，系统显示警告，但操作员确认后 Check-in 仍然成功。
6. Auto Return 释放库存，但不创建客户实际使用状态字段。
7. Auto Return 后执行人工 Return 修正时，记录操作员的操作，并保持 Payment 明细不受影响。
8. Daily Forced Return 能够处理跨午夜仍然没有 Return 的 Check-in 订单。
9. Payment 的最终金额等于 OrderItem 金额加上 adjustment 明细金额。
10. V1 的页面、API 和数据表都不依赖 Boat 或 BoatAssignment。
