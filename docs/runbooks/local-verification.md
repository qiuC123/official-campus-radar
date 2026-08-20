# 本地验证

先完成依赖与数据库初始化：

```powershell
py -3.13 -m pip install -r requirements.txt
py -3.13 manage.py migrate
```

运行完整自动化验证：

```powershell
py -3.13 manage.py makemigrations --check --dry-run
py -3.13 manage.py check
py -3.13 manage.py test radar.tests -v 2
py -3.13 manage.py import_source_catalog --path data/source_catalog.csv --dry-run
powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/install_daily_task.ps1)) | Out-Null"
```

启动仅监听本机回环地址的工作台：

```powershell
./scripts/run_local.ps1
```

打开 `http://127.0.0.1:8000/`。预期可见“个人校招信息工作台”、筛选栏、显示列复选框、官方公告和投递入口列、七种手动投递进度，以及漏跑时的 22:00 提醒与“立即更新”按钮。默认只显示招聘中记录；使用 `?status=expired` 可查看已截止历史。列选择仅写入当前浏览器的 `localStorage`。

fixture 测试会模拟 HTML、ETag、304 和来源失败，验证入库、去重、更新、过期和进度隔离；它不表示任何真实企业来源已通过准入。`data/source_catalog.csv` 仅有表头，dry-run 不写数据库。真实来源必须按 `docs/source-onboarding.md` 完成人工证据核验和单独批准后才可启用。

`scripts/install_daily_task.ps1` 默认只打印计划；不得在未单独批准时添加 `-Apply`。

## 受控本地演示数据

演示数据来自 `data/local_demo.json`，只使用保留且不可连接的 `demo.invalid`，不会默认加载。命令会创建一条明确标记为本地 demo 的准入链，并仅为正式列表门控走查将它设为 `enabled`；适配器固定为 `local_demo_disabled`，所以“立即更新”不会访问该域名，也不代表任何真实来源已获准。加载前建议先确认本地没有未保存的手工演示数据：

```powershell
py -3.13 manage.py load_local_demo
./scripts/run_local.ps1
```

预期有 3 条公告：一条北京招聘中（个人进度为“已面试”）、一条已截止和一条已撤回；招聘中记录没有投递入口。页面还会显示过去计划运行造成的漏跑提示。检查城市筛选、13 个独立列开关、`?status=expired`、进度保存、无投递链接提示和漏跑横幅。

本地 HTTP 走查的最小预期是：`/`、`/?status=expired` 和 `/?city=北京` 均返回 200；默认页只含 `demo-active`，历史筛选含 `demo-expired`；页面有 13 个不同的 `data-column` 值，进度 POST 经重定向后仍返回 200。解析器配置只有明确声明 `positions_complete=true` 时，才允许把本次未出现的岗位视为已移除；明确撤回不依赖该声明。

点击“立即更新”时，`local_demo_disabled` 会明确返回离线 `not_modified`，不会尝试解析域名或发出请求；这次点击产生的 `UpdateRun`/`FetchRun` 会继承精确 demo ownership。演示结束后只删除该 ownership 下的受控数据及专用运行记录，而不是按域名模糊删除：

```powershell
py -3.13 manage.py load_local_demo --remove
```

该清理命令不会删除任何其他组织、来源、公告或运行记录。自动化测试还会在测试包加载时阻断所有未 mock 的 `requests` 出站调用；因此未来测试误触网络会立即失败。
