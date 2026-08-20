# Phase 01 修复轮次事实报告

日期：2026-08-18

## 修复内容

- 来源目录导入现在一律创建待核验、未启用候选；来源准入校验官网 host，ATS 必须具备官网入口 URL、人工核验证据和许可 host。
- HTML 提取器要求每个节点具备独立公告链接、标题和招聘类型；不再硬编码校园招聘，非招聘节点被跳过，撤回选择器可显式标记候选撤回。
- 公告归属具体 `OfficialSource`，唯一性改为来源加公告 URL；组织别名可复用同一实际招聘主体，父子主体不会自动合并。
- 发布过程置于事务中，过滤非北上广深岗位；逐字段、岗位和投递链接证据关联对应版本与 locator。岗位/链接移除后保留历史而不在正式表展示，撤回后可重新开放。
- 采集适配器改为纯提取边界，更新编排集中写入一次 FetchRun；同哈希 200 标为 unchanged，不新增版本或重发公告；过期按成功来源而非组织处理。
- 漏跑判定支持“曾有计划运行后的前一晚缺失”，首次安装不误报；手动更新对无来源、全失败和异常显示事实性提示。
- 核验依据、版本、证据和抓取运行在 admin 中创建后不可改删；表格拆为 13 个独立显示列控制。
- 添加 `load_local_demo` / `--remove`：只操作 `demo.invalid` 的隔离本地数据，覆盖招聘中、已截止、已撤回、无投递入口、漏跑和个人进度；更新本地 runbook。

## TDD 分组证据

| 组 | 红灯命令与事实 | 最终绿灯 |
| --- | --- | --- |
| A 来源与身份链 | `py -3.13 manage.py test radar.tests.test_remediation_identity -v 2`：6 项中 4 failed、2 error，暴露自动核验、host 不匹配、硬编码招聘和公告无来源。 | 同命令：7/7 通过。 |
| B 发布证据与生命周期 | `py -3.13 manage.py test radar.tests.test_remediation_publication -v 2`：4 项中 1 failed，暴露城市筛选读取原文。其余新增测试验证事务、证据、生命周期。 | 最终该模块 5/5 通过，含不可信 HTTPS 投递 host 拒绝。 |
| C 抓取与任务 | `py -3.13 manage.py test radar.tests.test_remediation_updates -v 2`：5/5 failed，暴露同哈希重发、失败双记、组织级过期、漏跑和虚假完成提示。 | 同命令：5/5 通过。 |
| D 实体、审计与列 | `py -3.13 manage.py test radar.tests.test_remediation_admin_ui -v 2`：初次有别名和列控制失败；admin 测试的 request double 缺少 user 后先修正测试夹具。 | 同命令：3/3 通过。 |
| E 受控演示 | `py -3.13 manage.py test radar.tests.test_local_demo -v 2`：命令不存在错误。 | 同命令：1/1 通过。 |

中途将 FetchRun 记录责任迁移至更新器时出现过一次未闭合 `try` 的 SyntaxError；已立即定位为 `html.py` 的纯提取重构语法错误、修正后才生成 `0003` 并继续验证。未保留该失败状态。

## 最终验证

| 命令 | 结果 |
| --- | --- |
| `py -3.13 manage.py migrate` | 通过；应用 `radar.0002`、`radar.0003`。 |
| `py -3.13 manage.py makemigrations --check --dry-run` | 通过；`No changes detected`。 |
| `py -3.13 manage.py check` | 通过；无 system-check 问题。 |
| `py -3.13 manage.py test radar.tests -v 2` | 通过，46/46。 |
| 两份 PowerShell 脚本的 `[scriptblock]::Create(...)` 语法检查 | 通过；未执行 `-Apply`。 |
| `py -3.13 manage.py import_source_catalog --path data/source_catalog.csv --dry-run` | 通过；0 行、无写入。 |
| `py -3.13 manage.py load_local_demo` → `./scripts/run_local.ps1` → 本机 HTTP | 通过；`/` 与 `/?status=expired` 都返回 HTTP 200，发现 39 个页面单元的 `data-column` 属性。 |
| `py -3.13 manage.py load_local_demo --remove` | 通过；随后查询 `demo_rows=0`。 |

## 未做的外部操作与边界

- 未访问、导入或启用任何真实企业来源；`data/source_catalog.csv` 仍只有表头。
- 未注册或执行 Windows 计划任务，未运行 `install_daily_task.ps1 -Apply`。
- 未部署、发送通知、使用账号/Cookie 或自动投递。
- 未修改 `DEV_STATE.md`、`docs/handoffs/**`、`docs/superpowers/**` 或项目开发规范；这些状态文件仍由协调者根据本报告更新。
