# Phase 02 / 任务 01：配置驱动的 JSON 接口采集适配器

本文件是交给执行方（Codex）的完整任务说明，自包含，不依赖任何对话上下文。

---

## 一、背景

### 项目是什么

`official-campus-radar` 是一个**本地单用户**的校园招聘信息雷达。运行在项目所有者的 Windows 电脑上，每天定时抓取已核验的官方招聘来源，汇总成一张可筛选的岗位表，并记录个人投递进度。不做云部署、不做登录、不做多人协作、不自动投递。

技术栈：Python 3.13 + Django 5.2 + SQLite。依赖仅 `Django>=5.2.8,<5.3`、`requests>=2.32,<3`、`beautifulsoup4>=4.13,<5`。

### 当前状态

Phase 01 已交付可运行骨架，101 个测试全绿，但**零真实数据**：`data/source_catalog.csv` 只有表头，全部业务表 0 行。

已实现的核心能力（不要重复造，也不要破坏）：

- 来源准入链：`OfficialSource` 有 `admission_state`（候选→已核验→已启用→暂停/撤销），状态迁移由 `SourceAdmissionEvent` 记录，该模型是 append-only 且带哈希链（`previous_event_hash` / `event_hash`）。
- 逐字段证据：`Evidence` 模型记录每个展示字段的 `excerpt`（原文摘录）、`locator`（定位信息）、`raw_value`、`parsed_value`。append-only。
- 发布事件：`PublicationEvent` 记录每次发布/更新/拒绝，append-only。
- 前台 `RecruitmentNotice.objects.formal()` 是三重 fail-closed 门控：来源准入链有效 + 发布事件已应用 + 逐字段证据齐全，缺一不显示。
- 采集编排在 `radar/services/update_runner.py`，适配器在 `radar/collectors/`。

### 为什么要做这个任务

原设计的采集路线是「企业官网 HTML + 逐字段 CSS selector」。该路线已被否决，理由与实测证据见 `docs/adr/0001-recruitment-api-as-primary-source.md`（**开工前必读**）。要点：

1. `HtmlSourceAdapter.validate_source_config` 要求每个来源配 10 个必填 selector，按目标规模需维护数百套，官网改版即失效，单人不可持续。
2. 实测 7 个大厂招聘站点**全部为前端渲染（SPA）**，HTML 里没有岗位数据，但都必然有 JSON 接口，且通常免登录。
3. JSON 字段路径（如 `Data.Posts[3].RecruitPostName`）是比 CSS selector 稳定得多的 locator，与现有 `Evidence` 模型天然契合。

因此转向：**以配置驱动的 JSON 接口适配器为主采集形态**。接入一家新企业应当是「填一份配置」，不是「写一段代码」。

---

## 二、任务

按顺序执行，每步可独立验证。

### 步骤 1：读现有代码，理解契约

必读：`radar/collectors/base.py`、`radar/collectors/html.py`、`radar/collectors/registry.py`、`radar/services/update_runner.py`、`radar/models.py` 中的 `OfficialSource` / `RecruitmentNotice` / `NoticePosition` / `Evidence`。

适配器契约（`base.py` 中的 `SourceAdapter` Protocol）：

```python
def validate_source_config(source: OfficialSource) -> None   # staticmethod
def fetch(source: OfficialSource) -> FetchedPage
def extract(source: OfficialSource, page: FetchedPage) -> list[NoticeCandidate]
```

注意 `NoticeCandidate.positions` 已经是 `tuple[PositionCandidate, ...]`，**数据结构本就支持多岗位**，无需改 `base.py`。

### 步骤 2：为接口类来源增加 source_type 取值

在 `OfficialSource.SourceType` 增加 `API = "api", "官网招聘接口"`。生成 migration。不要改动已有取值。

### 步骤 3：实现 `radar/collectors/json_api.py`

新增 `JsonApiSourceAdapter`，全部行为由 `source.parser_config` 驱动。配置结构：

