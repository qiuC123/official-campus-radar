# Recruitment API discovery report

Generated: `2026-08-27T12:58:34+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target P14-C10

- Company: `大疆创新`
- Company type: `民企`
- Official-source evidence: `https://careers.dji.com/zh-CN/campus/hot-jobs`
- Entry page: `https://apply.careers.dji.com/campus-recruitment/dji/143359?locale=zh-CN#/jobs`
- Final page: `https://apply.careers.dji.com/campus-recruitment/dji/143359?locale=zh-CN#/jobs`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://apply.careers.dji.com/api/extension-server/extension/list-by-org?orgId=dji`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.extensions[0].apps`
- Candidate row count: `16`
- Total path: `not inferred`
- Reported total: `None`
- Confidence score: `13`
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
  "endpoint": "https://apply.careers.dji.com/api/extension-server/extension/list-by-org",
  "method": "GET",
  "list_path": "data.extensions[0].apps",
  "field_map": {
    "title": "name",
    "location": "config.locations"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "orgId": "dji"
  },
  "success": {
    "path": "code",
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "name": "tdAtsWebAggregationDjiHcForm",
  "config.locations": [
    {
      "slot": "head-counts-form",
      "client": [
        "hr-web",
        "hm-web"
      ]
    }
  ]
}
```

Sample 2:

```json
{
  "name": "tdAtsWebAggregationDjiOfferToJdBtn",
  "config.locations": [
    {
      "slot": "candidate-detail-button",
      "client": [
        "hr-web",
        "hr-mob"
      ]
    }
  ]
}
```

Sample 3:

```json
{
  "name": "tdAtsWebAggregationDjiBatchImportOfferMenu",
  "config.locations": [
    {
      "slot": "candidate-list-button",
      "client": [
        "hr-web"
      ]
    }
  ]
}
```

Sample 4:

```json
{
  "name": "tdAtsWebAggregationDjiOficialMenuConfig",
  "config.locations": [
    {
      "slot": "official-menu-config",
      "client": [
        "ap-web",
        "rc-web",
        "ap-mob",
        "rc-mob"
      ]
    }
  ]
}
```

Sample 5:

```json
{
  "name": "tdAtsWebAggregationDjiApplyForm",
  "config.locations": [
    {
      "slot": "apply-form",
      "client": [
        "ap-web",
        "rc-web",
        "ap-mob",
        "rc-mob"
      ]
    }
  ]
}
```
