# Recruitment API discovery report

Generated: `2026-08-27T12:48:22+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target P03-C08

- Company: `华为`
- Company type: `民企`
- Official-source evidence: `https://career.huawei.com/cn/campus-recruitment`
- Entry page: `https://career.huawei.com/cn/campus-recruitment`
- Final page: `https://career.huawei.com/cn/campus-recruitment`
- Page status: `200`
- Outcome: skipped
- Reason: 页面出现登录墙，按合规要求已跳过

## Target P06-C08

- Company: `百度`
- Company type: `民企`
- Official-source evidence: `https://talent.baidu.com/external/baidu/campus.html`
- Entry page: `https://talent.baidu.com/jobs`
- Final page: `about:blank`
- Page status: `200`
- Outcome: skipped
- Reason: 页面无可见内容且未捕获 JSON 响应，可能被无头浏览器拦截

## Target P09-C08

- Company: `小米`
- Company type: `民企`
- Official-source evidence: `https://campus.hr.xiaomi.com/`
- Entry page: `https://campus.hr.xiaomi.com/`
- Final page: `https://hr.xiaomi.com/website/campus.html`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://hr.xiaomi.com/website/cli/api/hrportal/domestic/campusNews/list`
- Response: `200` / `application/json`
- Candidate list path: `data`
- Candidate row count: `7`
- Total path: `not inferred`
- Reported total: `None`
- Confidence score: `18`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, cookie, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
- Replay verdict: **可接入** — 最简合规头返回等效非空候选列表；签名头非必需
- Suspicious URL/header/query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |
| 完整头 + Cookie（基线） | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉疑似签名头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉 Cookie | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 同时去掉两者 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 最简合规头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://hr.xiaomi.com/website/cli/api/hrportal/domestic/campusNews/list",
  "method": "GET",
  "list_path": "data",
  "field_map": {
    "position_key": "id",
    "title": "title",
    "raw_text": "description",
    "application_url": "linkUrl",
    "updated_at": "updateTime",
    "is_valid": "status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {},
  "success": {
    "path": "code",
    "expect": 200
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "id": 13,
  "updateTime": "2026-08-10 09:58:05",
  "title": "小米集团2027届全球校园招聘计划",
  "linkUrl": "",
  "status": 1
}
```

Sample 2:

```json
{
  "id": 2,
  "updateTime": "2026-08-10 09:58:07",
  "title": "小米集团2027届新零售招聘计划",
  "linkUrl": "campus-notice.html#id=retail",
  "status": 1
}
```

Sample 3:

```json
{
  "id": 3,
  "updateTime": "2026-06-10 17:37:02",
  "title": "小米集团实习生招聘",
  "linkUrl": "campus-notice.html#id=intern",
  "status": 1
}
```

Sample 4:

```json
{
  "id": 4,
  "updateTime": "2026-08-05 22:05:40",
  "title": "小米集团顶尖应届生计划",
  "linkUrl": "campus-notice.html#id=top-fresh",
  "status": 1
}
```

Sample 5:

```json
{
  "id": 5,
  "updateTime": "2026-08-05 22:05:45",
  "title": "小米集团顶尖实习生",
  "linkUrl": "campus-notice.html#id=top-intern",
  "status": 1
}
```

### Candidate 2

- Request: `GET https://hr.xiaomi.com/website/cli/api/hrportal/domestic/programs/list`
- Response: `200` / `application/json`
- Candidate list path: `data`
- Candidate row count: `3`
- Total path: `not inferred`
- Reported total: `None`
- Confidence score: `16`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, cookie, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
- Replay verdict: **可接入** — 最简合规头返回等效非空候选列表；签名头非必需
- Suspicious URL/header/query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |
| 完整头 + Cookie（基线） | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉疑似签名头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉 Cookie | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 同时去掉两者 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 最简合规头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://hr.xiaomi.com/website/cli/api/hrportal/domestic/programs/list",
  "method": "GET",
  "list_path": "data",
  "field_map": {
    "position_key": "id",
    "title": "title",
    "raw_text": "description",
    "updated_at": "updateTime",
    "is_valid": "status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {},
  "success": {
    "path": "code",
    "expect": 200
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "id": 2,
  "updateTime": "2026-08-05 22:19:28",
  "title": "2027届全球校园招聘计划",
  "status": 1
}
```

Sample 2:

```json
{
  "id": 5,
  "updateTime": "2026-08-05 21:53:19",
  "title": "2027届新零售招聘计划",
  "status": 1
}
```

Sample 3:

```json
{
  "id": 3,
  "updateTime": "2026-08-05 22:07:39",
  "title": "实习生招聘计划",
  "status": 1
}
```

## Target P10-C08

- Company: `网易`
- Company type: `民企`
- Official-source evidence: `https://campus.163.com/`
- Entry page: `https://campus.163.com/`
- Final page: `https://campus.163.com/app/index`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P14-C08

- Company: `大疆创新`
- Company type: `民企`
- Official-source evidence: `https://careers.dji.com/zh-CN/campus`
- Entry page: `https://careers.dji.com/zh-CN/campus/hot-jobs`
- Final page: `https://careers.dji.com/zh-CN/campus/hot-jobs`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.
