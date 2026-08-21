# Phase 02 / 任务 01：JSON API 采集适配器实施报告

## 结果

已实现配置驱动的 `JsonApiSourceAdapter`，并完成 API 来源准入、分页抓取、规范化快照、单公告多岗位提取、逐字段证据、注册表接入和 HTML 多岗位兼容。本次补充实现了可配置业务成功码、POST 固定请求体、嵌套分页路径、HTML 富文本清洗，以及腾讯/携程双接口形态的离线覆盖。未导入真实来源、未发起真实网络请求、未新增依赖，也未修改 append-only 审计模型或 formal/historical 门控。

## 文件清单

- `.gitignore`：忽略本地隔离开发使用的 `.worktrees/`。
- `radar/models.py`：增加 `OfficialSource.SourceType.API`。
- `radar/migrations/0010_officialsource_api_source_type.py`：更新来源类型 choices。
- `radar/services/admission.py`：让 API 来源走 HTTPS 与官方域名准入校验。
- `radar/collectors/base.py`：为 `FieldEvidenceValue` 增加向后兼容的可选纯文本 `excerpt`。
- `radar/collectors/json_api.py`：新增 JSON API 配置校验、抓取、规范化和提取实现。
- `radar/collectors/registry.py`：注册 `json_api` 适配器。
- `radar/collectors/html.py`：支持可选 `position_selector` 下的一公告多岗位提取。
- `radar/services/publication.py`：持久化适配器提供的可选 `raw_text` 证据，不改变必需证据门控。
- `radar/tests/test_admission.py`：覆盖 API 类型与官方域名准入。
- `radar/tests/test_collection.py`：覆盖 HTML 一公告多岗位及精确岗位定位。
- `radar/tests/test_json_api_adapter.py`：覆盖配置、注册表、GET/POST、业务成功码、嵌套分页、哈希、提取、HTML 证据、校招过滤和日期解析。
- `radar/tests/fixtures/json_api_page.json`：离线 JSON 接口响应 fixture。
- `radar/tests/fixtures/json_api_tencent.json`：任务指定的腾讯接口形态离线 fixture。
- `radar/tests/fixtures/json_api_ctrip.json`：任务指定的携程接口形态离线 fixture。
- `work/phase-02-01-json-api-adapter-report.md`：本报告。

## 关键实现

`fetch` 仅允许 GET/POST，使用透明 User-Agent、15 秒超时和页间固定延迟。每页请求前清空 Session Cookie，并禁用和拒绝 HTTP 重定向，避免跨页状态与官方 endpoint 之外的隐式取数。它支持 `page_index` 分页，将每页岗位合并回配置的 `list_path`，再用固定的 `json.dumps` 参数生成规范化 JSON 和 SHA-256。GET 使用 `params` 作为 query；POST 优先深拷贝固定 `body` 模板，并保留旧配置以 `params` 作为 JSON body 的回退行为。`page_param` / `size_param` 通过点号路径写入，可生成携程所需的 `pager.index` / `pager.size` 嵌套对象。

若配置 `success.path` / `success.expect`，配置校验会要求 `success` 为对象、`path` 非空且显式提供 `expect`；每页会在读取岗位列表前校验业务成功值，使用 `str(actual) == str(expect)` 兼容数字/字符串类型。不匹配或路径缺失即让该页失败。未配置 `success` 时仍只依赖既有 HTTP 状态校验，不硬编码腾讯 `Code == 200`。携程 fixture 验证了 `retCode: "201"` 成功和 `"500"` 失败。

`extract` 把完整岗位数组归为一条 `NoticeCandidate`，为每条有效岗位生成一个 `PositionCandidate`。空 `position_key` 会跳过并计数；`valid_values` 使用精确值匹配过滤。岗位证据使用形如 `$.Data.Posts[0].RecruitPostName` 的 JSON Path，固定公告字段使用规范化快照内 `$._radar.notice.*` 的真实位置。异常日期返回 `None`，不会中断整批提取。`html_fields` 指定的字段使用现有 BeautifulSoup 依赖去标签，并以换行保留可读段落；`PositionCandidate.raw_text`、持久化 `Evidence.excerpt` 和 `parsed_value` 使用纯文本，而 `Evidence.raw_value` 保留原始 HTML。`raw_text` 是可选附加证据，不加入既有 formal 门控的必需字段集合，缺少它的适配器行为不变。携程混合 fixture 明确证明 `kindName="应届校招生"` 被保留、空校招标识被白名单过滤。

