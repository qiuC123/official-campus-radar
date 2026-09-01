# wechat-oa 集成

招聘雷达把 `wechat-oa` 当作独立的只读微信公众号证据工具。工具源码位于
[`qiuC-tools/CLI/wechat-oa`](https://github.com/qiuC123/qiuC-tools/tree/main/CLI/wechat-oa)，
招聘雷达不复制其源码，也不安装或更新它。

## 本地前置检查

```powershell
wechat-oa --version
```

招聘雷达要求命令位于 `PATH`，且版本不低于 0.4.0。旧的 `wxcli` 可执行文件、
Python 客户端和管理命令不再作为回退路径。

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
