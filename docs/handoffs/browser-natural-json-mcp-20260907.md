# 浏览器自然 JSON 响应读取 MCP

用户要求将已验证的原有浏览器读取路线封装为 MCP。本次按推荐方向扩展现有 `web-crawler`；通用工具由 `E:\devlop\Pi-devlop\Web-Crawler-Agent` 维护，招聘雷达保留企业身份、公告、招聘对象、项目分区和正式准入判断。

## 能力与职责

新增能力围绕“打开公开页面 → 等待匹配端点自然返回 JSON → 按字段白名单投影 → 点击明确下一页 → 保留逐页结果”。工具不会构造或重放岗位请求，不修改页面请求参数，不读取或导出请求头、Cookie、签名或 CSRF。观察对象使用无查询参数的 `host/path`，不能把含签名的完整 URL 当作调用输入。

`inspect_page` 继续用于页面检查；采集统一使用 `crawl_site`，默认 `extraction_mode="html"` 处理 HTML，显式选择 `"browser_json"` 读取浏览器自然收到的结构化响应。旧 `observe_browser_json` 保留参数兼容，内部转发到同一个入口，不维护第二套采集实现。没有必须用 MCP 的业务要求：原脚本和 MCP 是同一读取路线的不同调用入口。

工具复用已有公开 URL 校验、隔离 context、资源阻断、请求预算、截止时间和访问限制停止机制。全部已放行资源请求计入预算，发送前被拦截的资源单独记账；页数与请求数分开。缺失下一页、真正末页、达到页数上限和中途失败分别记录，不把部分样本报告为全量。

仅返回白名单投影字段、逐页观察、记录唯一键、声明总数、请求账本和结束原因。不会输出招聘批次已准入、全项目覆盖、当前可投递等招聘雷达结论。生产浏览器仍遵守单企业 ADR 边界，封装 MCP 不扩大 ADR 0004。

## 离线参考数据

`work/xiaomi-natural-json-mcp-reference-20260907.json` 从已有受控样本报告投影出校园两页共 20 条记录，包含来源报告按 UTF-8 / LF 换行归一化后的 SHA-256，避免 Windows Git 换行转换改变校验结果。该文件是离线投影，不是新的网络抓取或完整接口响应。

| 输出字段 | 原始响应记录内点路径 |
| --- | --- |
| `id` | `id` |
| `title` | `title` |
| `subject_id` | `job_subject.id` |
| `recruit_type` | `recruit_type.name` |

已知响应记录数组为 `data.job_post_list`，声明总数为 `data.count`；样本当时总数 768、两页 ID 无交集。`subject_id` 只是官方项目身份线索，不能由 MCP 自动解释招聘对象或准入状态。

小米上轮全部网络请求累计已达 200/200、岗位已知累计 9/12。本次封装只做离线测试与不放行网络的协议检查，不能通过新工具、新进程或新 run 获得旧轮已耗尽的额度。

## 实现与验收状态

通用实现由用户指定的 MCP 维护任务“判断 Pi agent 产品定位”（`01a06503-3fc6-7351-9342-88e27bcd48dd`）负责。当前统一入口为 `crawl_site`；首次封装使用的 `observe_browser_json` 已作为兼容别名保留。首次核验与合并后的真实 stdio 验证分别记录在文末。

统一入口的自然 JSON 模式需要 `seed_url`、`extraction_mode="browser_json"` 和 `json_response`。后者包含必填的 `response_endpoint`、`records_path`、`fields`、`identity_path`，以及可选的 `total_path` 和 `success_assertion`。JSON `fields` 为 `{name, path, required}` 列表，点路径从单条记录开始；`records_path`、`total_path`、`success_assertion.path` 从响应根开始。目标端点与 seed 同 host，格式为精确的 `host[:port]/path`，不带 scheme、查询参数或 fragment。

