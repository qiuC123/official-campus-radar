# Phase 01 实施报告

日期：2026-08-18

## 实际改动

- 创建 Django 5.2 本地项目（`campus_radar`）和 `radar` 应用，SQLite 位于项目目录，时区为 `Asia/Shanghai`。
- 建立组织、官方来源、抓取/版本/更新运行、公告/岗位/链接/证据和个人投递进度模型，并生成 `radar/migrations/0001_initial.py`。
- 实现官方来源准入、北上广深地点匹配、URL 规范化、确定性发布和个人进度隔离。
- 实现低频 HTML 适配器、ETag/304、SHA-256 内容版本、失败留痕和离线 HTML fixture。
- 实现失败隔离的更新编排、截止历史迁移、`run_daily_update` 命令和无可执行来源时的非零失败。
- 实现本地“个人校招信息工作台”：筛选表、列显示记忆、官方链接、七种手动进度、手动更新反馈和漏跑提醒。
- 增加本地来源 CSV dry-run/原子导入、来源准入文档、本地启动脚本、计划任务预览/注册脚本及两个 runbook。

## TDD 证据

每项行为先增加测试并运行。缺失项目配置、模型、服务、采集器、视图、状态服务和 CSV 命令时，分别得到预期的 `manage.py`/模块/命令不存在红灯；实现最小功能后对应测试转绿。额外为“没有可执行来源时计划命令必须失败”增加了红灯测试，随后修复为绿灯。

## 验证命令与结果

| 命令 | 结果 |
| --- | --- |
| `py -3.13 -m pip install -r requirements.txt` | 通过；安装 Django 5.2.17，Requests 与 Beautiful Soup 已满足范围。 |
| `py -3.13 manage.py migrate` | 通过；应用全部内置迁移和 `radar.0001_initial`。 |
| `py -3.13 manage.py test radar.tests.test_project -v 2` | 通过，1 项。 |
| `py -3.13 manage.py test radar.tests.test_models -v 2` | 通过，3 项。 |
| `py -3.13 manage.py test radar.tests.test_admission radar.tests.test_locations radar.tests.test_publication -v 2` | 通过，5 项。 |
| `py -3.13 manage.py test radar.tests.test_collection -v 2` | 通过，3 项；HTTP 由 mock 驱动。 |
| `py -3.13 manage.py test radar.tests.test_update_runner -v 2` | 通过，3 项。 |
| `py -3.13 manage.py test radar.tests.test_views radar.tests.test_update_status -v 2` | 通过，8 项。 |
| `py -3.13 manage.py test radar.tests.test_source_catalog -v 2` | 通过，2 项。 |
| `py -3.13 manage.py import_source_catalog --path data/source_catalog.csv --dry-run` | 通过；`validated_rows=0 dry_run=true`，无写入。 |
| `py -3.13 manage.py makemigrations --check --dry-run` | 通过；`No changes detected`。 |
| `py -3.13 manage.py check` | 通过；无 Django system-check 问题。 |
| `py -3.13 manage.py test radar.tests -v 2` | 通过，25 项。 |
| `powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/install_daily_task.ps1)) \| Out-Null"` | 通过；仅语法解析，未传 `-Apply`。 |
| 同一 PowerShell 语法检查（`scripts/run_local.ps1`） | 通过。 |
| `./scripts/run_local.ps1` + `Invoke-WebRequest http://127.0.0.1:8000/` | 通过；HTTP 200，页面标题存在；进程已以 Ctrl+C 正常停止。 |

## 未满足的验收项

- 没有真实企业来源被人工核验、导入或访问；因此未证明任何企业页面的线上可用性。
- Windows 计划任务未注册、也未在 22:00 真实触发；只验证了脚本语法和 Python 命令参数契约。
- 未进行真实浏览器的人工点击验收；本地 HTTP 连通性和 Django 视图测试已覆盖对应行为。
- 按文件所有权限制，未修改 `DEV_STATE.md` 或 `docs/handoffs/` 中的协调文件。

## 残余风险

- 通用 CSS 选择器适配器只针对离线 fixture 验证；接入任何真实来源前仍需逐源保存 fixture、核验证据和低频访问策略。
- 当前本地数据库没有已启用来源，运行手动更新会记录失败而不是生成招聘内容，这是防止未经核验来源进入列表的预期保护。
- 页面用于单机本地使用；没有用户账号、通知或云端可用性保证。

## 建议下一步

先由用户审核本实现的只读结果；如继续，按 `docs/source-onboarding.md` 选取一批官方来源并单独批准其人工核验与启用。确认无误后，再单独批准 Windows 计划任务的 `-Apply` 注册与一次人工 22:00 验收。
