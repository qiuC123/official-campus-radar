# Phase 02 / 任务 02：招聘接口发现工具（开发期）

本文件是交给执行方（Codex）的完整任务说明，自包含，不依赖任何对话上下文。可与任务 01 并行执行，两者无代码依赖。

> 2026-08-21 现场验收规则修订：旧 Cycle 01 的失败记录永久保留；从
> Cycle 02 起，“单目标只打开一次页面”精确定义为每个目标只创建一个
> 浏览器上下文和一个页面实例，只执行一次初始导航。允许在该页面实例内
> 最多执行一次经过安全检查的同页点击及其同页导航；禁止刷新、第二次
> `goto`、新窗口、弹窗和为了补结果再次运行同一目标。

---

## 一、背景

### 项目是什么

`official-campus-radar` 是一个本地单用户的校园招聘信息雷达，运行在项目所有者的 Windows 电脑上。每天定时从已核验的官方来源抓取校招岗位，汇总成可筛选的表格，并记录个人投递进度。技术栈 Python 3.13 + Django 5.2 + SQLite，生产依赖仅 `Django`、`requests`、`beautifulsoup4`。

不做云部署、不做登录、不自动投递、不规避站点访问限制。

### 为什么需要这个工具

项目已确定以「企业招聘官网的 JSON 接口」为主数据源（决策与证据见 `docs/adr/0001-recruitment-api-as-primary-source.md`）。企业招聘站点几乎全是 SPA，岗位数据不在 HTML 里，但前端必然调用 JSON 接口取数据，且这些接口通常免登录。

问题在于**接口路径无法通过静态分析获得**，已实测确认：

- `careers.tencent.com/campus.html` 静态 HTML 仅 1896 字节，且不含任何 `<script>` 标签（脚本运行时动态注入）。
- `join.qq.com` 的 CDN JS bundle 对非浏览器请求返回**空响应体**。
- 按常见命名猜测端点（`/api/post/ByHomeInfo`、`/api/apply/campus-recruitment/{org}/jobs` 等）**全部 404**。

已知可行的办法只有一个：在真实浏览器里打开招聘页，观察它实际发出的 XHR/Fetch 请求。目前这一步靠人工 F12 抓包，每家 3~5 分钟。本任务要把它自动化，使其可批量执行、可复核、可复现。

### 已知的正确答案（用作本工具的验收基准）

两个端点已由人工抓包确认，工具必须能自动发现它们：

**携程**（POST）

```
POST https://careers.ctrip.com/api/hrrecruit/getJobAd
请求体：{"condition":{"kind":["1"],"category":2,"city":[],"keyword":"","fromId":[],
                    "country":[],"bucode":[],"jobFamilyCode":[],"jobFamilyGroupCode":[]},
        "pager":{"index":"1","size":"10"},"head":{"language":"zh_CN","version":"1"}}
响应：{"retCode":"201","retValue":{"total":N,"recruitJobAdList":[{...}]}}
入口页：https://careers.ctrip.com/  （校招在 #/campus）
```

**腾讯**（GET）

```
GET https://careers.tencent.com/tencentcareer/api/post/Query
     ?timestamp=0&pageIndex=1&pageSize=10&language=zh-cn&area=cn&attrId=
响应：{"Code":200,"Data":{"Count":N,"Posts":[{...}]}}
入口页：https://careers.tencent.com/search.html
```

---

## 二、任务

### 步骤 1：建立开发期依赖与目录隔离

- 新建 `requirements-dev.txt`，内容为 `playwright>=1.4,<2`（版本按实际可用的稳定版）。**不得修改 `requirements.txt`**。
- 新建 `tools/` 目录存放本工具。`tools/` 下的代码**不得被 `radar/` 下任何模块导入**，反向亦不得依赖 Django 应用上下文运行（工具应能在不启动 Django 的情况下独立执行）。
- 在 `tools/README.md` 说明：本目录为开发期工具，不属于运行时采集路径；安装方式 `py -3.13 -m pip install -r requirements-dev.txt` 与 `py -3.13 -m playwright install chromium`。

### 步骤 2：实现 `tools/discover_api.py`

命令行接口：

```bash
py -3.13 tools/discover_api.py --url <招聘页URL> [--wait 8] [--scroll] [--click "<CSS选择器>"] [--out <路径>]
py -3.13 tools/discover_api.py --targets tools/targets.json --out work/api-discovery.md
```

行为：

1. **启动 Chromium（headless）**。每个目标只创建一个浏览器上下文和一个
   页面实例，并且只对入口 URL 执行一次初始导航。

