# Development state

Last verified: 2026-08-26 Asia/Shanghai

Phase and status: Phase 02 / H1 Cycle 01～05 收到修改意见，静态原型进入 Cycle 06；H1/H2 未确认，因此 G07～G10 不得记为正式接受；H3 尚未开始。

## Current result

- 架构仍为 Django 5.2 + SQLite 服务端页面，没有引入 React/Vue 或生产浏览器依赖。
- T1 JSON 适配器、T2 接口发现工具的 `batch` / `official_page_url` 兼容候选已实现；旧 JSON 配置和证据字段由 0011 可逆迁移。兼容 Cycle 01/02 失败记录保留，Cycle 03 技术候选通过。
- 正式首页 `/` 使用 ORM ViewModel；`/history/` 显示截止/撤回批次；开发模式下 `/preview/phase-02/` 使用独立 Mock ViewModel，并始终标注模拟数据。
- 领域模型已改为 `RecruitmentBatch` / `RecruitmentPosition`，投递进度归单个岗位所有。
- 迁移 `0010`、`0011` 已依次应用。迁移前业务表 0 行，SQLite 已备份到系统临时目录。
- 地点不再限北上广深；未知地点保留原文，全国/远程参与任一具体城市筛选。

## Candidate validation evidence

- `py -3.13 manage.py makemigrations --check --dry-run`：No changes detected。
- `py -3.13 manage.py check`：0 个问题。
- `py -3.13 manage.py test -v 1`：249/249 通过，其中 `radar.tests` 199/199；T1+HTML 定向 62/62；T2 显式网络守卫 50/50。
- Cycle 03 独立只读评审：技术 blocker 为 0，G10 技术候选通过；冻结提交为 `303baba`。
- 临时测试数据库完整应用 0001～0011 后销毁；本地空库已实测 0011 反向回 0010、再正向应用 0011 均成功。
- 1440×900 浏览器检查：预览 Mock 标识、统计、筛选、前三岗位、展开全部、行内详情均正常；正式首页只显示真实 ORM 空状态。

## Pending human gates

- H1：用户确认 Cycle 06 公司类型拆分为外资/中外合资、公司/招聘/进度多选、省份最多 5 个、高密度横向表格和批次行进度的含义。
- H2：用户确认 Django 预览页的实际浏览器体验。
- G10：Cycle 03 技术候选已通过；只有 H1/H2 先通过后，才可正式接受。
- H3：确认企业名单、访问范围和最低成功线。H3 前禁止启动 T3 企业外网探测。

## Explicitly not started

T3 企业探测、真实来源准入、真实岗位采集、Windows 计划任务、微信模块和云部署均未开始。

## Exact next task

先等待用户验收 H1 Cycle 06；若仍有修改意见，新建 Cycle 07。H1 通过后先明确批次行进度的领域含义，再同步 Django 预览页并进行 H2。全程不自动访问任何企业网站。
