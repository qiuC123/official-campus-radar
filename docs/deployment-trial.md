# 阿里云小规模试部署边界

本轮只准备代码和独立运行环境，不等于网站已上线。目标是用户购买的阿里云 ECS（2 核、2 GiB、Alibaba Cloud Linux 3），不改用 Sites 托管，不重装系统，不覆盖系统 Python。

## 公开与个人使用隔离

- 公共 Web 进程必须使用 `campus_radar.settings_public`：`DEBUG=False`、`RADAR_PUBLIC_READONLY=True`，不提供关闭只读的环境开关。
- 路由白名单仅含招聘首页、历史批次、岗位详情；仅允许 GET/HEAD。个人进度、后台、预览及其他路径返回 404，公开路由写请求返回 405。管理员身份也不能绕过公共进程的限制。
- 公开页面不读取 ApplicationProgress，不显示、筛选或统计个人进度；传入 `progress` 参数不会影响返回结果。公共进程忽略访客传入的登录和消息 Cookie。
- SQLite 使用 `mode=ro` 连接已存在的指定数据库文件，避免未来新增接口意外写库；路径不可放在静态文件目录内。生产文件权限和反向代理仍须独立配置。
- 本地个人工作流不变。个人页面和管理/采集命令只能在本地或另一个仅绑定回环地址、经安全隧道访问的私有进程中运行；私有进程不得接入公网反向代理。不在本轮增加多用户账户体系。

## 必需配置与启动前置条件

公开配置必须显式提供 `DJANGO_SECRET_KEY`（至少 50 字符的随机值）、无通配符的 `DJANGO_ALLOWED_HOSTS`、已存在且绝对路径的 `RADAR_DATABASE_PATH`。可选 `RADAR_STATIC_ROOT` 指定 collectstatic 产物目录。

必须在受信任、仅回环监听的反向代理之后运行；只有代理覆写 `X-Forwarded-Proto` 时才设 `RADAR_TRUST_PROXY_HTTPS=1`。公开配置默认强制 HTTPS 和 secure cookies，禁止为了试访问而关闭这些保护。测试数据库及本地 `.env`、Windows 凭证、个人原始截图不上传。

Web 使用 Python 3.13、`requirements-server.txt`、一个 Gunicorn worker。将来采集串行运行，不与另一个更新进程并发写同一 SQLite。当前依赖文件仍为范围声明，正式发布前须冻结实际安装版本；2 GiB 不是高并发保证。

部署/更新数据库前先备份并审查迁移计划，`0035_exa_first_discovery_records` 继续不应用于业务数据库。公共配置不能用来运行 migrate、创建管理员或采集。不要把 `runserver`、数据库文件或后台入口直接暴露到公网。

## 中文解码

官网公告 HTTP 回读采用 BOM → HTTP 明示 charset → HTML 明示 charset → 严格 UTF-8 → 严格 GB18030 的顺序；候选编码无法严格解码时继续下一种。无法解码则核验失败，不用替换字符或搜索摘要补证据，不依赖可选 chardet 的猜测结果。无声明的其他遗留编码可能失败，需来源级核查，不能宣称识别全部网站编码。

## 仍需单独验收

- Alibaba Cloud Linux 3 上的浏览器及系统库兼容性；之前 Ubuntu/WSL 通过不代表该镜像已通过。
- 公共数据快照/业务数据库迁移、独立权限、反向代理、域名/HTTPS、公网访问及限流。
- 自动备份与恢复测试，以及云端 12:00/20:00 调度、重启恢复和漏跑判断；本轮不接管 Windows 计划任务。
- 云服务器上的完整来源采集和访问压力；网页可打开不能代替采集验收。

## 本轮验收记录 — 2026-09-05

- Windows Python 3.13 完整测试 612 项通过（29.413 秒）；WSL Ubuntu 的独立 Python 3.13 环境 612 项通过（32.102 秒）。Windows 系统检查、迁移漂移检查和差异空白检查通过。
- 阿里云原机安装独立 Python 3.13.15，路径 `/opt/radar-runtime/venv`；系统 `/usr/bin/python3` 仍为 3.6.8。测试代码位于 `/opt/radar-trial/source`，不是已上线服务。
- 阿里云完整测试 612 项通过（53.933 秒，含连接/启动总耗时 62.286 秒）；系统检查与 `uv pip check` 通过。测试使用临时测试数据库，结束后销毁；来源目录根部没有 SQLite 业务文件。
- 实装主要依赖：Django 5.2.17、Gunicorn 26.2.0、Playwright Python 包 1.62.0、Beautiful Soup 4.15.0。安装 Python 包不等于浏览器可运行；没有安装/验证 Chromium，也未执行真实采集。
- 服务器直连下载先后超过 180/420 秒。Workbench 超时不保证远端进程终止，本轮按已核验 PID 停止了两个残留安装进程。改为本机下载 Linux wheel、上传并核对 SHA-256 后离线安装成功；后续远端长命令同时使用服务器端 `timeout`。
- wheel 归档 SHA-256：`3423deafc0d66de6fa8c49e993d3b7ee0e5ef42741bdf9c3deeee4a9d8912090`。测试源码归档 SHA-256：`180e35d42669aee8e1b26a59bb0a24093eb992b1d697eaff6667c59fcb6bea8f`；此后只追加部署验收文档记录。
- 本地真实数据以公共只读配置验证：首页 HTTPS 测试请求为 200，无个人进度控件，后台为 404；公开配置的 SQLite 写入拒绝由回归测试覆盖。业务库只读确认 `0035` 未应用。
- `check --deploy` 剩余 W005/W021：尚未为全部子域启用 HSTS，也未启用预加载。域名确定前保留这两个警告，不宣称部署检查零警告。
- 15:08 检查服务器可用内存约 1565 MiB、磁盘可用 33 GiB，仅 22 端口监听；这是空闲快照，不是容量测试。未上传业务库、个人凭据或原始截图，未改安全组，未启动 Web 服务或云端定时任务。