```python
{
  "endpoint": "https://careers.tencent.com/tencentcareer/api/post/Query",
  "method": "GET",                          # 仅允许 GET / POST
  "params": {"language": "zh-cn", "area": "cn", "attrId": ""},
  "pagination": {
      "mode": "page_index",                 # 本任务仅需实现 page_index
      "page_param": "pageIndex",
      "size_param": "pageSize",
      "page_size": 200,
      "start_page": 1,
      "max_pages": 40                       # 硬上限，防失控
  },
  "list_path": "Data.Posts",                # 岗位数组的 JSON 路径
  "total_path": "Data.Count",               # 总数的 JSON 路径，可选
  "success": {"path": "Code", "expect": 200},  # 业务成功码校验，见下方要求 9
  "html_fields": ["raw_text"],              # 值为 HTML 富文本、需去标签的字段，见要求 10
  "notice": {
      "identity_key": "tencent-campus-2027",     # 该来源的公告身份，固定值
      "title": "腾讯 2027 校园招聘",
      "official_notice_url": "https://join.qq.com/",
      "recruitment_type": "campus_recruitment",
      "target_audience": "2027届"
  },
  "field_map": {
      "position_key": "PostId",
      "title": "RecruitPostName",
      "location": "LocationName",
      "raw_text": "Responsibility",
      "application_url": "PostURL",
      "updated_at": "LastUpdateTime",
      "is_valid": "IsValid"
  },
  "valid_values": {"is_valid": ["True", "true", true]}   # 可选，命中才视为在招
}
```

实现要求：

1. **`fetch`**：按配置逐页请求，拼接所有页的岗位到一个列表，把**规范化后的完整 JSON 文本**放进 `FetchedPage.body`，`content_hash` 取该文本的 sha256。规范化指 `json.dumps(..., ensure_ascii=False, sort_keys=True, separators=(",", ":"))`，保证同样数据产生同样哈希、能正确触发"内容未变化"。分页在 `total_path` 已取满、返回空列表、或达到 `max_pages` 时停止。请求间加固定延时（建议 1 秒，可配置），遵守低频访问约束。

2. **`extract`**：把扁平岗位列表归组为**一则公告 + 多个岗位**。

   归组方式：本任务只需实现 `single` 模式——整个来源的全部岗位归入一则公告，公告的 `identity_key`、`title`、`official_notice_url`、`recruitment_type`、`target_audience` 全部取自 `parser_config["notice"]`。

   理由：目标形态是「一行 = 一家企业的一则校招」，岗位在该行内聚合展示，投递进度按企业记录一次，而非每个岗位记一次。接口返回的是扁平岗位列表，没有公告概念，故由配置提供公告身份。

3. **每个岗位构造一个 `PositionCandidate`**，`position_key` 取 `field_map.position_key` 指向的值（必须非空，为空则跳过该岗位并计数）。`locator` 使用 JSON 路径形式，如 `$.Data.Posts[12]`。

4. **逐字段证据**：为公告和每个岗位填充 `field_evidence`。`FieldEvidenceValue.locator` 用完整 JSON 路径，如 `$.Data.Posts[12].RecruitPostName`；`raw_value` 为接口原值的字符串形式；`parsed_value` 为归一化后的值。这是本任务的关键——JSON 路径即 locator，不要伪造 CSS selector。

5. **`positions_complete`**：当分页正常走完（未因 `max_pages` 截断、未发生页级异常）时置 `True`，否则 `False`。该字段影响下游证据门控，不得无条件置 `True`。

6. **`validate_source_config`**：校验 `endpoint` 为 https、`method` 合法、`list_path` 与 `field_map.position_key` / `field_map.title` 非空、`pagination.max_pages` 为正整数且有上限。任一不满足抛 `ValueError`，消息说明缺什么。

7. **JSON 路径解析**：实现一个小工具函数支持点号路径（`Data.Posts`）即可，不要引入 jsonpath 之类的新依赖。

8. **时间解析**：`LastUpdateTime` 形如 `2026年08月20日`，需解析为 `date`。另需支持 `2026-08-21` 这类 ISO 格式（携程接口即为此格式）。解析失败置 `None`，不得抛异常中断整批。

9. **业务成功码校验**：不得假设 HTTP 200 即成功，也不得硬编码 `Code == 200`。按 `success` 配置取 `path` 指向的值与 `expect` 比较，不相等则视为该页失败。**实测依据**：携程接口的成功码是字符串 `"201"`（`retCode: "201", retMessage: "调用成功"`），腾讯是整数 `200`。比较时对字符串与数字做宽松相等（`str(actual) == str(expect)`），避免类型差异误判。`success` 未配置时退化为仅校验 HTTP 状态。

10. **HTML 富文本字段**：`html_fields` 列出的字段，其原值为 HTML 片段（携程 `requirements` 形如 `<p>招聘对象：本、硕、博。</p><p>毕业时间：……</p>`）。需去除标签取纯文本，保留段落间的换行或空格分隔，用作 `raw_text` / `excerpt`。`raw_value` 仍保存去标签**之前**的原始值，以保证证据可回溯。用标准库或已有的 `beautifulsoup4` 实现，不要手写正则去标签。

