# Phase 02 / T3 Cycle 03 三家 API 分页复验

日期：2026-08-27

状态：本 Cycle 已完成；3/3 家 API 分页复验通过，T3 累计可稳定接入数由 2/50 更新为 3/50，仍未达到 H3 的 25/50 最低线

## 本 Cycle 的范围

本轮只复验三个已经有明确 API 线索的目标：拼多多、理想汽车和中国中车。每家只请求第 1、2 页，不扩充企业名单，不访问其他企业，也不把结果写入数据库。

本轮验证“公开接口能否用最简请求稳定取到两页不同岗位”。它不是 T4 来源准入，不代表已经开始每日采集。

## 安全边界与请求预算

- 只访问企业官网或官网直链招聘系统的公开岗位接口。
- 不注册、不登录、不发送 Cookie、不提交求职表单。
- 不绕过验证码、签名、登录限制、访问控制或风控。
- 在线验收工具每家固定只请求第 1、2 页，不自动重试。
- 拼多多本 Cycle 使用 `2/6` 次，理想汽车使用 `2/6` 次。
- 中国中车在确认表单正文时已使用 3 次，本次再使用 2 次，累计停在 `5/6` 次。
- 仅保存允许字段的少量样本，不保存完整响应正文或请求头值。

机器配置：`tools/api-acceptance-cycle-03.json`

验收工具：`tools/validate_live_api_cycle03.py`

脱敏证据：`work/phase-02-t3-api-acceptance-cycle-03.json`

## 在线结果

| 企业 | 请求方式 | 第 1 页 | 第 2 页 | 分页 ID | 校招/实习原始证据 | 结论 |
| --- | --- | ---: | ---: | --- | --- | --- |
| 拼多多 | POST JSON | 10 条 | 3 条 | 两页无重复 | `recruitTypeName=管培生` | 通过 |
| 理想汽车 | GET query | 10 条 | 10 条 | 两页无重复 | 官方 API 路径含 `/school/` | 通过 |
| 中国中车 | POST form | 10 条 | 10 条 | 两页无重复 | 请求 `recruitType=1`，响应样本同为 `1` | 通过 |

三个接口均返回 HTTP 200 和 JSON，岗位 ID、标题、地点可取得。中国中车确认的完整分页正文为：

```text
recruitType=1&currentPage=<页码>&pageSize=10&coordinateLat=&coordinateLng=
```

这解决了 Cycle 02 “接口存在但页码参数未知”的阻断项。因此中国中车现在满足 H3 的五项人工判定，可稳定接入总数从 2 家增加到 3 家。

## 生产适配器兼容性

在线 API 通过不等于当前生产适配器已经能直接采集：

- 拼多多的 POST JSON 和理想汽车的 GET query 与当前适配器 transport 相容。
- 理想汽车返回的 `data.total_pages` 是页数，不能直接当作当前适配器所理解的岗位总条数；正式配置需要增加“总页数”语义或使用有界翻页策略。
- 中国中车必须发送 `application/x-www-form-urlencoded`，当前 `JsonApiSourceAdapter` 的 POST 只支持 JSON，因此正式接入前需要单独增加并测试 form transport。
- 拼多多的 `releaseTime` 和中国中车的 `publishDate` 是发布时间证据，不得冒充官网更新时间 `source_updated_on`。

保存的脱敏样本已通过现有批次/岗位提取契约的离线解析；中国中车“可离线解析”与“当前不能直接发送 form 请求”被分别记录，没有混为一谈。

## H3 核算

| 公司类型 | 冻结数 | 可稳定接入 |
| --- | ---: | ---: |
| 民企 | 20 | 2 |
| 央国企 | 10 | 1 |
| 外资 | 6 | 0 |
| 银行 | 5 | 0 |
| 中外合资 | 4 | 0 |
| 事业单位 | 3 | 0 |
| 社会机构 | 2 | 0 |
| 合计 | **50** | **3** |

结论：`3/50 = 6%`，仍低于 H3 要求的 `25/50 = 50%`。T4、真实采集和生产浏览器采集继续禁止启动。

## 验证命令

- `python -m unittest tools.tests.test_validate_live_api_cycle03 -v`：7/7 通过，全程离线。
- `python tools/validate_live_api_cycle03.py`：只运行一次，3/3 家在线分页复验通过。
- `py -3.13 manage.py test radar.tests.test_t3_cycle03_api_acceptance -v 1`：3/3 通过，验证保存样本的批次/岗位解析与时间语义。
- `py -3.13 manage.py check`：0 个问题。
- `py -3.13 manage.py makemigrations --check --dry-run`：No changes detected。
- `py -3.13 manage.py test -v 1`：273/273 通过。

## 停止线

Cycle 03 不重跑在线工具，也不把三家直接加入生产来源。后续如要接入中国中车，需在独立实现 Cycle 增加 form transport；其余企业继续按平台家族处理分页、招聘范围和读取方式，直到稳定数达到 25/50。
