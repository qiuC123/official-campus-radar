# Phase 02 / T3 Cycle 02 平台家族探测记录

日期：2026-08-26

状态：进行中；平台指纹基线和样板页只读验证已完成，家族适配验证尚未完成

## 本 Cycle 的决定

用户确认不再把 50 家企业完全视为 50 套独立系统。Cycle 02 改为先识别招聘平台家族，再为每个家族选择样板站验证可复用的岗位读取规则。

本决定只改变 T3 的开发期探测顺序，不代表允许在每日生产采集中运行浏览器，也不代表任何新来源已通过 T4 准入。

## 安全边界

- 企业池仍是 H3 冻结的 50 家，不换入、不扩充名单。
- 只读取无需登录即可访问的企业官网或官网直链招聘系统。
- 不注册、不登录、不填写或提交表单、不投递简历。
- 不绕过验证码、登录限制、访问控制或风控。
- 页面家族验证保持低频；遇到拦截立即停止并记录。
- Cycle 01 的失败、跳过和重放预算保持原样，不覆盖、不追认。
- 未达到 `25 / 50` 最低成功线前，T4 继续禁止启动。

## 50 家指纹基线

机器可读清单：`tools/recruitment-platform-families-cycle-02.json`

| 平台家族 | 已确认成员 | 数量 | 指纹 | 样板 |
| --- | --- | ---: | --- | --- |
| 北森招聘 / `zhiye.com` | S10 中国航空工业、J01 上汽大众、J03 广汽丰田 | 3 | `*.zhiye.com`、`beisen.com` 资源、Powered by 北森 | J03 |
| 大易 / WinTalent | P13 vivo、S03 中国电信、S08 中国中车、I01 中国信通院 | 4 | `/wt/<企业代码>/web/`、`hotjob.cn`、`wintalent.cn`、`wecruit.hotjob.cn` | I01、S08 |
| 智联企业定制校招站 | S04 中国联通、S07 中国海油 | 2 | `*.zhaopin.com`、`webapp.zhaopin.com`、企业定制岗位页 | S04 |
| 已知稳定 API 对照 | P11 拼多多、P20 理想汽车 | 2 | Cycle 01 已按 H3 五项条件人工确认 | P11、P20 |
| 尚未归入共享家族 | 其余目标 | 39 | 可能是企业自建、独立部署、静态内容站或尚未识别的第三方 ATS | 后续按证据处理 |

覆盖核对：`9 + 2 + 39 = 50`，没有遗漏或重复目标。

## 公开资料与样板页证据

### 北森招聘

- 北森官方招聘管理产品说明：<https://www.beisen.com/product/recruitment/>
- 北森自有示例招聘站：<https://beisen2.zhiye.com/>
- J03 广汽丰田公开校招页显示“职位名称、工作地点、发布时间”，页脚出现 `beisen.com` 资源和 Powered by 北森：<https://gac-toyota.zhiye.com/campus/>

结论：三家 `zhiye.com` 目标可以优先验证一套北森家族读取规则，但每家仍需单独配置租户、栏目和招聘范围。

### 大易 / WinTalent

- 公开 WinTalent 页面页脚标明“大易科技”：<https://www.hotjob.cn/wt/CT/web/index>
- I01 中国信通院经典 `/wt/` 岗位页公开显示职位名称、工作地点、发布时间以及 `286` 条、`29` 页分页：<https://www.hotjob.cn/wt/caict/web/index/webPosition210!getPostListByConditionShowPic>
- S08 中国中车入口使用 `wintalent.cn` 资源，并链接到 `wecruit.hotjob.cn` 校招岗位页：<https://sp.wintalent.cn/CRRC/homeMobile/index.html>
- S08 新版岗位页公开显示职位列表、工作地点和职位类别：<https://wecruit.hotjob.cn/SU64d480906202cc36e27a5fd8/mc/position/campus>

结论：该家族至少有经典 `/wt/` 与新版 `wecruit` 两代页面，不能强行共用同一套选择器，因此选择 I01、S08 两个样板。

### 智联企业定制校招站

- 智联校园招聘公开站：<https://xiaoyuan.zhaopin.com/>
- S04 中国联通当前公开页面标明 2027 校园招聘，并在岗位页显示职位名称和工作地点：<https://zglt.zhaopin.com/scjobs/index.html>
- S07 中国海油企业定制页和静态资源均位于智联域名：<https://cnooc.zhaopin.com/job/index.html>

结论：两家可以优先验证一套智联定制站规则；栏目年份和企业项目参数仍必须分别核对。

## 本阶段结论

- 已确认 3 个共享平台家族，覆盖 9/50 家。
- 已为三个家族选出 4 个样板页面；大易因两代架构而使用两个样板。
- 四个样板均能从公开页面看到至少岗位标题、地点或分页中的关键字段，证明“没有独立 JSON 时读取公开 HTML/浏览器 DOM”具有可行性。
- 这些结果只是家族级候选，不计入新的“可稳定接入”数量。只有完成校招范围、岗位字段、地点、分页和稳定读取验证后才能重新计数。
- 下一步是为北森、大易经典版、大易新版、智联定制站分别形成只读解析草案；拼多多和理想继续作为 JSON/API 成功对照。

## 当前停止线

Cycle 02 尚未结束，T3 仍未达到 H3 的 `25 / 50` 最低成功线。不得启动 T4、真实采集、定时任务或生产浏览器采集。

## 本阶段验证

- 机器清单覆盖：50 个目标、50 个唯一 ID、无遗漏、无重复。
- `py -3.13 -m unittest tools.tests.test_discover_api`：52/52 通过。
- `py -3.13 manage.py check`：0 个问题。
- `py -3.13 manage.py makemigrations --check --dry-run`：No changes detected。
- `py -3.13 manage.py test -v 1`：共 256 项，255 项通过，1 项旧测试失败。

失败项为 `test_partial_failure_displays_source_degradation_summary`。本机在 23:37 运行测试，而系统从 22:00 起若没有当天计划任务记录，会优先显示“计划更新可能漏跑”；旧测试没有固定当前时间，却始终断言“来源健康降级”。相关测试和生产模板均未被 Cycle 02 修改，本 Cycle 不混入无关修复，也不把完整测试套写成通过。
