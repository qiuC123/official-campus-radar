# Execution Brief — Phase 01 本地官方校招雷达 V0

状态：实施与多轮修复已完成；仅条件放行为本地离线、空库骨架。真实来源与任务注册仍未实施。

## 实施任务的目标

实现一个 Windows 本地、私有的官方校招信息雷达 V0。它使用 Django、SQLite 和来源适配器保存与展示北上广深的官方校招信息，支持个人投递进度、每日 22:00 任务命令和漏跑提醒。

## 已验证事实

- 当前目录：`D:\devlop\Ai定时任务\offer排行榜`。
- 当前不是 Git 仓库：`git rev-parse` 返回退出码 128；没有分支、工作树或可用提交。
- 当前没有 `manage.py`、依赖清单、应用目录或既有测试；基线应用测试不可运行，原因是应用尚未创建。
- 当前没有嵌套 `AGENTS.md`；会话提供的个人工作约定继续有效。
- 本机可用 `py -3.13`；计划已基于 Django 5.2 对 Python 3.13 的官方支持锁定版本范围。

## 交付与验收

以 `docs/superpowers/specs/2026-08-17-official-campus-recruitment-radar-design.md` 第 8 节和 `docs/superpowers/plans/2026-08-17-local-campus-radar-v0.md` 的十个任务为准。实现必须至少提供：

- 可迁移的本地数据模型、来源白名单、证据、公告/岗位、运行记录和七种个人投递进度；
- 确定性官方来源、地点、去重、发布、截止与失败隔离规则；
- fixture 驱动的 HTML 采集、版本变更检测、日更命令和漏跑判定；
- 本地筛选表、列显示控制、官方公告/投递入口、手动进度和立即更新入口；
- 仅生成、解析和说明 Windows 22:00 任务安装脚本，不注册任务；
- 通过计划中列出的 Django 测试、Django check、迁移检查和 PowerShell 语法检查。

## 唯一实施任务的文件所有权

实施任务拥有并可修改：

```text
requirements.txt
manage.py
campus_radar/ 下的文件
radar/ 下的文件
scripts/ 下的文件
data/ 下的文件
docs/runbooks/ 下的文件
docs/source-onboarding.md
work/phase-01-implementation-report.md
```

协调任务保留以下文件的写入权：

```text
DEV_STATE.md
docs/handoffs/ 下的文件
docs/PROJECT_DEVELOPMENT_SPEC.md
docs/superpowers/specs/ 下的文件
docs/superpowers/plans/ 下的文件
```

## 实施规则

- 逐个功能使用 TDD：先写能因缺少行为而失败的测试，确认失败，再写最小实现并确认通过。
- 只对慢速或外部 HTTP 边界使用 mock；测试不得访问真实企业来源。
- 页面风格以“个人校招信息工作台”为单一职责，保持信息密度、明确筛选和表格可读性；不做营销页，不添加集团标签、笔试信息、公司规模或自动投递。
- UI 可采用深墨蓝 `#102A43`、信号蓝 `#2563EB`、雾白 `#F5F8FC`、验证绿 `#0F9D68`、提醒橙 `#D97706` 与细分隔线 `#D9E2EC`；使用系统中文字体栈，不下载外部字体或资源。
- 未经额外授权不得：初始化 Git、提交、创建或注册 Windows 任务、访问真实企业来源、接入账号或 Cookie、购买/部署服务器、发送通知或向外部服务写入数据。
- 当前不是 Git 仓库，不能创建工作树。实施在当前目录进行；不因这一事实初始化 Git。

## 协调裁定

`subagent-driven-development` 的“每项任务一个实施者”流程不适用于本阶段：十项任务以同一 Django 数据模型、迁移和接口强依赖，且项目没有 Git 提交或工作树可用于其评审包。依据获批 Design Handoff，采用一个唯一的 `实施任务1` 完成所有代码、迁移、测试和事实报告；协调任务会在完成后另行发起只读审查。代价是单次实施任务更长，但避免并行写入冲突和未经授权的 Git 初始化。

## 停止条件与回报

如依赖安装、迁移、核心测试或计划接口出现无法通过证据解决的阻塞，停止并在 `work/phase-01-implementation-report.md` 写明命令、错误和最小阻塞原因。完成后也在该文件记录：实际修改文件、每个测试命令和结果、未满足的验收项、残余风险，以及建议的下一步。不要自行发起审查任务。
