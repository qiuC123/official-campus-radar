# Development state

Last verified: 2026-08-27 Asia/Shanghai

Phase and status: Phase 02 / H1、H2、G10、H3 已通过，T3、T4 和 T6 已完成。T6 Cycle 05 通过 ADR 0004 的中国联通单来源隔离浏览器发布 2704 个岗位；当前累计 25 个批次、7398 个当前岗位，25/25 来源通过。

## Current result

- 架构仍为 Django 5.2 + SQLite 服务端页面，没有引入 React/Vue。ADR 0004 已批准中国联通唯一的生产隔离浏览器例外；它不复用个人浏览器资料，也不扩展到其他来源。
- 正式页面数据归一化 Cycle 01 已完成：公司类型显示中文；本期泛称“应届毕业生”的校招在页面归入“2027届”；地点摘要和 `city` 筛选改为省级口径，具体岗位仍保留来源城市。原始数据库证据没有被改写。
- T1 JSON 适配器、T2 接口发现工具的 `batch` / `official_page_url` 兼容候选已实现；旧 JSON 配置和证据字段由 0011 可逆迁移。兼容 Cycle 01/02 失败记录保留，Cycle 03 技术候选通过。
- 正式首页 `/` 使用 ORM ViewModel；`/history/` 显示截止/撤回批次；开发模式下 `/preview/phase-02/` 使用独立 Mock ViewModel，并始终标注模拟数据。
- 领域模型使用 `RecruitmentBatch` / `RecruitmentPosition`；根据 ADR 0003，投递进度现在归招聘批次所有并由用户手动维护，不从岗位自动计算。
- 迁移 `0010`～`0012` 已依次应用。0012 前业务表仍为 0 行，SQLite 已备份到 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-0012-20260826-152726.sqlite3`；空库已实测 0012 反向回 0011、再正向应用 0012。
- 地点不再限北上广深；未知地点保留原文，全国/远程参与任一具体城市筛选。
- Django Mock 预览页使用 12 列横向表格；公司类型、招聘类型和投递进度支持多选，省份最多同时选择 5 个；每批次显示最多 5 个代表岗位并可展开全部。
- T3 Cycle 01 已覆盖冻结名单 50/50 家：19 家观察到候选、22 家无候选、9 家被跳过或访问失败。人工按 H3 五项标准复核后，仅拼多多、理想汽车 2 家可稳定接入；工具“可接入”误报不得计入。
- T3 运行暴露二进制请求正文 UTF-8 解码缺陷；Cycle 01 原报告保留，工具已改为省略非文本正文并记录说明，离线测试 52/52 通过。
- T3 Cycle 02 改用“平台家族优先”策略：已确认北森 `zhiye.com` 3 家、大易/WinTalent 4 家、智联企业定制站 2 家，共覆盖 9/50 家；另保留拼多多、理想汽车作为 2 个稳定 API 对照。广汽丰田、信通院、中国中车、中国联通 4 个样板页已完成公开只读验证。
- 四个家族样板已有机器可读解析草案和 7 项离线测试。Cycle 03 已确认中国中车的 form POST 分页正文，最简请求可连续取得两页不同校招岗位；它现在满足 H3 五项条件，稳定接入数更新为 3/50。Cycle 03 当时记录的 form POST 和总页数适配器缺口已在后续扩展 Cycle 01 修复。
- 适配器扩展 Cycle 01 已补充 form POST 与 `pagination.total_kind: pages`；旧 JSON/岗位总数配置保持兼容。相关提交为 `927e452`，当时完整测试 279/279 通过。
- T3 Cycle 04 对航空工业、上汽大众、广汽丰田、vivo、中国电信、中国信通院执行了 6 个入口请求和 4 个由入口离线导出的静态/根页请求。航空工业入口失效；上汽大众升级新版北森 Portal；广汽丰田仅 1 条岗位且无分页证据；vivo 已迁为自有 SPA；中国电信为 Vue 定制站并暴露新的 form POST 岗位候选；信通院连接超时。无一家新增满足 H3 五项条件，稳定数仍为 3/50。
- T3 Cycle 05 对中国电信、上汽大众、vivo 各执行一次受控 XHR 发现。上汽大众和 vivo 均使用北森新版 Portal 的 `POST /api/Jobad/GetJobAdPageList`，`Data` + `Count`、`PageIndex` + `PageSize` 传输结构一致，最简无 Cookie 请求可返回非空列表；vivo 的秋招筛选值为 `ClassificationOne: ["2"]`。但两家都缺保存下来的岗位标题/地点和第二页证据，上汽大众还缺校招范围；中国电信只命中网站栏目树，没有触发已知岗位 API。三家均不计稳定，仍为 3/50。
- T3 Cycle 06 修复发现工具对北森字段、嵌套路径和 `Category` 证据的识别，也让 JSON 适配器正确处理数组地点。vivo 以最简无 Cookie 请求取得两页各 20 条不同岗位，总数 137，标题、地点、`Category: 校园招聘` 和 `ChangeDate` 均完整，稳定来源增至 4/50。上汽大众官方 `/campus/jobs` 当前显示 0 个职位；中国电信已捕获真实 `POST /mode400/position/list`，空正文即可返回北京公司校园岗位，但旧报告未保存数组条数与 `rowCount` 实际值，暂不计稳定。
- T3 Cycle 07 证实中国电信空正文仅返回 10/2935 条，且仍未观察到页码参数，因此保持候选。下一组中，美团最简无 Cookie 接口取得第 2 页 10 条不同实习岗位，`jobType=2`、标题、地点和 57 页分页均有证据，稳定来源增至 5/50。OPPO 因 `Authorization` 未重放；亚马逊混有普通岗位且总数被 facet 误推断；工商银行捕获的是公告且最简重放失败，三家均不计稳定。
- T3 Cycle 08～10 修复数组 facet 总数误判和 `pageNo` / `pageNum` 识别，并继续精确页面与 Moka ATS 发现。生产代码新增通用 offset 分页和 Moka 公共校招 API 适配器；Playwright 仍只属于开发期发现工具。
- T3 Cycle 11～15 完整验证百度 157/157、京东 125/125、网易 494/494、顺丰 20/20、OPPO 117/117、腾讯 437/437、宁德时代 629/629。腾讯 Cycle 13 的失败来自验收标签白名单不完整，Cycle 14 以 0 次网络请求离线修正，旧失败报告保留。
- T3 Cycle 16 单项通过比亚迪 340/340、中国电信 8/8、中国联通 2699/2699、亚马逊全球 intern 194/194（其中中国 6 条）和苹果中国实习 17/17；一汽-大众、美的因服务端强制每页 10 条而在该 Cycle 保持失败。
- T3 Cycle 17 按服务端真实分页上限复验，一汽-大众 19/19、美的 149/149 通过。Cycle 18 补齐携程 53/53、大疆 139/139、吉利 6/6、东风日产实习 4/4、博世 54/54（其中明确 27 届校招 18 条）、广汽丰田 1/1 的统一证据。
- 最终稳定来源机器台账为 `tools/stable-sources-phase-02-t3.json`，共 25 家：民企 16、央国企 3、外资 3、中外合资 3。字节跳动匿名 POST 当前复测为 405，因此不计入；使用可重复的携程证据替代。
- T4 Cycle 01 根据用户“都进入”的确认生成 `data/source_catalog.csv` 25 行并完成候选落库。数据库现有 25 个 Organization、25 个 OfficialSource、25 个初始 SourceAdmissionEvent；全部为 `candidate`，哈希链 25/25 有效，`verified=0`、`enabled=0`，不会进入正式查询或真实采集。
- 正式公司类型已与领域词汇统一为民企、央国企、外资、中外合资、银行、事业单位、社会机构；迁移 0013 已应用。导入器新增 `official_entrypoint_url`，支持官网直链 ATS 的证据边界。
- T4 目录生成器会从冻结稳定台账和各 Cycle 配置生成 25 行，避免手工复制；适配器新增外部 ATS JSON 和 Apple/广汽丰田服务端内嵌岗位格式，并补充安全请求头、数组路径、字段回退、行过滤、单页和短页结束能力。本 Cycle 仍未执行任何企业网络请求。
- T4 Cycle 01 回归：目录检查 25/25、开发工具测试 137/137、Django 完整测试 362/362 均通过；`manage.py check`、迁移检查和 `git diff --check` 通过。
- T4 Cycle 02 使用 T3 脱敏样本和通过报告执行 25/25 离线提取验收，网络请求 0。修正美团城市对象、腾讯旧标签白名单、请求级范围字段和官网更新时间语义；中国电信发布时间、Apple 发布日期不再冒充更新时间。
- 当前数据库有 25 个 `verified`、0 个 `candidate`、0 个 `enabled`，50 个准入事件形成 25/25 有效哈希链，另有 8 个 ATS host 批准；业务批次和岗位仍为 0。Cycle 02 写入前备份为 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t4-cycle02-20260827.sqlite3`。
- T4 Cycle 02 回归：开发工具测试 140/140、Django 完整测试 369/369 均通过；目录和离线报告确定性检查、`manage.py check`、迁移检查和 `git diff --check` 通过。
- T4 Cycle 03 在用户明确确认后新增原子批量启用命令。命令先重建 Cycle 02 离线报告、核对冻结目录、哈希链、ATS host 和适配器，再追加 25 条 `verified → enabled` 事件；任一来源启用后准入复核失败会整批回滚。
- T4 Cycle 03 完成时有 25 个 `enabled`，25/25 `is_active=true` 且 `source_is_admitted` 通过；当时准入事件 75、`UpdateRun=0`、业务批次 0、岗位 0，Cycle 03 网络请求为 0。
- Cycle 03 写入前备份为 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t4-cycle03-20260827-160114.sqlite3`。复审提出的核验命令输出硬编码数量已改为 `len(sources)`；已启用配置仍禁止被候选目录导入器覆盖。
- T4 Cycle 03 回归：开发工具测试 140/140、Django 完整测试 370/370 均通过；目录和离线报告确定性检查、`manage.py check`、迁移检查和 `git diff --check` 通过。
- T6 Cycle 01 在用户确认后将 25 家分成 5 个手动 UpdateRun 串行采集。24 家网络/解析完成，中国联通因 `JSON API success check failed` 失败；10 家通过发布证据校验，14 家被安全拒绝，没有失败结果覆盖业务数据。
- 当前真实业务数据为 10 个 active 招聘批次、257 个 current 岗位。成功来源是拼多多、顺丰、OPPO、中国电信、亚马逊中国、苹果中国、携程、东风日产、博世中国、广汽丰田。
- 拒绝原因计数为：`incomplete_field_evidence=13`、`not_eligible_recruitment_type=11`、`incomplete_position_coverage=1`、`conflicting_position_identity=1`。分类器会被单个含“招标”的岗位污染整个批次，是已确认实现问题。
- Cycle 01 的更新器会把发布拒绝对应的 SourceVersion 标为已应用；同一内容哈希的普通重试会变成 `unchanged`。Cycle 02 已增加保留原拒绝事件的受控重处理机制，没有改写历史。
- 正式首页本地浏览器验收通过：10 个真实批次可见，无 Mock 标识，岗位展开正常。亚马逊地点仍显示部分国家/省份编码，需后续清洗。机器证据为 `work/phase-02-t6-cycle-01.json`。
- T6 Cycle 01 前数据库备份为 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t6-cycle01-20260827-160732.sqlite3`。本 Cycle 不保存原始响应、不注册定时任务。
- T6 Cycle 02 新增只允许“手工 + 明确来源 ID”的拒绝版本重处理开关，旧拒绝事件全部保留；分类优先级只对结构化适配器放宽，普通 HTML 负面词安全规则不变。未知地点诚实降级为“未说明”，重复岗位键只在整行完全相同时去重。
- Cycle 02 只重试来源 `2、3、4、5、6、7、8、11、12、13、15、18、19、21、22`；Cycle 01 已成功的 10 家没有再次访问。UpdateRun 6、7 各发布 5 家，UpdateRun 8 发布 4 家并因中国联通失败记为 `partial_failure`。
- 当前数据库有 24 个 active 招聘批次、4694 个 current 岗位，25 个来源仍全部 `enabled` 且准入复核通过。Cycle 02 新增发布 14 家、4437 个岗位；唯一未发布来源是中国联通。
- 中国联通当前公开页面可显示 2704 个岗位，但已保存配置和三个最小诊断请求均返回 HTTP 200、业务 `code=500`、`message=服务器出错`，没有 `data.jobList`。因此恢复 `success: code=200` 安全闸，不采用生产浏览器或第三方渲染结果绕过准入。
- Cycle 02 前备份为 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t6-cycle02-20260827-163122.sqlite3`；机器证据为 `work/phase-02-t6-cycle-02.json`。
- T6 Cycle 02 回归：开发工具测试 140/140、Django 完整测试 381/381 通过；目录、离线报告、两轮 T6 机器报告、系统检查、迁移检查和 `git diff --check` 均通过。正式首页浏览器验收为第一页 20 个批次、第二页 4 个批次，拼多多 13 个岗位可正常展开，无 Mock 数据；地点摘要最多展示 6 个，完整地点仍用于筛选。
- T6 Cycle 03 对中国联通只打开一次开发期页面并重新发现原端点；最初 5 级重放和单页最小请求短暂成功，但两个正式单源 UpdateRun 以及后续第 2 页/第 1 页判别均返回 HTTP 200、业务 `code=500`。因此未采用浏览器、代理或 246 页高频抓取，联通仍为 0 批次、0 岗位。
- Cycle 03 将 T2 可接入候选的公开最简 `Accept`/`Content-Type` 写入配置草案，避免以后再次丢失关键媒体类型；凭据头和环境代理安全限制不变。Cycle 03 机器证据为 `work/phase-02-t6-cycle-03.json`。
- T6 Cycle 03 回归：开发工具测试 140/140（另 62 个子测试）、Django 完整测试 386/386 通过；系统检查、迁移检查、机器报告重建和 `git diff --check` 通过。
- T6 Cycle 04 在用户确认的官网页面上核实 2704 个岗位、每页 11 条、共 246 页；用户 Edge 实际点击第 2 页后页码和岗位列表均正常变化。公开前端代码确认分页就是 `pageIndex`，没有隐藏游标。
- 同 Cycle 的无 Cookie、无签名、当前 Origin/Referer 匿名第 2 页请求仍返回 HTTP 200、业务 `code=500`。公开请求模块可能在已有浏览器会话中增加 `at`/`rt`，但本项目未读取或保留任何会话值，也未把浏览器引入生产采集。机器记录为 `work/phase-02-t6-cycle-04.json`。
- T6 Cycle 05 在用户明确确认后新增 ADR 0004 和中国联通专用 `isolated_browser_json`。适配器每次使用全新无头 Chromium context，不导入用户资料、Cookie、`storage_state`、账号或代理；只把已核验公开请求的 `pageSize` 从 11 改为 100，并按官方下一页控件低频翻页。
- Cycle 05 写入前备份为 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t6-cycle05-20260827-184535.sqlite3`，SHA-256 为 `D133AD9769CC981B4C2D89151DC2CF1CF4C6A5C8422F474EA167067CF0DF7BD4`。UpdateRun 11 和 FetchRun 43 均成功，发布中国联通 1 个批次、2704 个当前岗位；全库达到 25 个批次、7398 个当前岗位。
- T6 Cycle 05 回归：开发工具测试 140/140、Django 完整测试 394/394 通过；机器报告 `work/phase-02-t6-cycle-05.json` 可从数据库和备份确定性重建。T6 25/25 来源全部通过，但 T7 仍未授权。

