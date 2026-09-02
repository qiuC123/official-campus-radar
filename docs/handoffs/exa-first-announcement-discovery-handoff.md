# Exa-first 招聘公告候选发现交接

日期：2026-09-02  
状态：仅完成方案交接，尚未开始实现  
目标仓库：`E:\devlop\official-campus-radar`

## 1. 本交接的目的

把招聘雷达当前以 Codex CLI 为主要实时搜索入口的公告候选发现流程，调整为稳定、可观测、可批量执行的 Exa-first 流程：

1. 默认直接调用 Exa API 获取公告候选。
2. Exa 为空、有效候选不足、转载或非官方结果占主导、匹配困难，或者发生可降级的瞬时错误时，再调用 Codex CLI 扩展查询并排序候选。
3. 合并两路结果，统一做 URL 规范化、去重、来源记录、企业路由和安全校验。
4. 微信公众号候选交给 `wechat-oa` 核验；企业官网和官方 ATS 候选继续由招聘雷达已有的官方页面回读与来源准入流程核验。
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

`radar/services/wechat_oa_client.py` 当前把 Candidate Batch 的 `source.orchestrator` 写死为 `codex`。Exa-first 后应改为准确描述组装方，例如 `official-campus-radar`；`providers` 和每条候选的 `search_provenance.provider` 则记录实际检索来源，例如 `exa` 或 `codex_web_search`。`wechat-oa` 的 schema v1 已接受安全标识符形式的 orchestrator，不需要为此修改 WeChat OA。

### 2.3 不变的领域边界

- 搜索结果是 `Announcement Candidate`，不是 `Recruitment Announcement`。
- `wechat-oa` 负责微信公众号 URL、文章原文、账号身份、图片、OCR/QR 和 Article/Media Evidence。
- 招聘雷达负责企业归属、招聘批次、岗位、届次、投递入口和正式数据准入。
- `wechat-oa` 不能核验企业官网或 ATS；官网/ATS 仍使用招聘雷达现有回读器和来源准入规则。
- 搜索摘要、模型结论、搜索排名和 OCR 未人工确认文本都不能提升为正式证据。

## 3. 目标流程

```text
Organization + known official hosts + current recruitment criteria
        │
        ▼
Exa API（默认、每家公司独立、受控并发）
        │
        ├─ 有足够且可路由的候选 ─────────────┐
        │                                      │
        └─ 空/噪声过高/难匹配/可降级错误       │
                         │                     │
                         ▼                     │
              Codex CLI 条件兜底               │
              扩展查询 + 候选排序              │
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                  规范化 + 去重 + provenance 合并
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
          mp.weixin.qq.com/s/...            官网 / 官方 ATS
                    │                               │
                    ▼                               ▼
        wechat-oa Candidate Batch          官方页面回读 / 来源准入
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
                       招聘雷达领域判断与正式准入
```

任何分支都不得把搜索标题或摘要直接写成 `RecruitmentAnnouncement` 的证据字段。

## 4. Exa 默认搜索职责

Exa 是候选发现 Provider，不是证据 Provider。

每家公司至少应使用稳定、可测试的查询计划，包含：

- 企业法定名、常用名和招聘品牌名；
- 当前届次；
- `校园招聘`、`校招`、`秋招`、`春招`、`补录`、`实习` 等受控招聘术语；
- 已知企业官网域名、官方招聘系统域名；
- 微信候选使用严格的 `mp.weixin.qq.com/s/` 范围；
- 必要的发布日期范围。

调用必须显式设置结果数量、超时和内容预算。默认只需要 URL、标题、发布日期提示和受限 highlights/snippet，不下载无界全文。

Exa 原始响应不能原样进入领域模型。必须先转换为内部的、受限的候选结构，至少包含：

```text
company
query
url
title_hint
snippet
backend_date_hint
provider = exa
rank
result_id
discovered_at
```

