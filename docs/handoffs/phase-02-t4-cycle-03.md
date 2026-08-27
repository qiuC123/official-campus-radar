# Phase 02 / T4 Cycle 03：25 家来源启用

日期：2026-08-27

状态：25 家已启用；未运行采集；真实岗位仍为 0

## 用户决定

T4 Cycle 02 经独立复审采纳后，用户明确确认进入下一步。本 Cycle 的授权仅包括把 25 家来源从 `verified` 迁移到 `enabled`，不包括访问企业网站或执行 T6 首次真实采集。

## 启用安全检查

新增 `enable_t4_sources` 批量命令。写数据库前必须同时满足：

- Cycle 02 离线报告与当前保存证据、冻结台账和目录重新计算的结果完全一致；
- 25 家来源均处于 `verified`，且 `is_verified=true`、`is_active=false`；
- 来源 URL、适配器和解析配置与冻结目录一致；
- 每条准入哈希链有效，适配器配置再次通过校验；
- 招聘批次表和岗位表为空；
- ATS 来源已经具备有效的官网入口和 host 批准。

命令在一个数据库事务中追加 25 条 `verified → enabled` 事件。任意来源启用后不能通过完整准入复核，整个批次都会回滚。命令不会调用采集器。

## 数据库结果

| 项目 | 数量 |
| --- | ---: |
| 组织 | 25 |
| 官方来源 | 25 |
| `candidate` / `verified` | 0 / 0 |
| `enabled` | 25 |
| `is_active=true` | 25 |
| 完整准入复核通过 | 25 / 25 |
| 准入事件 | 75 |
| 有效准入哈希链 | 25 / 25 |
| ATS 主机批准 | 8 |
| UpdateRun | 0 |
| 招聘批次 / 岗位 | 0 / 0 |

写入前的数据库备份：`C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t4-cycle03-20260827-160114.sqlite3`。

## 复审意见处理

- `verify_t4_sources.py` 的输出数量已改为使用 `len(sources)`，不再硬编码 25。
- 候选目录导入器仍拒绝覆盖 `verified` / `enabled` 来源。这是有意保留的安全边界；未来若要更新已上线配置，应新增独立、可审计的更新流程。

## 边界与下一关

- `enabled` 表示来源现在具备进入正式采集的资格，不表示已经采集过。
- 本 Cycle 网络请求 0，`UpdateRun=0`，批次和岗位均为 0。
- 没有注册 Windows 定时任务，因此不会自行开始每日采集。
- 下一关是 T6 Cycle 01：受控执行首次真实采集。它会访问这 25 个公开招聘来源并可能写入批次和岗位，必须单独启动。

## 最终验证

- 开发工具测试：140 / 140 通过。
- Django 测试：370 / 370 通过。
- `tools/build_t4_source_catalog.py --check`：通过。
- `tools/validate_t4_offline.py --check`：25 / 25 通过，网络请求 0。
- `manage.py check`：0 个问题。
- `manage.py makemigrations --check --dry-run`：No changes detected。
- `git diff --check`：通过。
