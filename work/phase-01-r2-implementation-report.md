# Phase 01-R2 实施事实报告

日期：2026-08-18

## 结论与边界

Phase 01-R2 brief 的 A/B/C/D 四组缺陷修复已实施并完成实施者自验。最后一轮完整测试为 95/95，通过本机 `127.0.0.1` 的受控 demo “加载 → 页面立即更新 → 清理”验证后，demo 关联记录为零、sentinel 保留；sentinel 随后也单独移除，当前数据库核心表均为空。

本报告只陈述实施和验证事实，不代表阶段放行；仍等待协调者安排独立只读审查。

全程未初始化 Git、创建 worktree/提交，未访问、导入或启用真实企业来源，未注册 Windows 计划任务，未使用账号/Cookie，未自动投递，未发送消息，未部署云端，也未新增依赖。

## TDD 红灯与绿灯

每组均先运行只覆盖缺陷反例的测试并确认旧行为失败，再做最小根本修复。

| 组 | 红灯命令与事实 | 绿灯命令与事实 |
| --- | --- | --- |
| A 准入链、host、启用配置 | `py -3.13 manage.py test radar.tests.test_phase01r2_group_a_admission_chain -v 2`：首轮 7 项为 6 failed + 1 error；暴露断链/过期事件仍被信任、跨 source/event 可展示、host 可改写、启用不验 parser、demo adapter 未注册。可信性复查再加 3 项，旧行为 3/3 failed，证明非空事件文本和 host 证据可被改写。 | 首轮 7/7；追加链哈希与批准摘要后最终 10/10。 |
| B 投影值、证据、分类 | `py -3.13 manage.py test radar.tests.test_phase01r2_group_b_evidence_classification -v 2`：7/7 failed；标题/岗位/链接篡改和错误 hash 仍展示，候选证据错配仍发布，分类只看 type，HTML 为缺失节点生成伪 locator。 | 7/7。 |
| C 身份、生命周期、历史 | `py -3.13 manage.py test radar.tests.test_phase01r2_group_c_identity_lifecycle_history -v 2`：5/5 failed；完整页面只剩杭州时旧北京岗位仍在，identity/URL 冲突被覆盖，空白 identity 创建重复，数据库允许同源 URL 重复，撤回历史不可查。 | 5/5。 |
| D demo 所有权与离线测试 | `py -3.13 manage.py test radar.tests.test_phase01r2_group_d_demo_offline -v 2`：3 项中 2 failed；同 `demo.invalid` sentinel 被宽泛删除，测试配置未阻断未 mock 请求。 | 3/3；同时验证 suspended 来源不解析 adapter。 |

四组完成后的第一次全量回归为 92 项中 3 failed + 5 errors，均来自旧测试 fixture 不满足新的完整 parser 准入契约，或旧断言与新的 URL 冲突规则不一致；修正 fixture 和断言后 92/92。追加 A 组篡改检测后，最终为 95/95。没有删除测试、削弱证据断言或屏蔽错误。

## 关键变更

### A. 当前有效准入链

- `source_is_admitted()`、正式查询和采集共享 fail-closed 准入判断：重放完整事件序列，校验合法连续跃迁、当前 terminal、`is_verified/is_active`、actor/reason/evidence 和链式 SHA-256 哈希。
- `SourceAdmissionEvent` 直接断链追加会失败；普通模型保存不可修改，QuerySet 改写任意非空事实会导致链哈希不匹配。
- `ApprovedApplicationHost` 校验 source/event 一致、verified event、host/actor/evidence 非空，保存后不可修改；消费者重算批准摘要并确认事件仍属于有效链。
- HTML 来源从 `verified → enabled` 前必须满足完整 parser contract。`local_demo_disabled` 是注册过的显式离线 adapter，只返回 `not_modified`，绝不联网。
- 正式查询校验 `PublicationEvent.notice`、`SourceVersion.source`、公告 source 和有效准入链一致。

### B. 投影值与逐字段证据

- 新增共享证据服务，把候选和已持久化投影绑定到实际值、非空原文、精确 locator、规范化 parsed value 和 SHA-256 value hash。
- 标题、分类、对象、发布日期、截止日期、公告 URL、每个当前岗位名/地点和每个当前投递 URL 均逐值检查；Evidence 必须属于当前 version/event/notice 及对应 position/link。
- `formal()` 不再信任 `evidence_complete` 或“存在一条 Evidence”；投影或 Evidence 被改写会立即停止展示。
- HTML 节点或稳定 identity 缺失时不再拼装容器级 locator；缺字段只会造成证据不完整和拒绝发布。
- 分类同时检查 type、公告标题、岗位标题和节点原文；招商、招标、采购、招聘会新闻等否定信号优先。

### C. 身份、生命周期与历史

