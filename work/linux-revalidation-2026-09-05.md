# Linux 低配复验 — 2026-09-05

## 分层结论

两轮 Linux 真实全量更新均成功，网站请求全部成功，临时 Linux 定时触发链路也正常。2GiB 低访问量试部署优先评估 **单 Web worker＋串行采集＋SQLite**；双 worker 会触及 1.5GiB 应用预算，单 worker 本轮未触限，但容量余量仍较小。

**不能称为全部 Linux 验收通过或已可直接公网交付**：完整回归中，Windows 594/594 通过，干净 Linux 依赖环境 593/594 通过。发现一项中文 HTML 自动编码识别的不一致，已通过离线对照定位，业务代码和依赖清单尚未修改。

基线 commit：`31f7af2`。机器记录：[linux-revalidation-2026-09-05.json](linux-revalidation-2026-09-05.json)。此前网络中断与 Windows 补充试验仍保留在 [capacity-test-2026-09-05.md](capacity-test-2026-09-05.md)，不覆盖历史结果。

## 测试边界

- WSL2 Ubuntu，Python 3.13.15、Django 5.2.17、Gunicorn 26.2.0；同一生产采集代码，仅使用回环 Web 监听。
- 整个应用、采集器和 Chromium 后代进程受 systemd/cgroup `MemoryMax=1536M`、`MemorySwapMax=0`、`CPUQuota=200%` 限制；运行时读取控制文件并断言生效。1.5GiB 应用预算预留约 0.5GiB 给系统，但不是整台 2GiB 云 VM 的仿真。
- 2 个模拟访客浏览首页、第二页、vivo 筛选和历史页，每次响应后等待 2 秒；没有请求正文或网页 HTML 留存。
- 两轮都从同一新建 SQLite 快照开始，调用 29 个已准入官网/ATS 来源。只写各自副本；没有搜索 Exa/Codex、调用 wechat-oa 或导入个人浏览器会话。
- 正式数据库测试前后 SHA-256 相同：`2F72694BD581D2D7FEFC4F2D66C29842AAB6089318647D4D9576A738AD70110C`；正式最新 UpdateRun 仍为 28/success。两轮副本各自的 UpdateRun 29 不得解释为正式更新。

## 网络恢复的核查

本轮最初直接检查时，拼多多返回 302、vivo 返回 200；拼多多、腾讯、中国联通的 Linux DNS 解析已为公网地址。没有修改全局代理、DNS、hosts、防火墙或生产公网校验，也没有给采集器新增代理。网络恢复的外部原因未确定，不能声称本轮修复了上次的 Fake-IP/连接问题。

## 两轮结果

| 项目 | 双 Web worker | 单 Web worker |
| --- | --- | --- |
| 总耗时（含基线） | 308.00 秒 | 308.33 秒 |
| 已准入来源 | 29/29 成功 | 29/29 成功 |
| 副本发布 | 更新 28 批次，0 拒绝 | 更新 28 批次，0 拒绝 |
| 业务状态 | success | success |
| 基线请求 | 8/8 成功 | 8/8 成功 |
| 采集期间请求 | 153/153 成功 | 146/146 成功 |
| 采集期间 P50 / P95 | 2.2494 / 3.3672 秒 | 2.3512 / 3.7092 秒 |
| 采集期间最慢请求 | 6.2407 秒 | 6.5264 秒 |
| cgroup 内存峰值 | 1536.13MiB，约 1.50GiB | 1386.07MiB，约 1.35GiB |
| memory.events max | 1990 | 0 |
| OOM / OOM kill | 0 / 0 | 0 / 0 |

两轮中国联通均成功。本轮没有复现此前 Windows 限制条件下的单源超时，但不能由此断言之前仅是操作系统差异。

双 worker 的 `max` 事件说明内存分配碰到上限并触发回收，不是 1990 次 OOM。单 worker 峰值比 1.5GiB 应用上限低约 150MiB，不能描述为余量充裕。

总体 P95 不能掩盖个别路由的长尾：单 worker 的第二页 P95 为 6.4231 秒；它适合低访问量试运行，不代表页面性能优化已经完成。

两轮是顺序执行的单次实验，外部内容、网络和文件缓存可能不同，不把全部峰值或延迟差值归因于 worker 数量。没有覆盖云实例 CPU 性能、长期运行、高并发、PostgreSQL、TLS/反向代理、备份负载或云磁盘/带宽上限。

## 临时 Linux 定时触发

第一轮由 user systemd 一次性 `OnActive=5s` timer 启动，实际触发时间 `2026-09-05 10:30:55 CST`；服务启动后采集运行记录为 `trigger=scheduled`、日期 2026-09-05，最终业务状态 success。

`systemd-analyze calendar` 分别验证 `*-*-* 12:00:00 Asia/Shanghai` 与 `*-*-* 20:00:00 Asia/Shanghai`，下一次对应当日 12:00/20:00。这里只验证表达式和一次真实调度链，没有安装永久 Linux 计划任务，也没有验证重启后持久化、漏跑补偿或两个正式时段的连续执行。第二轮是手工触发对照。

测试后未发现测试 timer，18765 无监听；Windows 原有计划任务不变。

## 新发现：未声明编码检测依赖导致识别不一致

Linux 完整回归唯一失败为 `OfficialDiscoveryContractTests.test_probe_refetches_known_source_but_keeps_it_as_candidate`，断言 `recruitment_signal_found` 应为 true、实际为 false。

`radar/services/announcement_discovery.py` 的 HTTP 公告回读把 bytes 直接交给 `BeautifulSoup(body, "html.parser")` 自动猜编码。对测试中无 charset 声明的 UTF-8 中文 HTML：

- Windows 全局环境额外存在 chardet 5.1.0，BeautifulSoup 识别为 UTF-8，招聘词命中。
- Linux 按项目声明依赖准备的环境没有 chardet，识别成 `mac_latin2`，中文乱码，招聘词未命中。
- 同一 Linux 环境仅在独立临时 `--target` 目录加入 chardet 5.1.0，通过进程级 PYTHONPATH 注入后，识别恢复为 UTF-8，原失败测试单独运行 1/1 通过；未修改原虚拟环境或项目 requirements。
- 离线明确指定 UTF-8 的解析也正确；这些对照没有网络请求。不能据此把所有官网内容强制当作 UTF-8，修复仍需兼顾网站声明的其他编码。

因此这不是内存不足；它是依赖环境差异暴露的中文解码问题。当前两轮生产准入来源采集均成功，但未来官网公告候选核验可能漏识别。部署前应实施确定的解码/依赖策略并补充回归，再用干净 Linux 环境完整通过测试。本轮只定位、记录，不交付业务修复；额外注入 chardet 后未重跑全部 594 项，不能把定向 1/1 冒充全量通过。

## 验证及留存

- Windows `py -3.13 manage.py test -v 1`：594/594 通过；check、makemigrations --check --dry-run 均通过。
- Linux 原声明依赖环境 Python 3.13 完整测试：593/594，通过之外保留上述 1 个失败；check、迁移漂移检查均通过。
- 正式迁移 0035 未应用；测试库迁移与销毁不改变业务库。
- 只交付测试记录，没有修改业务代码、模板、配置或行为契约；因此本轮没有新增项目测试用例。
- 原始请求计时、采样、日志、临时脚本和数据库副本留在本机 Temp 的 `radar-linux-revalidation-20260905`、`radar-linux-singleworker-20260905` 目录；副本和依赖文件不进入 Git。
