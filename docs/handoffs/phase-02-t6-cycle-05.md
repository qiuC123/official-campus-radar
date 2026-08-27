# Phase 02 / T6 Cycle 05：中国联通隔离浏览器采集

日期：2026-08-27
状态：Cycle 05 已完成；中国联通 2704 个岗位已发布，T6 25/25 通过

## 授权与边界

用户在理解“隔离浏览器”和“个人生产浏览器”的区别后明确确认继续。本 Cycle 只允许中国联通使用生产隔离浏览器；不允许读取个人 Chrome/Edge、用户目录、Cookie、`storage_state`、账号、代理或扩展，也不启动 T7 Windows 定时任务。长期边界记录在 ADR 0004。

## 实现

新增 `isolated_browser_json` 适配器。它每次创建一个全新的无头 Chromium context，只打开中国联通公开招聘页，只拦截已核验的 `POST https://fe.zhaopin.com/grace/api/dsc/search-job-list`。

适配器不读取请求头或 Cookie，只校验公开 JSON 请求正文必须仍是已核验的组织范围和空筛选。页面原始 `pageSize=11` 被改成 100，然后按页面“下一页”控件顺序翻页；页间等待 1 秒。业务成功码、总数、页序、最大 40 页、列表结构或岗位唯一键出现异常时都会停止，且不发布不完整结果。

浏览器只负责取得页面已经成功返回的 JSON。字段映射、内容哈希、岗位去重、证据和正式发布仍复用 `JsonApiSourceAdapter`，没有第二套业务规则。

## 数据库安全

切换来源配置前已创建并核对 SQLite 备份：

- 路径：`C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t6-cycle05-20260827-184535.sqlite3`
- 大小：10,100,736 bytes
- SHA-256：`D133AD9769CC981B4C2D89151DC2CF1CF4C6A5C8422F474EA167067CF0DF7BD4`

配置通过“enabled → suspended → verified → enabled”追加 3 条准入事件后切换，没有修改历史事件。配置切换本身网络请求为 0。

## 正式单来源结果

执行命令：

```powershell
py -3.13 manage.py run_daily_update --trigger manual --source-id 15 -v 2
```

| 项目 | 结果 |
| --- | --- |
| UpdateRun | 11 / success |
| FetchRun | 43 / success / HTTP 200 |
| 页面请求规模 | 100 条/页，预计 28 页，页间 1 秒 |
| 发布 | 新增 1 个招聘批次、2704 个当前岗位 |
| 中国联通批次 | `中国联合网络通信集团有限公司校园招聘` / `2027届` |
| 全库结果 | 25 个招聘批次、7398 个当前岗位 |
| 个人浏览器资料 | 未使用 |
| 原始响应正文 | 未落盘 |

机器可重建报告：`work/phase-02-t6-cycle-05.json`。

## 结论

中国联通的公开岗位列表已完整发布，T6 达到 25/25 来源通过。该结果不授权把浏览器适配器复制到其他企业，也不授权安装 Windows 计划任务。T7 仍需用户单独确认。
