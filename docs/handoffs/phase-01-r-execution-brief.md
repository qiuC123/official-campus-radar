# Execution Brief — Phase 01-R 证据与生命周期一致性修复

状态：已完成；其后续放行边界和剩余风险以 `DEV_STATE.md` 与 Phase 01 handoff 为准。

## 目标与外部边界

继续使用 Django、SQLite、本地单用户和离线 fixture。它不是新产品阶段，也不增加外部权限。不得访问或启用真实企业来源、注册 Windows 任务、使用账号/Cookie、自动投递、云部署、初始化 Git 或创建提交。

目标是让“正式列表中的每一条招聘信息都来自已启用的官方来源，并能回溯到一次不可变页面版本和逐字段证据”成为模型和服务无法绕过的不变量。当前数据库没有正式来源、公告或演示数据；可做前向迁移，但绝不伪造历史可信性。

## 不变量

1. 默认正式列表绝不展示没有来源、来源未启用、没有已提交发布事件、没有完整必需证据或来源已经撤销准入的公告。
2. CSV 只创建候选来源；`candidate → verified → enabled → suspended/revoked` 是追加式、可审计状态迁移。`verified` 不可采集或发布。
3. 新公告没有稳定身份、分类不是明确校招/实习、没有目标城市证据或字段证据不完整时，只生成内部拒绝事件，绝不进入正式列表。
4. 投递链接可缺失；一旦展示，必须通过来源同 host 或经官方入口证据批准的投递 host 校验。公告 host 与投递 host 分开管理。
5. 同一个来源页的一次已应用更新，必须原子写入页面版本、全部候选决定、公告/岗位/链接/证据和生命周期变更；中途任一失败时不留下半页版本或正式投影。
6. 仅与该来源最近一次已应用版本比较 hash。连续同 hash 才是 unchanged；A→B→A 必须成为第三次已应用变化。
7. 身份冲突、解析覆盖不完整、来源失败或请求异常，不得自动撤回、过期或删除既有正式数据。
8. 已有公告撤回、或完整覆盖下目标岗位移除时，即使新页没有地点，也必须安全停止展示旧岗位；新公告准入和已有公告生命周期更新必须分流。
9. 采集、发布和生命周期代码绝不改写 `ApplicationProgress`。
10. 审计对象、更新运行和正式采集投影不能从 Django Admin 直接增改删；个人投递进度是唯一可直接编辑的个人状态。

## 最小模型与关系

保留已应用迁移，只增加前向迁移。可选择等价字段名，但不得弱化以下关系：

```text
Organization ─┬─ OrganizationAlias (normalized_alias 全局唯一)
              └─ OfficialSource
                   ├─ SourceAdmissionEvent (追加式状态迁移)
                   │    └─ ApprovedApplicationHost (官网外链证据)
                   └─ SourceVersion
                        └─ PublicationEvent (published/updated/rejected/withdrawn/out_of_scope/ambiguous)
                             ├─ RecruitmentNotice (source 非空，identity_key)
                             │    ├─ NoticePosition (position_key, is_current)
                             │    └─ ApplicationLink (is_current)
                             └─ Evidence (version、event、主体、字段、摘录、locator、value hash)
```

- `RecruitmentNotice.source` 必须非空，唯一身份为 `(source, identity_key)`；不得依赖 URL fragment 或 DOM 顺序。
- `PublicationEvent` 是不可变决定记录，可代表被拒绝候选而没有正式公告。
- `Evidence` 必须关联具体 `SourceVersion` 和 `PublicationEvent`，不得用 `update_or_create` 覆盖历史。
- 发现无法映射到可信来源的旧记录时，迁移必须停下要求人工处理；当前空库不得默认创建可信来源或回填证据。
- 别名冲突必须硬失败，不能取第一个。实际招聘主体继续独立展示；父子关系不得自动合并不同主体。

## 数据与服务契约

### 来源准入与 host