11. **校招/社招过滤**：`valid_values` 是通用的字段白名单过滤机制，命中才计入。**这一项是必需能力，不是可选优化**——实测表明同一个接口往往同时返回校招与社招岗位（携程去掉 `category` 筛选后，496 条中 99 条的校招标识字段为空，实为社招）。字段值大小写与中英文差异（`应届校招生` / `Fresh Graduates`）由配置的白名单列举，适配器不做语义猜测。

### 步骤 4：注册适配器

在 `radar/collectors/registry.py` 的 `AdapterRegistry.adapters` 增加 `"json_api": JsonApiSourceAdapter`。不要改动已有条目。

### 步骤 5：修正 HTML 适配器的单岗位硬编码

`radar/collectors/html.py` 第 184 行附近 `positions=(PositionCandidate(...),)` 硬编码只构造一个岗位。改为遍历配置的岗位选择器提取该公告下的全部岗位。**保持现有 101 个测试全绿**——若现有测试依赖单岗位行为，以不破坏其语义为前提最小化改动。

如果这一步与现有测试产生实质冲突，**停下来报告冲突点，不要强行改测试**。

### 步骤 6：测试

新增测试文件 `radar/tests/test_json_api_adapter.py`，覆盖：

- 配置校验：缺 `endpoint` / `list_path` / `position_key` / 非 https / 非法 method / 缺 `max_pages` 各自抛 `ValueError`。
- 分页拼接：多页响应正确合并，`total_path` 取满即停，`max_pages` 截断时 `positions_complete` 为 `False`。
- 内容哈希稳定性：同样数据、不同 key 顺序，`content_hash` 相同。
- 归组：扁平岗位列表正确归为一则公告 + N 个岗位，公告字段取自配置。
- 证据 locator：断言形如 `$.Data.Posts[0].RecruitPostName`。
- `position_key` 为空的岗位被跳过且不影响其余岗位。
- 日期解析：`2026年08月20日` 与 `2026-08-21` 均正确解析；异常格式落为 `None` 且不抛异常。
- `is_valid` 过滤：`valid_values` 命中才计入。
- 业务成功码：`expect` 为整数 `200` 而实际返回字符串 `"200"` 时视为成功；实际为 `"500"` 时视为该页失败；`success` 未配置时不因缺少该字段而失败。
- HTML 去标签：`<p>招聘对象：本、硕、博。</p><p>毕业时间：2026 年 9 月……</p>` 去标签后为可读纯文本且段落有分隔；同时断言 `raw_value` 仍为**去标签前**的原始 HTML。
- 校招过滤：同一响应内混有校招标识为 `"应届校招生"` 与空字符串的两条岗位，配置 `valid_values` 后仅前者计入。

**两个 fixture 都要建**，用于验证配置驱动对不同接口形态均生效：一个模仿腾讯结构（`Data.Posts`、`Code: 200`），一个模仿携程结构（`retValue.recruitJobAdList`、`retCode: "201"`、字段名与嵌套层级完全不同）。

**测试禁止真实网络请求**。项目已有 `radar/tests/network_guard.py`，沿用其机制。用离线 fixture 提供响应，fixture 放 `radar/tests/fixtures/`，结构模仿腾讯接口：

腾讯形态（`radar/tests/fixtures/json_api_tencent.json`）：

```json
{"Code":200,"Data":{"Count":2,"Posts":[
  {"PostId":"2034975730101809152","RecruitPostName":"腾讯云- MaaS高级产品经理",
   "LocationName":"深圳","CategoryName":"产品","Responsibility":"1.参与……",
   "LastUpdateTime":"2026年08月20日",
   "PostURL":"http://careers.tencent.com/jobdesc.html?postId=2034975730101809152",
   "IsValid":"True","RequireWorkYearsName":"三年以上工作经验"}
]}}
```

携程形态（`radar/tests/fixtures/json_api_ctrip.json`）——以下为真实抓包结果的删节版，字段名与结构请照抄：

```json
{"retCode":"201","retMessage":"调用成功",
 "retValue":{"total":1,"recruitJobAdList":[
   {"id":"29570670","fromId":"MJ036531",
    "jobId":"535f2df5-32a7-4857-9fdf-fad0acef18bb",
    "jobTitle":"测试职位（请勿投递）(MJ036531)",
    "publishDate":"2026-08-20","city":"CO0009","cityName":"上海",
    "requirements":"<p>招聘对象：本、硕、博。</p><p>毕业时间：2026 年 9 月至 2027 年 8 月期间毕业</p>",
    "jobFamilyGroupCode":"JFG_31","jobFamilyGroupName":"开发",
    "buName":"Trip.com Group","kind":"1","kindName":"应届校招生",
    "atsApiType":"Moka","category":"2"}]},
 "ResponseStatus":{"Ack":"Success","Errors":[]}}
```