翻页复用 `pagination.next_selector`，只接受 CSS；本次保持观察间隔 500 ms，显式传入其他 `wait_after_click_ms` 会被拒绝。`fetch_mode` 的 `auto` / `browser` 都使用隔离浏览器；`http`、非 null 的顶层 HTML 字段/条目选择器/路径过滤器、XPath 翻页都在创建 run 和联网前拒绝。HTML 模式不能携带 `json_response`，不会自动切换模式或静默忽略冲突参数。

两种模式共用 `page_limit`（统一入口默认 20，上限 20）、`endpoint_limit`（默认及上限 200）、`per_endpoint_limit`（默认及上限 20）和 `business_endpoint_limits`。JSON 示例显式限定 2 页；旧别名继续保持默认 2 页，并将旧 `next_selector` 转为 `pagination.next_selector`。目标响应端点自动计为业务端点，调用方必须传入真实剩余额度。

HTML 原有返回字段保持不变。统一入口和旧别名的 JSON 返回及持久化摘要均使用 `tool="crawl_site"`、`extraction_mode="browser_json"`，JSON 逐页文件和 `resumable=false` 继续保留；两种模式不强制使用相同的产物格式。

返回值包括 `run_id`、`pages_completed`、`records_count`、`unique_ids`、`declared_total`、`stop_reason`、`completeness`、`complete`、请求账本和逐页文件路径。每个 `page-NNNN.json` 只保存该页白名单投影记录、ID 和声明总数，批量记录不会全部塞进 MCP 对话返回。

`page_limit_reached` 始终表示部分结果。仅提前确认控件禁用末页、过程无异常且已配置声明总数匹配时，才能报告 `complete`。未配置 `total_path` 时，`complete` 仅表示这个分页入口遍历结束，不表示全站覆盖，也不表示招聘雷达准入。

## 小米零额度协议检查示例

以下 `crawl_site` 输入保存于 `work/xiaomi-crawl-site-json-zero-budget-20260907.json`。旧别名示例和原协议报告保持冻结，供核对兼容性。它用于检查协议及零额度停止，不产生官网请求或启动浏览器，不能把其中的 `0` 擅自改成新额度后执行。

```json
{
  "seed_url": "https://xiaomi.jobs.f.mioffice.cn/campus/",
  "extraction_mode": "browser_json",
  "json_response": {
    "response_endpoint": "xiaomi.jobs.f.mioffice.cn/api/v1/search/job/posts",
    "records_path": "data.job_post_list",
    "fields": [
      {
        "name": "id",
        "path": "id",
        "required": true
      },
      {
        "name": "title",
        "path": "title",
        "required": true
      },
      {
        "name": "subject_id",
        "path": "job_subject.id",
        "required": false
      },
      {
        "name": "recruit_type",
        "path": "recruit_type.name",
        "required": false
      }
    ],
    "identity_path": "id",
    "total_path": "data.count"
  },
  "pagination": {
    "next_selector": "li.atsx-pagination-next[title=\"下一页\"]"
  },
  "page_limit": 2,
  "endpoint_limit": 0,
  "per_endpoint_limit": 0,
  "business_endpoint_limits": {
    "xiaomi.jobs.f.mioffice.cn/api/v1/search/job/posts": 0
  }
}
```

## 首次封装的接入核验（合并前历史记录）

主任务通过真实 stdio 启动现有 `E:\devlop\Pi-devlop\Web-Crawler-Agent\.venv\Scripts\web-crawler-mcp.exe`，从 `tools/list` 成功发现 `observe_browser_json`，实际 schema 的页数/总请求/单端点上限分别为 20/200/20。客户端使用雷达本机 Python 3.13 与 MCP SDK 1.28.1；这是协议兼容检查，不给雷达生产采集增加 MCP 依赖。

首次调用旧 `xiaomi-observe-browser-json-zero-budget-20260907.json` 输入，返回 `stop_reason=endpoint_budget_exhausted`、`endpoint_requests.used=0`、`pages_completed=0`、`records_count=0`、`complete=false`，检查进程退出码 0。机器证据为 `work/xiaomi-observe-browser-json-protocol-20260907.json`，包含精确输入、实际 schema、返回值和客户端版本。此处的预算停止是预期验证结果，不是工具异常；没有实测封装后的真实小米采集。

