# 小米官方公告原文核验 — 2026-09-07

本批补齐官方公告原文和招聘对象证据，仍未完成公告与 ATS 项目的逐项绑定，新增正式接入为 0。原有 30 条岗位样本和历史失败记录保持不变。

## 已核实的原文

| 公告 | 官方招聘对象 | 官方网申时间 |
| --- | --- | --- |
| [小米集团2027届全球校园招聘计划](https://hr.xiaomi.com/website/campus-notice.html#id=13) | 2027 届海内外应届毕业生；毕业时间 2026-09-01 至 2027-08-31 | 2026-08-10 至 2027 年 6 月底 |
| [小米集团2027届新零售招聘计划](https://hr.xiaomi.com/website/campus-notice.html#id=2) | 同上；专业不限 | 原文为“即日起 - 2027年6月末”；不把后台创建或更新时间当成网申起始日 |
| [小米集团实习生招聘](https://hr.xiaomi.com/website/campus-notice.html#id=3) | 海内外高校全体在校大学生 | 全年招聘 |

官网项目导航另把实习分为“应届实习：面向2027届毕业生”和“非应届实习：面向全体在校大学生”。这是官方导航补充，不能把实习公告整体收窄成仅限 2027 届，也不能未经岗位稳定字段核对就自动新建两个批次。

本次公告接口共返回 7 条，包括上述 3 条、顶尖应届生计划、顶尖实习生、博士后工作站介绍和 FAQ。7 条内容不代表 7 个招聘批次；顶尖项目、博士后与现有 ATS 岗位池的关系未核验，FAQ 不充当独立批次公告。

## 官网到正文的读取链

本次使用普通 HTTP 直接回读官方来源，没有使用第三方转述或浏览器渲染。五个地址分别读取一次，均 HTTP 200：

1. `https://hr.xiaomi.com/website/campus.html`
2. `https://hr.xiaomi.com/website/cli/api/hrportal/domestic/campusNews/list`
3. `https://hr.xiaomi.com/website/assets/js/api.js`
4. `https://hr.xiaomi.com/website/cli/api/hrportal/domestic/programs/list`
5. `https://hr.xiaomi.com/website/campus-notice.html`

首页引入 `assets/js/api.js`，该脚本将公告模块指向上述 `campusNews/list`。列表页面用 `campus-notice.html#id=${item.id}` 生成链接；详情页读取数字 ID，以 `String(d.id) === String(id)` 从同一列表选中记录，再把 `data.title` 和 `data.body` 填入正文。因此本批冻结的是官网自身用于显示公告的原文字段，核验方式是 HTTP 原文加静态渲染逻辑核对，没有声称进行了浏览器视觉验收。

接口 `linkUrl` 仍含 `#id=retail`、`#id=intern` 等旧英文锚点，现行代码不按这些旧名称查找记录。候选公告 URL 使用当前代码生成的数字 ID，并保留旧链接作为历史提示。各 ID 的含义分开保存：例如公告 ID 2 是新零售，官网导航项目 ID 2 却是全球校园招聘；两者也都不是 ATS 的 `job_subject.id`。

官网项目列表还给全球校园和实习项目提供了“查看海外岗位”按钮，目标为 `https://career.mi.com/career`。本批只保存官网指向它的证据，未访问该地址。它与既有 ATS“2027届境外招聘计划”的关系、岗位是否重复或独立、是否属于本轮当前可投范围仍待核验；不能把这个新入口自动等同于已知境外项目。

## 预算与 MCP 状态

用户再次要求“继续项目”后，本批在既有企业公开官网核验范围内进行独立公告回读，预设最多 6 次普通 HTTP 请求、每端点新增最多 1 次、180 秒；实际 5 次，15:59:08 至 16:00:10 北京时间，62.119 秒。关闭自动重定向、重试和环境代理，保持 TLS 校验，每响应上限 1 MiB；没有启动浏览器或跟随 ATS 按钮。

这些官网端点此前已在发现阶段读取，但旧精确计数未完整保留。本批明确保留这个历史缺口，只能证明新增 5 次，不能把新增上限冒充全历史端点预算核验。此前已冻结的 ATS 台账仍为 257/400、岗位已知 10/12；本批没有动用 ATS 余额，没有重试停止的实习调用。公告回读停止后，本批未用的第 6 次额度也不用于追加探索。

开始时还通过当前已连接 MCP 做了一次 `.invalid` 零额度检查，run `20260907-075757-d0f3aa`，实际请求 0。返回仍没有 `error_facts` 和 `artifacts.errors`，说明当前连接尚未加载已经在磁盘验收的诊断修复。本批据此继续独立公告回读；没有用旧连接重试实习。证据为 `work/xiaomi-connected-mcp-diagnostics-20260907.json`。下一次选择 MCP 在线验证前，先重新连接并做零额度检查。

## 产物与剩余工作

- `work/xiaomi-official-announcement-evidence-20260907.json`：实际 HTTP 元数据、响应 SHA-256、选定公开公告字段、官网渲染代码片段和导航证据。响应哈希对应原响应字节；没有保存完整响应、请求头或接口追踪 ID。导航链接的推广查询值省略，仅保留查询键和无查询链接。
- `work/xiaomi-official-announcement-candidates-20260907.json`：按公告 ID 分开的原文区块、招聘对象、网申时间及确定性的来源哈希。每条候选的 ATS 项目编号仍为空，当前投递状态仍待核验。
- `tools/prepare_xiaomi_announcements.py`：只从冻结证据生成上述候选，不联网、不导入爬虫、不写数据库；默认打印摘要，`--write` 写入候选文件。

下一步仍优先小米：核对公告到稳定 ATS 项目的映射（尤其全球校园与境外、实习分层）、实习入口有效样本、海外入口关系、完整分页和独立可投递状态。公告写“全年招聘”或有网申时间范围，均不能代替 ADR 0010 的当前状态证据。官网导航、公告记录和 ATS 样本的数量也不能代替 ADR 0011 的完整项目覆盖。

旧离线岗位候选保存的是此前取证时点的四项缺口，本批不改写旧文件；当前状态应合并阅读本记录。官方原文已取得，完整的“公告、招聘对象与项目绑定”门禁仍未整体通过。生产浏览器接入依然需要小米单企业 ADR，不外推 ADR 0004；数据库、迁移、云端与定时任务未变更。

复现离线投影：

```powershell
py -3.13 tools/prepare_xiaomi_announcements.py
py -3.13 tools/prepare_xiaomi_announcements.py --write
py -3.13 -m unittest tools.tests.test_prepare_xiaomi_announcements -v
```

5 项专项测试覆盖旧锚点与数字身份、实习不继承毕业届别、不以全年招聘推断当前可投、损坏响应拒绝、跨命名空间身份隔离和离线可重复生成。Python 3.13 全量回归 678 项，676 通过、2 项平台跳过，退出码 0；`manage.py check`、`makemigrations --check --dry-run`、`git diff --check` 通过。交付前逐一核对 5 个原响应哈希、7 条公告投影及 MCP 落盘摘要一致，之后删除本批临时原始抓取文件，保留可复核证据与离线候选。