对应配置（用于测试，`endpoint` 在测试中不实际请求）：

```python
{
  "endpoint": "https://careers.ctrip.com/api/hrrecruit/getJobAd",
  "method": "POST",
  "body": {"condition": {"kind": ["1"], "category": 2, "city": [],
                         "keyword": "", "fromId": [], "country": [],
                         "bucode": [], "jobFamilyCode": [],
                         "jobFamilyGroupCode": []},
           "head": {"language": "zh_CN", "version": "1"}},
  "pagination": {"mode": "page_index", "page_param": "pager.index",
                 "size_param": "pager.size", "page_size": 100,
                 "start_page": 1, "max_pages": 20},
  "list_path": "retValue.recruitJobAdList",
  "total_path": "retValue.total",
  "success": {"path": "retCode", "expect": "201"},
  "html_fields": ["raw_text"],
  "field_map": {"position_key": "jobId", "title": "jobTitle",
                "location": "cityName", "raw_text": "requirements",
                "updated_at": "publishDate",
                "category": "jobFamilyGroupName", "recruit_kind": "kindName"},
  "valid_values": {"recruit_kind": ["应届校招生", "Fresh Graduates"]}
}
```

注意该配置暴露了两个 POST 场景的额外需求，需一并实现：

- **请求体模板**：POST 来源的固定条件放在 `body`，适配器发送时与分页参数合并。
- **分页参数为嵌套路径**：携程的分页在 `pager.index` / `pager.size`，即 `page_param` 可能是点号路径而非顶层键名，写入时需按路径逐层创建。腾讯的则是顶层 query 参数。两种都要支持。

---

## 三、约束

**技术边界**

- 只用现有三个依赖，**不得引入任何新依赖**（不要 jsonpath、httpx、playwright、pydantic 等）。
- Python 3.13、Django 5.2 语法。类型注解风格与现有代码一致（`str | None` 而非 `Optional[str]`）。
- 不得引入浏览器自动化。SPA 一律走接口。

**不能动的部分**

- `SourceAdmissionEvent`、`ApprovedApplicationHost`、`PublicationEvent`、`Evidence` 的 append-only 语义和哈希链逻辑，一律不改。
- `RecruitmentNoticeQuerySet.formal()` / `historical()` 的门控逻辑不改。
- 不放宽任何证据门控。本任务的目标是让接口数据**满足**现有门控，不是绕过它。
- 现有 101 个测试必须保持全绿。

**采集行为约束（项目硬约束，违反即不可接受）**

- 不登录、不携带 Cookie、不使用代理池、不绕过验证码、不伪装身份规避反爬。
- 只低频访问公开接口，请求间必须有延时。
- User-Agent 沿用现有风格（`OfficialCampusRadar/0.1 (local low-frequency collector)`），不伪装成浏览器。
- 单个来源失败不得中断其他来源，不得因抓取失败删除或改写已有招聘记录。

**范围边界**

- 本任务**只做采集适配器**。不改前台模板、不改筛选表单、不改城市限制、不做微信相关功能、不注册 Windows 定时任务。这些是后续独立任务。
- 不导入任何真实来源数据，不执行对外网络请求作为交付的一部分。本任务交付的是能力，不是数据。

---

## 四、验收标准

全部命令在项目根目录执行，须全部通过：

```bash
py -3.13 manage.py makemigrations --check --dry-run   # 期望：No changes detected
py -3.13 manage.py check                              # 期望：0 issues
py -3.13 manage.py test radar.tests -v 2              # 期望：全绿，且总数 > 101
```

另需满足：

1. 新增测试文件 `radar/tests/test_json_api_adapter.py` 覆盖步骤 6 列出的全部场景，无一跳过。
2. 测试运行期间无任何真实网络请求（`network_guard` 生效）。
3. `AdapterRegistry.get()` 对 `adapter_name="json_api"` 返回新适配器，对未注册名仍抛 `ValueError`。
4. 提交一份简短实施报告到 `work/phase-02-01-json-api-adapter-report.md`，说明：实际改动的文件清单、步骤 5 是否与现有测试产生冲突及如何处理、`positions_complete` 的判定条件、任何偏离本说明的地方及理由。

若任一步骤无法在不违反约束的前提下完成，**停止并报告**，不要自行放宽约束或修改门控逻辑。
