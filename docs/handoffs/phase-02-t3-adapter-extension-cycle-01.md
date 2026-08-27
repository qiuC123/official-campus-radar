# Phase 02 / T3 适配器扩展 Cycle 01

日期：2026-08-27

状态：已完成离线实现与回归；没有访问企业网站，没有执行来源准入

## 目标

解决 T3 Cycle 03 暴露的两个通用适配问题：

1. 中国中车一类接口要求 `application/x-www-form-urlencoded`，而原适配器的 POST 只能发送 JSON。
2. 理想汽车、中国中车返回的是总页数，原适配器只把 `total_path` 当作岗位总条数。

## 新配置契约

### POST 请求正文

- `body_encoding` 省略时保持旧行为：GET 使用 query，POST 使用 JSON。
- POST 可明确配置 `body_encoding: "json"` 或 `body_encoding: "form"`。
- GET 只允许 `body_encoding: "query"`。
- form 模式只允许扁平的标量字段，页码和每页数量也必须是顶层字段；嵌套对象或数组会在发请求前被拒绝。

中国中车类接口的 transport 片段示例：

```json
{
  "method": "POST",
  "body_encoding": "form",
  "body": {
    "recruitType": "1",
    "coordinateLat": "",
    "coordinateLng": ""
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "currentPage",
    "size_param": "pageSize",
    "page_size": 10,
    "start_page": 1,
    "max_pages": 40,
    "total_kind": "pages"
  },
  "total_path": "data.pageForm.totalPage"
}
```

这只是 transport/pagination 示例，不是已准入的完整来源配置。

### 总量语义

- `pagination.total_kind` 省略或为 `items`：`total_path` 表示岗位总条数，保持历史行为。
- `pagination.total_kind: "pages"`：`total_path` 表示总页数；适配器取完报告的全部页数后才标记完整。
- `pages` 模式必须配置 `total_path`。
- 非整数、负数以及“非空岗位页却报告 0 页”都会 fail-closed。

## 安全与兼容边界

- 没有改变 GET、POST JSON 或旧 `total_path` 配置的默认含义。
- 继续清空 Session Cookie、禁用环境代理/认证配置、禁止自动跟随跳转。
- 没有添加浏览器、Cookie、签名计算或新的生产依赖。
- 本 Cycle 只解决传输和分页语义。外部 ATS host 的官网证据与准入仍由 T4 独立审核，不能因为 transport 可发送就自动信任。
- `publishDate`、`releaseTime` 等发布时间字段仍不得自动映射为官网更新时间。

## 离线验证

- POST form 确认使用 `data=`，不会同时发送 JSON 或 query。
- form 嵌套字段、嵌套分页路径和请求方法不匹配均会在请求前拒绝。
- 总页数为 2、第一页 10 条时不会误认为“已经达到总数 2”而提前停止。
- 总页数取完、达到上限以及异常 0 页的完整性语义均有测试覆盖。