- 发布前先计算目标城市岗位。已有可信公告在 `positions_complete=True` 且目标岗位为零时写 `out_of_scope`，即使页面仍含杭州岗位，也停用旧岗位/链接且不改个人进度。
- 每个候选同时查 `(source, trimmed identity_key)` 和 `(source, canonical official_notice_url)`；冲突只写 `ambiguous`，不创建、不覆盖、不下线旧投影。
- 模型和迁移增加 `(source, official_notice_url)` 唯一约束。迁移发现空白/未规范 identity、不可信 URL 或重复规范 URL 会中止，不合并或回填历史。
- 当前列表继续只用 `formal()`；`expired/withdrawn` 使用独立 `historical()`，要求来源曾有有效 enabled 链，并重新验证此前完整 published/updated event 的逐字段证据。来源后来 revoked 也不会抹掉可信历史。

### D. demo 所有权与零联网

- `OfficialSource` 和 `UpdateRun` 增加 `local_demo_key`。demo 加载、立即更新和初始运行记录都使用同一精确 ownership；清理不再按 `official_domain` 模糊匹配。
- 清理按关联顺序删除 demo Evidence/岗位/链接/事件/版本/FetchRun/UpdateRun/准入链/来源/组织，保留所有非 demo sentinel。
- `radar.tests` 初始化时替换 `requests.Session.request` 为 fail-fast guard；现有需要 HTTP 行为的测试均 mock `Session.get`，未 mock 出站会立即抛出 `RuntimeError`。

## 前向迁移

| 迁移 | 内容 | 历史安全边界 |
| --- | --- | --- |
| `0007_phase01r2_notice_url_identity` | 同源规范公告 URL 唯一约束 | 先扫描 identity/HTTPS/同 host/规范 URL/重复；任何问题都中止。 |
| `0008_phase01r2_demo_ownership` | 来源和更新运行的 demo ownership 字段 | 空字符串代表非 demo，不按域名推断。 |
| `0009_phase01r2_audit_chain_hashes` | 准入事件前序哈希、事件哈希、host 批准摘要 | 若存在任何未哈希准入事件或 host 批准记录则中止，绝不伪造哈希历史。 |

执行前数据库核心表计数为 `[0, 0, 0, 0, 0, 0, 0, 0, 0, 0]`；`0007`–`0009` 已应用。`makemigrations --check --dry-run` 确认模型与迁移一致。

## 最终新鲜验证

| 命令 | 结果 |
| --- | --- |
| `py -3.13 manage.py makemigrations --check --dry-run` | 退出 0，`No changes detected`。 |
| `py -3.13 manage.py check` | 退出 0，0 个 system-check 问题。 |
| `py -3.13 manage.py test radar.tests -v 2` | 退出 0，95/95，通过，耗时 1.960s。 |
| `powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/install_daily_task.ps1)) \| Out-Null"` | 退出 0，只做语法解析，未使用 `-Apply`。 |
| `powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/run_local.ps1)) \| Out-Null"` | 退出 0，只做语法解析。 |
| `py -3.13 manage.py import_source_catalog --path data/source_catalog.csv --dry-run` | 退出 0，`validated_rows=0 dry_run=true`。 |

## demo 加载 → 立即更新 → 清理

1. 创建同域组织 sentinel 与独立 UpdateRun sentinel，记录 ID 为 `6`、`3`。
2. `py -3.13 manage.py load_local_demo` 输出 `local_demo_loaded=true notices=3 fixture=data/local_demo.json`。
3. 以 `py -3.13 manage.py runserver 127.0.0.1:8000 --noreload` 启动本地服务，system check 为 0 问题。
4. 真实 HTTP：`/`、`/?status=expired`、`/?city=北京` 和 POST `/update-now/` 跟随重定向后均为 200；默认页含 active 不含 expired，历史页含 expired，北京筛选含 active，页面有 13 个唯一列，更新反馈为“手动更新完成”。
5. 点击后数据库为 `demo_update_runs=2`、`demo_fetch_runs=1`、`not_modified=1`，两个 sentinel 均仍为 1。
6. Ctrl-C 停止开发服务；退出码 1 来自人工中止，不是应用失败。
7. `load_local_demo --remove` 后 demo organization/source/notice/version/event/evidence/fetch/update/admission 计数均为 0，两个 sentinel 均仍为 1。
8. 单独删除 sentinel 后，Organization、OfficialSource、RecruitmentNotice、UpdateRun、FetchRun、SourceVersion、PublicationEvent、Evidence、ApplicationProgress、SourceAdmissionEvent、ApprovedApplicationHost 最终计数均为 0。

## 未做的外部操作与剩余边界

- 未访问或验证任何真实企业网页，因此不证明真实来源可解析或已获准。
- 未执行 `scripts/install_daily_task.ps1 -Apply`，因此没有注册或真实运行 Windows 计划任务。
- 未使用账号、Cookie、验证码、代理或自动投递；未发送通知、未部署云端。
- 迁移策略对非空旧审计历史明确 fail-closed。若未来把其他数据库升级到本版本，必须人工审阅并处理报错，不能跳过保护或补造哈希。
- 实施者自验已完成，但独立只读审查尚未进行；本报告不宣布 Phase 01-R2 放行。
