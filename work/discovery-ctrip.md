# Recruitment API discovery report

Generated: `2026-08-21T15:22:05+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target 1

- Entry page: `https://careers.ctrip.com/`
- Final page: `https://careers.ctrip.com/#/`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

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
  "params": {
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
    "value": "201"
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
