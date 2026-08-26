# Phase 02 / T2 现场验收 Cycle 02

日期：2026-08-21（Asia/Shanghai）

## 目的与历史边界

本文件定义 T2 的第二个、独立现场验收周期。Cycle 01 因携程目标累计创建
5 个页面、同一 `getEmployeeStory` 端点累计重放 10 次而失败；该历史记录
保持只读，不因本周期结果被覆盖或追认。

## 页面生命周期硬约束

每个目标必须满足：

1. 只执行一次工具命令；
2. 只创建一个浏览器上下文；
3. 只创建一个页面实例；
4. 只执行一次入口 URL 的初始导航；
5. 允许在该页面内滚动，并允许最多一次经过安全检查的点击及其同页导航；
6. 禁止刷新、第二次 `goto`、新窗口、弹窗、表单提交和诊断性补跑；
7. 若未发现目标端点，立即记录本周期失败，不追加页面访问。

两个目标串行执行，目标之间至少间隔 3 秒。

## 重放预算

- 每个标准化端点在整个 Cycle 02 中累计不超过 6 次请求；固定验证阶梯为 5 次。
- 不通过第二个进程或重复目标调用重置端点预算。
- 不登录、不携带凭据、不绕过验证码、不使用代理或 stealth、不扫描路径、
  不穷举参数、不逆向签名。

## 唯一获准命令

以下两条命令各执行一次：

```powershell
C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe tools/discover_api.py --url https://careers.ctrip.com/#/campus --wait 10 --scroll --click "text=查看所有职位" --out work/discovery-ctrip-cycle-02.md
C:\Users\Mayn\AppData\Local\Programs\Python\Python313\python.exe tools/discover_api.py --url https://careers.tencent.com/search.html --wait 10 --scroll --out work/discovery-tencent-cycle-02.md
```

## 验收判定

Cycle 02 只有在以下条件全部满足时才通过：

- 两个目标均遵守页面生命周期硬约束和重放预算；
- 携程报告发现 `POST /api/hrrecruit/getJobAd`，列表路径为
  `retValue.recruitJobAdList`；
- 腾讯报告发现 `GET /tencentcareer/api/post/Query`，列表路径为
  `Data.Posts`；
- 携程最简合规头返回等效非空列表，能够证明签名头非必需；
- 报告保留 `kindName`、`RequireWorkYearsName` 等校招判别字段原值，
  并将端点可调用性与校招数据性质分开判定；
- 输出文件为 Cycle 02 独立文件，不覆盖 Cycle 01 报告。

现场结果与完整计数写入
`work/phase-02-02-live-acceptance-cycle-02.md`。
