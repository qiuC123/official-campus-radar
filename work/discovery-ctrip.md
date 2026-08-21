# Recruitment API discovery report

Generated: `2026-08-21T15:31:10+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target 1

- Entry page: `https://careers.ctrip.com/#/campus`
- Final page: `https://careers.ctrip.com/#/campus/jobList`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://careers.ctrip.com/api/hrrecruit/listActiveNews`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `retValue.recruitNewsList`
- Total path: `retValue.total`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-length, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, w-payload-source` (values redacted)
- Replay verdict: **可接入** — 最简合规头返回等效非空候选列表；签名头非必需
- Suspicious query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |
| 完整头 + Cookie（基线） | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉疑似签名头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉 Cookie | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 同时去掉两者 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 最简合规头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add notice metadata and confirm campus scope.

```json
{
  "endpoint": "https://careers.ctrip.com/api/hrrecruit/listActiveNews",
  "method": "POST",
  "body": {
    "recruitDomain": "School",
    "pager": {
      "index": 1,
      "size": 5
    },
    "head": {
      "language": "zh_CN",
      "version": "1"
    }
  },
  "list_path": "retValue.recruitNewsList",
  "field_map": {
    "position_key": "id",
    "title": "title",
    "raw_text": "content",
    "updated_at": "updateTime",
    "is_valid": "publishStatus"
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "pager.index",
    "size_param": "pager.size",
    "page_size": 5,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "retValue.total",
  "success": {
    "path": "retCode",
    "expect": "201"
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "id": "69a27decffa2676d0f9a5f2d",
  "publishStatus": "true",
  "publishType": "Advertisement",
  "recruitDomain": "School",
  "title": "携程集团2026年春季校园招聘全球启动",
  "updateTime": "2026-03-05"
}
```

Sample 2:

```json
{
  "id": "69a29310d0d9d72154494021",
  "publishStatus": "true",
  "publishType": "Advertisement",
  "recruitDomain": "School",
  "title": "旅行官星辰计划",
  "updateTime": "2026-03-05"
}
```

Sample 3:

```json
{
  "id": "69a28b18ffa2676d0f9a5f32",
  "publishStatus": "true",
  "publishType": "Advertisement",
  "recruitDomain": "School",
  "title": "Eagle Program",
  "updateTime": "2026-03-05"
}
```

Sample 4:

```json
{
  "id": "69a1773dd0d9d72154494000",
  "publishStatus": "true",
  "publishType": "Advertisement",
  "recruitDomain": "School",
  "title": "携程集团2026年春招FAQ",
  "updateTime": "2026-02-28"
}
```

Sample 5:

```json
{
  "id": "699d99d4c0baa9276370261d",
  "publishStatus": "true",
  "publishType": "Advertisement",
  "recruitDomain": "School",
  "title": "选择携程的N个理由——技术篇",
  "updateTime": "2026-02-28"
}
```

### Candidate 2

- Request: `POST https://careers.ctrip.com/api/hrrecruit/getJobAd`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `retValue.recruitJobAdList`
- Total path: `retValue.total`
- Confidence score: `50`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-length, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, w-payload-source` (values redacted)
- Replay verdict: **可接入** — 最简合规头返回等效非空候选列表；签名头非必需
- Suspicious query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |
| 完整头 + Cookie（基线） | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉疑似签名头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉 Cookie | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 同时去掉两者 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 最简合规头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add notice metadata and confirm campus scope.

```json
{
  "endpoint": "https://careers.ctrip.com/api/hrrecruit/getJobAd",
  "method": "POST",
  "body": {
    "condition": {
      "fromId": [],
      "keyword": "",
      "kind": [],
      "country": [],
      "city": [],
      "bucode": [],
      "jobFamilyCode": [],
      "jobFamilyGroupCode": [],
      "category": 2
    },
    "pager": {
      "index": "1",
      "size": "10"
    },
    "head": {
      "language": "zh_CN",
      "version": "1"
    }
  },
  "list_path": "retValue.recruitJobAdList",
  "field_map": {
    "position_key": "id",
    "title": "jobTitle",
    "location": "cityName",
    "updated_at": "publishDate"
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "pager.index",
    "size_param": "pager.size",
    "page_size": 10,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "retValue.total",
  "success": {
    "path": "retCode",
    "expect": "201"
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "id": "29572971",
  "jobTitle": "测试职位（请勿投递）(MJ036531)",
  "publishDate": "2026-08-20",
  "cityName": "上海",
  "internalId": null,
  "kind": "1",
  "kindName": "应届校招生",
  "atsApiType": "Moka"
}
```

### Candidate 3

- Request: `POST https://careers.ctrip.com/api/hrrecruit/getEmployeeStory`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `retValue`
- Total path: `not inferred`
- Confidence score: `15`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-length, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, w-payload-source` (values redacted)
- Replay verdict: **可接入** — 最简合规头返回等效非空候选列表；签名头非必需
- Suspicious query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |
| 完整头 + Cookie（基线） | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉疑似签名头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉 Cookie | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 同时去掉两者 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 最简合规头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add notice metadata and confirm campus scope.

```json
{
  "endpoint": "https://careers.ctrip.com/api/hrrecruit/getEmployeeStory",
  "method": "POST",
  "body": {
    "head": {
      "language": "zh_CN",
      "version": "1"
    }
  },
  "list_path": "retValue",
  "field_map": {
    "title": "title",
    "raw_text": "content",
    "updated_at": "shareTime"
  },
  "success": {
    "path": "retCode",
    "expect": "201"
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "title": "在开放包容型组织中腾飞",
  "shareTime": " "
}
```

Sample 2:

```json
{
  "title": "与全球化平台共同发展",
  "shareTime": "发布于 2023-02-01"
}
```

Sample 3:

```json
{
  "title": "坚持自我，跳脱庸碌",
  "shareTime": " "
}
```
