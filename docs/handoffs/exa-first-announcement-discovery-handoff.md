# Exa-first 招聘公告候选发现交接

日期：2026-09-02  
状态：方案审查与设计决策已确认，尚未开始实现或真实 A/B
目标仓库：`E:\devlop\official-campus-radar`

## 1. 本交接的目的

把招聘雷达当前以 Codex CLI 为主要实时搜索入口的官网和 ATS 公告候选发现流程，调整为稳定、可观测、可批量执行的 Exa-first 流程：

1. 先回读已经准入的官网、公告源和 ATS；没有合格候选时，再调用 Exa API。
2. Exa 为空、有效候选不足、转载或非官方结果占主导、匹配困难，或者发生可降级的瞬时错误时，再调用 Codex CLI 扩展查询并排序候选。
3. 合并两路结果，统一做 URL 规范化、去重、来源记录、企业路由和安全校验。
4. 企业官网和官方 ATS 候选继续由招聘雷达已有的官方页面回读与来源准入流程核验；微信公众号搜索不进入本轮 Exa 改造。
5. Exa 或 Codex 返回的标题、摘要、排名、模型判断永远只是候选元数据，不能成为公告证据，也不能直接创建正式招聘批次。

这不是修改 Codex 自身的搜索方式，也不是修改 `wechat-oa`。本轮实现范围只属于招聘雷达的搜索编排和候选契约。

## 2. 当前实现事实

### 2.1 官网候选发现

当前 `radar/services/announcement_discovery.py` 在已知来源没有合格候选时启动：

```text
codex --search exec --ephemeral --sandbox read-only --output-schema ...
```

单企业模式把一个企业交给一次同步 Codex 进程；`--all` 模式先逐家检查已知来源，再把没有原始信号的企业集中放入一次 Codex Prompt。招聘雷达不能明确控制 Codex 实际执行多少条查询、每家公司返回多少搜索结果或是否并发。

本机 Codex CLI 的公开命令契约只保证 `--search` 启用原生 Responses `web_search`，不保证底层使用 Exa。即使某次 Agent 通过 Skill 或 MCP 选择了 Exa，也不能把这种临时决策作为招聘雷达的稳定搜索契约。

### 2.2 微信候选发现和核验

招聘雷达当前不会自行搜索微信公众号文章。操作者或外部 Agent 先产生 Candidate Batch，再由：

```text
import_wechat_oa_announcements
  → WeChatOAClient
  → wechat-oa discovery hydrate --input -
```

完成微信文章回读。Candidate Batch 不能授权浏览器；只有操作者显式添加 `--allow-browser` 才能把一次性浏览器许可传给 `wechat-oa`。

本轮已经确认 Exa 不搜索微信公众号文章，因此不因 Exa-first 修改 `wechat-oa` Candidate Batch 的 orchestrator/provider 契约。以后若要让招聘雷达组装微信 Candidate Batch，必须作为独立边界变更重新审查。

### 2.3 不变的领域边界

- 搜索结果是 `Announcement Candidate`，不是 `Recruitment Announcement`。
- `wechat-oa` 负责微信公众号 URL、文章原文、账号身份、图片、OCR/QR 和 Article/Media Evidence。
- 招聘雷达负责企业归属、招聘批次、岗位、届次、投递入口和正式数据准入。
- `wechat-oa` 不能核验企业官网或 ATS；官网/ATS 仍使用招聘雷达现有回读器和来源准入规则。
- 搜索摘要、模型结论、搜索排名和 OCR 未人工确认文本都不能提升为正式证据。

## 3. 目标流程

```text
Organization + admitted sources + explicit recruitment criteria
        │
        ▼
已知官网 / 公告源 / ATS 安全回读
        │
        ├─ 有合格候选 ─────────────────────────────┐
        │                                           │
        └─ 没有合格候选                            │
                         │                          │
                         ▼                          │
              Exa API（外部搜索首选）               │
                         │                          │
        ┌────────────────┴────────────────┐         │
        │                                 │         │
        ▼                                 ▼         │
有足够且可路由的候选          空/噪声/冲突/可降级错误 │
        │                                 │         │
        │                                 ▼         │
        │                      Codex CLI 条件兜底    │
        │                                 │         │
        └────────────────┬────────────────┘         │
                         ▼                          │
               规范化 + 去重 + 检索观察合并         │
                         │                          │
                         ▼                          │
                 官网 / 官方 ATS 安全回读            │
                         │                          │
                         └──────────────┬───────────┘
                                        ▼
                             招聘雷达领域判断与正式准入
```

