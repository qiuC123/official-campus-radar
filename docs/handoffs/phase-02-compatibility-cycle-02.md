# Phase 02 新契约兼容验收 / Cycle 02

日期：2026-08-26

状态：失败（历史记录，禁止覆盖）

冻结提交：`e95c446`（父提交 `34306ac`）

## 范围

- T1：仅使用保存的腾讯、携程 fixture 和 HTML fixture，验证批次/岗位新契约。
- T2：仅进行离线兼容验证，并安装 `requests` 网络守卫；没有访问企业网站。
- 迁移、页面 ViewModel、正式/预览隔离和测试结果均以冻结提交为准。

## 自动化结果

- 全套测试：248/248 通过。
- `radar.tests`：198/198 通过。
- T1 + HTML 定向测试：62/62 通过。
- T2 显式网络守卫：50/50 通过。
- `manage.py check`：0 个问题。
- `manage.py makemigrations --check --dry-run`：无待生成迁移。
- `git diff --check`：通过；冻结点的 tracked worktree/index 干净，仅有用户截图未跟踪。

## 独立只读评审结论

评审发现 1 个必须修复的信任边界问题，因此本 Cycle 失败：

- ATS 来源只检查是否存在获批主机记录，没有在消费时复核记录摘要、必填事实和所绑定的准入事件。
- ATS 来源主机上的投递链接还会走同主机直接放行路径。
- 如果数据库中的 `approval_digest` 被篡改，来源仍可能进入正式页面，未做到失败关闭。

自动化全绿不抵消该问题。修复必须固化为新的 Git 提交，并在新的 Cycle 重新执行完整验证和独立只读评审；不得把本文件改写为通过。

## 历史证据索引

- T1 历史实现报告：`work/phase-02-01-json-api-adapter-report.md`
- T2 Cycle 01 失败与 Cycle 02 基准结果：`work/phase-02-02-live-acceptance-cycle-02.md`
- T2 Cycle 02 现场约束：`docs/handoffs/phase-02-02-live-acceptance-cycle-02.md`

## 停止线

本 Cycle 不授权 T3。即使后续技术 Cycle 通过，H1、H2 和 H3 仍必须分别由用户确认。
