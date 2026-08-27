# Phase 02 / T4 Cycle 01：25 家候选来源入队

日期：2026-08-27

状态：已完成候选落库；未核验、未启用、未采集

## 用户决定

用户明确回复“都进入”，因此 T3 稳定台账中的 25 家全部进入 T4。这里的“进入”定义为创建候选来源和初始准入事件，不等于直接上线。

## 本 Cycle 完成内容

- 从 `tools/stable-sources-phase-02-t3.json` 和各 T3 验收配置生成 25 行 `data/source_catalog.csv`。
- 公司类型按领域词汇保存为民企、央国企、外资和中外合资；模型同时具备银行、事业单位、社会机构三个已确认类别。
- CSV 新增 `official_entrypoint_url`，把企业官网入口与外部 ATS 实际招聘页分开保存。
- 增加外部 ATS JSON 适配器，以及 Apple 服务端 hydration、广汽丰田服务端 HTML 两种只读转换器。
- 通用 JSON 适配器新增安全请求头白名单、数组路径、回退路径、行过滤、单页和短页完成规则。
- 应用迁移 `0013`，导入 25 个 Organization、25 个 OfficialSource 和 25 个初始 SourceAdmissionEvent。

## 数据库结果

| 项目 | 数量 |
| --- | ---: |
| 组织 | 25 |
| 官方来源 | 25 |
| 初始准入事件 | 25 |
| 有效候选哈希链 | 25 |
| `candidate` | 25 |
| `verified` | 0 |
| `enabled` | 0 |
| 招聘批次 / 岗位 | 0 / 0 |

本地 SQLite 写入前已备份到 `C:\Users\Mayn\AppData\Local\Temp\official-campus-radar-before-t4-20260827.sqlite3`。

## 边界

- 本 Cycle 没有访问任何企业网站，也没有触发真实岗位采集。
- T3 的“稳定来源”只用于候选证据，不能自动跳过 `verified` 和 `enabled`。
- 下一 Cycle 必须用保存的脱敏样本逐来源验证字段映射、招聘范围、唯一键和完整性；失败来源继续停在 `candidate`，不得硬升状态。

## 验证

- `tools/build_t4_source_catalog.py --check`：25 行与冻结台账一致。
- `import_source_catalog --dry-run`：25 行通过。
- 开发工具测试：137/137 通过。
- Django 完整测试：362/362 通过。
- `manage.py check`：0 个问题。
- `makemigrations --check --dry-run`：No changes detected。
- `git diff --check`：通过。
