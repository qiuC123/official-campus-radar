# Development state

Last verified: 2026-08-26 Asia/Shanghai

Phase and status: Phase 02 / H1 Cycle 06 已通过；Cycle 07 后置修正和批次级手动进度已实现；Cycle 08 已完成视觉收敛并通过 1440 × 900 浏览器复验。Django 预览页已同步进度语义和管理员运维权限，但尚未完成 Cycle 08 高密度表格的完整视觉同步，因此 H2 仍待开始；G10 尚未正式接受，H3 尚未开始。

## Current result

- 架构仍为 Django 5.2 + SQLite 服务端页面，没有引入 React/Vue 或生产浏览器依赖。
- T1 JSON 适配器、T2 接口发现工具的 `batch` / `official_page_url` 兼容候选已实现；旧 JSON 配置和证据字段由 0011 可逆迁移。兼容 Cycle 01/02 失败记录保留，Cycle 03 技术候选通过。
- 正式首页 `/` 使用 ORM ViewModel；`/history/` 显示截止/撤回批次；开发模式下 `/preview/phase-02/` 使用独立 Mock ViewModel，并始终标注模拟数据。
- 领域模型使用 `RecruitmentBatch` / `RecruitmentPosition`；根据 ADR 0003，投递进度现在归招聘批次所有并由用户手动维护，不从岗位自动计算。
- 迁移 `0010`～`0012` 已依次应用。0012 前业务表仍为 0 行，SQLite 已备份到 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-0012-20260826-152726.sqlite3`；空库已实测 0012 反向回 0011、再正向应用 0012。
- 地点不再限北上广深；未知地点保留原文，全国/远程参与任一具体城市筛选。

## Candidate validation evidence

- `py -3.13 manage.py makemigrations --check --dry-run`：No changes detected。
- `py -3.13 manage.py check`：0 个问题。
- `py -3.13 manage.py test -v 1`：254/254 通过。
- Cycle 03 独立只读评审：技术 blocker 为 0，G10 技术候选通过；冻结提交为 `303baba`。
- 临时测试数据库完整应用 0001～0012 后销毁；0012 迁移守卫覆盖单一映射、多进度冲突和不可安全反向三类场景。
- 1440×900 浏览器检查：预览 Mock 标识、统计、筛选、前三岗位、展开全部、行内详情均正常；正式首页只显示真实 ORM 空状态。

## Human gates

- H1：Cycle 06 已于 2026-08-26 通过。Cycle 07 进一步修正批次官网术语、未知截止时间、岗位展开和批次级手动进度；Cycle 08 统一颜色、按钮层级、圆角、字距和表格密度，均未改变已通过的信息结构。
- H2：用户确认 Django 预览页的实际浏览器体验。
- G10：Cycle 03 技术候选已通过；只有 H1/H2 先通过后，才可正式接受。
- H3：确认企业名单、访问范围和最低成功线。H3 前禁止启动 T3 企业外网探测。

## Explicitly not started

T3 企业探测、真实来源准入、真实岗位采集、Windows 计划任务、微信模块和云部署均未开始。

## Exact next task

把 Cycle 08 的高密度表格、公司/招聘/省份多选筛选和视觉规则完整同步到 Django Mock 预览页，保存 H2 Cycle 02 技术记录后交给用户进行 H2 浏览器验收。全程不自动访问任何企业网站。
