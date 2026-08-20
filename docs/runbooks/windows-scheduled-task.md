# Windows 每日 22:00 更新任务

前提：已安装 Python 3.13、已执行 `py -3.13 -m pip install -r requirements.txt` 和 `py -3.13 manage.py migrate`。任务只会调用本地更新命令，不会存储账号或 Cookie。

先进行不会注册任务的预览：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_daily_task.ps1
```

确认输出的任务名、工作目录和命令后，**这是需要用户明确批准的本地系统变更**，才可执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_daily_task.ps1 -Apply
```

在“任务计划程序”中检查 `OfficialCampusRadarDailyUpdate`，其动作应等价于：

```text
py -3.13 <项目目录>\manage.py run_daily_update --trigger scheduled
```

可在任务计划程序中右键“运行”作手动测试；成功、部分失败或失败都会写入本地 `UpdateRun` 记录。电脑关机或休眠时任务可能漏跑；下次打开页面会保留该计划任务未完成的审计事实，即使之后执行了手动更新。

删除任务同样是需要用户明确批准的本地系统变更：

```powershell
Unregister-ScheduledTask -TaskName OfficialCampusRadarDailyUpdate -Confirm:$false
```