原有 MCP 服务启动命令保持可用。已连接任务的工具列表可能保留启动时快照；合并后需要重新连接 `web-crawler` 或重启客户端，在 `crawl_site` schema 中确认出现 `extraction_mode` 和 `json_response`。刷新不自动执行公司采集。

招聘雷达侧 Python 3.13 完整测试 659 项，657 通过、2 项平台跳过；项目检查、迁移漂移检查和差异检查通过。新增回归核对离线参考与原报告哈希/记录一致、示例额度全为零、实际 stdio 报告与输入和上限一致。MCP 项目的行为测试由维护任务单独运行，结果另行记录，不用本项目的测试数代替。

主任务独立运行 MCP 新模块专项测试 26 项全部通过，其中包括真实 Chromium 使用本地 `route.fulfill` 模拟两页 JSON 的验证，以及重复/不变页、总数冲突、空列表、预算/截止时间、访问墙、敏感字段和迟到响应等情况。这些是离线测试，没有进行新的公司网络采集。

维护任务最终回报：MCP 项目 Python 全量 96/96、TypeScript 5/5、`npm run check` 全部通过，退出码均为 0；无未完成的必需项。权威工具契约位于 `E:\devlop\Pi-devlop\Web-Crawler-Agent\docs\OBSERVE_BROWSER_JSON.md`，实现位于该项目 `src/web_crawler_agent/browser_json.py`。现有 MCP 注册和启动命令无需修改。MCP 项目没有改写招聘雷达文件或生产配置。

收尾将参考文件哈希改为显式 LF 归一化时，首次回归因元数据仍保留旧 CRLF 原始字节哈希而失败；已同步更新参考文件中的归一化哈希。历史采集报告和岗位数据未改写，相关 11 项回归随后通过。

## 统一入口后的接入核验

用户明确要求合并后，`crawl_site` 已加入显式提取模式，旧 `observe_browser_json` 只转发到同一分派入口。主任务再次通过实际 MCP stdio 运行三次零额度调用：统一 JSON 模式、旧别名和未指定模式的默认 HTML。三次均按预期停止、请求数为 0，协议检查进程退出码 0。

JSON 两个入口均返回 `tool="crawl_site"`、`extraction_mode="browser_json"`、`stop_reason=endpoint_budget_exhausted`，完成页数和记录数为 0，`complete=false`、`resumable=false`；返回值与各自落盘摘要逐项一致。默认 HTML 继续返回原有 `navigation_status`、完成/失败计数和 CSV/checkpoint 路径，不增加 JSON 模式字段。实际 schema 确认统一入口页数默认 20、旧别名默认 2，上限仍为 20/200/20。

本次精确输入、两个工具的实际 schema、三次返回值和 JSON 持久化摘要保存在 `work/xiaomi-crawl-site-json-protocol-20260907.json`。此证据只证明协议、分派和零额度停止；公司真实采集仍引用此前原脚本样本，不能据此增加小米请求或认定生产准入。零额度运行目录作为审计产物保留。

雷达侧合并批次的 Python 3.13 全量回归共 661 项，659 通过、2 项平台跳过；`manage.py check`、`makemigrations --check --dry-run` 通过。新增两项回归核对统一示例与旧字段映射/耗尽台账一致，并核对实际 schema、兼容入口、停止状态及持久化摘要。

维护任务最终回报统一入口批次：MCP Python 全量 104/104、TypeScript 5/5、`npm run check` 全部通过，退出码均为 0；没有未完成的必需项。主任务独立核对分派代码、兼容别名、实际 stdio 和已更新的 MCP 文档/Skill。MCP 启动与注册无需修改；源码项目本身没有 Git 仓库，本批雷达侧调用说明和验收记录单独提交。