任何分支都不得把搜索标题或摘要直接写成 `RecruitmentAnnouncement` 的证据字段。

## 4. Exa 外部搜索职责

Exa 是候选发现 Provider，不是证据 Provider。

每家公司至少应使用稳定、可测试的查询计划，包含：

- 企业法定名、常用名和招聘品牌名；
- 显式提供的招聘对象；
- `校园招聘`、`校招`、`秋招`、`春招`、`补录`、`实习` 等受控招聘术语；
- 已知企业官网域名、官方招聘系统域名；
- 必要的发布日期范围。

调用必须显式设置结果数量、超时和内容预算。默认只需要 URL、标题、发布日期提示和受限 highlights/snippet，不下载无界全文。

Exa 原始响应不能原样进入领域模型。必须先转换为内部的、受限的候选结构，至少包含：

```text
company
query
url
title_hint
backend_date_hint
provider = exa
rank
result_id
discovered_at
```

受限 `snippet` 只在当前运行的内存中用于排序，数据库最多保存其哈希和确定性信号判断；`backend_date_hint` 可以作为有长度上限的非证据提示保存。两者都不能成为发布日期、招聘对象或企业身份的最终证据。

## 5. Codex CLI 兜底条件

Codex 不再作为每次搜索的默认入口。编排先把一次检索目标固定为“企业 + 招聘对象 + 招聘类型 + 日期窗口”；只有至少一条候选通过 HTTPS/URL 安全检查、路由到已知或已准入官网/ATS、具有招聘语义、不是泛化招聘首页且没有明显范围冲突，该检索目标才算有足够结果。

Codex 只在下列情况调用：

1. Exa 成功但返回 0 条结果。
2. URL 规范化、去重和路由后没有满足上述条件的候选。
3. 结果主要来自聚合站、转载站或无法关联企业身份的第三方页面。
4. 没有候选同时满足企业别名和招聘语义信号。
5. 候选之间存在明显届次、项目或企业身份冲突，需要扩展查询。
6. Exa 遇到超时、429、5xx 或短暂网络连接失败，并且有限重试已经耗尽。

未知 ATS 只进入来源身份待审查队列，不算该检索目标的有效命中，因此不会阻止 Codex fallback。

以下情况不得静默降级，以免隐藏配置问题：

- Exa API Key 缺失、401 或 403；
- 请求结构或响应 schema 不兼容；
- 本地安全策略拒绝请求；
- 代码契约错误或无法识别的错误。

Codex 兜底输入只包含企业名称与批准别名、已知官方域名、显式招聘条件、规范化 URL、截断标题以及确定性的拒绝或冲突分类；不传 Exa 原始摘要、完整响应、错误对象、费用或请求头。Codex 输出继续受严格 JSON Schema、数量上限和字段白名单约束，Provider 固定记录为 `codex_web_search`，不能接受模型自报来源。

## 6. 候选合并与 URL 分流

合并规则必须确定且可测试：

1. 同时保留实际访问用的 `fetch_url` 和只用于候选身份的 `identity_url`；后者只规范 scheme/host、IDN、默认端口、fragment 和明确追踪参数，保留功能性查询参数与路径大小写。
2. 同一规范 URL 只保留一个候选实体，但保留所有 provider observation。
3. Provider 不能伪造另一个 Provider 的排名或 result ID。
4. 相同标题但 URL 不同不能仅凭标题合并。
5. 官网/ATS URL 必须通过现有 HTTPS、SSRF、企业域名和来源准入边界；拒绝 userinfo、非 HTTPS 和非 443 端口。
6. 未知 ATS 可以保存为来源身份待审查候选，但不得自动回读或进入正式核验队列；聚合站和转载站只保留拒绝分类与计数。

内部 Candidate Batch schema v2 把一个候选实体与多条追加式检索观察分开表达；每条观察保留 query、Provider、rank、result ID 和发现时间。旧 schema v1 继续只读兼容，并在导入时转换为一个候选和一条观察；新输出只生成 v2，不能用 v1 覆盖已经存在的多来源记录。

建议把候选的“发现来源”和“证据来源”分开记录：

- `discovery_provenance`：Exa/Codex 查询、排名和结果 ID；
- `evidence_provenance`：招聘雷达官方页面回读结果。

