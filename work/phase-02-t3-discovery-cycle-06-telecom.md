# Recruitment API discovery report

Generated: `2026-08-27T12:11:44+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target S03-C06

- Company: `中国电信集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.chinatelecom.com.cn/ct/zp/`
- Entry page: `https://job.chinatelecom.com.cn/wt/TELE/web/index?brandCode=1#/`
- Final page: `https://job.chinatelecom.com.cn/wt/TELE/web/index?brandCode=1#/postinquiry?data=eyJrZXkiOjU4MTYxNywidHlwZSI6IjEiLCJyZWNydWl0UHJvamVjdCI6IiIsInJlY3J1aXRQcm9qZWN0TmFtZSI6IiJ9`
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
  "addDate": null,
  "f_id": 1,
  "f_msg_category": "annual_announcement_title",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 2,
  "f_msg_category": "annual_announcement_content",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 8,
  "f_msg_category": "regist_online",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 9,
  "f_msg_category": "organize_written_interview",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "addDate": null,
  "f_id": 10,
  "f_msg_category": "notice_and_signature",
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
  "addDate": null,
  "f_id": 31,
  "f_msg_category": "dianxin_advantage_1",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 32,
  "f_msg_category": "dianxin_advantage_2",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 33,
  "f_msg_category": "dianxin_advantage_3",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 34,
  "f_msg_category": "dianxin_advantage_4",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "addDate": null,
  "f_id": 35,
  "f_msg_category": "dianxin_advantage_5",
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
  "addDate": null,
  "f_id": 3,
  "f_msg_category": "corp_brief",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 4,
  "f_msg_category": "recruit_target",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 5,
  "f_msg_category": "recruit_unit",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 6,
  "f_msg_category": "recruit_position",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "addDate": null,
  "f_id": 7,
  "f_msg_category": "recruit_workplace",
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
  "addDate": null,
  "f_id": 45,
  "f_msg_category": "campus_recruitment_arrangement",
  "f_type": "list",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 46,
  "f_msg_category": "job_application",
  "f_type": "list",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 47,
  "f_msg_category": "compensation_and_benefits",
  "f_type": "list",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 48,
  "f_msg_category": "training_and_sending_letters",
  "f_type": "list",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "addDate": null,
  "f_id": 49,
  "f_msg_category": "common_problem",
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
  "addDate": null,
  "f_id": 50,
  "f_msg_category": "campus_recruitment_arrangement_1",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 51,
  "f_msg_category": "campus_recruitment_arrangement_2",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 52,
  "f_msg_category": "campus_recruitment_arrangement_3",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 53,
  "f_msg_category": "campus_recruitment_arrangement_4",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "addDate": null,
  "f_id": 54,
  "f_msg_category": "campus_recruitment_arrangement_5",
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
  "addDate": null,
  "f_id": 55,
  "f_msg_category": "job_application_1",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 56,
  "f_msg_category": "job_application_2",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 57,
  "f_msg_category": "job_application_3",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 58,
  "f_msg_category": "job_application_4",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "addDate": null,
  "f_id": 60,
  "f_msg_category": "job_application_6",
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
  "addDate": null,
  "f_id": 67,
  "f_msg_category": "common_problem_1",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 68,
  "f_msg_category": "common_problem_2",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 69,
  "f_msg_category": "common_problem_3",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 72,
  "f_msg_category": "common_problem_6",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "addDate": null,
  "f_id": 73,
  "f_msg_category": "common_problem_7",
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
  "addDate": null,
  "f_id": 88,
  "f_msg_category": "regist_online",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 89,
  "f_msg_category": "organize_written_interview",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 90,
  "f_msg_category": "notice_and_signature",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 91,
  "f_msg_category": "talent_plan1",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "addDate": null,
  "f_id": 92,
  "f_msg_category": "organize_written_interview",
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
  "addDate": null,
  "f_id": 27,
  "f_msg_category": "talent_train_history_1",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 28,
  "f_msg_category": "talent_train_history_2",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 29,
  "f_msg_category": "talent_train_history_3",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 30,
  "f_msg_category": "talent_train_history_4",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 5:

```json
{
  "addDate": null,
  "f_id": 84,
  "f_msg_category": "talent_train_history_5",
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
  "addDate": null,
  "f_id": 37,
  "f_msg_category": "recruitTarget",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 38,
  "f_msg_category": "recruitPosition",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 39,
  "f_msg_category": "organizeWrittenInterview",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 40,
  "f_msg_category": "noticeAndSignature",
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
  "addDate": null,
  "f_id": 109,
  "f_msg_category": "",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 110,
  "f_msg_category": "",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 111,
  "f_msg_category": "",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 112,
  "f_msg_category": "",
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
  "addDate": null,
  "f_id": 17,
  "f_msg_category": "corp_culture_1",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 19,
  "f_msg_category": "corp_culture_2",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 21,
  "f_msg_category": "corp_culture_3",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 4:

```json
{
  "addDate": null,
  "f_id": 23,
  "f_msg_category": "corp_culture_4",
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
  "addDate": null,
  "f_id": 61,
  "f_msg_category": "compensation_and_benefits_1",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 62,
  "f_msg_category": "compensation_and_benefits_2",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 63,
  "f_msg_category": "compensation_and_benefits_3",
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
  "addDate": null,
  "f_id": 64,
  "f_msg_category": "training_and_sending_letters_1",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 65,
  "f_msg_category": "training_and_sending_letters_2",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 3:

```json
{
  "addDate": null,
  "f_id": 66,
  "f_msg_category": "training_and_sending_letters_3",
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
  "addDate": null,
  "f_id": 103,
  "f_msg_category": "recruitTarget",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

Sample 2:

```json
{
  "addDate": null,
  "f_id": 104,
  "f_msg_category": "recruitPosition",
  "f_type": "content",
  "f_status": "0",
  "langTypeStr": "zh-cn"
}
```

### Candidate 16

- Request: `POST https://job.chinatelecom.com.cn/wt/TELE/web/mode400/position/list`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.details`
- Total path: `data.rowCount`
- Confidence score: `48`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-length, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://job.chinatelecom.com.cn/wt/TELE/web/mode400/position/list",
  "method": "POST",
  "list_path": "data.details",
  "field_map": {
    "position_key": "PostId",
    "title": "PostName",
    "location": "WorkPlace",
    "updated_at": "ReleaseTime"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {},
  "total_path": "data.rowCount"
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "PostId": 137902,
  "PostName": "区域解决方案经理（市区）",
  "WorkPlace": "北京市",
  "PostType": "解决方案经理",
  "RecruitNumber": "若干",
  "ReleaseTime": "2026-08-23",
  "RecruitType": 1,
  "quickRecruitType": 21,
  "RecruitTypeName": "校园招聘"
}
```

Sample 2:

```json
{
  "PostId": 137903,
  "PostName": "区域客户经理（市区）",
  "WorkPlace": "北京市",
  "PostType": "",
  "RecruitNumber": "若干",
  "ReleaseTime": "2026-08-23",
  "RecruitType": 1,
  "quickRecruitType": 21,
  "RecruitTypeName": "校园招聘"
}
```

Sample 3:

```json
{
  "PostId": 137905,
  "PostName": "区域客户经理（近郊区）",
  "WorkPlace": "北京市",
  "PostType": "",
  "RecruitNumber": "若干",
  "ReleaseTime": "2026-08-23",
  "RecruitType": 1,
  "quickRecruitType": 21,
  "RecruitTypeName": "校园招聘"
}
```

Sample 4:

```json
{
  "PostId": 137908,
  "PostName": "行业解决方案经理",
  "WorkPlace": "北京市",
  "PostType": "解决方案经理",
  "RecruitNumber": "若干",
  "ReleaseTime": "2026-08-23",
  "RecruitType": 1,
  "quickRecruitType": 21,
  "RecruitTypeName": "校园招聘"
}
```

Sample 5:

```json
{
  "PostId": 137909,
  "PostName": "行业客户经理",
  "WorkPlace": "北京市",
  "PostType": "",
  "RecruitNumber": "若干",
  "ReleaseTime": "2026-08-23",
  "RecruitType": 1,
  "quickRecruitType": 21,
  "RecruitTypeName": "校园招聘"
}
```