`snippet` 和 `backend_date_hint` 都只能用于排序或决定是否回读，不能成为发布日期、招聘对象或企业身份的最终证据。

## 5. Codex CLI 兜底条件

Codex 不再作为每次搜索的默认入口，只在下列情况调用：

1. Exa 成功但返回 0 条结果。
2. URL 规范化、去重和路由后没有候选。
3. 结果主要来自聚合站、转载站或无法关联企业身份的第三方页面。
4. 没有候选同时满足企业别名和招聘语义信号。
5. 候选之间存在明显届次、项目或企业身份冲突，需要扩展查询。
6. Exa 遇到超时、限流或服务端瞬时错误，并且错误策略允许降级。

以下情况不得静默降级，以免隐藏配置问题：

- Exa API Key 缺失或无效；
- 请求结构或响应 schema 不兼容；
- 本地安全策略拒绝请求；
- 代码契约错误。

Codex 兜底输入可以包含已经脱敏、受限的 Exa 候选元数据，允许它扩展查询和排序，但不能让它把摘要改写为证据。Codex 输出继续受严格 JSON Schema、数量上限和字段白名单约束。

## 6. 候选合并与 URL 分流

合并规则必须确定且可测试：

1. 先按现有 `canonicalize_url` 规范化。
2. 同一规范 URL 只保留一个候选实体，但保留所有 provider observation。
3. Provider 不能伪造另一个 Provider 的排名或 result ID。
4. 相同标题但 URL 不同不能仅凭标题合并。
5. 微信 URL 只接受 HTTPS、精确主机 `mp.weixin.qq.com`、受支持的 `/s` 文章路径、无 userinfo。
6. 官网/ATS URL 必须通过现有 HTTPS、SSRF、企业域名和来源准入边界。
7. 聚合站和转载站可以保留为拒绝/诊断计数，但不能进入正式核验队列。

建议把候选的“发现来源”和“证据来源”分开记录：

- `discovery_provenance`：Exa/Codex 查询、排名和结果 ID；
- `evidence_provenance`：`wechat-oa` Article Evidence 或招聘雷达官方页面回读结果。

前者不能代替后者。

## 7. 并发、资源和失败策略

- 并发发生在“公司级搜索”，不是无界启动 Codex 子进程。
- Exa 使用小规模固定并发，具体默认值在实现前通过测试和 API 限额确定；必须有全批次上限。
- 同一公司内部的查询数量、结果数量和内容字符预算都必须有上限。
- 429 尊重服务端重试提示，只允许有限重试；禁止无限退避。
- 单公司失败不能污染其他公司的结果；批次结果必须明确 `partial`。
- Codex 兜底应设置单公司或小批次上限，避免再次把所有未命中企业塞入一个不可观测的大 Prompt。
- 不自动访问二维码载荷、搜索摘要中的链接或文章外链。

## 8. 密钥与配置安全

直接 Exa API 需要新的运行时凭据边界：

- 只从安全的运行时配置读取 `EXA_API_KEY`；不得写入数据库、Candidate Batch、日志、命令参数、测试 fixture、文档或 Git。
- 日志只记录 Provider、请求 ID、状态、延迟、结果数、费用字段和稳定错误分类。
- HTTP 客户端固定到 Exa 官方 HTTPS API 主机，不接受候选内容修改 API 目标。
- 不打印请求头、环境变量或完整异常对象中的凭据。
- 测试使用注入的 fake transport/runner，不执行真实 Exa、Codex、WeChat 或 Chrome。
- 真实搜索必须继续由显式 `--allow-live-search` 或等价控制授权，不能因为配置了 API Key 就自动联网。

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
5. 现有 `WeChatOAClient`
   - 继续只 hydrate 微信 Candidate Batch；更新 orchestrator/provider 契约，不添加搜索或证据判断。
6. 现有官网 probe/admission
   - 继续核验官网/ATS，不复制 `wechat-oa` 功能。

## 10. 测试要求

