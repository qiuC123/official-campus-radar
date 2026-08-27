# 官方来源准入流程

模板 `data/source_catalog.csv` 不包含任何已启用的企业来源。CSV 中的 `admission_evidence` 只作为待复核候选备注；导入命令只创建 `candidate`，绝不会凭这段文本自动核验或启用。准入状态只能按 `candidate → verified → enabled → suspended/revoked` 追加迁移，已写事件不能在 Admin 改写或删除。

新增来源须由人工完成以下步骤：

1. 从已同意的目标企业池识别候选组织；
2. 在该组织官方域名中定位招聘入口；
3. 记录能证明招聘页或官方招聘公众号归属关系的证据；官网来源 URL host 必须属于官方域名。若投递系统是 ATS，必须记录官网入口 URL 和被明确许可的 ATS/投递 host；
4. 记录低频、公开、无需登录的访问策略；
5. 使用已保存且不含敏感信息的 fixture 离线验证配置。JSON API 来源必须记录 `batch` 配置、稳定岗位唯一键、分页规则、列表路径、字段映射和业务成功条件；必须抽样保存校招判别字段原值并核对岗位性质。POST 默认为 JSON，确需表单时必须显式配置 `body_encoding: form` 且只使用扁平标量字段；`total_path` 表示总页数时必须显式配置 `pagination.total_kind: pages`，否则默认按岗位总条数解释；
6. API 请求必须证明去掉 Cookie、签名头和无关浏览器头后，使用最简合规请求头仍能成功；分页第二页必须与第一页不同，岗位唯一键必须非空且在来源内唯一；
7. HTML 来源至少要有稳定批次/岗位 identity，以及标题、分类、对象、发布日期、截止日期、岗位名、地点、官方页面和原文 selector；
8. 运行 `py -3.13 manage.py import_source_catalog --path data/source_catalog.csv --dry-run`；
9. 在启用新的线上来源批次前取得单独批准。

每次经批准的本地状态迁移都必须记录操作者标签、理由和新的证据。例如核验候选（示例 ID 仅为占位，执行前先在 Admin 只读页或 Django shell 确认真实 ID）：

```powershell
py -3.13 manage.py transition_source_admission --source-id 1 --to-state verified --actor "local-owner" --reason "official domain checked" --evidence "saved local verification record"
```

离线配置验证完成且用户批准该批次后，才能再执行 `--to-state enabled`。暂停或撤销分别使用 `suspended`、`revoked`，不能直接编辑 `is_active`/`is_verified` 绕过事件链。外部 ATS/投递 host 必须先通过 `approve_application_host(...)` 本地服务记录官网入口证据；招聘批次官方页面 URL 仍只允许来源自身 host，二者不会合并为一个宽松白名单。

准入事件按前一事件哈希形成连续链，外部投递 host 批准记录也带事实摘要。正式查询和采集每次都会重新验证这些值；直接改数据库中的派生状态、事件文本或 host 证据会使来源 fail-closed（拒绝进入正式查询或采集）。因此不得通过 SQL、Admin 或脚本补造/改写历史；迁移发现旧审计记录没有可信哈希时会中止并要求人工处理。

本项目不保存 Cookie、账号或验证码处理信息，也不会绕过访问限制。
