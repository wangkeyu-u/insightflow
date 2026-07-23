# InsightFlow 项目深度理解与面试手册

这份文档不是产品宣传稿，而是一套“能讲清业务、能讲清代码、能扛技术追问”的项目说明。面试前先熟悉前五节，再按目标岗位补后面的深挖题。

## 1. 先用一句话讲清项目

InsightFlow 是一个面向中型 B2B 企业的桌面端运营分析工作台，把订单、客户、商品、库存、应收、物流、区域目标、报表、审计和 AI 分析放进同一套可追溯的数据链路中，让管理者从经营指标直接下钻到业务记录并采取行动。

英文版：

> InsightFlow is a desktop operations intelligence workspace for mid-sized B2B teams. It connects orders, customers, inventory, receivables, fulfillment, targets, reports, audit history, and grounded AI analysis in one traceable workflow.

## 2. 这个项目真正解决什么问题

典型企业的数据散落在订单表、客户表、库存表和财务表中，常见问题不是“没有图表”，而是：

- 指标与明细对不上，管理者看到营收下降却找不到具体订单。
- 销售、财务、库存各看一套数据，逾期应收和缺货风险无法一起判断。
- Excel 导入后容易产生库存、客户累计消费额等派生指标不一致。
- 不同角色拥有相同按钮，直到请求失败才知道没有权限。
- AI 容易脱离企业数据编数字，回答不可审计。

InsightFlow 的核心价值是把“发现信号—定位记录—执行操作—留下审计”串成闭环，而不只是做一个漂亮 Dashboard。

## 3. 面试现场的 5 分钟演示顺序

不要逐页念功能。用一个经营问题带着面试官走：

1. 登录后看 Dashboard：解释总营收、订单量、逾期应收、低库存，以及这些数字都来自真实关联记录。
2. 点进 Orders：按客户、商品、销售、区域、状态或订单号搜索，展示分页、排序、付款和物流状态。
3. 打开一个客户：展示客户累计消费额和订单历史来自同一订单事实表，而不是前端写死。
4. 进入 Inventory 和 Analytics：把低库存、商品表现、区域目标完成率、逾期天数串起来。
5. 让 AI 回答“本周最需要关注什么”：说明回答只使用服务端生成的数据上下文；无 API Key 时走确定性本地分析，不伪装成模型结果。
6. 最后展示 Reports、Audit Logs 和 User Management：说明导入导出、可追溯性与权限边界。

一句收尾：

> 我重点做的不是多堆几个页面，而是保证同一个业务事实跨 Dashboard、客户、库存、分析、导出和 AI 都能对得上。

## 4. 系统架构

### 前端

- React 18 + TypeScript + Vite。
- TailwindCSS + shadcn/ui 负责一致的桌面端组件和交互状态。
- ECharts 绘制趋势、区域和商品表现图。
- Zustand 保存登录令牌与当前用户。
- Axios 拦截器统一附加 Bearer Token，401 时清理会话并返回登录页。
- 页面使用路由级懒加载，图表依赖只在对应页面加载。

### 后端

- FastAPI 负责路由、依赖注入、OpenAPI 文档和参数校验。
- Pydantic 定义请求和响应契约。
- SQLAlchemy 2.0 管理 ORM、关系和聚合查询。
- Service 层承载 Dashboard、Analytics、CSV 和 AI 的业务逻辑。
- Router 层负责权限、事务边界、HTTP 语义和审计调用。
- PostgreSQL 是正式数据库；聚合查询也兼容 SQLite，方便无 Docker 的本地演示和自动化测试。

### 一次请求如何流动

```text
React Page
  -> typed API function
  -> Axios /api + JWT
  -> Vite proxy strips /api
  -> FastAPI router
  -> get_current_user / require_role
  -> Pydantic validation
  -> SQLAlchemy query or service
  -> transaction + audit log
  -> typed JSON response
  -> UI state and visualization
```

开发环境中，前端请求 `/api/orders`，Vite 代理到后端 `/orders`。这样前端不需要硬编码后端域名，也减少本地跨域配置。

## 5. 数据模型：14 张表为什么这样设计

### 身份与权限

- `roles`：角色名和可扩展权限字段。
- `users`：账号、bcrypt 密码哈希、角色外键、启用状态。

### 商业主数据

- `customers`：客户资料、区域、类型、累计消费额、最近购买日。
- `suppliers`：供应商资料。
- `products`：SKU、分类、售价、成本、当前库存、补货点、状态。

