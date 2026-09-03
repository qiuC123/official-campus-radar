# 本地验证

## 自动验证

```powershell
py -3.13 -m pip install -r requirements.txt
py -3.13 -m playwright install chromium
py -3.13 manage.py migrate
py -3.13 manage.py makemigrations --check --dry-run
py -3.13 manage.py check
py -3.13 manage.py test -v 2
py -3.13 -m unittest tools.tests.test_discover_api
```

测试会阻断未 mock 的 `requests` 外网调用。T1/T2 兼容测试只读保存的 fixture，不代表任何真实企业来源已经准入。

Chromium 仅供 ADR 0004 批准的中国联通隔离采集器使用。它不会读取本机 Chrome/Edge 的用户目录；不要给配置增加 Cookie、`storage_state`、代理或个人资料路径。

## 页面走查

```powershell
./scripts/run_local.ps1
```

打开以下本机地址：

- `http://127.0.0.1:8000/`：招聘中的正式 ORM 数据；空库显示诚实空状态。
- `http://127.0.0.1:8000/history/`：已截止或撤回的可信历史批次。
- `http://127.0.0.1:8000/preview/phase-02/`：仅开发模式可用的模拟预览，必须显示“模拟数据，不是线上岗位”。

在 1280px 以上窗口检查：四项统计、完整筛选、每批次前三岗位、展开全部、行内岗位详情、岗位级进度，以及七个独立列开关。公司/批次、岗位标题、城市、进度和投递入口始终显示；其余七项选择保存在浏览器 `localStorage`。

预览页的“立即更新”必须禁用。可用 `?health=normal`、`?health=missing`、`?health=failure` 检查三种模拟运行状态，用 `?view=history` 检查模拟历史页。正式页不得出现模拟企业。

正式岗位进度通过 `POST /positions/<id>/progress/` 自动保存；失败时页面恢复旧值。缺少岗位直投链接时，“批次官网”必须仍是可点击链接。展开接口 `GET /batches/<id>/positions/` 应保留当前筛选参数。

## 受控演示数据

`data/local_demo.json` 只使用不可连接的 `demo.invalid`，不会默认加载，也不会授权真实来源：

```powershell
py -3.13 manage.py load_local_demo
./scripts/run_local.ps1
py -3.13 manage.py load_local_demo --remove
```

清理命令只删除专属 demo ownership 下的数据。Windows 定时任务通过 `scripts/install_daily_task.ps1` 预演，并只在用户明确授权后使用 `-Apply` 注册或替换；当前时段和检查方法见 `docs/runbooks/windows-scheduled-task.md`。