2. **监听全部网络响应**，对每条响应记录：URL、请求方法、请求头、请求体（POST）、响应状态、`content-type`、响应体（仅 JSON 且体积在上限内时保留，建议上限 2 MB）。

3. **触发更多请求**：等待 `--wait` 秒；`--scroll` 时在同一页面实例内滚动到页面底部若干次（触发懒加载）；`--click` 时最多点击一次给定选择器（用于「查看职位」这类安全导航控件）。点击只允许在当前页面实例中继续导航；不得刷新、再次调用 `goto`、打开新窗口或弹窗。这些动作只做页面浏览，**不填写表单、不提交任何数据**。

4. **筛选候选岗位接口**。判定规则（纯函数，须可单测）：响应体解析为 JSON 后，在其中递归查找「元素为对象的数组」，若某数组满足下列条件则视为候选岗位列表：
   - 长度 ≥ 1；
   - 元素的键集合中，同时存在「疑似标题」键与「疑似地点或时间」键。疑似标题键匹配 `title|name|job|post|position`（不区分大小写）；疑似地点键匹配 `city|location|area|place|region`；疑似时间键匹配 `date|time|update|publish`。

   记录该数组在响应中的 JSON 路径（如 `retValue.recruitJobAdList`、`Data.Posts`），以及同一响应中疑似总数字段的路径（键名匹配 `total|count`，值为整数）。

5. **合规可调用性重放验证**（关键步骤）。对每个候选接口，用 `requests` 重放，逐级递减请求头，判定哪些是必需的：
   - 完整头 + Cookie（基线）
   - 去掉疑似签名头（键名匹配 `sign|token|payload|nonce|trace|w-`）
   - 去掉 Cookie
   - 同时去掉两者
   - **最简合规头**：仅 `accept`、`content-type`、`user-agent: OfficialCampusRadar/0.1 (local low-frequency collector)`

   报告每级是否仍返回等效数据（判据：候选列表路径仍存在且非空）。**最简合规头能调通的接口才标记为「可接入」**；只有携带前端生成签名才能调用的标记为「不可接入」。

6. **产出配置草案**，直接可粘贴进任务 01 适配器的 `parser_config`：端点、方法、请求体、分页参数猜测（键名匹配 `page|index|offset|size|limit`，含嵌套路径如 `pager.index`）、`list_path`、`total_path`、`success`（业务成功码：取响应顶层键名匹配 `code|status|ret` 且值为 `200`/`201`/`0`/`success` 的字段）、以及依据元素键名推断的 `field_map` 候选。

7. **输出 Markdown 报告**：每个目标一节，含入口页、发现的候选接口（按可信度排序）、重放验证结果表、配置草案代码块、以及抽样 5 条岗位记录的关键字段值（供人工判断是否校招）。

8. **失败与拦截的如实报告**：若页面出现登录墙、验证码、或无头浏览器被拦截（页面无内容、返回异常状态），**如实记录并跳过该目标**，在报告中标注原因。不得尝试绕过。

### 步骤 3：单元测试

新建 `tools/tests/test_discover_api.py`（或项目既有测试布局下的等价位置），对**纯函数**做离线测试，不启动浏览器、不发网络请求：

- 候选数组识别：给定携程形态 JSON（`retValue.recruitJobAdList`）与腾讯形态 JSON（`Data.Posts`），均能正确定位路径。
- 干扰排除：含有数组但元素缺少标题/地点键的响应（如城市字典 `[{"code":"CO0009","name":"上海"}]`）不被误判为岗位列表。注意此例含 `name`，但缺少地点/时间键，应被排除——用它作为断言用例。
- 总数字段定位：`retValue.total`、`Data.Count` 均能识别。
- 业务成功码识别：`{"retCode":"201"}` 与 `{"Code":200}` 均能识别。
- 分页参数推断：能从 `{"pager":{"index":"1","size":"10"}}` 推断出嵌套路径 `pager.index` / `pager.size`；能从 query 串 `pageIndex=1&pageSize=10` 推断出顶层参数名。
- 字段映射推断：从携程元素键名推断出 `title←jobTitle`、`location←cityName`、`updated_at←publishDate`、`position_key←jobId`（优先选取值形如 UUID 或长数字且在样本中唯一的键）。

### 步骤 4：对两个基准目标实跑验证

手工执行（非自动化测试，因需真实网络）：

