# Phase 02 新契约兼容验收 / Cycle 03

日期：2026-08-26

状态：技术 G10 候选通过；正式接受等待 H1、H2

冻结提交：`303baba`（父提交 `e95c446`）

## 范围与边界

- T1：仅使用保存的腾讯、携程 fixture 和 HTML fixture，验证批次/岗位新契约、官网更新时间、全地点、多岗位和证据门控。
- T2：仅进行离线兼容验证，确认输出新的 `batch` 配置格式；测试安装 `requests` 网络守卫。
- 复核 0011 迁移、岗位级进度、页面 ViewModel、正式/预览/历史隔离和 ATS 准入修复。
- 本 Cycle 没有访问任何企业网站，没有启动 T3。

## Cycle 02 阻断项复验

Cycle 02 发现的 ATS 信任边界问题已修复并通过回归验证：

- 来源准入、ATS 同源投递链接和 `enabled` 状态迁移共同复用完整的批准记录校验。
- 校验覆盖主机、必填事实、批准摘要、所属来源和所绑定的 `verified` 准入事件。
- 篡改 `approval_digest` 后，来源、投递链接和正式批次都会失败关闭。

Cycle 02 仍保持失败状态，未被本文件覆盖或追认。

## 冻结点验证结果

| 验证项 | 结果 |
| --- | --- |
| 全套测试 | 249/249 通过 |
| `radar.tests` | 199/199 通过 |
| ATS 准入专项 | 11/11 通过 |
| 篡改摘要阻止 `enabled` 专项 | 1/1 通过 |
| T1 + HTML 定向测试 | 62/62 通过 |
| T2 显式 `requests` 网络守卫 | 50/50 通过 |
| `manage.py check` | 0 个问题 |
| `makemigrations --check --dry-run` | 无待生成迁移 |
| Git 冻结点 | tracked/index 干净；仅用户截图未跟踪 |

独立只读评审结论：技术 blocker 为 0，G10 技术候选通过。评审未修改文件、未访问企业网站。

## 既有迁移与浏览器证据

- 迁移前业务表为 0 行；SQLite 已备份到系统临时目录。
- `0010`、`0011` 已按顺序应用；本地空库已验证 0011 反向回 0010、再正向应用 0011。
- 1440×900 技术检查已覆盖 Mock 标识、统计、筛选、列控制、前三岗位、展开全部、行内详情和正式 ORM 空状态。
- H1/H2 尚未由用户确认，因此以上技术证据不能代替产品验收。

## 历史证据索引

- T1 历史实现报告：`work/phase-02-01-json-api-adapter-report.md`
- T2 现场基准结果：`work/phase-02-02-live-acceptance-cycle-02.md`
- 新契约兼容 Cycle 01：`docs/handoffs/phase-02-compatibility-cycle-01.md`
- 新契约兼容 Cycle 02：`docs/handoffs/phase-02-compatibility-cycle-02.md`
- H1 原型记录：`docs/handoffs/phase-02-page-prototype.md`
- H2 预览记录：`docs/handoffs/phase-02-h2-acceptance-cycle-01.md`

## 剩余风险与停止线

- 旧岗位时间只能从旧批次首次发现/下线时间保守回填，不能伪造官网更新时间。
- 反向迁移遇到同一批次多个岗位均有进度时会主动中止，禁止猜测合并。
- 若 H1/H2 修改 G08 字段或交互契约，需要开启新的技术复核 Cycle。
- 正式 G10 只有在 H1、H2 依序通过后才可接受；H3 前禁止启动 T3。