HTML 适配器在配置 `position_selector` 时遍历公告内全部岗位节点，并相对每个岗位节点解析身份、标题、地点和申请链接；未配置时仍把公告节点视为唯一岗位节点，保留既有单岗位语义。若配置了岗位选择器却零匹配，即使配置声明完整，也会强制 `positions_complete=False`，避免页面改版误下架旧岗位。该步骤没有与现有测试产生实质冲突。

## `positions_complete` 判定

- 某页返回空岗位列表时为 `True`。
- 配置了 `total_path` 且累计岗位数达到总数时为 `True`。
- 达到 `max_pages` 时若仍未满足上述完成条件则为 `False`。
- HTTP 错误、非法 JSON、错误的 `list_path` 或非法总数会让本次抓取失败，不产生可供发布的快照，因此不会误标为完整。
- HTML 多岗位选择器零匹配时强制为 `False`；明确撤回仍由既有撤回语义处理。

## 经确认的说明修订与偏离

原任务示例的公告配置没有 `published_on` 和 `deadline`，但现有逐字段证据门控要求这两个字段完整；同时，固定配置值并不存在于接口原始响应中。按执行前确认的修订：

- `published_on`、`deadline` 必须提供固定 ISO 日期，或分别通过 `field_map` 映射到接口字段；映射日期支持 ISO 和中文年月日格式。
- 规范化快照保留配置的 `list_path`，并加入 `_radar` 元数据，保存公告固定值、字段映射、有效值过滤和完整性标记。这样固定值拥有可复核的 JSON locator，相关配置变化也会改变内容哈希。
- API 来源的 `source_url` 与接口 endpoint 都必须为 HTTPS 且属于组织官方域名；公告 URL 还必须与 `source_url` 同主机，以满足既有 notice URL 门控，没有放宽信任边界。

验收命令要求使用 `py -3.13`，但当前机器的 Python Launcher 返回 `No installed Python found!`。因此使用已安装的同版本解释器 `C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe`（Python 3.13.14）执行等价命令。

## 验证结果

在隔离工作树根目录执行：

```text
python.exe manage.py makemigrations --check --dry-run
No changes detected

python.exe manage.py check
System check identified no issues (0 silenced).

python.exe manage.py test radar.tests.test_json_api_adapter -v 2
Found 38 test(s).
Ran 38 tests in 0.078s
OK

python.exe manage.py test radar.tests -v 2
Found 146 test(s).
Ran 146 tests in 2.096s
OK
```

测试数为 146，大于验收要求的 101；测试配置中的网络守卫测试也通过。新增离线端到端测试证明 JSON 适配器候选可以通过既有 formal/evidence 门控，同时外域申请链接仍被既有 URL 门控拒绝。

## Fix Round 2：配置、证据与传输边界加固

- 配置准入现在要求 `body` 为对象；`html_fields` 为无重复、非空且受支持的岗位角色列表（`title`、`location`、`raw_text`、`application_url`），每个角色必须有非空 `field_map` 路径。
- 分页参数路径拒绝空点号段，并在实际选中的请求模板（GET `params`、POST `body`、POST 旧版 `params` 回退）中拒绝标量中间节点碰撞；旧版 POST 回退仍保留。
- 所有配置为 HTML 的岗位角色均保留原始 HTML `raw_value`，同时提供清洗后的 `parsed_value` 与持久化 excerpt。excerpt 覆盖仅在相应角色出现在 `html_fields` 时启用，未配置 HTML 的 URL 证据仍沿用原始值 excerpt 语义。
- endpoint 拒绝包括空用户名/密码形式在内的 URL userinfo；请求 Session 设置 `trust_env=False`，不继承环境代理、认证或 Cookie 配置。
- `request_delay_seconds` 必须严格为正数，离线测试配置使用 `0.25` 秒并验证分页 sleep 参数。`total_path` 只接受非布尔整数或规范整数字符串，拒绝浮点数、前导零、正号与外围空白。

最新隔离验证结果：

```text
python.exe manage.py test radar.tests.test_json_api_adapter -v 2
Found 52 test(s).
Ran 52 tests in 0.613s
OK

python.exe manage.py test radar.tests -v 2
Found 160 test(s).
Ran 160 tests in 2.615s
OK

python.exe manage.py check
System check identified no issues (0 silenced).

python.exe manage.py makemigrations --check --dry-run
No changes detected

git diff --check
exit 0（仅 Git 的既有 LF/CRLF 工作副本提示）
```

本轮未修改模型、迁移、准入状态机、发布/formal 门控、HTML 适配器或前端。