## Candidate validation evidence

- `py -3.13 manage.py makemigrations --check --dry-run`：No changes detected。
- `py -3.13 manage.py check`：0 个问题。
- 2026-08-27 凌晨运行 `py -3.13 manage.py test -v 1`：新增 7 项草案测试被完整发现，共 263/263 通过。上一阶段在 23:37 曾出现 1 个旧健康状态测试失败，原因是该测试未固定 22:00 后的“计划更新漏跑”时间分支；相关生产代码和旧测试仍未由本 Cycle 修改。
- T3 Cycle 03 在线工具只运行一次：拼多多、理想汽车、中国中车均取得两页不同岗位，分别使用 2、2、2 次验收请求；中国中车连同正文确认请求累计 `5/6`。工具离线安全测试 7/7 通过，保存样本的现有适配器提取测试 3/3 通过。
- Cycle 03 完整回归：`manage.py check` 和迁移检查通过，完整测试共 273/273 通过。
- Cycle 04 最终回归：工具安全测试 8/8，通过 `manage.py check` 和迁移检查，完整测试共 287/287 通过。
- Cycle 05 在线发现只运行一次；3 个目标串行、各 1 次初始导航且无点击，每个选择的接口使用固定 5 级请求头重放并停在 `5/6`。目标和工具离线约束测试 56/56 通过。
- Cycle 05 最终回归：`manage.py check` 和迁移检查通过，完整测试共 291/291 通过。
- Cycle 06 在线动作均只执行一次：vivo 两个页码请求；上汽大众一次页面查看和一次安全导航点击、0 个 API 验收请求；中国电信一次页面监听、一次同页公司点击及一组 5 级重放。离线工具测试 65/65、定向回归 131/131 通过。
- Cycle 06 最终回归：`manage.py check` 和迁移检查通过，完整测试共 307/307 通过。
- Cycle 07 在线动作均只执行一次：中国电信 1 个完整性请求；4 家下一组各 1 次页面发现及端点预算内重放；美团使用第 6 次最终请求验证第 2 页。新增安全测试 13/13 通过，`manage.py check`、迁移检查通过，完整测试共 320/320 通过。
- Cycle 11～18 的统一报告均不写数据库、不保存原始响应。Cycle 16 的两个失败和 Cycle 13 的标签失败均保留，后续使用独立 Cycle 修复。
- T3 收口验证：开发工具测试 137/137、Django 完整测试 358/358 通过；`manage.py check` 无问题，`manage.py makemigrations --check --dry-run` 无模型变更。
- Cycle 03 独立只读评审：技术 blocker 为 0，G10 技术候选通过；冻结提交为 `303baba`。
- 临时测试数据库完整应用 0001～0012 后销毁；0012 迁移守卫覆盖单一映射、多进度冲突和不可安全反向三类场景。
- 1280×720 浏览器检查：预览 Mock 标识、12 列横向表格、5 省上限、代表岗位、展开 7 个全部岗位、批次进度模拟保存、URL 筛选和外站拦截均正常；正式首页只显示真实 ORM 空状态。

## Human gates

- H1：Cycle 06 已于 2026-08-26 通过。Cycle 07 进一步修正批次官网术语、未知截止时间、岗位展开和批次级手动进度；Cycle 08 统一主蓝色、按钮层级、圆角、字距和表格密度。分类徽章低饱和方案已按用户要求撤回，保留原有分类配色；以上均未改变已通过的信息结构。
- H2：Cycle 02 已于 2026-08-26 由用户完成浏览器验收并明确确认通过。
- G10：Cycle 03 技术复核为 0 blocker；H1/H2 前置条件满足后已正式接受。
- H3：已通过。企业类型配额、公开只读访问范围、25/50 最低成功线和具体 50 家名单均已确认；名单见 `docs/handoffs/phase-02-company-pool-candidate.md`。T3 只能在此边界内执行。

## Explicitly not started

除 ADR 0004 的中国联通单来源隔离浏览器外，不做其他生产浏览器采集。Windows 计划任务、微信模块和云部署均未开始。T6 已累计发布 25/25 家并通过。

## Exact next task

等待用户单独决定是否启动 T7 Windows 定时任务。未经明确授权，不运行 `scripts/install_daily_task.ps1 -Apply`。
