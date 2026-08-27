# Phase 02 / T6 Cycle 03：中国联通独立复验

日期：2026-08-27
状态：Cycle 03 已完成；重新发现成功，但生产分页仍不稳定，未发布岗位

## 授权与边界

用户确认只对中国联通启动新一轮复验。本 Cycle 允许一次开发期 T2 页面监听、少量公开 JSON 判别请求、审计配置修正和中国联通单源采集；不访问其他 24 家，不启用生产浏览器、代理池、登录、Cookie、签名逆向或定时任务。

## 重新发现

T2 只创建 1 个页面上下文并打开 1 次 `https://zglt.zhaopin.com/scjobs/index.html`。它重新观察到：

- `POST https://fe.zhaopin.com/grace/api/dsc/search-job-list`
- 岗位数组 `data.jobList`
- 总数 `data.pageInfo.totalNum = 2704`
- 页面原始请求为 `pageIndex=1`、`pageSize=11`
- 固定 5 级重放全部返回等效非空列表；Cookie 和签名头均不需要

独立发现证据保存在 `work/phase-02-t6-cycle-03-unicom-discovery.md`，没有覆盖 T2 Cycle 01/02 或 T3 历史证据。

## 请求头修正

旧配置携带已经过期的 `webapp.zhaopin.com` Origin/Referer。一次 100 条最小请求曾返回业务 `code=200`，因此配置改为只保留两个公开 JSON 头：

```json
{
  "Accept": "application/json, text/plain, */*",
  "Content-Type": "application/json;charset=UTF-8"
}
```

项目自己的低频 User-Agent 仍由适配器统一添加。没有加入 Cookie、Authorization、签名或系统代理。适配器只新增 `Content-Type` 这一项无凭据白名单，Cookie 等凭据头仍会被拒绝。

两次配置细化均按“暂停 → 改配置 → 复核 → 启用”追加审计事件，历史事件没有删除或覆盖。第一次只删除旧 Origin/Referer；后续判别确认精确媒体类型后，再追加第二组事件写入最终值。

## 正式单源结果

正式采集仅指定来源 ID 15：

| UpdateRun | 范围 | 结果 | 安全结果 |
| ---: | --- | --- | --- |
| 9 | 中国联通 | `JSON API success check failed` | 0 批次、0 岗位、0 发布事件 |
| 10 | 中国联通 | `JSON API success check failed` | 0 批次、0 岗位、0 发布事件 |

进一步有界判别显示，接口并非稳定的普通页码接口：`pageIndex=2` 在 `pageSize=100` 和官网使用的 `pageSize=11` 下都返回 HTTP 200、业务 `code=500`；随后第 1 页也再次返回同样业务错误。接口曾短暂成功，不能证明它可供每日完整、低频、可重复采集。

因此本 Cycle 不提高 100 页安全上限，不发起约 246 页抓取，不使用浏览器或代理绕过，也不把短暂成功追认为接入成功。

## 数据库与备份

- Cycle 03 前备份：`C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t6-cycle03-20260827-174349.sqlite3`
- 最终请求头修正前备份：`C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t6-cycle03-final-20260827-174637.sqlite3`
- 中国联通仍为 0 批次、0 岗位；已有 24 家、4694 个岗位未受影响。
- 原始响应未落盘；机器记录为 `work/phase-02-t6-cycle-03.json`。

## 结论

Cycle 03 的“重新发现与安全复验”已完成，但中国联通仍未达到稳定发布标准。T6 保持部分通过：24/25 家已发布，联通等待上游恢复或未来获得新的公开分页契约。T7 仍不启动。

最终离线回归：开发工具测试 140/140（另 62 个子测试）、Django 测试 386/386；`manage.py check`、迁移检查、机器报告重建和 `git diff --check` 均通过。
