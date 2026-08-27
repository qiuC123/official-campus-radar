# Recruitment API discovery report

Generated: `2026-08-27T11:29:02+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target S03-C05

- Company: `中国电信集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.chinatelecom.com.cn/ct/zp/`
- Entry page: `https://job.chinatelecom.com.cn/wt/TELE/web/index?brandCode=1#/`
- Final page: `https://job.chinatelecom.com.cn/wt/TELE/web/index?brandCode=1#/`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data`
- Total path: `not inferred`
- Confidence score: `74`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 1,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 2,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 8,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 9,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 10,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 2

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[10].children`
- Total path: `not inferred`
- Confidence score: `74`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[10].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 31,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 32,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 33,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 34,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 35,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 3

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[12].children`
- Total path: `not inferred`
- Confidence score: `74`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[12].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 3,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 4,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 5,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 6,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 7,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 4

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[17].children`
- Total path: `not inferred`
- Confidence score: `74`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[17].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 45,
  "f_type": "list",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 46,
  "f_type": "list",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 47,
  "f_type": "list",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 48,
  "f_type": "list",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 49,
  "f_type": "list",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 5

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[17].children[0].children`
- Total path: `not inferred`
- Confidence score: `74`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[17].children[0].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 50,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 51,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 52,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 53,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 54,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 6

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[17].children[1].children`
- Total path: `not inferred`
- Confidence score: `74`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[17].children[1].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 55,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 56,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 57,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 58,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 60,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 7

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[17].children[4].children`
- Total path: `not inferred`
- Confidence score: `74`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[17].children[4].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 67,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 68,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 69,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 72,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 73,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 8

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[26].children`
- Total path: `not inferred`
- Confidence score: `74`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[26].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 88,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 89,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 90,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 91,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 92,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 9

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[8].children`
- Total path: `not inferred`
- Confidence score: `74`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[8].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 27,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 28,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 29,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 30,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 84,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 10

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[13].children`
- Total path: `not inferred`
- Confidence score: `73`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[13].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 37,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 38,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 39,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 40,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 11

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[30].children`
- Total path: `not inferred`
- Confidence score: `73`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[30].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 109,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 110,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 111,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 112,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 12

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[9].children`
- Total path: `not inferred`
- Confidence score: `73`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[9].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 17,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 19,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 21,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 23,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 13

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[17].children[2].children`
- Total path: `not inferred`
- Confidence score: `72`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[17].children[2].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 61,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 62,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 63,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 14

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[17].children[3].children`
- Total path: `not inferred`
- Confidence score: `72`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[17].children[3].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 64,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 65,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 66,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 15

- Request: `GET https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent?corpCode=TELE`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[28].children`
- Total path: `not inferred`
- Confidence score: `71`
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/web/platform/mvc/officialWeb/briefContent",
  "method": "GET",
  "list_path": "data[28].children",
  "field_map": {
    "position_key": "f_id",
    "title": "cnName",
    "updated_at": "addDate",
    "is_valid": "f_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "corpCode": "TELE"
  },
  "success": {
    "path": "status",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 103,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "cnName": null,
  "addDate": null,
  "f_id": 104,
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

## Target J01-C05

- Company: `上汽大众汽车有限公司`
- Company type: `中外合资`
- Official-source evidence: `https://www.csvw.com/`
- Entry page: `https://csvw.zhiye.com/jobs`
- Final page: `https://csvw.zhiye.com/jobs`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://csvw.zhiye.com/api/Jobad/GetJobAdPageList`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `Data`
- Total path: `Count`
- Confidence score: `44`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, eagleeye-traceid, host, langtype, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, x-requested-with` (values redacted)
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
  "endpoint": "https://csvw.zhiye.com/api/Jobad/GetJobAdPageList",
  "method": "POST",
  "list_path": "Data",
  "field_map": {
    "position_key": "Id",
    "title": "JobAdId",
    "raw_text": "Channel4RewardDescription",
    "updated_at": "PostDateInt",
    "is_valid": "Status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "PageIndex": 0,
    "PageSize": 20,
    "KeyWords": "",
    "SpecialType": 0,
    "PortalId": "",
    "DisplayFields": [
      "Category",
      "Kind",
      "LocId",
      "PostDate",
      "ClassificationOne",
      "ClassificationTwo",
      "WorkWeChatQrCode"
    ]
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "PageIndex",
    "size_param": "PageSize",
    "page_size": 20,
    "start_page": 0,
    "max_pages": 10
  },
  "total_path": "Count",
  "success": {
    "path": "Code",
    "expect": 200
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "Id": "b4814129-6d07-4b99-9ca0-14494a8a91a0",
  "JobAdId": 621082783,
  "PostDateInt": 1774255184000,
  "Kind": "全职",
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```

