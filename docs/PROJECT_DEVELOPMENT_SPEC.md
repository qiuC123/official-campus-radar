# Project Development Specification — 官方校招信息雷达

Status: Approved — 书面设计已获用户确认；实施计划待用户审阅

Owner: 用户 / 协调任务

Links: `docs/superpowers/specs/2026-08-17-official-campus-recruitment-radar-design.md`

## Project context

- Problem and target users: 为项目所有者提供北上广深互联网大厂、央企和国企的官方校招信息本地雷达。
- Constraints and assumptions: Windows 本机、每日 22:00 更新、只使用公开官方来源、自动发布但严格校验、电脑关机时提示漏跑。
- Project-wide non-goals: 云部署、公开访问、账号系统、自动投递、社区经验信息、规避站点访问限制。

## Goals

### Short-term objective — current deliverable

- 建成可在本地运行的 V0：来源白名单、定时更新、官方公告目录、个人投递进度和漏跑提醒。
- Measurable success and acceptance criteria: 以设计文档第 8 节的七项验收标准为准。
- Explicitly excluded from the current delivery: 任何云端持续运行或外部发布能力。

### Long-term direction — non-binding

- 可在获得明确批准后迁移到始终在线的运行环境。
- 可扩展到更多企业、更多城市或经标注的社区经验信息。
- Known uncertainties: 企业发现策略、官方公众号内容的长期可访问性和各官网结构变化。
- This direction does not authorize current scope: 长期方向不授权云购买、部署、公开发布或接入不可信来源。

### Future-compatibility constraints

- 保持来源适配器、采集运行记录和业务目录解耦。
- 数据层应能从 SQLite 迁移到 PostgreSQL，而不改变核心领域字段。
- 个人投递进度必须与自动采集结果隔离。
- Explicit deferrals: 云调度、消息队列、多人协作、社区舆情与自动投递。
- Promotion triggers requiring a new approved phase: V0 连续稳定运行并且用户明确批准扩大范围或迁移运行环境。

## Architecture and durable boundaries

- Module ownership and dependency direction: 页面与目录查询调用应用服务；应用服务调用领域数据与来源适配器；适配器不直接决定前台展示。
- Data classification, contracts, and compatibility policy: 官方公告与链接为公开招聘信息；个人投递进度为本地私有数据；不保存个人敏感资料或登录凭据。
- External-service, security, and approval boundaries: 仅低频读取公开来源；任何登录、绕过限制、云部署或外部写入必须另获用户批准。
- Observability and failure-handling expectations: 每个来源和每次更新均有结果记录；失败不会删除历史数据。

## Lifecycle and authority

- Phase naming and coordinator-reuse policy: 当前为 Phase 01 / V0 本地单体；同一协调任务在阶段完成、边界不变且上下文可信时可复用。
- Human approval matrix: 书面设计审阅后才可写实施计划；实施计划获批并收到明确实施授权后才可修改应用代码；云部署、购买、提交和外部写入须单独批准。
- Design Handoff, implementation, validation, review, and terminal-handoff rules: 使用 Phase 01 Design Handoff 记录范围、计划、验证和交接；实现与只读审查分离。
- Change-control and ADR triggers: 运行环境、数据保留期、来源范围、公开可见性、依赖框架或外部服务发生实质变化时新增 ADR 或新阶段批准。

## Milestones and delivery forecast

| Milestone | Outcome | Effort range / time window | Dependencies | Replan trigger |
| --- | --- | --- | --- | --- |
| M1：书面设计 | 设计和实施计划获用户批准 | 当前阶段 | 用户审阅 | 用户改变范围或自动发布规则 |
| M2：本地 V0 | 可运行的本地目录、采集和 22:00 任务 | 待实施计划估算 | 获批计划、首批来源 | 来源访问策略或技术约束改变 |
| M3：稳定试跑 | 首批来源连续更新并得到验收证据 | V0 后 | M2 完成 | 重复、误发或漏报超出验收阈值 |

## Quality and release policy

- Definition of Ready / Definition of Done: 书面设计、实施计划和明确实施授权齐备；完成时必须具有测试、Windows 任务手工验证和范围审查证据。
- Required validation evidence and review thresholds: 对业务规则的自动化测试；采集和定时任务的集成或手工验证；实施后进行独立只读审查。
- Release, rollback, incident, and feedback rules (if in scope): 本地版本通过可恢复的数据库备份和变更记录回退；不自动删除历史招聘记录。

## Documentation map

- Phase handoffs: `docs/handoffs/phase-01-v0-design-handoff.md`
- Implementation plans: `docs/superpowers/plans/`（待书面设计获批后创建）
- ADRs: `docs/adr/`（需要实质架构变更时创建）
- Test evidence / runbooks: 待实施计划定义
