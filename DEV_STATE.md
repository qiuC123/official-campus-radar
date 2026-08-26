# Development state

Last verified: 2026-08-26 Asia/Shanghai

Phase and status: Phase 02 / H1、H2、G10 已通过；当前停在 H3。首批 50 家企业的七类配额已由用户确认，具体名单、访问范围和最低成功线仍待确认；T3 尚未开始。

## Current result

- 架构仍为 Django 5.2 + SQLite 服务端页面，没有引入 React/Vue 或生产浏览器依赖。
- T1 JSON 适配器、T2 接口发现工具的 `batch` / `official_page_url` 兼容候选已实现；旧 JSON 配置和证据字段由 0011 可逆迁移。兼容 Cycle 01/02 失败记录保留，Cycle 03 技术候选通过。
- 正式首页 `/` 使用 ORM ViewModel；`/history/` 显示截止/撤回批次；开发模式下 `/preview/phase-02/` 使用独立 Mock ViewModel，并始终标注模拟数据。
- 领域模型使用 `RecruitmentBatch` / `RecruitmentPosition`；根据 ADR 0003，投递进度现在归招聘批次所有并由用户手动维护，不从岗位自动计算。
- 迁移 `0010`～`0012` 已依次应用。0012 前业务表仍为 0 行，SQLite 已备份到 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-0012-20260826-152726.sqlite3`；空库已实测 0012 反向回 0011、再正向应用 0012。
- 地点不再限北上广深；未知地点保留原文，全国/远程参与任一具体城市筛选。
- Django Mock 预览页使用 12 列横向表格；公司类型、招聘类型和投递进度支持多选，省份最多同时选择 5 个；每批次显示最多 5 个代表岗位并可展开全部。

## Candidate validation evidence

- `py -3.13 manage.py makemigrations --check --dry-run`：No changes detected。
- `py -3.13 manage.py check`：0 个问题。
- `py -3.13 manage.py test -v 1`：254/254 通过。
- Cycle 03 独立只读评审：技术 blocker 为 0，G10 技术候选通过；冻结提交为 `303baba`。
- 临时测试数据库完整应用 0001～0012 后销毁；0012 迁移守卫覆盖单一映射、多进度冲突和不可安全反向三类场景。
- 1280×720 浏览器检查：预览 Mock 标识、12 列横向表格、5 省上限、代表岗位、展开 7 个全部岗位、批次进度模拟保存、URL 筛选和外站拦截均正常；正式首页只显示真实 ORM 空状态。

## Human gates

- H1：Cycle 06 已于 2026-08-26 通过。Cycle 07 进一步修正批次官网术语、未知截止时间、岗位展开和批次级手动进度；Cycle 08 统一主蓝色、按钮层级、圆角、字距和表格密度。分类徽章低饱和方案已按用户要求撤回，保留原有分类配色；以上均未改变已通过的信息结构。
- H2：Cycle 02 已于 2026-08-26 由用户完成浏览器验收并明确确认通过。
- G10：Cycle 03 技术复核为 0 blocker；H1/H2 前置条件满足后已正式接受。
- H3：企业类型配额已确认（民企 20、央国企 10、外资 6、银行 5、中外合资 4、事业单位 3、社会机构 2，共 50 家）；具体企业名单、访问范围和最低成功线待确认。H3 完成前禁止启动 T3 企业外网探测。

## Explicitly not started

T3 企业探测、真实来源准入、真实岗位采集、Windows 计划任务、微信模块和云部署均未开始。

## Exact next task

继续完成 H3：先确认允许访问的范围和禁止行为，再确认 T3 最低成功线，最后按已确认配额形成具体 50 家企业名单。在 H3 获得明确授权前，不访问任何企业网站，不启动 T3。
