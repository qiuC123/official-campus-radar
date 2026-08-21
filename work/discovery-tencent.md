# Recruitment API discovery report

Generated: `2026-08-21T15:22:50+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target 1

- Entry page: `https://careers.tencent.com/search.html`
- Final page: `https://careers.tencent.com/search.html`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=1787296948654&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=&attrId=&keyword=&pageIndex=1&pageSize=10&language=zh-cn&area=cn`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `Data.Posts`
- Total path: `Data.Count`
- Confidence score: `66`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://careers.tencent.com/tencentcareer/api/post/Query",
  "method": "GET",
  "params": {
    "timestamp": "1787296948654",
    "countryId": "",
    "cityId": "",
    "bgIds": "",
    "productId": "",
    "categoryId": "",
    "parentCategoryId": "",
    "attrId": "",
    "keyword": "",
    "pageIndex": "1",
    "pageSize": "10",
    "language": "zh-cn",
    "area": "cn"
  },
  "list_path": "Data.Posts",
  "field_map": {
    "position_key": "PostId",
    "title": "RecruitPostName",
    "location": "LocationName",
    "raw_text": "Responsibility",
    "application_url": "PostURL",
    "updated_at": "LastUpdateTime",
    "is_valid": "IsValid"
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "pageIndex",
    "size_param": "pageSize",
    "page_size": 10,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "Data.Count",
  "success": {
    "path": "Code",
    "value": 200
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "PostId": "2074756585305059328",
  "RecruitPostId": 121026,
  "RecruitPostName": "智能体套件-高级产品经理-CodeBuddy/WorkBuddy",
  "LocationName": "深圳",
  "LastUpdateTime": "2026年08月21日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=2074756585305059328",
  "IsValid": true,
  "RequireWorkYearsName": "五年以上工作经验"
}
```

Sample 2:

```json
{
  "PostId": "2017980286347935744",
  "RecruitPostId": 117675,
  "RecruitPostName": "《王者荣耀》游戏AI算法研究员- LLM/NLP方向",
  "LocationName": "成都",
  "LastUpdateTime": "2026年08月21日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=2017980286347935744",
  "IsValid": true,
  "RequireWorkYearsName": "三年以上工作经验"
}
```

Sample 3:

```json
{
  "PostId": "2026142331174023168",
  "RecruitPostId": 117904,
  "RecruitPostName": "品牌经理-营销策划方向",
  "LocationName": "深圳",
  "LastUpdateTime": "2026年08月21日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=2026142331174023168",
  "IsValid": true,
  "RequireWorkYearsName": "一年以上工作经验"
}
```

Sample 4:

```json
{
  "PostId": "2076927402918981632",
  "RecruitPostId": 121167,
  "RecruitPostName": "《金铲铲之战》-赛事发行策划项目经理",
  "LocationName": "深圳",
  "LastUpdateTime": "2026年08月21日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=2076927402918981632",
  "IsValid": true,
  "RequireWorkYearsName": "三年以上工作经验"
}
```

Sample 5:

```json
{
  "PostId": "2066401749501132800",
  "RecruitPostId": 120570,
  "RecruitPostName": "腾讯云AI解决方案架构师-(成都/上海/深圳)",
  "LocationName": "北京",
  "LastUpdateTime": "2026年08月21日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=2066401749501132800",
  "IsValid": true,
  "RequireWorkYearsName": "五年以上工作经验"
}
```
