# Phase 01-R 实施事实报告

日期：2026-08-18

## 结论与边界

Phase 01-R execution brief 要求的七组应用代码修复已实施，新鲜完整测试为 70/70 通过，受控本地 demo 已完成 HTTP 走查并清理为零。本报告只陈述实施与验证事实；不宣布进入下一阶段，仍等待协调者安排独立只读审查。

全程未初始化 Git，未创建 worktree/提交，未访问或启用真实企业来源，未导入真实数据，未注册计划任务，未使用账号/Cookie，未自动投递，未云部署，也未新增生产依赖。

## TDD 红灯与绿灯

每组先加最小验收测试并确认旧行为失败，再做该组最小根本修复。

| 组 | 红灯命令与事实 | 绿灯事实 |
| --- | --- | --- |
| 1 正式列表门控 | `py -3.13 manage.py test radar.tests.test_phase01r_group1_formal_gate -v 2`：初次 3 项中 1 failed + 2 errors，暴露 source 可空、缺稳定身份/发布事件和 Admin 可变更。后续伪造 `evidence_complete=True` 仍能展示的回归测试再次红灯；Organization Admin 可新增的边界测试也红灯。 | 模块 3/3；实际九类字段证据查询门控与扩展 Admin 边界回归均通过。 |
| 2 来源准入与 host | `py -3.13 manage.py test radar.tests.test_phase01r_group2_admission -v 2`：初次 4 项中 1 failed + 3 errors，缺追加式迁移、别名冲突和外部投递 host 批准。管理命令测试初次为 `Unknown command` 红灯。 | 模块 5/5；含命令写入可审计状态事件。 |
| 3 身份、分类与证据 | `py -3.13 manage.py test radar.tests.test_phase01r_group3_identity_evidence -v 2`：初次因缺 `FieldEvidenceValue` 无法导入；稳定节点 ID 用例初次得到空 identity。最后边界测试确认 HTML 适配器会错把未声明完整的岗位覆盖当作完整。 | 模块 5/5；补充边界测试后，默认 `positions_complete=False`，只接受适配器显式声明。 |
| 4 整页原子更新 | `py -3.13 manage.py test radar.tests.test_phase01r_group4_atomic_page -v 2`：2/2 failed，中途失败留下 SourceVersion，A→B→A 只有两版。 | 2/2；失败整页回滚后只写一条脱敏 FetchRun，同 hash 可重试，A→B→A 为三个已应用版本。 |
| 5 新公告准入/已有公告下线分流 | `py -3.13 manage.py test radar.tests.test_phase01r_group5_lifecycle -v 2`：初次 3/3 failed，明确撤回和完整移除被新公告地点门槛拦截，不完整覆盖会删掉未见岗位。额外用 `positions_complete=False` 的明确撤回用例再现“撤回被拒绝”红灯。 | 3/3；明确撤回优先于覆盖完整性门槛，完整无目标岗位写 `out_of_scope`，不完整解析只写 rejected 事件，三者均不改个人进度。 |
| 6 当前岗位、健康与事实反馈 | `py -3.13 manage.py test radar.tests.test_phase01r_group6_health_ui -v 2`：初次 4/4 failed，已移除岗位仍匹配、无降级摘要、22:01 漏跑事实错误，错误串泄露 query/令牌/本地用户路径。 | 4/4；只查当前岗位，partial failure 显示来源摘要，手动成功不覆盖计划漏跑，错误信息脱敏。 |
| 7 离线 demo 与 runbook | `py -3.13 manage.py test radar.tests.test_phase01r_group7_demo -v 2`：初次 2 项中缺 fixture，旧 demo 又触发身份唯一性错误。 | 2/2；默认不导入，只使用 `demo.invalid`，清理保留非 demo 数据。 |

旧测试在新 schema 下的第一次完整回归为 69 项中 9 failed + 9 errors。已按新契约迁移夹具和断言，没有删除用例、降低断言或屏蔽错误；补入管理命令用例后，最终为 70/70。

## 关键实施选择

