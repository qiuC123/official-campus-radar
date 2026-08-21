# Phase 02 / 任务 01：JSON API 采集适配器实施报告

## 结果

已实现配置驱动的 `JsonApiSourceAdapter`，并完成 API 来源准入、分页抓取、规范化快照、单公告多岗位提取、逐字段证据、注册表接入和 HTML 多岗位兼容。未导入真实来源、未发起真实网络请求、未新增依赖，也未修改 append-only 审计模型或 formal/historical 门控。

## 文件清单

- `.gitignore`：忽略本地隔离开发使用的 `.worktrees/`。
- `radar/models.py`：增加 `OfficialSource.SourceType.API`。
- `radar/migrations/0010_officialsource_api_source_type.py`：更新来源类型 choices。
- `radar/services/admission.py`：让 API 来源走 HTTPS 与官方域名准入校验。
- `radar/collectors/json_api.py`：新增 JSON API 配置校验、抓取、规范化和提取实现。
- `radar/collectors/registry.py`：注册 `json_api` 适配器。
- `radar/collectors/html.py`：支持可选 `position_selector` 下的一公告多岗位提取。
- `radar/tests/test_admission.py`：覆盖 API 类型与官方域名准入。
- `radar/tests/test_collection.py`：覆盖 HTML 一公告多岗位及精确岗位定位。
- `radar/tests/test_json_api_adapter.py`：覆盖配置、注册表、GET/POST、分页、哈希、提取、证据、过滤和日期解析。
- `radar/tests/fixtures/json_api_page.json`：离线 JSON 接口响应 fixture。
- `work/phase-02-01-json-api-adapter-report.md`：本报告。

## 关键实现

`fetch` 仅允许 GET/POST，使用透明 User-Agent、15 秒超时和页间固定延迟。每页请求前清空 Session Cookie，并禁用和拒绝 HTTP 重定向，避免跨页状态与官方 endpoint 之外的隐式取数。它支持 `page_index` 分页，将每页岗位合并回配置的 `list_path`，再用固定的 `json.dumps` 参数生成规范化 JSON 和 SHA-256。请求参数在 GET 中进入 query，在 POST 中进入 JSON body；测试全部 mock，没有真实网络访问。

`extract` 把完整岗位数组归为一条 `NoticeCandidate`，为每条有效岗位生成一个 `PositionCandidate`。空 `position_key` 会跳过并计数；`valid_values` 使用精确值匹配过滤。岗位证据使用形如 `$.Data.Posts[0].RecruitPostName` 的 JSON Path，固定公告字段使用规范化快照内 `$._radar.notice.*` 的真实位置。异常日期返回 `None`，不会中断整批提取。

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

python.exe manage.py test radar.tests -v 2
Found 131 test(s).
Ran 131 tests in 2.309s
OK
```

测试数为 131，大于验收要求的 101；测试配置中的网络守卫测试也通过。新增离线端到端测试证明 JSON 适配器候选可以通过既有 formal/evidence 门控，同时外域申请链接仍被既有 URL 门控拒绝。
