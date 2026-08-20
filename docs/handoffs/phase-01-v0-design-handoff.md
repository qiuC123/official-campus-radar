# Design Handoff — 本地官方校招雷达 V0

Status: Conditional pass — 仅限本地离线、空库可运行骨架

Owner: 协调任务 /root

Phase: 01

## Goal and scope

- Problem: 将分散的官方校招信息变成可筛选、可追溯、每日更新的本地目录。
- In scope: Windows 本地应用、每日 22:00 更新、官网与已核验官方招聘公众号、北上广深岗位、自动发布规则、个人投递进度、漏跑提醒。
- Out of scope: 云端运行、账号、多用户、公开网站、自动投递、社区笔试信息、规避访问限制。

## Decisions and assumptions

- Confirmed decisions: 详见 `docs/superpowers/specs/2026-08-17-official-campus-recruitment-radar-design.md` 第 2 节。
- Assumptions to validate: 首批可低频访问的官方来源数量、动态官网对浏览器渲染的实际需求、官方公众号公开文章的可访问性。
- Alternatives rejected and why: 全网搜索加 AI 汇总会降低官方性；云优先会增加未验证的成本；每日多次更新对 V0 无必要。
- Technical and safety constraints: Django + SQLite + Windows 任务计划的本地模块化单体；不保存登录凭据，不绕过反爬，不进行外部写入。

## Acceptance criteria

- [x] User-visible behavior: 本地筛选表、13 个独立列、官方公告/投递入口、七种个人投递进度、漏跑提醒；已用受控 demo 实测。
- [x] Error and edge cases: fixture 覆盖去重、截止/撤回历史、来源失败不误删、未提供投递入口、历史城市/岗位组合筛选和个人进度隔离。
- [x] Local verification and observability: 101/101 离线测试、迁移检查、Django check、脚本语法和本地 UI 走查均通过；运行/来源健康事实可见。
- [ ] Live-source and scheduled-task validation: 未导入真实来源，未注册或实际触发 Windows 22:00 任务；这不是当前条件放行的一部分。

## Attached implementation plan

- Plan location or embedded plan: `docs/superpowers/plans/2026-08-17-local-campus-radar-v0.md`，已获用户确认；执行交接见 `docs/handoffs/phase-01-execution-brief.md`。
- Ordered steps: 以实施计划的十项任务为准；先建立应用骨架与测试，再实现数据模型、规则、采集、目录、漏跑提醒、来源导入、Windows 任务安装脚本与验证。
- Affected modules / contracts / data: 实施计划的“Planned File Structure”和“Cross-Task Interfaces”已锁定当前 Phase 01 的文件和接口范围。
- Ownership and non-overlap: 实施阶段仅创建一个负责集成的写入任务；审查阶段只读。实施文件与协调文件的精确边界见执行交接。

## Validation plan

- Automated tests and commands: `py -3.13 manage.py test radar.tests -v 2` 现为 101/101 通过；`makemigrations --check` 与 Django check 均通过。
- Manual checks: 受控 demo 的本地网页筛选、独立列开关、进度保存、撤回历史组合筛选和清理已完成；真实官方链接没有访问。
- Evidence required before default, external, or production-affecting changes: 真实来源启用、ATS、HTML 采集与 Windows 任务注册仍需各自的直接证据和用户授权。

## Risks and approval gates

- Known risks: 真实 HTML 多岗位页面、selector identity、启用后 parser 配置、ATS 批准 host 和混合库 demo 清理尚未验证或尚有明确修复门槛。
- Decisions requiring human approval: 首批真实来源准入/访问、Windows 任务 `-Apply`、云端购买或部署、Git 初始化/提交。
- Exact next human instruction needed: 若要进入真实数据阶段，请授权一个明确的官方来源核验批次；若只需离线骨架，当前 Phase 01 可交接。