前者不能代替后者。

## 7. 并发、资源和失败策略

- 并发发生在“公司级 Exa 搜索”，默认并发 2；SQLite 写入仍在主线程按企业顺序执行。
- 每批默认最多 8 家，每家公司最多 4 条 Exa 查询、每条 10 个结果、合并前 40 个结果；批次总时限 10 分钟。
- Exa 连接超时 5 秒、读取超时 20 秒；429/5xx 最多重试 1 次，`Retry-After` 最多等待 10 秒。
- 每批最多 3 家触发 Codex，每家公司最多调用 1 次且超时 180 秒；禁止把所有未命中企业重新塞入一个大 Prompt。
- 批次状态使用 `complete/partial/failed`，企业状态使用 `complete/degraded/failed`，Provider 调用状态使用 `success/empty/transient_error/permanent_error/skipped`。Exa 失败但 Codex 补齐仍是 `degraded`，批次为 `partial`。
- 不自动访问二维码载荷、搜索摘要中的链接或文章外链。

## 8. 密钥与配置安全

直接 Exa API 需要新的运行时凭据边界：

- 只从安全的运行时配置读取 `EXA_API_KEY`；不得写入数据库、Candidate Batch、日志、命令参数、测试 fixture、文档或 Git。
- 日志只记录 Provider、请求 ID、状态、延迟、结果数、费用字段和稳定错误分类。
- HTTP 客户端固定到 Exa 官方 HTTPS API 主机与允许路径，不接受候选内容修改 API 目标；禁用自动重定向、Cookie、`.netrc` 和隐式系统代理，并限制解压后的响应大小。
- `EXA_API_KEY` 只在创建专用 Exa 客户端时读取；启动 Codex、`wechat-oa` 或浏览器子进程时必须从子进程环境显式移除。
- 不打印请求头、环境变量或完整异常对象中的凭据。
- 测试使用注入的 fake transport/runner，不执行真实 Exa、Codex、WeChat 或 Chrome。
- `--allow-live-search` 只授权 Exa，`--allow-codex-fallback` 单独授权 Codex，`--record` 单独授权候选与观察写库；官网原文回读继续使用独立 live-fetch 授权。配置了 API Key 不能自动获得任何联网权限。

## 9. 建议实现分层

以下是职责建议，不要求机械照搬文件名：

1. `ExaDiscoveryClient`
   - 固定 API 主机、鉴权、超时、有限重试、响应上限和错误分类；
   - 返回纯搜索 observation，不返回领域证据。
2. `AnnouncementSearchPlanner`
   - 根据企业别名、届次、已知域名和候选类型生成稳定查询；
   - 不持有密钥，不做网络请求。
3. `AnnouncementDiscoveryOrchestrator`
   - Exa-first；判断是否触发 Codex；合并、去重、分流和汇总 partial 状态。
4. 现有 Codex adapter
   - 保留为 fallback；收窄到受控的扩展搜索和排序职责。
5. 现有官网 probe/admission
   - 继续核验官网/ATS，不复制 `wechat-oa` 功能。

## 10. 测试要求

实现必须测试至少以下行为：

### Exa 客户端

- API Key 缺失、无效和不泄漏；
- 成功、空结果、超时、429、5xx、无效 JSON、未知字段和超大响应；
- 固定 API 主机、HTTPS、超时、重试上限；
- 结果数和内容字符预算；
- 请求 ID、费用和错误分类的安全记录。
- Codex、`wechat-oa` 与浏览器子进程环境中不存在 `EXA_API_KEY`。

### 编排

- Exa 有合格候选时不启动 Codex；
- Exa 空、噪声过高或难匹配时只启动一次受控 fallback；
- 配置/契约错误不静默 fallback；
- Exa 与 Codex 重复 URL 合并且保留两路 provenance；
- 多企业隔离、受控并发、单企业失败和批次 partial；
- 官网、已知 ATS、未知 ATS、转载和恶意 URL 的确定性分流。

### 证据边界

- Exa/Codex 摘要不能成为公告正文、发布日期、招聘对象或企业身份证据；
- 官网/ATS 候选必须经过原文回读和来源准入；
- Candidate Batch 不能携带浏览器、凭据或文件路径授权。

### 命令和兼容

