# Windows 每日 12:00、20:00 更新任务

前提：已安装 Python 3.13、已执行 `py -3.13 -m pip install -r requirements.txt` 和 `py -3.13 manage.py migrate`。任务只会调用本地更新命令，不会存储账号或 Cookie。

先进行不会注册任务的预览：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_daily_task.ps1
```

确认输出的任务名、工作目录和命令后，**这是需要用户明确批准的本地系统变更**，才可执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_daily_task.ps1 -Apply
```

在“任务计划程序”中检查 `OfficialCampusRadarDailyUpdate`。它只有一个任务、两个每日触发器，分别为本机时间 12:00 和 20:00；动作应等价于：

```text
py -3.13 <项目目录>\manage.py run_daily_update --trigger scheduled
```

任务固定使用安装时解析到的 `py.exe` 绝对路径和项目绝对路径。若电脑在触发时关机或不可用，任务会在下次可用时启动；同一个任务仍在运行时，新的触发会被忽略，单次运行最长两小时，避免两次全量采集并发写入 SQLite。

任务只执行 `run_daily_update --trigger scheduled`，直接更新已经准入的企业官网、官方 ATS 和公开岗位接口。它不会运行公告候选发现，也不会调用 Exa、Codex 或 `wechat-oa`。

可在任务计划程序中右键“运行”作手动测试；成功、部分失败或失败都会写入本地 `UpdateRun` 记录。页面按最近已经到期的 12:00 或 20:00 时段判断是否漏跑；手工更新不能冒充计划任务记录。

只读检查任务配置：

```powershell
Get-ScheduledTask -TaskName OfficialCampusRadarDailyUpdate | Select-Object -ExpandProperty Triggers
Get-ScheduledTaskInfo -TaskName OfficialCampusRadarDailyUpdate
```

删除任务同样是需要用户明确批准的本地系统变更：

```powershell
Unregister-ScheduledTask -TaskName OfficialCampusRadarDailyUpdate -Confirm:$false
```