### 交易事实

- `orders`：订单头，保存客户、日期、区域、销售、付款/物流状态和总额。
- `order_items`：订单明细，保存商品、数量、成交单价和行总额。

订单头与明细分开是标准的一对多建模：订单级状态只存一次，商品级数量和价格按行保存；历史成交单价不能只读商品当前售价，否则商品改价会篡改历史营收。

### 履约与运营

- `inventory`：商品的仓库库存记录。
- `payments`：支付金额、方式、状态、到期日和支付日。
- `shipments`：承运商、运单号、发货与签收时间。
- `sales_targets`：区域、年份、周期和目标额。

### 可治理性

- `upload_history`：CSV 文件、成功/失败/重复行数和错误摘要。
- `audit_logs`：谁在什么时间对什么实体做了什么操作。
- `ai_reports`：AI 问题、回答、类型和数据上下文。

## 6. 最重要的数据一致性规则

这是最容易体现工程深度的部分。

### 订单总额

```text
order_item.total = quantity * unit_price
order.total_amount = sum(order_item.total)
```

金额由后端计算，不信任前端提交的总额，避免篡改或浮动状态不一致。

### 客户累计消费额

- 新建订单：给客户 `total_spending` 加上订单额。
- 删除订单：减去订单额，最低为 0，并重算最近购买日。
- 修改订单客户：从旧客户扣除，再给新客户增加。
- CSV 导入订单：走同样的累计消费与最近购买日更新。

更大规模系统会取消这个冗余字段，改用实时聚合、物化视图或事件驱动投影。当前保留它是为了列表查询性能和演示清晰度，但所有写入口必须维护同一个不变量。

### 商品库存

`products.current_stock` 用于高频列表和预警，`inventory.quantity` 保存运营库存记录。商品 CRUD、商品 CSV 和库存 CSV 都同步两处，低库存统一定义为：

```text
status == active AND current_stock <= reorder_level
```

生产系统进一步演进时，应该把库存流水作为事实来源，通过入库、出库、预占和释放事件计算可用库存，避免双写。

### 删除策略

- 有历史订单的客户不能硬删，改为 `customer_type = archived`。
- 被订单明细引用的商品不能硬删，改为 `status = archived`。
- 删除订单时先清理支付和物流，再依赖级联删除订单明细。
- 批量删除与单条删除遵守同样规则，不能让批量接口绕过业务约束。

这既保护外键完整性，也保留历史报表可解释性。

## 7. 指标口径

- 总营收：`SUM(orders.total_amount)`，当前项目表示已录入订单的 booked revenue，不等同于已回款收入。
- 平均客单价：指定周期营收 / 订单数，SQL 使用 `AVG(total_amount)`。
- 增长率：`(本期营收 - 上期营收) / 上期营收 * 100%`；上期为 0 时单独处理，避免除零。
- 复购率：订单数大于 1 的客户数 / 全部客户数。
- 商品毛利率：`(unit_price - cost_price) / unit_price * 100%`。这是目录价格口径，不是逐单真实毛利；若要精确，应保存订单行成交成本。
- 逾期金额：只统计 `payment.status == overdue` 且 `due_date < today` 的支付记录。`pending` 不能直接算逾期。
- 逾期天数：`today - due_date`。
- 目标完成率：区域年度实际营收 / 区域目标额。
- 低库存：当前库存小于等于补货点且商品仍为 active。

如果面试官问“营收为什么不只算 paid”，回答：当前口径是订单营收/booking，财务回款应单独提供 cash collected 指标。项目已把支付事实拆表，因此后续可以同时展示 booked revenue、collected cash 和 AR outstanding。

## 8. 权限与安全

### JWT 流程

1. 登录提交邮箱与密码。
2. 后端用 bcrypt 校验哈希。
3. 签发带用户 ID 和过期时间的 JWT。
4. 前端 Axios 自动附加 `Authorization: Bearer <token>`。
5. 后端每次解码 Token，再从数据库确认用户存在且仍启用。

不能只相信 Token 里的角色，因为管理员可能已停用或调整该用户。当前实现每次查库，保证权限变更立即生效。

### RBAC

- `admin`：全部能力，包括用户管理和审计日志。
- `manager`：经营数据 CRUD、批量操作、CSV 导入、分析和报告。
- `staff`：经营数据、分析、AI 和导出的只读访问。

权限有三层：导航可见性、前端路由/按钮、后端 `require_role`。前端限制改善体验，后端限制才是真正的安全边界。