### 1. 正式列表是数据库级与查询级双重门控

- `RecruitmentNotice.source` 改为非空，公告身份唯一键为 `(source, identity_key)`。
- `RecruitmentNotice.objects.formal()` 要求来源当前是 enabled，有已应用 SourceVersion，有最新 published/updated 事件，且同一版本/事件下真实存在公告六字段、每个当前岗位的岗位名/地点，以及每个当前投递链接证据。不信任单独布尔标记。
- 默认页面、城市/状态/岗位搜索均从 formal 查询集出发；岗位搜索只用 `is_current=True`。

### 2. 来源准入和 host 信任分离

- CSV 只创建 candidate；`candidate → verified → enabled → suspended/revoked` 由服务或 `transition_source_admission` 命令追加 `SourceAdmissionEvent`。revoked 为终态；旧 `is_verified/is_active` 仅作同步兼容字段，不能绕过事件链。
- `OrganizationAlias.normalized_alias` 全局唯一；名称与别名映射到不同主体时整批硬失败，不选“第一个”。
- 公告 host 必须在已准入来源 host 上；投递 host 与公告 host 单独管理。外部 ATS 只能在官网入口证据存在时追加 `ApprovedApplicationHost`。

### 3. 稳定身份、严格分类和不可变证据

- 适配器提供稳定公告 ID 和岗位 ID，不以 DOM 顺序或 URL fragment 当唯一身份。页内同 ID 内容冲突、同规范 URL 冲突或仅 fragment 不同，只写 ambiguous/rejected 事件。
- 分类是 `campus_recruitment` / `internship` / `other` / `unknown`；只前两类可新建公告，招商、招标、招聘会新闻等反例被拒绝。
- `Evidence` 每条关联具体 SourceVersion 和 PublicationEvent，记录字段、原文/原始 href、精确 locator、解析值和 value hash；只 `.create()` 追加，模型拒绝修改/删除。
- `positions_complete` 默认为 false；只有适配器配置明确声明整页岗位覆盖完整，才可将未见岗位标记为移除。

### 4. 来源页为一个原子更新边界

- 抓取/解析在事务外；随后一个事务锁定来源，只与最近已应用版本比 hash，并一次写版本、全部候选决定、公告/岗位/链接/证据/生命周期和成功 FetchRun。
- 任一写入失败会整页回滚，再用短事务写且只写一条脱敏失败 FetchRun。因失败版本未应用，下次相同 hash 仍可重试。
- 每个来源独立失败；一个来源失败不阻断其他来源，也不过期/撤回其旧数据。

### 5. 生命周期、个人进度和管理边界

- 新公告才应用稳定身份、严格分类、目标城市、完整证据和 host 门槛。已有公告明确撤回会立即停止展示旧岗位/链接；完整覆盖且无目标岗位写 `out_of_scope`；解析不完整仅记录拒绝。
- 发布、生命周期、抓取和清理逻辑都不改写 `ApplicationProgress`。
- partial failure、整体成功/失败、计划漏跑和手动刷新是独立事实。页面显示降级来源摘要；22:01 当日无计划运行即漏跑，手动成功不会掩盖。
- 除 ApplicationProgress 外，Organization/Alias/Source、公告/岗位/链接、准入/版本/发布/证据/运行记录在 Django Admin 均无 add/change/delete 权限。

## 模型与迁移

| 迁移 | 内容 | 安全性 |
| --- | --- | --- |
| `radar.0004_phase01r_formal_gate` | source 非空、identity_key、SourceVersion 应用标记、PublicationEvent 及最新事件 | 若存在 source 为空的旧公告则主动中止，不伪造来源/发布事件。 |
| `radar.0005_phase01r_source_admission` | 全局唯一别名、SourceAdmissionEvent、ApprovedApplicationHost | 不从旧布尔字段伪造准入事件。 |
| `radar.0006_phase01r_identity_evidence` | 严格分类、position_key、Evidence 强制关联版本/事件并增逐字段值 | 若发现无法证明的旧 Evidence 或 NoticePosition 则中止，不自动回填证据。 |