- 未提供 `--allow-live-search` 时真实 Exa/Codex 调用数为 0；
- 未提供 `--allow-codex-fallback` 时 Codex 调用数为 0；
- 未提供 `--record` 时数据库写入数为 0；
- 现有离线 `--input` 路径保持可用，但默认只预演；
- 批量选择优先使用可重复的 `--organization` 或冻结的 `--batch-file`；兼容 `--all` 时必须同时提供 `--max-companies`，超出上限直接拒绝；
- 旧候选和已有数据库记录不需要 destructive migration；
- JSON 输出稳定且不混入诊断文本。

## 11. 验收指标

先用固定企业和已知公告构建离线/人工批准的基准集，再决定是否替换默认路径。至少记录：

- `recall@10` / `recall@20`；
- 官方候选 `precision@10` 和首个正确候选排名；
- 重复率和转载/聚合站比例；
- 可安全回读率；
- Exa 单公司延迟与费用；
- Codex fallback 触发率、成功补充率和额外耗时；
- 最终证据核验通过率；
- 无证据候选误入正式数据的数量，必须为 0。

基准真值由人工冻结，逐项记录企业、招聘对象、招聘类型、已核验官方 URL 身份、入口类别、标注证据和确认时间；重定向到同一已核验最终 URL 的结果视为同一正确候选。建议用 Exa-only、Codex-only、Exa-first + Codex fallback 三组运行同一基准集。首批冻结 12 家：腾讯、理想汽车、美的集团、OPPO，以及一汽-大众、东风日产、中国中车、亚马逊中国、广汽丰田、携程、网易、苹果中国。初始硬预算为 Exa 最多 48 次请求、Codex-only 最多 12 次、组合方案最多 3 次 Codex fallback。指标按“企业 + 检索目标”做宏平均；没有基准数据前，不凭主观感觉宣称 Exa 或 Codex 的召回率更高。

## 12. 非目标

- 不修改 `wechat-oa` 搜索、文章回读、验证码、OCR、二维码或 Evidence 实现。
- 不使用 Exa 搜索微信公众号文章，也不修改 `wechat-oa` Candidate Batch orchestrator/provider 契约。
- 不绕过微信验证码，不自动操作可见浏览器。
- 不把 Brave Direct Discovery 加入招聘雷达本轮默认路径。
- 不实现自动入库、自动发布、自动创建招聘批次或自动确认投递入口。
- 不读取或迁移用户浏览器 Cookie。
- 不在本交接阶段新增依赖、配置、数据库迁移、代码或测试。

## 13. 建议实施顺序

实现任务开始后，每一步先写失败测试，再写最小实现：

1. 冻结内部搜索 observation 和错误分类契约。
2. 实现纯 Exa 客户端及 fake transport 测试。
3. 实现稳定查询计划和候选规范化/去重。
4. 把现有 Codex 搜索收窄为 fallback。
5. 增加 URL 分流、未知 ATS 身份待审查状态和追加式检索观察。
6. 接入管理命令的显式 live-search 授权与 partial 汇总。
7. 完成离线完整回归。
8. 用户另行授权后，使用冻结的 12 家基准集做真实 Exa/Codex 验收。
9. 数据证明达到门槛后，再决定是否设为生产默认。

## 14. 已确认的设计决策与剩余授权

新任务先阅读本文件、仓库根目录 `AGENTS.md`、`CONTEXT.md`、`DEV_STATE.md`、`docs/adr/0005-official-announcement-driven-recruitment.md`、`docs/adr/0007-wechat-first-primary-announcement.md` 和 `docs/runbooks/wechat-oa-integration.md`。

2026-09-02 的方案审查已确认：已知来源优先、官网/ATS 外部发现采用 Exa-first、Codex 仅条件兜底、微信与 Brave 不进入本轮、候选与追加式检索观察分离、搜索条件显式提供、各类联网和写库权限分开、旧 schema v1 只读兼容、新输出使用 v2、按企业原子写入，并采用本文件的初始资源上限和冻结基准集。

本次确认只授权记录设计，不授权业务代码、数据库迁移应用或任何真实 Exa/Codex/WeChat/Chrome 调用。实现开始、真实 A/B、生产默认切换仍分别需要用户明确授权。

## 15. 新任务启动指令

```text
先阅读 ADR 0008、docs/handoffs/exa-first-announcement-discovery-handoff.md 以及其中列出的项目文档。除非用户明确回复“开始实现”，不要写业务代码、应用迁移或执行真实 Exa、Codex、WeChat、Chrome 调用；真实 A/B 和生产默认切换还需要各自单独授权。
```