### 已处理的安全边界

- 公开注册无法指定 admin/manager；首个用户用于初始化 admin，之后只能注册 staff。
- 只有 admin API 能分配高权限角色。
- 密码限制 8–72 字符，符合 bcrypt 输入边界。
- 管理员不能停用或降级自己的当前账号，避免误锁死。
- 登录、CRUD、批量操作会写审计日志。

### 生产化还要做什么

- JWT 现在放在 `localStorage`，实现简单但需严防 XSS；生产可改为 HttpOnly、Secure、SameSite Cookie，并加入 CSRF 防护。
- 更换默认 `SECRET_KEY`，使用密钥管理服务并支持轮换。
- 增加登录限流、失败次数锁定、刷新令牌和撤销列表。
- 注册接口在企业环境通常关闭，改为管理员邀请制或 SSO/OIDC。
- 审计日志在数据库层设为 append-only，并输出到独立日志/安全平台。

## 9. CSV 导入为什么不只是“读一个文件”

流程是：

1. 验证扩展名和空文件。
2. Pandas 读取并标准化列名。
3. 区分必填列和可选列；缺失可选列先物化再填默认值。
4. 去空格、处理空值、转换数字和日期。
5. 按业务键检测文件内重复。
6. 解析或创建关联实体，例如按客户名解析客户、按供应商名创建供应商。
7. 写入业务数据并同步派生指标。
8. 事务提交，记录上传历史和有限长度的错误摘要。

当前实现适合中小文件和面试展示。生产大文件应使用流式读取、分块事务、后台队列、幂等键、失败重试、对象存储和进度查询，避免长请求占用 Web Worker。

## 10. AI 为什么可信

AI 模块不是把整库数据直接发给模型，而是先由服务端执行受控聚合，构建包含营收、订单、区域、热销商品、付款状态和低库存的业务上下文，再让模型基于上下文回答。

响应结构固定为：

- `short_answer`：直接结论。
- `data_evidence`：具体数据证据。
- `reasoning`：推导逻辑。
- `suggested_actions`：下一步动作。
- `confidence`：high / medium / low。

系统提示要求只使用给定上下文、数据不足要明确说明。输出经过 JSON 解析和 Pydantic 校验。每次交互写入 `ai_reports`，方便追溯。

没有 OpenAI Key 或外部调用失败时，系统使用确定性本地 fallback：直接基于相同聚合生成证据和动作，并明确说明没有发生外部模型推理。这样演示不会因网络或 Key 失败，也不会把模板答案冒充 AI。

如果面试官问“怎么进一步减少幻觉”，可以回答：增加指标语义层、查询白名单、引用到具体实体 ID、结构化工具调用、答案与 SQL 结果自动核验、置信度校准和离线评测集。

## 11. 前端设计思路

- 产品明确只做桌面端，最低宽度 1180px，不为移动端牺牲表格密度。
- 左侧导航按 Workspace、Operations、Intelligence 分组，避免十几个入口平铺。
- 每页统一为 eyebrow、标题、说明、右上主操作。
- 筛选区先解释当前范围，再放搜索、状态、日期和排序。
- 表格操作固定在右侧，主操作与破坏性操作有清晰层级。
- 状态不仅靠颜色，还显示文字 Badge。
- 页面懒加载，避免 ECharts 和大页面进入首屏主包。
- Staff 看到的是只读工作台，不出现注定失败的写操作。

## 12. 测试策略与当前验收

自动化后端测试覆盖：

- 登录与当前用户。
- Dashboard 基础指标和逾期口径。
- 客户、商品、库存、订单完整生命周期。
- 订单跨客户移动后的累计消费额。
- 单条/批量删除和关联支付、物流清理。
- 客户/商品软删除保护。
- 最简 CSV、四类导入、上传历史与数据同步。
- 用户角色创建、更新、停用和自我停用保护。
- Staff 只读权限与 admin 专属资源。
- 公开注册不能提权。
- 4 个 AI 入口的离线 fallback。
- 3 个 CSV、业务 PDF 和订单 PDF 导出。
- SQLite 与 PostgreSQL 兼容的月度趋势聚合。

验收还包括 TypeScript 编译、Vite 生产构建、真实种子库接口冒烟和导出文件有效性检查。

测试不是为了追求行覆盖率，而是保护业务不变量：金额、库存、外键、角色和降级路径。

## 13. 当前演示数据如何讲

种子数据是固定随机种子生成的 18 个月 B2B 历史，而不是每次刷新随机变化：

