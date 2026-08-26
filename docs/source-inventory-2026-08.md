# 来源接入难度清单（2026-08-21 探测快照）

本文件是一次性可行性探测的结果快照，用于排定来源接入顺序。方法与结论依据见 `docs/adr/0001-recruitment-api-as-primary-source.md`。

## 探测方法

对每家企业的主域尝试 8 个常见招聘子域（`campus` / `hr` / `talent` / `job` / `zhaopin` / `careers` / `jobs` / `recruit`），DNS 命中者发起一次低频 GET，记录：HTTP 状态、渲染方式（去除脚本后的可见文字量、Vue/Angular 模板占位符数量）、第三方招聘系统（ATS）指纹、页面内出现的接口路径线索。

全部为公开页面的只读访问，无登录、无 Cookie、无身份伪装。

## 结论：接口路径无法静态获得

腾讯、Moka 两处均已确认：接口服务器存在且返回自有格式的 JSON 错误（Moka 为 `{"message":"您访问的页面不存在","code":-1}`），但路径无法通过抓取页面 HTML 或 JS bundle 得到——SPA 脚本动态注入、CDN 对非浏览器请求返回空响应、按常见命名猜测的端点全部 404。

**每家（或每套 ATS）需要一次浏览器抓包**：打开校招岗位列表页 → F12 → Network → 筛选 Fetch/XHR → 翻页或改筛选条件 → 找到返回岗位列表的请求 → 记录 URL、方法、参数、响应中列表与字段的 JSON 路径。单次约 3~5 分钟，一次性。

## 分层与建议顺序

### 第一梯队：ATS 通用适配器（待验证）

| 目标 | 证据 | 说明 |
| --- | --- | --- |
| **Moka（mokahr.com）** | 携程 `careers.ctrip.com`、宁德时代 `talent.catl.com` 均命中 `app.mokahr.com` / `static-ats.mokahr.com` | 主流第三方招聘 SaaS。**通用性尚未验证**，见下方携程实测结论 |

宁德时代的 URL 形态 `talent.catl.com/social-recruitment/catlhr/96144/` 呈现 Moka 典型结构 `/{招聘类型}/{组织标识}/{站点号}/`，组织标识为 `catlhr`，疑似直连 Moka。**若要验证「一套适配器覆盖多家 Moka 客户」的假设，应抓宁德时代的包，而非携程的**——携程已证实是自建接口层包装 Moka（见下）。

### 携程接口实测详情（2026-08-21）

抓包结果：`POST https://careers.ctrip.com/api/hrrecruit/getJobAd`

请求体结构：

```json
{
  "condition": {"fromId": [], "keyword": "", "kind": ["1"], "country": [],
                "city": ["CO0009"], "bucode": [], "jobFamilyCode": [],
                "jobFamilyGroupCode": [], "category": 2},
  "pager": {"index": "1", "size": "10"},
  "head": {"language": "zh_CN", "version": "1"}
}
```

响应结构：`retCode`（成功码为 **`"201"`**，非 200）、`retMessage`、`retValue.total`、`retValue.recruitJobAdList[]`，外层另有携程自研 SOA 框架的 `ResponseStatus`。岗位对象含 `atsApiType: "Moka"` 字段——**证实携程为自建接口层包装 Moka，该配置不能直接套用于其他 Moka 客户**。

合规性验证（关键结论）：

| 验证项 | 结果 |
| --- | --- |
| 签名头 `w-payload-source`（前端 JS 生成） | **非必需**，去掉后仍返回 HTTP 200 与完整数据 |
| Cookie | 调用层面**非必需** |
| 项目自有 UA（`OfficialCampusRadar/0.1`，不伪装浏览器） | 正常返回 |

即无需逆向签名算法、无需伪装身份，符合项目硬约束。

字段映射：

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| `list_path` | `retValue.recruitJobAdList` | |
| `total_path` | `retValue.total` | |
| `success` | `retCode == "201"` | 不可假设 200 |
| `position_key` | `jobId` | UUID，实测 100/100 非空且唯一 |
| `title` | `jobTitle` | |
| `location` | `cityName` | `city` 为编码（`CO0009`），不可用 |
| `raw_text` | `requirements` | HTML 富文本，需去标签 |
| `updated_at` | `publishDate` | `2026-08-21`，标准格式 |
| `category` | `jobFamilyGroupName` | |
| 校招判别 | `kindName == "应届校招生"` / `Fresh Graduates` | |

其他实测事实：

- **`category: 2` 是校招的正确筛选条件。** 去掉该条件后 `total` 由 1 升至 525、`kind:["1"]` 时为 496，但 `kindName` 分布为 `{'': 99, 'Fresh Graduates': 1}`，且标题多为「资深…」「Senior…」「政府关系经理/资深经理」，**混入的是社招岗位，不是校招**。
- **携程 2027 校招当前仅 1 条岗位，且为「测试职位（请勿投递）」。** 接口技术上完全可用，但暂无有价值数据。适合作为适配器正确性的验证样本，不适合作为首个数据源。
- 语言由 **Cookie `language=zh-CN`** 控制，非请求头亦非 body 的 `head.language`。不带该 Cookie 时返回英文（`Shanghai` / `Software development` / `Fresh Graduates`）。建议不带 Cookie、改由适配器侧维护英文到中文的映射表，以免触碰"不携带 Cookie"约束。
- 分页正常，`pager.size` 实测可取 100。

