# Phase 01 历史投影筛选修复事实报告

日期：2026-08-18

## 结论与范围

本次仅修复历史页投影筛选这一项缺陷。历史公告的展示岗位、展示投递链接、城市筛选和岗位筛选现在都来自同一个经逐字段证据校验通过的最新 `published`/`updated` Event；当前正式列表继续只使用 `is_current=True` 的岗位与链接。个人投递进度的关联和保存逻辑未改变。

本报告只陈述实施与验证事实，不代表阶段放行。

## TDD 红灯与绿灯

先新增 `radar/tests/test_history_projection.py` 的 4 个回归用例，再修改应用代码。

红灯命令：

```powershell
py -3 manage.py test radar.tests.test_history_projection -v 2
```

旧行为结果：4 项中 2 项失败、2 项通过。

- `test_withdrawn_history_filters_use_the_prior_trusted_event_projection` 失败：撤回后可信岗位已经不是 current，`status=withdrawn&city=北京` 无法找到公告。
- `test_history_does_not_display_or_filter_by_children_outside_selected_event` 失败：历史页展示了没有归属所选可信 Event Evidence 的 `Ghost Analyst`。
- expired 城市/岗位筛选基线与 current 不受非 current 岗位污染的基线通过。

绿灯命令：

```powershell
py -3 manage.py test radar.tests.test_history_projection -v 2
```

修复后结果：4/4 通过，覆盖：

1. published → withdrawn 后按北京和 `Engineer` 均可找到可信历史。
2. expired 历史按上海和 `Engineer` 均可找到。
3. 事后挂到历史公告、但没有归属所选 Event Evidence 的岗位和链接既不展示，也不参与筛选。
4. current 正式列表仍只按 current 岗位筛选和展示；非 current 历史岗位不污染当前列表。

撤回用例同时保存了 `ApplicationProgress=interviewed`，筛选请求后状态不变。

## 最小根因修复

- `radar/services/evidence.py` 新增 `trusted_historical_projection()`：按 Event 主键倒序检查可信 `published`/`updated` Event；只有公告逐字段证据、Event/Version/Source 归属、岗位字段证据和链接证据全部对齐时，才返回该 Event 绑定的 position/link ID 集合。
- `notice_has_trusted_history()` 复用同一个投影选择函数，历史准入资格和页面投影不再各自推断。
- `radar/views.py` 明确拆分两条投影：
  - 历史分支只装载选定可信 Event 的 position/link ID，并用这批同源对象完成城市筛选、岗位筛选和展示。
  - 当前分支保留 `is_current=True` 的筛选，并只预取 current 岗位与链接。
- `radar/templates/radar/notice_table.html` 只渲染视图已绑定的 `visible_positions` 与 `visible_application_links`，不再展开公告全部关联子记录。

没有新增或修改数据库字段，因此没有迁移。

## 完整验证

| 命令 | 结果 |
| --- | --- |
| `py -3 manage.py test radar.tests.test_history_projection -v 2` | 4/4 通过。 |
| `py -3 manage.py test radar.tests -v 1` | 99/99 通过，耗时 1.693s。 |
| `py -3 manage.py makemigrations --check --dry-run` | 退出 0，`No changes detected`。 |
| `py -3 manage.py check` | 退出 0，0 个 system-check 问题。 |
| 对 `scripts/*.ps1` 逐个调用 PowerShell Parser | `install_daily_task.ps1`、`run_local.ps1` 均为 `OK`；没有执行 `-Apply`。 |

## 受控离线 demo：历史组合筛选 → 立即更新 → 清理

初始核验时，Organization、OfficialSource、SourceAdmissionEvent、ApprovedApplicationHost、UpdateRun、FetchRun、SourceVersion、RecruitmentNotice、PublicationEvent、NoticePosition、ApplicationLink、Evidence、ApplicationProgress 均为 0。

1. `py -3 manage.py load_local_demo` 输出 `local_demo_loaded=true notices=3 fixture=data/local_demo.json`。
2. 使用 Django 本地 Test Client 请求 `/?status=withdrawn&city=深圳&position=演示岗位`，HTTP 200；页面包含且只包含 `https://demo.invalid/notices/demo-withdrawn`，不含 active/expired 公告 URL。
3. POST `/update-now/` 并跟随重定向，HTTP 200；demo 来源产生 1 条 `not_modified` FetchRun，此时 demo UpdateRun 为 2、公告为 3。
4. `py -3 manage.py load_local_demo --remove` 输出 `local_demo_removed=true`。
5. 清理后上述 13 个核心表计数全部为 0。

第一次走查脚本用中文页面正文作断言时，命令行中文字面量受当前终端编码影响而断言失败；拆分诊断确认返回行正确，随后改用稳定的 ASCII canonical URL 作等价完整断言并通过。没有把该环境问题当作应用缺陷，也没有据此修改代码。

## 外部边界

- 未访问、导入、验证或启用任何真实企业来源。
- 未注册或触发 Windows 计划任务。
- 未使用账号、Cookie、验证码、代理或自动投递。
- 未发送外部消息、未部署云端、未初始化或操作 Git、未新增依赖。