- 5 个用户，覆盖 admin、manager、staff。
- 20 个企业客户，分布在 5 个区域。
- 18 个 SKU 和 5 个供应商。
- 277 张订单、990 条订单明细。
- 277 条支付记录、273 条物流记录。
- 5 个当前年度区域目标和 36 条初始审计事件。

数据特意包含低库存、逾期支付、区域表现差异、复购客户和取消订单，用于驱动真实的筛选、预警和分析。固定 seed 保证面试前后口径一致。

## 14. 高频深挖问题与回答

### Q1：为什么选 FastAPI？

类型提示、Pydantic 校验、依赖注入和自动 OpenAPI 很适合数据型 API。`Depends` 可以统一注入数据库会话与 RBAC，减少每个路由重复安全代码。异步不是选择它的唯一原因；当前 SQLAlchemy 会话是同步的，I/O 规模上升后再评估 async engine。

### Q2：为什么不用 Django？

Django 的 admin 和完整生态很强，但这个项目主要是 API + 独立 React 前端，FastAPI 的契约和轻量分层更直接。若需求包含复杂内容管理和后台表单，Django 可能更高效。

### Q3：如何避免 N+1？

订单列表/详情、商品供应商和库存关系使用 `joinedload` 提前加载；聚合榜单直接在 SQL 中 group by，而不是先取全表再用 Python 循环查询。

### Q4：为什么订单行保存 unit_price？

商品目录售价会变化。订单行保存成交时价格，才能保证历史发票和营收不随商品改价而变化。

### Q5：事务有没有问题？

一次业务操作的核心变更在同一 SQLAlchemy Session 中提交。审计目前在业务提交后单独提交，优点是实现简单，缺点是极端情况下业务成功而审计失败。生产上应把业务与 outbox 事件放在同一事务，再异步写审计系统。

### Q6：并发创建订单会不会把客户累计金额写丢？

当前是 read-modify-write，高并发下可能 lost update。可以改成数据库原子更新 `total_spending = total_spending + :amount`，或把订单作为唯一事实来源实时聚合；更强一致性场景使用行锁或可序列化事务。

### Q7：库存为什么没有因为下单自动扣减？

当前订单与库存是分析/维护模型，没有实现预占和履约库存账。真实系统应在订单确认时创建 reservation，在发货时过账出库，取消时释放，并保证幂等，而不是简单把 current_stock 减一遍。

### Q8：为什么软删除？

客户和商品被历史订单引用，硬删会破坏外键和报表解释。归档既保留历史，又能从活动列表中筛掉。生产可增加统一 `archived_at`、`archived_by` 字段和默认查询 scope。

### Q9：分页为什么用 offset/limit？

实现简单，适合当前数据量。大数据深分页会越来越慢，生产可改用按 `(order_date, id)` 的 keyset/cursor pagination，并为搜索和筛选建立组合索引。

### Q10：PostgreSQL 和 SQLite 怎么兼容？

正式环境用 PostgreSQL；测试/本地演示支持 SQLite。月度分组根据 dialect 选择 `date_trunc` 或 `strftime`，年份过滤改为日期范围，既跨库又更利于索引。

### Q11：为什么不把所有逻辑写在 Router？

Router 应处理 HTTP、权限和事务；Dashboard、Analytics、CSV、AI 聚合放 Service，便于独立测试和复用。简单 CRUD 仍留在 Router，是在项目规模下的务实取舍。

### Q12：AI 失败怎么办？

使用相同数据库聚合的确定性 fallback，并在 reasoning 中明确来源。外部服务失败不能让核心运营系统不可用，也不能静默返回伪造结果。

### Q13：怎么证明不是 mock 数据页面？

对同一订单做新增、改客户和删除，可以看到客户累计消费额变化；商品 CSV 会同步库存页；逾期订单能在 Dashboard、Analytics 和 Orders 筛选互相对应；所有操作写审计日志。它是同一关系数据驱动的闭环。

### Q14：下一步最值得做什么？

优先做 Alembic 迁移、原子金额/库存更新、后台导入任务、HttpOnly 会话、可观测性和前端 E2E 测试；然后再做多租户和真实库存流水，而不是继续堆图表。

## 15. 坦诚讲技术债，反而更显成熟

不要说“项目已经是生产级且没有问题”。更好的说法：

