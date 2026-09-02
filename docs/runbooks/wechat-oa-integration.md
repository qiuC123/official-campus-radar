# wechat-oa 集成

招聘雷达把 `wechat-oa` 当作独立的只读微信公众号证据工具。工具源码位于
[`qiuC-tools/CLI/wechat-oa`](https://github.com/qiuC123/qiuC-tools/tree/main/CLI/wechat-oa)，
招聘雷达不复制其源码，也不安装或更新它。

## 本地前置检查

```powershell
wechat-oa --version
```

招聘雷达要求命令位于 `PATH`。导入外部 Candidate Batch 要求版本不低于 0.4.0；
由 `wechat-oa` 原生调用 Exa 的 Direct Discovery 要求版本不低于 0.7.1；0.7.0 会把
企业、账号和日期提示错误收窄为 Provider 硬过滤，可能在候选产生前造成零召回。旧的
`wxcli` 可执行文件、Python 客户端和管理命令不再作为回退路径。

Exa Key 由操作者在交互终端配置一次，并只保存在 `wechat-oa` 自己的 Windows
凭据管理器中：

```powershell
wechat-oa discovery auth configure --provider exa
wechat-oa --json discovery auth status --provider exa
```

招聘雷达不读取、不传递该凭据；启动 `wechat-oa` 时会从子进程环境移除
`EXA_API_KEY`。

## 由 wechat-oa 直接发现公众号公告

开始前，企业必须已经在招聘雷达中登记至少一个带身份核验证据和核验时间的官方公众号；
命令不会根据搜索结果猜测或自动创建公众号身份。缺少该记录时会在启动 `wechat-oa`
之前停止。

默认命令只生成预演，不启动 `wechat-oa`，也不写数据库：

```powershell
py -3.13 manage.py discover_wechat_oa_announcements `
  --organization "企业名称" `
  --query "2027届 秋招" `
  --published-after "2026-06-01" `
  --published-before "2026-09-02"
```

明确允许 Exa 搜索和微信公众号 HTTP 回读时添加 `--allow-live-search`。这仍然不会
写数据库：

```powershell
py -3.13 manage.py discover_wechat_oa_announcements `
  --organization "企业名称" `
  --query "2027届 秋招" `
  --published-after "2026-06-01" `
  --published-before "2026-09-02" `
  --allow-live-search
```

检查结果后，需要导入已核验 Article Evidence 时再单独添加 `--record`。
`--record` 必须与 `--allow-live-search` 同时使用，并按企业事务原子写入。Direct
Discovery 固定调用：

```text
wechat-oa --json discovery search QUERY --company COMPANY --account ACCOUNT
  --provider exa --hydrate --no-browser
```

企业和公众号名称来自招聘雷达数据库；只有具备核验证据和核验时间的公众号身份才会
传给 `wechat-oa`。该路径始终显式禁止 Chrome，不启用媒体分析或 OCR。搜索标题、摘要、
日期提示和排名只作为候选元数据；公告日期、公众号身份和正文只接受 Hydration 返回的
Article Evidence。

空搜索是成功的空候选结果；单篇回读失败会显示为 `partial`，并保留候选级错误码。
Provider 顶层失败会保留 `AUTHENTICATION_ERROR` 或 `NETWORK_ERROR` 以及稳定的
`provider=exa`、`reason`，但不会输出凭据或 Exa 原始响应正文。

命令输出是可被任意 Windows 控制台编码安全写出的 JSON；非 ASCII 字符可能显示为
`\uXXXX` 转义，JSON 解析后的文本不变。

## 导入 Candidate Batch

```powershell
py -3.13 manage.py import_wechat_oa_announcements `
  --organization "企业名称" `
  --input "candidate-batch.json"
```

需要使用非 `PATH` 中的程序时，显式传入：

```powershell
--wechat-oa-path "C:\tools\wechat-oa.exe"
```

命令会在启动 `wechat-oa` 前重新校验字段白名单、凭证特征和微信文章 URL。
Candidate Batch 不能授权浏览器；只有操作者明确添加 `--allow-browser` 时，
招聘雷达才会向 `wechat-oa discovery hydrate` 追加 `--browser`。

`wechat-oa` 只提供文章和媒体证据。企业归属、招聘批次、岗位、投递入口以及
图片 OCR 是否经过人工确认，仍由招聘雷达判断。