Sample 2:

```json
{
  "Id": "891dcd4a-a28d-4d5c-bec4-5cab208fdeb9",
  "JobAdId": 621082769,
  "PostDateInt": 1774253905000,
  "Kind": "全职",
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```

Sample 3:

```json
{
  "Id": "8d250e13-7923-4dcb-85fe-568245ca6aff",
  "JobAdId": 621082747,
  "PostDateInt": 1774252802000,
  "Kind": "全职",
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```

Sample 4:

```json
{
  "Id": "7499fab6-2b82-44a9-b84a-33ec98bf3681",
  "JobAdId": 621080450,
  "PostDateInt": 1773730409000,
  "Kind": "全职",
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```

Sample 5:

```json
{
  "Id": "7c8db6d1-cb99-484d-bbc1-b5e68e9c6113",
  "JobAdId": 621077942,
  "PostDateInt": 1773125282000,
  "Kind": "全职",
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```

## Target P13-C05

- Company: `vivo`
- Company type: `民企`
- Official-source evidence: `https://hr.vivo.com/home`
- Entry page: `https://hr-campus.vivo.com/jobs?1=%5B%7B%22id%22%3A%222%22%2C%22label%22%3A%22%E7%A7%8B%E5%AD%A3%E6%A0%A1%E5%9B%AD%E6%8B%9B%E8%81%98%22%7D%5D`
- Final page: `https://hr-campus.vivo.com/jobs?1=%5B%7B%22id%22%3A%222%22%2C%22label%22%3A%22%E7%A7%8B%E5%AD%A3%E6%A0%A1%E5%9B%AD%E6%8B%9B%E8%81%98%22%7D%5D`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://hr-campus.vivo.com/api/Jobad/GetJobAdPageList`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `Data`
- Total path: `Count`
- Confidence score: `44`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, eagleeye-traceid, host, langtype, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, x-requested-with` (values redacted)
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
  "endpoint": "https://hr-campus.vivo.com/api/Jobad/GetJobAdPageList",
  "method": "POST",
  "list_path": "Data",
  "field_map": {
    "position_key": "Id",
    "title": "JobAdId",
    "raw_text": "Channel4RewardDescription",
    "updated_at": "PostDateInt",
    "is_valid": "Status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "PageIndex": 0,
    "PageSize": 20,
    "ClassificationOne": [
      "2"
    ],
    "KeyWords": "",
    "SpecialType": 0,
    "PortalId": "",
    "DisplayFields": [
      "Category",
      "LocId",
      "HeadCount",
      "WorkWeChatQrCode"
    ]
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "PageIndex",
    "size_param": "PageSize",
    "page_size": 20,
    "start_page": 0,
    "max_pages": 10
  },
  "total_path": "Count",
  "success": {
    "path": "Code",
    "expect": 200
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "Id": "73c608d4-e2d3-42b2-bf0a-5af3422d287e",
  "JobAdId": 561282866,
  "PostDateInt": 0,
  "Kind": null,
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```

Sample 2:

```json
{
  "Id": "97d2aef4-c7d8-4c24-99ec-21116a6fa17c",
  "JobAdId": 561282792,
  "PostDateInt": 0,
  "Kind": null,
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```

Sample 3:

```json
{
  "Id": "ee9b82de-304f-45cf-ad43-467e079ef22a",
  "JobAdId": 561282623,
  "PostDateInt": 0,
  "Kind": null,
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```

Sample 4:

```json
{
  "Id": "611a6cbb-f7d9-425f-adf0-abcc40ae0dae",
  "JobAdId": 561282620,
  "PostDateInt": 0,
  "Kind": null,
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```

Sample 5:

```json
{
  "Id": "1cdcdb88-0f5e-4846-a9a4-1c514fbfb8c4",
  "JobAdId": 561282516,
  "PostDateInt": 0,
  "Kind": null,
  "Status": 1,
  "Channel4IsAllowCampusRecommend": false,
  "Channel4CampusReward": null,
  "Channel4CampusScore": null,
  "Channel4CampusRewardDescription": null
}
```