- 当前是单租户模型；多租户需要给核心表增加 tenant_id，并在所有查询、唯一索引和审计中强制隔离。
- 表由 ORM 创建，正式团队开发应加入 Alembic migration 和版本化回滚。
- 金额使用 Float，生产财务系统应使用 Decimal/Numeric，并明确币种与舍入规则。
- CSV 在请求内同步处理，适合演示数据量；大文件需要任务队列。
- 缺少浏览器级 E2E 套件，当前主要由 API 工作流测试和生产构建保证。
- 还没有库存预占、退款、部分付款、部分发货等复杂状态机。
- 前端目前以控制台和局部错误文案为主，后续可统一 toast、错误码和重试策略。

这种回答体现你知道“能工作的项目”和“规模化生产系统”之间的距离。

## 16. 你可以直接使用的项目介绍

### 60 秒版本

> 我做的是 InsightFlow，一个面向中型 B2B 团队的桌面端运营分析平台。它不是单纯的 Dashboard，而是把订单、客户、商品、库存、应收、物流、区域目标、导入导出、审计和 AI 分析放到同一个可追溯数据模型中。前端用 React、TypeScript、ECharts 和 Zustand，后端用 FastAPI、SQLAlchemy、Pydantic、Pandas 和 PostgreSQL。我重点解决了三个工程问题：第一，保证订单、客户消费额和库存跨 CRUD、批量操作与 CSV 导入保持一致；第二，做 admin、manager、staff 三层 RBAC，并让前后端权限表现一致；第三，AI 只基于服务端聚合数据回答，没有 Key 时走明确的本地分析 fallback。当前用固定的 18 个月 B2B 数据演示，并通过完整 API 工作流、导出和生产构建验证。

### 3 分钟版本

> 这个项目的出发点是企业通常不是缺少图表，而是缺少从指标到业务记录的闭环。所以首页看到逾期应收或低库存后，可以进入订单、客户和库存继续定位；报表和 AI 使用的也是同一份数据库事实。
>
> 架构上，React 前端通过类型化 API 层访问 FastAPI。后端用依赖注入统一数据库 Session、JWT 用户和角色权限，聚合逻辑放在 service 层，Pydantic 保证输入输出契约。数据库有 14 张表，订单头与订单行分离，支付和物流独立建模，另外用 upload_history、audit_logs、ai_reports 解决可治理性。
>
> 我投入最多的地方是数据一致性。例如订单改到另一个客户时，要同时调整新旧客户的累计消费；删除有支付和物流的订单，要按正确顺序清理；有历史订单的客户和商品只能归档；CSV 导入商品要同步 inventory，导入库存也要同步产品库存。批量接口不能绕过单条接口的业务规则。这些都被写成端到端 API 测试。
>
> AI 部分先由后端生成受控业务上下文，再要求模型返回带证据、推理、动作和置信度的结构化结果。没有外部模型时仍能基于真实聚合做确定性分析，并明确告诉用户是 fallback。这样核心系统不会因为第三方 API 不可用而失效。
>
> 如果继续生产化，我会优先把金额改成 Decimal，加入 Alembic、原子更新和 outbox，CSV 改为后台任务，并把 JWT 从 localStorage 移到 HttpOnly Cookie。

## 17. 简历表述

- Built a full-stack B2B operations intelligence platform with React, TypeScript, FastAPI, SQLAlchemy, PostgreSQL, and ECharts across 14 relational tables.
- Implemented traceable KPI analytics, RBAC, audit history, CSV/PDF workflows, and grounded AI analysis with deterministic offline fallback.
- Preserved customer spend, inventory, and foreign-key invariants across CRUD, batch deletion, and four CSV import pipelines; validated critical workflows with integration tests.
- Optimized the desktop experience with route-level code splitting, role-aware actions, dense operational tables, and consistent filtering/navigation patterns.

## 18. 面试前最后检查

- 能不看文档说出一句话定位和 60 秒介绍。
- 能画出 React → Axios → FastAPI → Dependency → Service → SQLAlchemy → PostgreSQL。
- 能解释订单头/订单行为什么拆开。
- 能准确说出营收、复购率、逾期、毛利率、目标完成率口径。
- 能解释三层权限和为什么前端隐藏不等于安全。
- 能讲一个数据一致性 bug 及修复，例如批量删除或 CSV 双写。
- 能坦诚说出 Float、并发写、JWT 存储、同步 CSV 和无迁移的技术债。
- 演示前使用 admin 账号，确认前后端服务与 5173/8000 端口正常。

默认管理员：`admin@insightflow.com` / `password123`。这些仅为本地演示凭据，生产环境必须删除或更换。