- `import_source_catalog` 只导入 candidate，不能携带自动启用语义。
- 提供受审计的本地服务或管理命令完成核验、启用、暂停、撤销，记录操作者标签、时间、理由和证据；管理员不得直接改写审计记录。
- 采集来源公告 host、同源公告 host 和外部投递 host 分别校验。ATS 只有具有官网入口证据时才可批准。

### 身份、分类与证据

- 适配器必须提供稳定公告 ID，或规范公告 URL 加稳定节点 ID；没有稳定 ID 不发布。
- 页面内规范 URL/稳定 ID 冲突、同 URL 仅靠 fragment 区分、或相同 ID 内容冲突时，写 `ambiguous`/rejected 事件，不合并、不覆盖、不下线旧数据。
- 招聘分类至少包含 `campus_recruitment`、`internship`、`other`、`unknown`；仅前两类可创建新公告。不得以文本包含“招”作为充分条件，测试必须涵盖招商、招标、招聘会新闻等反例。
- 每个正式显示字段均有与 `SourceVersion`、`PublicationEvent` 关联的不可变证据：标题、分类、对象、发布日期、截止日期、公告 URL、岗位名、地点和投递链接分别记录原文摘录、精确 locator、解析值或原始 href、value hash。`evidence_excerpt` 若保留，只能是上下文，不能替代逐字段证据。

### 整页更新与生命周期

1. 在事务外抓取和解析整页，完成节点身份冲突检查。
2. 以一页来源为事务边界：在一个数据库事务内锁定来源、比较最近已应用 hash、写 SourceVersion、所有 PublicationEvent、所有投影/证据/生命周期和成功 FetchRun。
3. 写入失败时整体回滚；随后用短事务仅写一条安全脱敏的失败 FetchRun。下次同 hash 必须可以重试。
4. 新公告的目标城市/完整证据门槛不适用于已有公告的明确撤回或完整覆盖下的下线；后者必须停止展示旧岗位/链接，但保留历史。
5. 页面上不见某公告不等于撤回；来源失败、解析不完整、身份冲突不得下线既有数据。
6. `partial_failure` 与成功、失败、漏跑是不同事实；页面显示来源降级摘要。手动刷新不能掩盖错过的 22:00 计划执行。

## 实施者文件所有权

唯一实施者可修改：

```text
requirements.txt
manage.py
campus_radar/ 下的文件
radar/ 下的文件（含迁移、测试、fixture）
scripts/ 下的文件
data/ 下的文件
docs/runbooks/ 下的文件
docs/source-onboarding.md
work/phase-01-r-implementation-report.md
```

协调者保留：`DEV_STATE.md`、`docs/handoffs/**`、`docs/PROJECT_DEVELOPMENT_SPEC.md`、`docs/superpowers/**`。

## TDD 验收顺序

每组都必须先确认最小测试在旧行为下失败，再实现并确认该组通过；不得先堆测试最后统一修改。

1. 正式列表门控、不可空 source、发布事件及 Admin 不可改删。
2. 来源候选/核验/启用状态迁移、host 信任链、别名冲突。
3. 招聘分类、稳定节点身份/冲突拒绝、逐字段证据。
4. 整页事务、连续 hash 与 A→B→A、失败单一记账和可重试。
5. 新公告准入和已有公告撤回/岗位移除的分流、个人进度隔离。
6. 当前岗位关键词查询、partial failure 健康提示、漏跑/手动更新的事实反馈、错误信息脱敏。
7. 离线 demo fixture 和 runbook：只生成本地示例数据、验收后清理，绝不默认自动导入。

最终必须新鲜运行：

```powershell
py -3.13 manage.py makemigrations --check --dry-run
py -3.13 manage.py check
py -3.13 manage.py test radar.tests -v 2
powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/install_daily_task.ps1)) | Out-Null"
powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/run_local.ps1)) | Out-Null"
```

还要用受控 demo 做本地浏览器或 HTTP 走查后清理数据。事实报告须列实际命令、红绿测试、真实结果和未执行的外部操作。完成后由协调者发起新的只读审查；实施者不得自行宣布可进入下一阶段。