实现必须测试至少以下行为：

### Exa 客户端

- API Key 缺失、无效和不泄漏；
- 成功、空结果、超时、429、5xx、无效 JSON、未知字段和超大响应；
- 固定 API 主机、HTTPS、超时、重试上限；
- 结果数和内容字符预算；
- 请求 ID、费用和错误分类的安全记录。

### 编排

- Exa 有合格候选时不启动 Codex；
- Exa 空、噪声过高或难匹配时只启动一次受控 fallback；
- 配置/契约错误不静默 fallback；
- Exa 与 Codex 重复 URL 合并且保留两路 provenance；
- 多企业隔离、受控并发、单企业失败和批次 partial；
- 微信、官网、ATS、转载和恶意 URL 的确定性分流。

### 证据边界

- Exa/Codex 摘要不能成为公告正文、发布日期、招聘对象或企业身份证据；
- 微信候选必须经过 `wechat-oa` Article Evidence；
- 官网/ATS 候选必须经过原文回读和来源准入；
- Candidate Batch 不能携带浏览器、媒体分析、凭据或文件路径授权；
- `orchestrator=official-campus-radar` 和实际 providers 可通过 `wechat-oa` schema v1。

### 命令和兼容

- 未提供 `--allow-live-search` 时真实 Exa/Codex 调用数为 0；
- 现有离线 `--input` 路径保持可用；
- 旧候选和已有数据库记录不需要 destructive migration；
- JSON 输出稳定且不混入诊断文本。

## 11. 验收指标

先用固定企业和已知公告构建离线/人工批准的基准集，再决定是否替换默认路径。至少记录：

- `recall@10` / `recall@20`；
- 官方候选精确率；
- 微信候选可回读率；
- 重复率和转载/聚合站比例；
- Exa 单公司延迟与费用；
- Codex fallback 触发率、成功补充率和额外耗时；
- 最终证据核验通过率；
- 无证据候选误入正式数据的数量，必须为 0。

建议用 Exa-only、Codex-only、Exa-first + Codex fallback 三组运行同一基准集。没有基准数据前，不凭主观感觉宣称 Exa 或 Codex 的召回率更高。

## 12. 非目标

- 不修改 `wechat-oa` 搜索、文章回读、验证码、OCR、二维码或 Evidence 实现。
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
5. 增加 URL 分流和 `wechat-oa` Candidate Batch provenance 更新。
6. 接入管理命令的显式 live-search 授权与 partial 汇总。
7. 完成离线完整回归。
8. 用户另行授权后，使用固定小基准集做真实 Exa/Codex/WeChat 验收。
9. 数据证明达到门槛后，再决定是否设为生产默认。

## 14. 实施前必须确认的事项

新任务先阅读本文件、仓库根目录 `AGENTS.md`、`CONTEXT.md`、`DEV_STATE.md`、`docs/adr/0005-official-announcement-driven-recruitment.md`、`docs/adr/0007-wechat-first-primary-announcement.md` 和 `docs/runbooks/wechat-oa-integration.md`。

在开始写代码前，必须向用户确认：

1. 本轮是否只实现 Exa 客户端和离线编排，还是同时接入管理命令；
2. Exa API Key 的本机安全配置方式；
3. 第一批真实 A/B 基准企业和调用预算；
4. 是否保持 Brave 完全不进入招聘雷达默认流程；
5. 是否批准把新的 Candidate Batch orchestrator 改为 `official-campus-radar`。

没有这些确认，不执行真实联网、不写业务代码、不改数据库。

## 15. 新任务启动指令

```text
先阅读 docs/handoffs/exa-first-announcement-discovery-handoff.md 以及其中列出的项目文档。
当前只做方案审阅和问题清单，不要开始写代码，不要执行真实 Exa、Codex、WeChat 或 Chrome 调用，不要修改数据库，也不要推送 GitHub。等待用户明确确认实施范围后再继续。
```