```bash
py -3.13 tools/discover_api.py --url https://careers.ctrip.com/#/campus --wait 10 --scroll --click "text=查看所有职位" --out work/discovery-ctrip-cycle-02.md
py -3.13 tools/discover_api.py --url https://careers.tencent.com/search.html --wait 10 --scroll --out work/discovery-tencent-cycle-02.md
```

这两条命令各执行一次且仅执行一次。若某次未发现目标端点，记录本周期失败并
停止，不得追加 DOM 盘点、诊断性重开页面或第二次目标调用。两个目标串行执行，
间隔至少 3 秒。完整计数与判定写入
`work/phase-02-02-live-acceptance-cycle-02.md`，不得覆盖 Cycle 01 产物。

须证明：报告中出现 `careers.ctrip.com/api/hrrecruit/getJobAd`（POST）与 `careers.tencent.com/tencentcareer/api/post/Query`（GET），`list_path` 分别为 `retValue.recruitJobAdList` 与 `Data.Posts`，且携程的重放验证结论为「最简合规头可调通、签名头非必需」（该结论已由人工验证，若工具得出相反结论则为工具缺陷）。

---

## 三、约束

**性质与隔离**

- 本工具是**开发期工具**，产出物是配置文本。它**不属于运行时采集路径**，生产采集只用 `requests`。
- playwright 只进 `requirements-dev.txt`，不得进 `requirements.txt`。`radar/` 下任何模块不得导入 `tools/`。
- 不得因本任务修改 `radar/` 下的任何文件，不得修改数据模型或生成 migration。

**访问合规（硬约束，违反即不可接受）**

- 不登录、不提交表单、不输入任何凭据、不绕过验证码。
- 不使用 stealth 插件或任何反检测手段伪装无头浏览器。若站点拦截无头浏览器，如实报告并跳过。
- 不逆向、不复现前端生成的签名算法。签名必需的接口一律标记为不可接入。
- 同一站点访问必须低频：每个目标只创建一个浏览器上下文、一个页面实例和一次初始导航；允许同一页面内最多一次安全点击及其同页导航；禁止刷新、第二次 `goto`、新窗口、弹窗和补跑同一目标。多目标之间延时 ≥ 3 秒，不并发访问同一域名。
- 重放验证对单个标准化端点在整个验收周期内累计不超过 6 次（固定阶梯实际为 5 次），不得通过第二次进程或补跑重置预算；不做参数穷举、不做路径扫描。
- 每轮现场验收使用独立的 Cycle 编号和产物文件；历史失败记录只读保留，新周期不得覆盖或追认旧周期。

**探测纪律**

- 报告中不得把「发现了端点」写成「接入成功」。是否为校招数据由人工依据抽样字段判断，工具只呈现事实。
- 抽样输出必须包含校招判别字段的原值（如携程 `kindName`、腾讯 `RequireWorkYearsName`），供人工核对。

**代码风格**

- Python 3.13，类型注解风格与项目现有代码一致（`str | None` 而非 `Optional[str]`）。
- 纯函数与 IO 分离：识别、推断、配置生成必须是不依赖浏览器与网络的纯函数，以便单测。

---

## 四、验收标准

```bash
py -3.13 -m pip install -r requirements-dev.txt
py -3.13 -m playwright install chromium
py -3.13 -m pytest tools/tests -v          # 或项目既有测试命令，全绿
py -3.13 manage.py test radar.tests         # 期望：仍为原有全绿状态，数量不变
py -3.13 manage.py check                    # 期望：0 issues
py -3.13 manage.py makemigrations --check --dry-run   # 期望：No changes detected
```

另需满足：

1. 步骤 3 列出的全部单测场景有对应用例，无跳过。
2. 步骤 4 的两次实跑分别只执行一次，产出 Cycle 02 独立报告文件；报告中出现两个基准端点及正确的 `list_path`，并证明每个目标仅一个上下文、一个页面实例、一次初始导航、零刷新，且安全点击不超过一次。
3. `requirements.txt` 未被修改（`git diff` 可证）。
4. `radar/` 下无任何文件改动（`git diff` 可证）。
5. 保留实施报告 `work/phase-02-02-api-discovery-tool-report.md` 中的 Cycle 01 历史结论，并新增 `work/phase-02-02-live-acceptance-cycle-02.md`，说明：两个基准目标的实跑结果（成功/失败及原因）、页面生命周期与端点重放计数、被无头浏览器拦截或需交互触发的情况、任何偏离本说明之处及理由。

若某一步无法在不违反约束的前提下完成，**停止并报告**，不要自行放宽约束、不要引入反检测手段、不要尝试破解签名。
