# Phase 02 / T4 Cycle 02：25 家来源离线核验

日期：2026-08-27

状态：25 家已核验；0 家启用；未采集真实岗位

## 用户决定

用户确认启动本 Cycle。授权范围是使用已经保存的脱敏样本做离线配置验收，并将通过者从 `candidate` 迁移到 `verified`；不包含 `enabled` 或真实岗位采集。

## 离线验收结果

`tools/validate_t4_offline.py` 从冻结台账、T3 通过报告和脱敏岗位样本重建最小 JSON，交给注册的生产适配器提取。25 家均通过以下检查：

- T3 指定来源的招聘范围证据和分页完整性证据通过；
- 适配器配置通过安全契约；
- 每个样本均能提取到唯一岗位键和岗位标题；
- 地点映射有样本值或 T3 必填字段验收证据；
- 样本岗位键不重复，岗位列表标记为完整；
- 全程网络请求 0 次、业务数据库写入 0 次。

机器报告：`work/phase-02-t4-offline-validation-cycle-02.json`。

## 本 Cycle 修正

- 美团地点从 `cityList` 修正为 `cityList[].name`，不再把城市对象当成显示文字。
- 腾讯由请求中的 `projectMappingIdList` 限定三个校招项目，移除 Cycle 13 已证明不完整的岗位标签白名单。
- 请求参数已经固定招聘范围时，不再强制响应岗位重复返回同名字段；修复比亚迪数值批次和一汽-大众不回显 `recruitType` 时被误删的问题。
- 百度 `updateDate`、网易/比亚迪 `updateTime`、vivo `ChangeDate`、联通 `job.modifiedTime` 和 Moka `updatedAt` 作为官网更新时间；新增 Unix 秒/毫秒时间戳解析。
- 中国电信 `ReleaseTime` 和 Apple `postingDate` 是发布时间，不再冒充官网更新时间。
- 目录重导入只允许刷新仍处于 `candidate` 的配置；已经核验或启用的来源禁止被目录覆盖。

## 数据库结果

| 项目 | 数量 |
| --- | ---: |
| 组织 | 25 |
| 官方来源 | 25 |
| `candidate` | 0 |
| `verified` | 25 |
| `enabled` | 0 |
| 准入事件 | 50 |
| 有效准入哈希链 | 25 / 25 |
| ATS 主机批准 | 8 |
| 招聘批次 / 岗位 | 0 / 0 |

状态写入前，本地 SQLite 已备份到 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t4-cycle02-20260827.sqlite3`。

## 边界与下一关

- `verified` 表示官网归属、招聘范围、字段映射和离线提取证据已核对，不表示来源已经上线。
- 所有来源仍为 `is_active=false`，正式查询和每日采集均不会读取它们。
- 下一关是 T4 Cycle 03 的 `enabled` 批次批准。必须由用户明确确认后才能执行；启用本身仍不等于启动 T6 首次真实采集。

## 最终验证

- 开发工具测试：140 / 140 通过。
- Django 测试：369 / 369 通过。
- `tools/build_t4_source_catalog.py --check`：通过。
- `tools/validate_t4_offline.py --check`：25 / 25 通过，网络请求 0。
- `manage.py check`：0 个问题。
- `manage.py makemigrations --check --dry-run`：No changes detected。
- `git diff --check`：通过。