### 教训：先验证数据性质，再看数量

本轮探测中连续三次因「取得表面信号即认定成功」而下错结论：腾讯社招接口被当作校招、华为未渲染的 Vue 模板被当作服务端渲染内容、携程去掉 `category` 后的 525 条社招被当作校招。

**接入任何来源前必须先验证数据性质**：检查校招判别字段（`kindName` / `RequireWorkYearsName` 等）的取值分布、抽样核对岗位标题是否符合校招特征，确认无误后才看数量。数量增长本身不构成接入成功的证据。

抓包前亦应先在页面上确认存在真实岗位（非测试数据、非空池），避免抓到空结果后误判接口不可用。

同类值得后续识别的 ATS：北森（beisen.com / italent.cn）、大易（dayee.com）、Workday（myworkdayjobs.com）。本轮样本中未命中，但在央企国企中常见，扩大名单后应重新扫描。

### 第二梯队：互联网大厂，各需一次抓包

全部为 SPA，岗位数据不在 HTML 中，接口必然存在。

| 企业 | 招聘站点 | 状态 |
| --- | --- | --- |
| 腾讯 | `join.qq.com`（校招，独立于社招 `careers.tencent.com`） | 社招接口已验证可用；校招接口待抓包 |
| 阿里巴巴 | `talent.alibaba.com`（`campus`/`job` 子域均跳转至此） | SPA 空壳 |
| 字节跳动 | `jobs.bytedance.com` | SPA，HTML 794 KB 但可见文字 22 字 |
| 百度 | `talent.baidu.com` | SPA，线索 `/jobs`，默认跳转 `/jobs/social` |
| 京东 | `campus.jd.com` | SPA 空壳（`talent.jd.com` 无效，跳错误页） |
| 网易 | `campus.163.com` / `hr.163.com` | SPA 空壳 |
| 小米 | `hr.xiaomi.com`（`job` 子域跳转至此） | SPA 空壳 |
| 快手 | `campus.kuaishou.cn` | SPA 空壳（`hr`/`talent` 子域返回 502） |
| 哔哩哔哩 | `jobs.bilibili.com` | SPA 空壳 |
| 美团 | `zhaopin.meituan.com` | SPA，线索 `/api/category/allData` |
| 华为 | `career.huawei.com` | Vue 模板未渲染；模板变量暴露 `pageVO` 分页结构 |
| 比亚迪 | `job.byd.com` / `careers.byd.com` | SPA 空壳（`hr` 子域 403） |
| 中国电信 | `job.chinatelecom.com.cn` | SPA 空壳 |
| 中国联通 | `campus.chinaunicom.cn` | SPA 空壳 |

### 第三梯队：可能较易接入

| 企业 | 站点 | 线索 |
| --- | --- | --- |
| 大疆 | `careers.dji.com` | 可见文字 2402 字，接口线索 `/zh-CN/position/collect`、`/zh-CN/position/process`，值得优先试 |
| 中国建筑 | `hr` / `talent` / `recruit` 三个子域同一套系统 | 线索 `/api/auth/get_customer_css`，`get_customer_css` 为多租户 SaaS 特征，可能又是一套可复用 ATS |

### 第四梯队：有访问防护，需单独评估

| 企业 | 站点 | 状态 |
| --- | --- | --- |
| 国家电网 | `zhaopin.sgcc.com.cn` | HTTP 412 |
| 中国石油 | `zhaopin.cnpc.com.cn` | HTTP 412 |

两者返回同一类状态码，疑似同一防护方案。**不得以伪装身份或绕过手段接入**（项目硬约束）。可考虑的合规路径：确认是否有对应的公开公告页、或该企业是否同时在其他官方渠道发布。若无合规路径，归入"仅存公告链接"层。

### 第五梯队：需人工查找入口

常见招聘子域不存在或无效，需人工确认官方招聘入口后再评估。

| 企业 | 情况 |
| --- | --- |
| 拼多多 | `campus`/`hr`/`talent` 三个子域全部重定向至主站，招聘入口不在此 |
| 招商银行、中国银行、国家能源集团 | 无常见招聘子域 |
| 中国石化 | `hr` 连接失败、`job` SSL 错误 |
| 中国中车 | `hr.crrcgc.cc` 连接失败 |
| 工商银行 | `job.icbc.com.cn` SSL 错误 |

## 建议接入顺序

1. **Moka**（携程或宁德时代任一站点抓包）——投入产出比最高，一次可能解锁数十家。
2. **大疆**——第三梯队中线索最明确，可用于快速验证适配器框架对真实数据的正确性。
3. **腾讯校招**（`join.qq.com`）、**阿里**、**字节**——目标用户最关心的企业。
4. **中国建筑**——确认其 SaaS 身份，若为另一套通用 ATS 则优先级上调至第一梯队。
5. 其余按需求排序，第四、五梯队最后处理。

## 复核提示

本快照基于单次探测，站点结构会变化。子域可达性、渲染方式、ATS 指纹在接入前应重新确认。企业名单为按项目设计文档第 2 节目标范围拟定的默认名单，尚未经用户确认，须以用户最终名单为准。
