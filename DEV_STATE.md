# Development state

Last verified: 2026-08-20 Asia/Shanghai

Phase and status: Phase 02 / 方案已定稿，待实施 —— 数据来源策略重大转向，见 ADR 0001

## Current goal

按 ADR 0001 的两级架构接入首批真实数据：以企业招聘官网接口（或服务端渲染页面）为岗位主数据源，每日自动同步；微信公众号降级为低频人工补充的发现渠道，第一版不实现。首个交付为腾讯单企业端到端闭环。

## Completed and verified

- Phase 01：Django 5.2 + SQLite 本地骨架已实现并通过 101 个测试；含来源准入链（哈希链事件）、逐字段证据、发布事件、公告/岗位生命周期、七种个人投递进度、每日更新命令、漏跑提醒、13 个独立列控制、离线 demo 加载与清理。
- Phase 01 结论：可条件放行为「本地离线可运行骨架」，不可表述为真实来源采集或生产就绪。当前零真实数据。
- 2026-08-20 来源可达性实测（免登录）：腾讯 `careers.tencent.com` 接口返回 2276 个岗位、字段完整、`pageSize` 可开至 200，但经工作经验分布核查**该接口为社招池**，国内校招在 `join.qq.com` 独立系统；阿里、字节、美团、华为均为前端渲染，接口必然存在但路径需抓包（华为可见文字为未渲染的 Vue 模板占位符，非真实岗位）；中国移动有接口线索；国家电网返回 HTTP 412 有反爬；教育部就业平台岗位列表需登录，已放弃。微信文章 2 篇样本正文纯图片、纯文本长度均为 0，可稳定提取标题/公众号身份/发布时间/外链。
- 已确认接口路径无法通过静态分析可靠获得（腾讯校招页静态 HTML 无 `<script>` 标签、CDN bundle 对非浏览器请求返回空、猜测端点全部 404），每家企业需一次浏览器抓包。

## Key decisions

- 本地模块化单体：Django、SQLite、独立来源适配器和 Windows 任务脚本。权威说明见 `docs/superpowers/specs/2026-08-17-official-campus-recruitment-radar-design.md`。
- **数据来源策略以 `docs/adr/0001-recruitment-api-as-primary-source.md` 为准，该 ADR 覆盖原设计中「企业官网招聘页 HTML + 逐字段 CSS selector」的采集路线。**
- 产品定位：先做好项目所有者自用，再考虑开放。不做云部署、公开访问、自动投递、社区笔试信息或规避访问限制；不保存账号、Cookie、简历或凭据。
- 放开城市限制：抓取并存储全量城市，前台提供筛选器，不再写死北上广深。
- 保留现有审计架构（准入哈希链、逐字段证据、append-only）。接口路线下 JSON 字段路径即为 locator，证据门控无需放宽。
- 本机所有者可直接改 SQLite/源码的情形不属于 V0 防篡改威胁模型；应用层和 Admin 对审计对象采用 fail-closed/只读约束。

## Important files and modules

- `docs/adr/0001-recruitment-api-as-primary-source.md` — 当前数据来源策略与实测证据（最新，优先级高于原设计的采集章节）。
- `docs/superpowers/specs/2026-08-17-official-campus-recruitment-radar-design.md` — 已确认设计的完整说明（采集路线部分已被 ADR 0001 覆盖）。
- `docs/PROJECT_DEVELOPMENT_SPEC.md` — 持久项目边界和阶段路线。
- `docs/superpowers/plans/2026-08-17-local-campus-radar-v0.md` — Phase 01 的详细实施任务、接口、测试和验证命令。
- `work/phase-01-r2-implementation-report.md`、`work/phase-01-history-projection-report.md` — Phase 01 最终修复和验证事实报告。

## Validation evidence

- `py -3.13 manage.py makemigrations --check --dry-run` — `No changes detected`。
- `py -3.13 manage.py check` — 0 个系统问题。
- `py -3.13 manage.py test radar.tests -v 2` — 101/101 通过，内存测试数据库已销毁。
- 两份 PowerShell 脚本均通过语法解析；`OfficialCampusRadarDailyUpdate` 计划任务当前不存在。
- 受控 demo 在 `127.0.0.1` 实测：13 个独立列、进度保存、撤回历史的城市/岗位组合筛选和中文招聘类型显示；随后已清理。
- 只读 SQLite 复核：所有 `radar_*` 业务表、`auth_user` 和 `django_session` 均为 0 行。

## Known issues and risks

- 仍无任何真实来源接入；`data/source_catalog.csv` 只有表头，全部业务表 0 行。
- `radar/collectors/html.py` 中 `positions=(PositionCandidate(...),)` 硬编码单岗位，无法承载一则公告多岗位，接入真实来源前必须修正。
- 尚无 JSON 接口适配器与服务端渲染页面适配器；`OfficialSource.source_type` 缺接口类取值，`adapter_name` 默认 `html_selector` 不适用于接口来源。
- 国家电网类返回 HTTP 412 的来源需单独评估访问策略；不得以伪装身份或绕过限制的方式接入。
- 微信文章正文为图片的比例仅由 2 篇样本得出，不足以推广；若日后启用微信层需扩大样本再判断。
- 微信文章内容存在版权风险。个人本地自用可接受；若未来转向开放访问，批量转载文章内容须先做合规评估。
- demo 清理仅适用于空库或确认不存在同组织非 demo 数据的库；混合库使用前必须收紧清理范围。
- Windows 任务尚未注册；本机关闭/休眠仍会漏跑，应用只会提示。云端运行尚未设计或购买。
- Phase 01 独立审查中曾创建并立即删除一条命名探针记录；当前业务表均为空，但 SQLite 自增序列可能已前移。

## Exact next task

按 ADR 0001 交付**配置驱动的 JSON 接口适配器**：端点、请求方法、参数、分页方式、列表 JSON 路径与字段映射全部由 `OfficialSource.parser_config` 承载，接入新企业为填配置而非写代码；JSON 字段路径直接充当 `Evidence.locator`；支持一则来源多岗位。以腾讯 `careers.tencent.com` 接口作为技术验证夹具（该接口真实可用，虽为社招池，足以验证框架正确性）。

框架完成后再依次：抓包确定首批企业的校招接口路径 → 填配置接入 → 放开城市筛选并改造前台。微信发现层、Windows 定时任务注册均延后，须另获授权。