执行迁移前的当前 SQLite 核心表为空，因此三个前向迁移已安全应用。`makemigrations --check --dry-run` 确认模型与迁移一致。

## 最终新鲜验证

| 命令 | 真实结果 |
| --- | --- |
| `py -3.13 manage.py migrate` | 已成功应用 `radar.0004`–`0006`。 |
| `py -3.13 manage.py makemigrations --check --dry-run` | 退出 0，`No changes detected`。 |
| `py -3.13 manage.py check` | 退出 0，0 个 system-check 问题。 |
| `py -3.13 manage.py test radar.tests -v 2` | 退出 0，70/70 通过，耗时 2.085s。 |
| `py -3.13 manage.py import_source_catalog --path data/source_catalog.csv --dry-run` | 退出 0，`validated_rows=0 dry_run=true`，CSV 仍只有表头，无写入。 |
| `powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/install_daily_task.ps1)) \| Out-Null"` | 语法通过；未使用 `-Apply`，未注册任务。 |
| `powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/run_local.ps1)) \| Out-Null"` | 语法通过。 |

## 受控 demo HTTP 走查与清理

1. 执行 `py -3.13 manage.py load_local_demo`，输出 `local_demo_loaded=true notices=3 fixture=data/local_demo.json`。
2. 用 `py -3.13 manage.py runserver 127.0.0.1:8000 --noreload` 启动 Django 5.2.17 本地服务，system check 无问题。
3. 真实 HTTP 请求结果：
   - `/`、`/?status=expired`、`/?city=北京` 均为 200。
   - 默认页含 `demo-active` 且不含 `demo-expired`；历史筛选含 `demo-expired`；北京筛选含 `demo-active`。
   - 发现 13 个唯一 `data-column`，页面显示计划漏跑横幅和“未提供官方投递链接”。
   - POST `/notices/4/progress/` 服务端先返回 302，跟随重定向后为 200；数据库确认 `demo_progress=applied`。
4. Ctrl-C 中止开发服务；该人工中止导致进程退出码 1，不是应用失败。
5. 执行 `py -3.13 manage.py load_local_demo --remove`，输出 `local_demo_removed=true`。随后查询 Organization、OfficialSource、RecruitmentNotice、SourceVersion、PublicationEvent、Evidence、ApplicationProgress、SourceAdmissionEvent 和 demo UpdateRun，得到 `demo_counts=[0, 0, 0, 0, 0, 0, 0, 0, 0]`。

demo 只使用保留且不可连接的 `demo.invalid`，适配器固定为 `local_demo_disabled`。它显式创建本地 demo 准入链仅为走查 formal 门控，不代表真实来源获准。自动测试另确认 `--remove` 不会删除非 demo 数据。

## 文档与本地操作契约

- `docs/source-onboarding.md` 已记录 candidate-only 导入、状态迁移命令、官方网站/ATS 准入、公告 host 与投递 host 分离，以及别名冲突硬失败。
- `docs/runbooks/local-verification.md` 已记录最短本地验证、demo 加载/清理、HTTP 预期和 `positions_complete` 显式声明规则。
- `data/source_catalog.csv` 仍只有精确表头；`data/local_demo.json` 只是本地可清理演示 fixture，不会默认导入。

## 未做的外部操作和剩余风险

- 未对真实企业网页做任何网络请求、适配、证据核验、导入或启用；因此本轮不证明真实来源解析能力。
- 未执行 `scripts/install_daily_task.ps1 -Apply`；因此只验证了计划任务脚本语法和参数契约，没有验证真实 Windows Task Scheduler 运行。
- 未使用账号/Cookie，未发送通知，未自动投递，未云部署。
- 当前数据库原本为空，迁移对非空旧库采用“无法证明即中止”。如将来对其他非空数据库升级，需先人工处理报错的旧记录，不应绕过防护。
- 本轮已完成实施者自验，但尚未完成协调者要求的新一轮独立只读审查。
