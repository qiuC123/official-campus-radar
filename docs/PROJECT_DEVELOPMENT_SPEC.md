# Project Development Specification — 官方校招信息雷达

Status: Phase 02 前端优先实现候选；H1、H2、G10 待验收

Owner: 用户 / 协调任务

Links: `docs/superpowers/specs/2026-08-17-official-campus-recruitment-radar-design.md`

## Project context

- Problem and target users: 为项目所有者提供不限城市的官方校招岗位本地雷达，并按岗位记录个人投递进度。
- Constraints and assumptions: Windows 本机、每日 22:00 更新、只使用公开官方来源、自动发布但严格校验、电脑关机时提示漏跑。
- Project-wide non-goals: 云部署、公开访问、账号系统、自动投递、社区经验信息、规避站点访问限制。

## Goals

### Short-term objective — current deliverable

- 完成 Phase 02 的需求、原型、Django 预览页、批次/岗位数据分离和既有 T1/T2 离线兼容候选。
- Measurable success and acceptance criteria: 以 `docs/handoffs/phase-02-product-requirements.md`、页面数据契约和 H1/H2/G10 记录为准。
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
- Data classification, contracts, and compatibility policy: 招聘批次、岗位与官方链接为公开招聘信息；岗位级个人进度为本地私有数据；页面通过 ViewModel 与企业 JSON 隔离。
- External-service, security, and approval boundaries: 仅低频读取公开来源；任何登录、绕过限制、云部署或外部写入必须另获用户批准。
- Observability and failure-handling expectations: 每个来源和每次更新均有结果记录；失败不会删除历史数据。

## Lifecycle and authority

- Phase naming and coordinator-reuse policy: 当前为 Phase 02 / 前端优先，本地 Django + SQLite 单体；H3 前禁止启动 T3 企业外网探测。
- Human approval matrix: Phase 02 前端优先计划已获明确实施授权；H1、H2、H3 及任何云部署、购买、外部写入仍须分别批准。
- Design Handoff, implementation, validation, review, and terminal-handoff rules: 使用 Phase 02 PRD、页面契约、Cycle 记录和执行清单记录范围、验证与交接；实现与只读审查分离。
- Change-control and ADR triggers: 运行环境、数据保留期、来源范围、公开可见性、依赖框架或外部服务发生实质变化时新增 ADR 或新阶段批准。

## Milestones and delivery forecast

| Milestone | Outcome | Effort range / time window | Dependencies | Replan trigger |
| --- | --- | --- | --- | --- |
| M1：H1 原型 | 用户接受静态原型的布局、字段与交互 | 当前停止点 | 原型 Cycle 01 | 用户要求调整视觉或字段 |
| M2：H2 页面 | 用户接受 Django Mock 预览的实际体验 | H1 后 | H1 通过、预览候选 | 空状态、筛选或交互需要重做 |
| M3：G10/H3 | 接受页面契约兼容证据并决定是否探测企业 | H2 后 | H2、独立复核、企业范围拍板 | 用户不授权外网探测或更改最低成功线 |

## Quality and release policy

- Definition of Ready / Definition of Done: 本轮实现候选须有测试、迁移、浏览器和独立只读审查证据；Windows 任务与真实来源属于后续关卡，不冒充本轮完成项。
- Required validation evidence and review thresholds: 对业务规则的自动化测试；采集和定时任务的集成或手工验证；实施后进行独立只读审查。
- Release, rollback, incident, and feedback rules (if in scope): 本地版本通过可恢复的数据库备份和变更记录回退；不自动删除历史招聘记录。

## Documentation map

- Phase handoffs: `docs/handoffs/phase-02-execution-plan.md`
- Implementation plans: `docs/handoffs/phase-02-execution-plan.md`、`docs/superpowers/plans/`
- ADRs: `docs/adr/`（需要实质架构变更时创建）
- Test evidence / runbooks: `docs/handoffs/phase-02-compatibility-cycle-*.md`、`docs/runbooks/local-verification.md`
