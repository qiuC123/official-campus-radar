# Execution Brief — Phase 01-R2 最终可信性门控修复

状态：已完成；最终裁定为本地离线、空库骨架的条件放行，不增加任何外部范围。

## 不可改变的外部边界

本地 Django + SQLite、单用户、离线 fixture。禁止真实来源访问/启用/导入、任务计划注册、账号/Cookie、自动投递、云部署和 Git 操作。当前数据库必须在验收结束时不含真实数据或 demo 残留。

## 事实与共同根因

根因不是 UI，而是最终查询和跨版本发布仍相信了可手工改写的派生状态或“存在一条证据”，没有把当前投影重新绑定到不可变事实。所有以下验收项必须先有失败回归测试，再最小修复并转绿。

## A. 准入链、host 与启用配置

1. 正式查询和 `source_is_admitted()` 共享一个 fail-closed 的“当前有效准入链”判断：
   - 最新事件必须为 enabled，和来源当前状态一致；
   - 状态跃迁连续且合法，不能 `candidate → enabled` 直跳；
   - actor、reason、evidence 非空；
   - 手工把 source 状态改为 enabled、无事件、过期 enabled 后又 suspended/revoked、或断链事件都不得展示/采集。
2. 正式查询还必须校验 `PublicationEvent.notice`、`SourceVersion.source`、公告 source 和准入事件属于同一链路。
3. `ApprovedApplicationHost` 必须验证 admission event 的 source 与自身 source 一致，事件处于可用于 host 的有效状态，host/actor/evidence 非空，且创建后不可改写；消费者再次 fail-closed 验证。
4. `verified → enabled` 前必须调用适配器配置校验：HTML 来源至少具有稳定公告/岗位 identity 及标题、分类、对象、日期、地点、链接/原文所需 selector。无完整 parser contract 不得生成 enabled event。
5. `local_demo_disabled` 需要明确、绝不联网的 demo adapter，而不是靠未注册 adapter 失败。

## B. 投影值、证据与分类

1. 建立共享的候选投影值 ↔ evidence 校验。标题、对象、发布日期、截止日期、公告 URL、岗位名、地点及存在时的投递 URL，均要求：
   - 实际值、原文值和精确字段 locator 非空；
   - evidence parsed value 等于规范化后的实际投影值；
   - value hash 匹配 parsed value；
   - Evidence 关联当前 SourceVersion、PublicationEvent、公告/岗位/链接主体。
2. `formal()` 必须重新比较已持久化证据和当前展示值，不能只信 `evidence_complete` 或字段名存在。合法“未说明”字段应有明确拒绝/缺失决定，不能用空字符串或公告容器 locator 伪装证据。
3. HTML selector 缺失或节点未命中时不得生成容器级伪 locator。
4. 分类必须同时考虑类型字段、标题、岗位标题和节点原文；招商、招标、采购、招聘会新闻等否定信号优先。加入走完整发布链的反例测试。

## C. 身份、生命周期与历史查询

1. 先计算目标城市岗位。已存在且可信的公告，在 `positions_complete=True` 且目标岗位为空时，无论页面还是否有杭州等非目标岗位，都应写 out_of_scope、停止展示旧目标岗位/链接，且不得触碰个人进度。
2. 发布前同时查询 `(source, identity_key)` 与 `(source, canonical official_notice_url)`；二者指向不同公告时写 ambiguous/rejected，不创建、不覆盖、不下线旧投影。规范化 identity 空白值。
3. 为来源+规范公告 URL增加安全唯一防线；迁移遇到不可信或重复历史数据必须停止而非合并/伪造。
4. 分离当前正式列表和可信历史查询。`status=withdrawn`/`expired` 必须能够展示有此前完整发布链的历史，但当前默认列表仍只展示 current published/updated、当前岗位和有效准入链。

## D. Demo 所有权与测试离线性

1. demo 加载后点击立即更新再清理，必须删除该 demo 独有的 UpdateRun/FetchRun/对象，同时保留非 demo sentinel 运行；不得以宽泛域名误删其他本地夹具。
2. 测试必须严格无网络。修正不安全测试以正式暂停/未启用状态禁用来源、mock adapter 并断言未调用；在测试配置中阻断未 mock 的 `requests` 出站请求，使未来误联网立即失败。

## 文件所有权

实施者可修改 `campus_radar/`、`radar/`（含迁移、测试、fixture）、`scripts/`、`data/`、`docs/runbooks/`、`docs/source-onboarding.md` 与 `work/phase-01-r2-implementation-report.md`。不得修改 `DEV_STATE.md`、`docs/handoffs/**`、`docs/PROJECT_DEVELOPMENT_SPEC.md`、`docs/superpowers/**`。

## 最终验证

逐组红绿后新鲜运行：

```powershell
py -3.13 manage.py makemigrations --check --dry-run
py -3.13 manage.py check
py -3.13 manage.py test radar.tests -v 2
powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/install_daily_task.ps1)) | Out-Null"
powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/run_local.ps1)) | Out-Null"
```

随后用受控 demo 完成“加载 → 点击立即更新 → 清理”的本地验证，并记录 sentinel 运行保留、所有 demo 关联记录为零。事实报告须列红灯、绿灯、迁移、最终命令、数据库清理和未执行的外部操作。完成后等待独立审查，实施者不得自行宣告放行。
