# Development state

Last verified: 2026-08-18 Asia/Shanghai

Phase and status: Phase 01 / Conditional pass — 仅限本地离线、空库可运行骨架

## Current goal

交付一个本地、单用户的官方校招信息雷达骨架：用可审计的官方来源准入、证据、公告生命周期和个人投递进度承载未来的真实来源；当前不接入真实来源。

## Completed and verified

- Django 5.2 + SQLite 本地应用已实现；包含来源候选/核验/启用事件、来源版本、发布决定、逐字段证据、公告/岗位/链接历史和七种个人投递进度。
- 默认正式列表只显示通过当前有效准入链、已应用发布事件和逐字段证据门控的北上广深当前岗位；历史筛选从同一可信发布事件的证据投影取岗位/链接。
- 每日更新命令、22:00 漏跑提醒、来源失败/部分失败事实提示、Windows 任务预览脚本、离线 demo 加载/清理和 13 个独立列控制均已实现。
- 已完成多轮独立只读审查与发布裁定。最终裁定：可条件放行为“本地离线可运行骨架”，不可表述为真实来源采集或生产就绪。

## Key decisions

- 本地模块化单体：Django、SQLite、独立来源适配器和 Windows 任务脚本。权威说明见 `docs/superpowers/specs/2026-08-17-official-campus-recruitment-radar-design.md`。
- 不做云部署、公开访问、自动投递、社区笔试信息或规避访问限制；不保存账号、Cookie、简历或凭据。
- 本机所有者可直接改 SQLite/源码的情形不属于 V0 防篡改威胁模型；应用层和 Admin 对审计对象采用 fail-closed/只读约束。

## Important files and modules

- `docs/superpowers/specs/2026-08-17-official-campus-recruitment-radar-design.md` — 已确认设计的完整说明。
- `docs/PROJECT_DEVELOPMENT_SPEC.md` — 持久项目边界和阶段路线。
- `docs/handoffs/phase-01-v0-design-handoff.md` — Phase 01 条件放行交接。
- `docs/superpowers/plans/2026-08-17-local-campus-radar-v0.md` — Phase 01 的详细实施任务、接口、测试和验证命令。
- `work/phase-01-r2-implementation-report.md`、`work/phase-01-history-projection-report.md` — 最终修复和验证事实报告。

## Validation evidence

- `py -3.13 manage.py makemigrations --check --dry-run` — `No changes detected`。
- `py -3.13 manage.py check` — 0 个系统问题。
- `py -3.13 manage.py test radar.tests -v 2` — 101/101 通过，内存测试数据库已销毁。
- 两份 PowerShell 脚本均通过语法解析；`OfficialCampusRadarDailyUpdate` 计划任务当前不存在。
- 受控 demo 在 `127.0.0.1` 实测：13 个独立列、进度保存、撤回历史的城市/岗位组合筛选和中文招聘类型显示；随后已清理。
- 只读 SQLite 复核：所有 `radar_*` 业务表、`auth_user` 和 `django_session` 均为 0 行。

## Known issues and risks

- 当前不是 Git 仓库；未获授权初始化或创建提交。
- 未导入或启用任何真实来源；真实 HTML 来源启用前必须补齐多岗位完整提取、稳定 selector locator 和运行时 parser 配置复核。ATS 来源启用前还必须将批准 host 的完整性复核接入所有消费者。
- demo 清理仅适用于空库或确认不存在同组织非 demo 数据的库；混合库使用前必须收紧清理范围。
- Windows 任务尚未注册；本机关闭/休眠仍会漏跑，应用只会提示。云端运行尚未设计或购买。
- 独立审查中曾创建并立即删除一条命名探针记录；当前业务表均为空，但 SQLite 自增序列可能已前移。

## Exact next task

等待用户单独授权下一步：先修复真实来源启用前的剩余阻断，并对一小批官方来源完成证据核验与适配器验收；之后如仍需要，再授权注册本机 22:00 Windows 任务。
