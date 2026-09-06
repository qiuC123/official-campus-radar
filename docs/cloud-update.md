# 云端每日两次更新

仅更新现有已准入企业官网、官方 ATS 和公开岗位接口，不发现新企业、不调用 Exa、Codex 或微信，也不改变 SSH 私有预览的访问范围。

## 数据与发布

`scripts/export_collector_seed.py` 从只读事务导出全新采集库，显式复制企业、来源配置、公告、岗位、准入及发布证据；不复制个人进度、账户、会话、历史执行日志或搜索候选。未列入清单的表只保留空 schema；旧 SourceVersion 的可空 fetch_run 引用置空，准入证据链原样保留。配置存在凭据提示或非官网来源时拒绝导出。导出不应用数据库迁移，0035 保持未应用。

私有采集库不是公开展示快照。两者位于 `/var/lib/radar-cloud-update/generations/<generation>/`，只有展示文件对 `radar-preview` 组可读；采集数据库、运行日志及报告为采集用户私有。Web 仍读取只含两张展示表的 SQLite。

每轮复制当前采集库到新 generation，串行执行全部已准入岗位来源。只有 `status=success`、来源数大于零、来源失败和批次拒绝均为零，才导出并验证快照。通过原子替换 `current` 符号链接同时切换采集库和展示库。失败或超时不会切换，旧快照继续可读，页面显示实际快照生成时间而非本轮尝试时间。暂停/撤销准入等业务规则不在云端放宽。

## 调度和资源

`radar-cloud-update.timer` 在 `Asia/Shanghai` 的 12:00、20:00 触发，`Persistent=true` 补跑服务器关机错过的触发。systemd 同一个 oneshot 不会重叠，手动脚本与定时任务另有 flock 互斥。错过多个时段合并补跑，不承诺逐时段重放。

采集服务为无登录的 `radar-collector`，无新增端口；`MemoryHigh=768M`、`MemoryMax=1280M`，worker 超时 6600 秒，服务上限 6900 秒并终止整个进程组。浏览器来自独立 Playwright 目录，不读取用户浏览器 profile。内存限制不是完整容量压测。

安装脚本只首次安装，不自动启用定时器。必须先执行真实一轮，检查实际结果后再 `systemctl enable --now radar-cloud-update.timer`。不自动接管/禁用 Windows 的独立本地更新任务。

Windows 源码归档解压必须使用 `tar --no-same-permissions -xzf ...`，保持 root 所有、目录 755、文件 644；首次安装也会归一化权限并拒绝意外符号链接。采集和展示用户都不得修改源码。单文件上传后同样须恢复 644，不能继承 Windows 的 666/777 权限。

## 运维入口（服务器终端）

```sh
systemctl start --no-block radar-cloud-update.service
/opt/radar-runtime/venv/bin/python /opt/radar-private-preview/source/scripts/cloud_update.py --root /var/lib/radar-cloud-update --status
systemctl show radar-cloud-update.service -p ActiveState -p SubState -p Result
systemctl list-timers radar-cloud-update.timer
```

`latest.json` 记录最新尝试；`current` 才是正在展示的版本。服务被系统强杀时，JSON 可能停在 running，必须结合 systemd 的 Result 判断，不把运行中或退出码 0 自动解释为发布成功。定时器只负责执行，不主动向个人聊天发送通知。

## 本机备份与恢复

保留当前版本、最初 seed、最近 7 个成功旧版本及最近 1 个失败工作副本。失败不会挤掉成功备份。SQLite backup API 和 integrity_check 验证工作副本，导出快照另有字段/URL 校验；失败副本只供管理员检查，不可作为恢复目标。

使用实际保留的成功目录名进行恢复（不要在采集运行时操作）：

```sh
runuser -u radar-collector -- /opt/radar-runtime/venv/bin/python /opt/radar-private-preview/source/scripts/cloud_update.py --root /var/lib/radar-cloud-update --restore <generation>
```

恢复同样持有锁，并原子切换两份数据库；记录 `restore.json`，不会假称进行了新采集。初次安装还保留 root 所有的 `display.before-cloud.sqlite3`。这些是同一云盘上的版本备份，可以防更新错误，不能防整盘丢失；异地备份尚未实现。

## 2026-09-06 实机验收

- 阿里云 Linux 3 安装 28 项浏览器系统依赖，以及 Playwright 的 Chromium Headless Shell 151.0.7922.34/revision 1234 和 FFmpeg 1011。Playwright 使用 Ubuntu fallback build，非其官方支持发行版；非 root 空白页启动和本轮真实浏览器来源采集均通过，不将其泛化为所有浏览器特性兼容。
- 首轮为手动启动计划服务单元，13:07:03—13:12:20 完成；generation `run-20260906T050703-7c6ccaf2`、云端 UpdateRun 1：29 来源通过、13 批次更新、0 来源失败、0 拒绝。运行中一次内存观测约 588 MiB，不是全过程峰值或并发压测。
- 新快照生成于北京时间 13:12:17：17 家企业、33 在招批次、9423 岗位、2 历史批次；SHA-256 `0c954886ae43237fee36bc0f1ddef5e8be8ea427cc77a42c6fba9fa269b231ac`。
- 云端采集库的 auth_user、django_session、ApplicationProgress、WeChatAccountIdentity、AnnouncementDiscoveryCandidate 均为 0 行，0035 迁移记录为 0。种子 SHA-256 `293063ec0e63ceb920ffc4ba685279e2c59959733f7165d9bf60caef83c7718a`；导出未改本地业务库。
- 以 `radar-collector` 实际恢复 seed，再恢复新 generation；两次展示文件哈希均与预期一致，HTTP 首页均成功。Linux 集成测试另验收原子指针切换和 flock 竞争拒绝。
- `radar-cloud-update.timer` 已启用，下一次显示为 2026-09-06 20:00 CST；Web 与 timer 均配置随开机恢复，未实际重启服务器。Windows 本地任务保持不变，若电脑开机仍会独立更新本地库。
- Windows Python 3.13 完整测试发现 635 项，633 通过、2 项 Linux 专属测试跳过；ECS 23 项相关测试全部通过（包含这两项 Linux 测试）。check、迁移漂移检查和 diff 检查通过。隧道首页 200、显示快照时间且无个人进度；网站仍仅监听 127.0.0.1:8765。
- 收尾实际发现 Windows 归档继承 666/777 源码权限，已归一化为 root 所有、文件 644/目录 755，并补充 Linux 回归。非 root 采集用户不能改源码；Web 用户不能读采集库、不能写展示库，仍能读取展示快照。
