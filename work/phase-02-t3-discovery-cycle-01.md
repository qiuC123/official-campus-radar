# Recruitment API discovery report

Generated: `2026-08-26T19:13:35+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target P01

- Company: `腾讯`
- Company type: `民企`
- Official-source evidence: `https://hr.tencent.com/zh-cn/jobopportunity.html`
- Entry page: `https://careers.tencent.com/search.html`
- Final page: `https://careers.tencent.com/search.html`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://careers.tencent.com/tencentcareer/api/post/Query?timestamp=1787741943463&countryId=&cityId=&bgIds=&productId=&categoryId=&parentCategoryId=&attrId=&keyword=&pageIndex=1&pageSize=10&language=zh-cn&area=cn`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `Data.Posts`
- Total path: `Data.Count`
- Confidence score: `66`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://careers.tencent.com/tencentcareer/api/post/Query",
  "method": "GET",
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
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "timestamp": "1787741943463",
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
    "expect": 200
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "PostId": "1955108178685480960",
  "RecruitPostId": 114091,
  "RecruitPostName": "混元大模型语音算法工程师（北京/上海）",
  "LocationName": "深圳",
  "LastUpdateTime": "2026年08月26日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=1955108178685480960",
  "IsValid": true,
  "RequireWorkYearsName": "三年以上工作经验"
}
```

Sample 2:

```json
{
  "PostId": "2067081198903144448",
  "RecruitPostId": 120608,
  "RecruitPostName": "腾讯云- 可用性架构师",
  "LocationName": "杭州",
  "LastUpdateTime": "2026年08月26日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=2067081198903144448",
  "IsValid": true,
  "RequireWorkYearsName": "五年以上工作经验"
}
```

Sample 3:

```json
{
  "PostId": "2046210923894571008",
  "RecruitPostId": 119508,
  "RecruitPostName": "业务经营管理部-CSIG经营分析经理",
  "LocationName": "深圳",
  "LastUpdateTime": "2026年08月26日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=2046210923894571008",
  "IsValid": true,
  "RequireWorkYearsName": "五年以上工作经验"
}
```

Sample 4:

```json
{
  "PostId": "2047202940304912384",
  "RecruitPostId": 119583,
  "RecruitPostName": "FC ONLINE-游戏运营（本地化策划）-新星引力计划",
  "LocationName": "深圳",
  "LastUpdateTime": "2026年08月26日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=2047202940304912384",
  "IsValid": true,
  "RequireWorkYearsName": "两年以上工作经验"
}
```

Sample 5:

```json
{
  "PostId": "1993913307752456192",
  "RecruitPostId": 116247,
  "RecruitPostName": "无畏契约手游-游戏引擎开发工程师-图形渲染",
  "LocationName": "深圳",
  "LastUpdateTime": "2026年08月26日",
  "PostURL": "http://careers.tencent.com/jobdesc.html?postId=1993913307752456192",
  "IsValid": true,
  "RequireWorkYearsName": "两年以上工作经验"
}
```

## Target P02

- Company: `携程集团`
- Company type: `民企`
- Official-source evidence: `https://pages.ctrip.com/commerce/promote/201108/other/hire/aboutctrip1.html`
- Entry page: `https://careers.ctrip.com/#/campus`
- Final page: `https://careers.ctrip.com/#/campus`
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
  "endpoint": "https://careers.ctrip.com/api/hrrecruit/listActiveNews",
  "method": "POST",
  "list_path": "retValue.recruitNewsList",
  "field_map": {
    "position_key": "id",
    "title": "title",
    "raw_text": "content",
    "updated_at": "updateTime",
    "is_valid": "publishStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
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
  "title": "携程集团2027届秋季校园招聘全球启动",
  "updateTime": "2026-08-26"
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
  "updateTime": "2026-08-26"
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
  "updateTime": "2026-08-26"
}
```

Sample 4:

```json
{
  "id": "69a1773dd0d9d72154494000",
  "publishStatus": "true",
  "publishType": "Advertisement",
  "recruitDomain": "School",
  "title": "携程集团2027届秋招FAQ",
  "updateTime": "2026-08-26"
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

- Request: `POST https://careers.ctrip.com/api/hrrecruit/getEmployeeStory`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `retValue`
- Total path: `not inferred`
- Confidence score: `15`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-length, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, w-payload-source` (values redacted)
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
  "endpoint": "https://careers.ctrip.com/api/hrrecruit/getEmployeeStory",
  "method": "POST",
  "list_path": "retValue",
  "field_map": {
    "title": "title",
    "raw_text": "content",
    "updated_at": "shareTime"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "head": {
      "language": "zh_CN",
      "version": "1"
    }
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

## Target P03

- Company: `华为`
- Company type: `民企`
- Official-source evidence: `https://career.huawei.com/cn/campus-recruitment`
- Entry page: `https://career.huawei.com/reccampportal/portal5/campus-recruitment.html?jobTypes=0`
- Final page: `https://career.huawei.com/reccampportal/portal5/campus-recruitment.html?jobTypes=0`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://career.huawei.com/reccampportal/services/portal/portalpub/pub/list/lang/en_US/PORTAL_JOBFAM_CLASS`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: ``
- Total path: `not inferred`
- Confidence score: `16`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-type, cookie, host, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, x-csrf-token, x-jalor-tenantalias, x-requested-with` (values redacted)
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
  "endpoint": "https://career.huawei.com/reccampportal/services/portal/portalpub/pub/list/lang/en_US/PORTAL_JOBFAM_CLASS",
  "method": "GET",
  "list_path": "",
  "field_map": {
    "position_key": "itemId",
    "title": "itemName",
    "updated_at": "creationDate",
    "is_valid": "status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {}
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "creationDate": "2014-09-25T11:45:52.000+0800",
  "itemId": 3771,
  "itemName": "Technology",
  "status": 1,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

Sample 2:

```json
{
  "creationDate": "2014-09-25T11:45:52.000+0800",
  "itemId": 3770,
  "itemName": "Sales",
  "status": 1,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

Sample 3:

```json
{
  "creationDate": "2016-07-05T08:51:15.000+0800",
  "itemId": 7873,
  "itemName": "Service Class",
  "status": 1,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

Sample 4:

```json
{
  "creationDate": "2014-09-25T11:45:52.000+0800",
  "itemId": 3768,
  "itemName": "Supply Chain",
  "status": 1,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

Sample 5:

```json
{
  "creationDate": "2014-09-25T11:45:52.000+0800",
  "itemId": 3769,
  "itemName": "Finance",
  "status": 1,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

### Candidate 2

- Request: `GET https://career.huawei.com/reccampportal/services/portal/portalpub/pub/list/lang/en_US/appraise_bad_reason`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: ``
- Total path: `not inferred`
- Confidence score: `14`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-type, cookie, host, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, x-csrf-token, x-jalor-tenantalias, x-requested-with` (values redacted)
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
  "endpoint": "https://career.huawei.com/reccampportal/services/portal/portalpub/pub/list/lang/en_US/appraise_bad_reason",
  "method": "GET",
  "list_path": "",
  "field_map": {
    "position_key": "itemId",
    "title": "itemName",
    "updated_at": "creationDate",
    "is_valid": "status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {}
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "creationDate": "2024-09-26T09:50:21.000+0800",
  "itemId": 13104,
  "itemName": "Inaccurte recommendations and large deviation",
  "status": 1,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

Sample 2:

```json
{
  "creationDate": "2024-09-26T09:50:21.000+0800",
  "itemId": 13106,
  "itemName": "Slow response and poor user expirence",
  "status": 1,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

Sample 3:

```json
{
  "creationDate": "2024-09-26T09:50:21.000+0800",
  "itemId": 13108,
  "itemName": "no practical help",
  "status": 1,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

### Candidate 3

- Request: `GET https://career.huawei.com/reccampportal/services/portal/portalpub/pub/list/lang/en_US/AI_Job_Recommend_Total_Times`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: ``
- Total path: `not inferred`
- Confidence score: `12`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-type, cookie, host, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, x-csrf-token, x-jalor-tenantalias, x-requested-with` (values redacted)
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
  "endpoint": "https://career.huawei.com/reccampportal/services/portal/portalpub/pub/list/lang/en_US/AI_Job_Recommend_Total_Times",
  "method": "GET",
  "list_path": "",
  "field_map": {
    "position_key": "itemId",
    "title": "itemName",
    "updated_at": "creationDate",
    "is_valid": "status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {}
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "creationDate": "2025-03-15T15:28:32.000+0800",
  "itemId": 13433,
  "itemName": "20",
  "status": 1,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

## Target P04

- Company: `阿里巴巴`
- Company type: `民企`
- Official-source evidence: `https://campus-talent.alibaba.com/campus/gov`
- Entry page: `https://campus-talent.alibaba.com/campus/position`
- Final page: `https://campus-talent.alibaba.com/campus/position?batchId=100000760001`
- Page status: `200`

### Capture notes

- `GET https://lang.alicdn.com/mcms/recruit-careers-center/0.0.56/recruit-careers-center.json` / `200` — JSON body could not be retained: Expecting value: line 1 column 1 (char 0)
- `GET https://lang.alicdn.com/mcms/recruit-careers-portal/0.0.88/recruit-careers-portal.json` / `200` — JSON body could not be retained: Expecting value: line 1 column 1 (char 0)
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://campus-talent.alibaba.com/position/search?_csrf=d638f891-1e2b-458a-b79f-ba6d93e42ba4`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `content.datas`
- Total path: `content.totalCount`
- Confidence score: `62`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-length, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
- Replay verdict: **不可接入** — 最简合规头未返回等效非空候选列表
- Suspicious URL/header/query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |
| 完整头 + Cookie（基线） | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉疑似签名头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉 Cookie | 403 | no | HTTP 403 |
| 同时去掉两者 | 403 | no | HTTP 403 |
| 最简合规头 | 403 | no | HTTP 403 |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://campus-talent.alibaba.com/position/search",
  "method": "POST",
  "list_path": "content.datas",
  "field_map": {
    "position_key": "id",
    "title": "positionUrl",
    "location": "workLocations",
    "raw_text": "description",
    "application_url": "positionUrl",
    "updated_at": "publishTime",
    "is_valid": "status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "batchId": 100000760001,
    "pageIndex": 1,
    "pageSize": 10,
    "channel": "campus_group_official_site",
    "language": "zh"
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "pageIndex",
    "size_param": "pageSize",
    "page_size": 10,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "content.totalCount"
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "positionUrl": null,
  "id": 199907620013,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "广州",
    "杭州",
    "上海",
    "深圳"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

Sample 2:

```json
{
  "positionUrl": null,
  "id": 199907740040,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "广州",
    "杭州",
    "上海"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

Sample 3:

```json
{
  "positionUrl": null,
  "id": 199907640056,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "成都",
    "广州",
    "杭州",
    "上海",
    "深圳"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

Sample 4:

```json
{
  "positionUrl": null,
  "id": 199907640058,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "广州",
    "杭州",
    "上海",
    "深圳"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

Sample 5:

```json
{
  "positionUrl": null,
  "id": 199907720043,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "杭州"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

### Candidate 2

- Request: `POST https://campus-talent.alibaba.com/position/search?_csrf=d638f891-1e2b-458a-b79f-ba6d93e42ba4`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `content.datas`
- Total path: `content.totalCount`
- Confidence score: `62`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, bx-v, content-length, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
- Replay verdict: **未重放** — 共享端点预算只允许一个完整五级重放梯度；该过滤变体已保留但未发出请求
- Suspicious URL/header/query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://campus-talent.alibaba.com/position/search",
  "method": "POST",
  "list_path": "content.datas",
  "field_map": {
    "position_key": "id",
    "title": "positionUrl",
    "location": "workLocations",
    "raw_text": "description",
    "application_url": "positionUrl",
    "updated_at": "publishTime",
    "is_valid": "status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "batchId": 100000760001,
    "pageIndex": 1,
    "pageSize": 10,
    "customDeptCode": "",
    "channel": "campus_group_official_site",
    "language": "zh"
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "pageIndex",
    "size_param": "pageSize",
    "page_size": 10,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "content.totalCount"
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "positionUrl": null,
  "id": 199907620013,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "广州",
    "杭州",
    "上海",
    "深圳"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

Sample 2:

```json
{
  "positionUrl": null,
  "id": 199907740040,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "广州",
    "杭州",
    "上海"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

Sample 3:

```json
{
  "positionUrl": null,
  "id": 199907640056,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "成都",
    "广州",
    "杭州",
    "上海",
    "深圳"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

Sample 4:

```json
{
  "positionUrl": null,
  "id": 199907640058,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "广州",
    "杭州",
    "上海",
    "深圳"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

Sample 5:

```json
{
  "positionUrl": null,
  "id": 199907720043,
  "status": "recruit",
  "publishTime": null,
  "workLocations": [
    "北京",
    "杭州"
  ],
  "experience": null,
  "positionType": null,
  "categoryType": "freshman",
  "useInternal": null
}
```

## Target P05

- Company: `字节跳动`
- Company type: `民企`
- Official-source evidence: `https://jobs.bytedance.com/campus/page-6272Gc`
- Entry page: `https://jobs.bytedance.com/campus/position`
- Final page: `https://jobs.bytedance.com/campus/position`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list`
- Total path: `data.count`
- Confidence score: `61`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list",
  "field_map": {
    "position_key": "id",
    "title": "title",
    "location": "city_info",
    "raw_text": "description",
    "updated_at": "publish_time"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "7677480459190389045",
  "title": "剪映Agent策略运营 - 剪映CapCut",
  "city_info": {
    "code": "CT_128",
    "name": "深圳",
    "en_name": "Shenzhen",
    "location_type": null,
    "i18n_name": "深圳",
    "py_name": null,
    "mdm_code": null,
    "node_status": null
  },
  "recruit_type": {
    "id": "201",
    "name": "正式",
    "en_name": "Regular",
    "i18n_name": "正式",
    "depth": 2,
    "parent": {
      "id": "2",
      "name": "校招",
      "en_name": "Campus",
      "i18n_name": "校招",
      "depth": 1,
      "parent": null,
      "children": null,
      "active_status": 1,
      "selectability": 1
    },
    "children": null,
    "active_status": 1,
    "selectability": 1
  },
  "publish_time": 1787552829692,
  "process_type": 2
}
```

Sample 2:

```json
{
  "id": "7676094235288324405",
  "title": "质量检查（QA）实习生 - TikTok生活服务",
  "city_info": {
    "code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "location_type": null,
    "i18n_name": "北京",
    "py_name": null,
    "mdm_code": null,
    "node_status": null
  },
  "recruit_type": {
    "id": "202",
    "name": "实习",
    "en_name": "Intern",
    "i18n_name": "实习",
    "depth": 2,
    "parent": {
      "id": "2",
      "name": "校招",
      "en_name": "Campus",
      "i18n_name": "校招",
      "depth": 1,
      "parent": null,
      "children": null,
      "active_status": 1,
      "selectability": 1
    },
    "children": null,
    "active_status": 1,
    "selectability": 1
  },
  "publish_time": 1787230042970,
  "process_type": 2
}
```

Sample 3:

```json
{
  "id": "7675650909445572869",
  "title": "营销活动实习生 - 抖音电商",
  "city_info": {
    "code": "CT_125",
    "name": "上海",
    "en_name": "Shanghai",
    "location_type": null,
    "i18n_name": "上海",
    "py_name": null,
    "mdm_code": null,
    "node_status": null
  },
  "recruit_type": {
    "id": "202",
    "name": "实习",
    "en_name": "Intern",
    "i18n_name": "实习",
    "depth": 2,
    "parent": {
      "id": "2",
      "name": "校招",
      "en_name": "Campus",
      "i18n_name": "校招",
      "depth": 1,
      "parent": null,
      "children": null,
      "active_status": 1,
      "selectability": 1
    },
    "children": null,
    "active_status": 1,
    "selectability": 1
  },
  "publish_time": 1787126914812,
  "process_type": 2
}
```

Sample 4:

```json
{
  "id": "7675353973675460869",
  "title": "大模型安全产品实习生 - 火山方舟",
  "city_info": {
    "code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "location_type": null,
    "i18n_name": "北京",
    "py_name": null,
    "mdm_code": null,
    "node_status": null
  },
  "recruit_type": {
    "id": "202",
    "name": "实习",
    "en_name": "Intern",
    "i18n_name": "实习",
    "depth": 2,
    "parent": {
      "id": "2",
      "name": "校招",
      "en_name": "Campus",
      "i18n_name": "校招",
      "depth": 1,
      "parent": null,
      "children": null,
      "active_status": 1,
      "selectability": 1
    },
    "children": null,
    "active_status": 1,
    "selectability": 1
  },
  "publish_time": 1787057652321,
  "process_type": 2
}
```

Sample 5:

```json
{
  "id": "7675304803947841797",
  "title": "商品策略实习生 - 抖音电商运营",
  "city_info": {
    "code": "CT_125",
    "name": "上海",
    "en_name": "Shanghai",
    "location_type": null,
    "i18n_name": "上海",
    "py_name": null,
    "mdm_code": null,
    "node_status": null
  },
  "recruit_type": {
    "id": "202",
    "name": "实习",
    "en_name": "Intern",
    "i18n_name": "实习",
    "depth": 2,
    "parent": {
      "id": "2",
      "name": "校招",
      "en_name": "Campus",
      "i18n_name": "校招",
      "depth": 1,
      "parent": null,
      "children": null,
      "active_status": 1,
      "selectability": 1
    },
    "children": null,
    "active_status": 1,
    "selectability": 1
  },
  "publish_time": 1787046566874,
  "process_type": 2
}
```

### Candidate 2

- Request: `GET https://jobs.bytedance.com/api/v1/config/job/filters/3?_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.city_list`
- Total path: `not inferred`
- Confidence score: `28`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, cookie, env, host, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/config/job/filters/3",
  "method": "GET",
  "list_path": "data.city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "_signature": "[REDACTED]"
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
  "code": "CT_11",
  "name": "北京",
  "location_type": 3,
  "node_status": 1
}
```

Sample 2:

```json
{
  "code": "CT_125",
  "name": "上海",
  "location_type": 3,
  "node_status": 1
}
```

Sample 3:

```json
{
  "code": "CT_128",
  "name": "深圳",
  "location_type": 3,
  "node_status": 1
}
```

Sample 4:

```json
{
  "code": "CT_52",
  "name": "杭州",
  "location_type": 3,
  "node_status": 1
}
```

Sample 5:

```json
{
  "code": "CT_45",
  "name": "广州",
  "location_type": 3,
  "node_status": 1
}
```

### Candidate 3

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[0].city_list`
- Total path: `data.count`
- Confidence score: `25`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[0].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_128",
  "name": "深圳",
  "location_type": null,
  "node_status": null
}
```

Sample 2:

```json
{
  "code": "CT_11",
  "name": "北京",
  "location_type": null,
  "node_status": null
}
```

### Candidate 4

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[1].city_list`
- Total path: `data.count`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[1].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_11",
  "name": "北京",
  "location_type": null,
  "node_status": null
}
```

### Candidate 5

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[2].city_list`
- Total path: `data.count`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[2].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_125",
  "name": "上海",
  "location_type": null,
  "node_status": null
}
```

### Candidate 6

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[3].city_list`
- Total path: `data.count`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[3].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_11",
  "name": "北京",
  "location_type": null,
  "node_status": null
}
```

### Candidate 7

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[4].city_list`
- Total path: `data.count`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[4].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_125",
  "name": "上海",
  "location_type": null,
  "node_status": null
}
```

### Candidate 8

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[5].city_list`
- Total path: `data.count`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[5].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_11",
  "name": "北京",
  "location_type": null,
  "node_status": null
}
```

### Candidate 9

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[6].city_list`
- Total path: `data.count`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[6].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_11",
  "name": "北京",
  "location_type": null,
  "node_status": null
}
```

### Candidate 10

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[7].city_list`
- Total path: `data.count`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[7].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_11",
  "name": "北京",
  "location_type": null,
  "node_status": null
}
```

### Candidate 11

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[8].city_list`
- Total path: `data.count`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[8].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_11",
  "name": "北京",
  "location_type": null,
  "node_status": null
}
```

### Candidate 12

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[9].city_list`
- Total path: `data.count`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[9].city_list",
  "field_map": {
    "position_key": "code",
    "title": "name",
    "location": "location_type",
    "is_valid": "node_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "code": "CT_11",
  "name": "北京",
  "location_type": null,
  "node_status": null
}
```

### Candidate 13

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[0].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `22`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[0].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "7497171927871930371",
  "name": "中国大陆广东省深圳市南山区创业路1555号景湖大厦，邮编：518052",
  "city": {
    "city_code": "CT_128",
    "name": "深圳",
    "en_name": "Shenzhen",
    "i18n_name": "深圳",
    "py_name": "shenzhen"
  },
  "active_status": 1
}
```

Sample 2:

```json
{
  "id": "7516800185394921473",
  "name": "中国大陆北京市海淀区北三环西路甲18号院大钟寺广场1号楼，邮编：100098",
  "city": {
    "city_code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "i18n_name": "北京",
    "py_name": "beijing"
  },
  "active_status": 1
}
```

### Candidate 14

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[1].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `21`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[1].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "7597790889070906571",
  "name": "中国大陆北京市海淀区魏公村路6号院1号楼丽金智地中心西塔，邮编：100081",
  "city": {
    "city_code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "i18n_name": "北京",
    "py_name": "beijing"
  },
  "active_status": 1
}
```

### Candidate 15

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[2].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `21`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[2].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "2064",
  "name": "中国大陆上海市杨浦区民府路678号上海新江湾广场T4号楼2层，邮编：200082",
  "city": {
    "city_code": "CT_125",
    "name": "上海",
    "en_name": "Shanghai",
    "i18n_name": "上海",
    "py_name": "shanghai"
  },
  "active_status": 1
}
```

### Candidate 16

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[3].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `21`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[3].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "7449297142948937732",
  "name": "中国大陆北京市海淀区海淀大街3号鼎好DH3大厦B座，邮编：100080",
  "city": {
    "city_code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "i18n_name": "北京",
    "py_name": "beijing"
  },
  "active_status": 1
}
```

### Candidate 17

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[4].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `21`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[4].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "2064",
  "name": "中国大陆上海市杨浦区民府路678号上海新江湾广场T4号楼2层，邮编：200082",
  "city": {
    "city_code": "CT_125",
    "name": "上海",
    "en_name": "Shanghai",
    "i18n_name": "上海",
    "py_name": "shanghai"
  },
  "active_status": 1
}
```

### Candidate 18

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[5].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `21`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[5].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "1137",
  "name": "中国大陆北京市海淀区花园东路19号中兴大厦1层，邮编：100191",
  "city": {
    "city_code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "i18n_name": "北京",
    "py_name": "beijing"
  },
  "active_status": 1
}
```

### Candidate 19

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[6].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `21`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[6].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "1892",
  "name": "中国大陆北京市朝阳区朝阳北路152号时尚万科中心1层，邮编：100025",
  "city": {
    "city_code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "i18n_name": "北京",
    "py_name": "beijing"
  },
  "active_status": 1
}
```

### Candidate 20

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[7].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `21`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[7].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "1844",
  "name": "中国大陆北京市朝阳区七圣中街12号院融中心A座，邮编：100020",
  "city": {
    "city_code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "i18n_name": "北京",
    "py_name": "beijing"
  },
  "active_status": 1
}
```

### Candidate 21

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[8].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `21`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[8].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "7516806289746477058",
  "name": "中国大陆北京市海淀区北三环西路27号北京方恒中心D座，邮编：100098",
  "city": {
    "city_code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "i18n_name": "北京",
    "py_name": "beijing"
  },
  "active_status": 1
}
```

### Candidate 22

- Request: `POST https://jobs.bytedance.com/api/v1/search/job/posts?keyword=&limit=10&offset=0&job_category_id_list=&tag_id_list=&location_code_list=&subject_id_list=&recruitment_id_list=&portal_type=3&job_function_id_list=&storefront_id_list=&portal_entrance=1&_signature=%5BREDACTED%5D`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.job_post_list[9].job_post_info.address_list`
- Total path: `data.count`
- Confidence score: `21`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `accept, accept-encoding, accept-language, connection, content-length, content-type, cookie, env, host, origin, portal-channel, portal-platform, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, website-path, x-csrf-token` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `query._signature`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://jobs.bytedance.com/api/v1/search/job/posts",
  "method": "POST",
  "list_path": "data.job_post_list[9].job_post_info.address_list",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "location": "city",
    "is_valid": "active_status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "keyword": "",
    "limit": 10,
    "offset": 0,
    "job_category_id_list": [],
    "tag_id_list": [],
    "location_code_list": [],
    "subject_id_list": [],
    "recruitment_id_list": [],
    "portal_type": 3,
    "job_function_id_list": [],
    "storefront_id_list": [],
    "portal_entrance": 1
  },
  "pagination_candidates": {
    "limit": 10,
    "offset": 0
  },
  "pagination_note": "Offset-based pagination is unsupported by the Phase 02 T1 page_index adapter; manual review is required.",
  "total_path": "data.count",
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
  "id": "1892",
  "name": "中国大陆北京市朝阳区朝阳北路152号时尚万科中心1层，邮编：100025",
  "city": {
    "city_code": "CT_11",
    "name": "北京",
    "en_name": "Beijing",
    "i18n_name": "北京",
    "py_name": "beijing"
  },
  "active_status": 1
}
```

## Target P06

- Company: `百度`
- Company type: `民企`
- Official-source evidence: `https://talent.baidu.com/jobs/campus`
- Entry page: `https://talent.baidu.com/jobs/list`
- Final page: `about:blank`
- Page status: `200`
- Outcome: skipped
- Reason: 页面无可见内容且未捕获 JSON 响应，可能被无头浏览器拦截

## Target P07

- Company: `京东`
- Company type: `民企`
- Official-source evidence: `https://zhaopin.jd.com/`
- Entry page: `https://zhaopin.jd.com/`
- Final page: `https://zhaopin.jd.com/home;jsessionid=98464A206B25FB6A699F6509545071D6.s1`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P08

- Company: `美团`
- Company type: `民企`
- Official-source evidence: `https://zhaopin.meituan.com/`
- Entry page: `https://job.meituan.com/web/campus`
- Final page: `https://job.meituan.com/web/campus`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://job.meituan.com/api/official/job/getJobList`
- Response: `200` / `application/json`
- Candidate list path: `data.list`
- Total path: `data.page.totalPage`
- Confidence score: `74`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-length, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, x-requested-with` (values redacted)
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
  "endpoint": "https://job.meituan.com/api/official/job/getJobList",
  "method": "POST",
  "list_path": "data.list",
  "field_map": {
    "position_key": "jobUnionId",
    "title": "jobUnionId",
    "location": "cityList",
    "updated_at": "firstPostTime",
    "is_valid": "jobStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "page": {
      "pageNo": 1,
      "pageSize": 10
    },
    "jobShareType": "1",
    "keywords": "",
    "cityList": [],
    "department": [],
    "jfJgList": [],
    "jobType": [
      {
        "code": "1",
        "subCode": []
      },
      {
        "code": "2",
        "subCode": []
      }
    ],
    "typeCode": [],
    "specialCode": [],
    "u_query_id": "cb46af2b7c4d29f3d4f5f34439e2c22d",
    "r_query_id": "178774211029155625160"
  },
  "pagination_candidates": {
    "page.pageSize": 10
  },
  "total_path": "data.page.totalPage"
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "jobUnionId": "4721378720",
  "jobType": "2",
  "jobStatus": "000",
  "cityList": [
    {
      "code": null,
      "name": "北京市",
      "children": null,
      "sort": null,
      "subCode": null,
      "mapping": null,
      "outerCode": null,
      "bgNode": false
    }
  ],
  "workYear": null,
  "firstPostTime": null
}
```

Sample 2:

```json
{
  "jobUnionId": "4061749831",
  "jobType": "2",
  "jobStatus": "000",
  "cityList": [
    {
      "code": null,
      "name": "北京市",
      "children": null,
      "sort": null,
      "subCode": null,
      "mapping": null,
      "outerCode": null,
      "bgNode": false
    }
  ],
  "workYear": null,
  "firstPostTime": null
}
```

Sample 3:

```json
{
  "jobUnionId": "4241222974",
  "jobType": "2",
  "jobStatus": "000",
  "cityList": [
    {
      "code": null,
      "name": "北京市",
      "children": null,
      "sort": null,
      "subCode": null,
      "mapping": null,
      "outerCode": null,
      "bgNode": false
    }
  ],
  "workYear": null,
  "firstPostTime": null
}
```

Sample 4:

```json
{
  "jobUnionId": "4709281316",
  "jobType": "2",
  "jobStatus": "000",
  "cityList": [
    {
      "code": null,
      "name": "上海市",
      "children": null,
      "sort": null,
      "subCode": null,
      "mapping": null,
      "outerCode": null,
      "bgNode": false
    }
  ],
  "workYear": null,
  "firstPostTime": null
}
```

Sample 5:

```json
{
  "jobUnionId": "4705246640",
  "jobType": "2",
  "jobStatus": "000",
  "cityList": [
    {
      "code": null,
      "name": "北京市",
      "children": null,
      "sort": null,
      "subCode": null,
      "mapping": null,
      "outerCode": null,
      "bgNode": false
    }
  ],
  "workYear": null,
  "firstPostTime": null
}
```

## Target P09

- Company: `小米`
- Company type: `民企`
- Official-source evidence: `https://hr.xiaomi.com/website/campus.html`
- Entry page: `https://hr.xiaomi.com/campus/list`
- Final page: `https://hr.xiaomi.com/campus/list`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P10

- Company: `网易`
- Company type: `民企`
- Official-source evidence: `https://campus.163.com/app/index`
- Entry page: `https://campus.163.com/app/index`
- Final page: `https://campus.163.com/app/index`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P11

- Company: `拼多多`
- Company type: `民企`
- Official-source evidence: `https://careers.pddglobalhr.com/campus/grad`
- Entry page: `https://careers.pddglobalhr.com/campus/grad`
- Final page: `https://careers.pddglobalhr.com/campus/grad`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://careers.pddglobalhr.com/api/careers/api/recruit/position/list`
- Response: `200` / `application/json`
- Candidate list path: `result.list`
- Total path: `not inferred`
- Confidence score: `40`
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
  "endpoint": "https://careers.pddglobalhr.com/api/careers/api/recruit/position/list",
  "method": "POST",
  "list_path": "result.list",
  "field_map": {
    "position_key": "id",
    "title": "jobName",
    "location": "workLocation",
    "updated_at": "releaseTime"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "page": 1,
    "pageSize": 10,
    "t": null
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "page",
    "size_param": "pageSize",
    "page_size": 10,
    "start_page": 1,
    "max_pages": 10
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "id": "d7b39bad-01cd-4734-b284-65dbc24eeb99",
  "workLocation": "上海",
  "jobName": "语言",
  "releaseTime": 1783316661000,
  "recruitTypeName": "管培生"
}
```

Sample 2:

```json
{
  "id": "f40e809d-f585-43d6-a43c-7f0c76c92ed9",
  "workLocation": "上海",
  "jobName": "职能",
  "releaseTime": 1783255809000,
  "recruitTypeName": "管培生"
}
```

Sample 3:

```json
{
  "id": "54ad4666-f80b-47be-840b-5a99cf04a3d7",
  "workLocation": "广东省",
  "jobName": "职能",
  "releaseTime": 1785218152000,
  "recruitTypeName": "管培生"
}
```

Sample 4:

```json
{
  "id": "8ab7c0c7-1bcb-413d-a87a-86739b24d716",
  "workLocation": "上海",
  "jobName": "运营",
  "releaseTime": 1783408143000,
  "recruitTypeName": "管培生"
}
```

Sample 5:

```json
{
  "id": "a8313a59-90d2-4769-be6e-d39ea37ef3de",
  "workLocation": "上海",
  "jobName": "产品",
  "releaseTime": 1783256848000,
  "recruitTypeName": "管培生"
}
```

## Target P12

- Company: `OPPO`
- Company type: `民企`
- Official-source evidence: `https://careers.oppo.com/university/oppo/campus/`
- Entry page: `https://careers.oppo.com/campus/post`
- Final page: `https://careers.oppo.com/university/oppo/campus/post`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://careers.oppo.com/openapi/position/pageNew`
- Response: `200` / `application/json`
- Candidate list path: `data.records`
- Total path: `data.total`
- Confidence score: `100`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, authorization, content-length, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, tenant-id, traceparent, user-agent` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `header.authorization`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://careers.oppo.com/openapi/position/pageNew",
  "method": "POST",
  "list_path": "data.records",
  "field_map": {
    "position_key": "atsProjectPositionId",
    "title": "positionName",
    "location": "workCityName",
    "updated_at": "releaseTime",
    "is_valid": "positionStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "pageNum": 1,
    "pageSize": 10,
    "positionName": "",
    "projectList": [],
    "positionTypeList": [],
    "workCityCodeList": [],
    "shareId": ""
  },
  "pagination_candidates": {
    "pageSize": 10
  },
  "total_path": "data.total",
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
  "idRecruitPosition": 1769,
  "atsProjectPositionId": 1783,
  "recruitmentTypeName": "应届生",
  "recruitmentType": "Graduate",
  "positionType": "AI/algorithm",
  "positionTypeName": "AI/算法类",
  "positionName": "电池算法工程师",
  "workCityName": "东莞市",
  "positionStatus": 0,
  "releaseTime": "2026-07-15",
  "specialRecruitment": ""
}
```

Sample 2:

```json
{
  "idRecruitPosition": 1873,
  "atsProjectPositionId": 1894,
  "recruitmentTypeName": "应届生",
  "recruitmentType": "Graduate",
  "positionType": "Products",
  "positionTypeName": "产品类",
  "positionName": "人因工程师",
  "workCityName": "东莞市",
  "positionStatus": 0,
  "releaseTime": "2026-08-24",
  "specialRecruitment": ""
}
```

Sample 3:

```json
{
  "idRecruitPosition": 1872,
  "atsProjectPositionId": 1893,
  "recruitmentTypeName": "博士生",
  "recruitmentType": "doctor",
  "positionType": "Hardware_class",
  "positionTypeName": "硬件类",
  "positionName": "高级音频仿真工程师-博士",
  "workCityName": "东莞市",
  "positionStatus": 0,
  "releaseTime": "2026-08-24",
  "specialRecruitment": ""
}
```

Sample 4:

```json
{
  "idRecruitPosition": 1871,
  "atsProjectPositionId": 1892,
  "recruitmentTypeName": "博士生",
  "recruitmentType": "doctor",
  "positionType": "Hardware_class",
  "positionTypeName": "硬件类",
  "positionName": "高级通信感知工程师-博士",
  "workCityName": "东莞市",
  "positionStatus": 0,
  "releaseTime": "2026-08-24",
  "specialRecruitment": ""
}
```

Sample 5:

```json
{
  "idRecruitPosition": 1870,
  "atsProjectPositionId": 1891,
  "recruitmentTypeName": "应届生",
  "recruitmentType": "Graduate",
  "positionType": "Hardware_class",
  "positionTypeName": "硬件类",
  "positionName": "新材料应用工程师",
  "workCityName": "东莞市",
  "positionStatus": 0,
  "releaseTime": "2026-08-06",
  "specialRecruitment": ""
}
```

### Candidate 2

- Request: `GET https://careers.oppo.com/openapi/offer/office/location/chnCityList`
- Response: `200` / `application/json`
- Candidate list path: `data`
- Total path: `not inferred`
- Confidence score: `24`
- Shared endpoint replay budget: `0 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, authorization, cookie, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, tenant-id, traceparent, user-agent` (values redacted)
- Replay verdict: **不可接入** — URL、查询或请求正文含疑似签名/凭据字段；未发出重放请求，也未尝试移除或逆向
- Suspicious URL/header/query/body paths: `header.authorization`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://careers.oppo.com/openapi/offer/office/location/chnCityList",
  "method": "GET",
  "list_path": "data",
  "field_map": {
    "position_key": "buildingId",
    "title": "countryNameEn",
    "location": "cityName"
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
    "expect": 0
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "buildingId": "BLDG055",
  "countryNameEn": "China",
  "cityName": "深圳市"
}
```

Sample 2:

```json
{
  "buildingId": "BLDG031",
  "countryNameEn": "China",
  "cityName": "东莞市"
}
```

Sample 3:

```json
{
  "buildingId": "BLDG052",
  "countryNameEn": "China",
  "cityName": "北京市"
}
```

Sample 4:

```json
{
  "buildingId": "BLDG060",
  "countryNameEn": "China",
  "cityName": "上海市"
}
```

Sample 5:

```json
{
  "buildingId": "BLDG075",
  "countryNameEn": "China",
  "cityName": "成都市"
}
```

## Target P13

- Company: `vivo`
- Company type: `民企`
- Official-source evidence: `https://hr.vivo.com/wt/vivo/web/index/CompvivoAboutCampus`
- Entry page: `https://hr.vivo.com/wt/vivo/web/index/CompvivoAboutCampus`
- Final page: `https://hr.vivo.com/home`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:15.715",
  "id": "M2370",
  "name": "热门城市"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:15.363",
  "id": "M2338",
  "name": "河北省"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:15.093",
  "id": "M2315",
  "name": "山西省"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:16.516",
  "id": "M2444",
  "name": "内蒙古自治区"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:15.863",
  "id": "M2384",
  "name": "辽宁省"
}
```

### Candidate 2

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[0].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[0].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:15.791",
  "id": 2377,
  "name": "北京"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:15.742",
  "id": 2373,
  "name": "上海"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:15.802",
  "id": 2378,
  "name": "广州"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:15.724",
  "id": 2371,
  "name": "深圳"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:15.782",
  "id": 2376,
  "name": "杭州"
}
```

### Candidate 3

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[10].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[10].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:18.254",
  "id": 2589,
  "name": "厦门"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:18.295",
  "id": 2593,
  "name": "福州"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:18.244",
  "id": 2588,
  "name": "南平"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:18.234",
  "id": 2587,
  "name": "三明"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:18.407",
  "id": 2604,
  "name": "莆田"
}
```

### Candidate 4

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[11].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[11].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:18.690",
  "id": 2630,
  "name": "南昌"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:18.659",
  "id": 2627,
  "name": "九江"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:18.503",
  "id": 2613,
  "name": "景德镇"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:18.482",
  "id": 2611,
  "name": "鹰潭"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:18.524",
  "id": 2615,
  "name": "新余"
}
```

### Candidate 5

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[12].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[12].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:18.765",
  "id": 2637,
  "name": "济南"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:18.732",
  "id": 2634,
  "name": "青岛"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:18.776",
  "id": 2638,
  "name": "聊城"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:18.742",
  "id": 2635,
  "name": "德州"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:18.829",
  "id": 2643,
  "name": "东营"
}
```

### Candidate 6

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[13].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[13].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:19.263",
  "id": 2683,
  "name": "郑州"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:19.226",
  "id": 2680,
  "name": "开封"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:19.196",
  "id": 2677,
  "name": "洛阳"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:19.237",
  "id": 2681,
  "name": "平顶山"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:19.207",
  "id": 2678,
  "name": "安阳"
}
```

### Candidate 7

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[14].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[14].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:19.739",
  "id": 2723,
  "name": "武汉"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:20.038",
  "id": 2748,
  "name": "十堰"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:19.872",
  "id": 2735,
  "name": "襄阳"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:19.718",
  "id": 2721,
  "name": "荆门"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:19.748",
  "id": 2724,
  "name": "孝感"
}
```

### Candidate 8

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[15].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[15].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:20.794",
  "id": 2813,
  "name": "长沙"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:20.749",
  "id": 2809,
  "name": "衡阳"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:20.629",
  "id": 2797,
  "name": "张家界"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:20.781",
  "id": 2812,
  "name": "常德"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:20.689",
  "id": 2803,
  "name": "益阳"
}
```

### Candidate 9

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[16].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[16].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:20.152",
  "id": 2758,
  "name": "广州"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:20.097",
  "id": 2753,
  "name": "深圳"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:20.132",
  "id": 2756,
  "name": "清远"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:20.161",
  "id": 2759,
  "name": "韶关"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:20.117",
  "id": 2755,
  "name": "河源"
}
```

### Candidate 10

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[17].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[17].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:20.929",
  "id": 2825,
  "name": "南宁"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:21.031",
  "id": 2835,
  "name": "桂林"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:20.939",
  "id": 2826,
  "name": "柳州"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:20.980",
  "id": 2830,
  "name": "梧州"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:21.099",
  "id": 2842,
  "name": "贵港"
}
```

### Candidate 11

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[18].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[18].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:21.596",
  "id": 2891,
  "name": "海口"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:21.568",
  "id": 2888,
  "name": "三亚"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:21.558",
  "id": 2887,
  "name": "三沙"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:21.587",
  "id": 2890,
  "name": "儋州"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:21.549",
  "id": 2886,
  "name": "文昌"
}
```

### Candidate 12

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[19].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[19].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:21.366",
  "id": 2868,
  "name": "成都"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:21.355",
  "id": 2867,
  "name": "广元"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:21.347",
  "id": 2866,
  "name": "绵阳"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:21.189",
  "id": 2851,
  "name": "德阳"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:21.405",
  "id": 2872,
  "name": "南充"
}
```

### Candidate 13

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[1].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[1].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:15.502",
  "id": 2351,
  "name": "石家庄"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:15.385",
  "id": 2340,
  "name": "邯郸"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:15.414",
  "id": 2343,
  "name": "唐山"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:15.544",
  "id": 2355,
  "name": "保定"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:15.456",
  "id": 2347,
  "name": "秦皇岛"
}
```

### Candidate 14

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[20].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[20].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:21.674",
  "id": 2898,
  "name": "贵阳"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:21.683",
  "id": 2899,
  "name": "六盘水"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:21.631",
  "id": 2894,
  "name": "遵义"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:21.655",
  "id": 2896,
  "name": "安顺"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:21.640",
  "id": 2895,
  "name": "毕节"
}
```

### Candidate 15

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[21].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[21].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:21.958",
  "id": 2923,
  "name": "昆明"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:21.810",
  "id": 2910,
  "name": "曲靖"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:21.795",
  "id": 2909,
  "name": "玉溪"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:21.896",
  "id": 2917,
  "name": "丽江"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:21.948",
  "id": 2922,
  "name": "昭通"
}
```

### Candidate 16

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[22].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[22].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:22.063",
  "id": 2932,
  "name": "西安"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:22.130",
  "id": 2938,
  "name": "延安"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:22.170",
  "id": 2942,
  "name": "铜川"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:22.074",
  "id": 2933,
  "name": "渭南"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:22.109",
  "id": 2936,
  "name": "咸阳"
}
```

### Candidate 17

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[23].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[23].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:22.232",
  "id": 2948,
  "name": "兰州"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:22.285",
  "id": 2953,
  "name": "嘉峪关"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:22.369",
  "id": 2960,
  "name": "金昌"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:22.255",
  "id": 2950,
  "name": "白银"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:22.304",
  "id": 2955,
  "name": "天水"
}
```

### Candidate 18

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[24].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[24].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:22.892",
  "id": 3001,
  "name": "西宁"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:22.912",
  "id": 3003,
  "name": "海东"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:22.882",
  "id": 3000,
  "name": "格尔木"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:22.902",
  "id": 3002,
  "name": "德令哈"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:22.922",
  "id": 3004,
  "name": "玉树"
}
```

### Candidate 19

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[25].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[25].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:22.804",
  "id": 2993,
  "name": "拉萨"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:22.823",
  "id": 2995,
  "name": "日喀则"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:22.813",
  "id": 2994,
  "name": "昌都"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:22.837",
  "id": 2996,
  "name": "林芝"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:22.794",
  "id": 2992,
  "name": "山南"
}
```

### Candidate 20

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[26].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[26].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:23.088",
  "id": 3017,
  "name": "银川"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:23.145",
  "id": 3022,
  "name": "石嘴山"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:23.101",
  "id": 3018,
  "name": "吴忠"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:23.071",
  "id": 3016,
  "name": "中卫"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:23.125",
  "id": 3020,
  "name": "固原"
}
```

### Candidate 21

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[27].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[27].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:22.604",
  "id": 2978,
  "name": "乌鲁木齐"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:22.704",
  "id": 2985,
  "name": "克拉玛依"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:22.748",
  "id": 2988,
  "name": "吐鲁番"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:22.758",
  "id": 2989,
  "name": "哈密"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:22.489",
  "id": 2970,
  "name": "喀什"
}
```

### Candidate 22

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[28].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[28].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-09-07T11:57:15.838",
  "id": 3604,
  "name": "台湾"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:23.019",
  "id": 3012,
  "name": "台北"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:22.963",
  "id": 3007,
  "name": "新北"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:22.948",
  "id": 3006,
  "name": "桃园"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:22.974",
  "id": 3008,
  "name": "台中"
}
```

### Candidate 23

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[2].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[2].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:15.229",
  "id": 2326,
  "name": "太原"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:15.268",
  "id": 2329,
  "name": "大同"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:15.168",
  "id": 2321,
  "name": "朔州"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:15.306",
  "id": 2333,
  "name": "阳泉"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:15.257",
  "id": 2328,
  "name": "长治"
}
```

### Candidate 24

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[31].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[31].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:23.199",
  "id": 3027,
  "name": "美国"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:23.190",
  "id": 3026,
  "name": "英国"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:23.217",
  "id": 3029,
  "name": "法国"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:23.209",
  "id": 3028,
  "name": "德国"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:23.246",
  "id": 3032,
  "name": "意大利"
}
```

### Candidate 25

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[3].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[3].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:16.552",
  "id": 2447,
  "name": "呼和浩特"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:16.596",
  "id": 2451,
  "name": "包头"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:16.574",
  "id": 2449,
  "name": "乌海"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:16.586",
  "id": 2450,
  "name": "赤峰"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:16.608",
  "id": 2452,
  "name": "呼伦贝尔"
}
```

### Candidate 26

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[4].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[4].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:15.990",
  "id": 2396,
  "name": "沈阳"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:16.010",
  "id": 2398,
  "name": "大连"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:16.047",
  "id": 2401,
  "name": "朝阳"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:16.174",
  "id": 2412,
  "name": "阜新"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:15.949",
  "id": 2392,
  "name": "铁岭"
}
```

### Candidate 27

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[5].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[5].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:16.493",
  "id": 2442,
  "name": "长春"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:16.275",
  "id": 2422,
  "name": "吉林"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:16.410",
  "id": 2434,
  "name": "白城"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:16.288",
  "id": 2423,
  "name": "松原"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:16.338",
  "id": 2428,
  "name": "四平"
}
```

### Candidate 28

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[6].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[6].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:16.812",
  "id": 2471,
  "name": "哈尔滨"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:17.169",
  "id": 2496,
  "name": "齐齐哈尔"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:16.782",
  "id": 2468,
  "name": "黑河"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:17.033",
  "id": 2485,
  "name": "大庆"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:16.898",
  "id": 2479,
  "name": "伊春"
}
```

### Candidate 29

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[7].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[7].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:17.453",
  "id": 2521,
  "name": "南京"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:17.565",
  "id": 2531,
  "name": "徐州"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:17.342",
  "id": 2512,
  "name": "连云港"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:17.409",
  "id": 2517,
  "name": "宿迁"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:17.233",
  "id": 2501,
  "name": "淮安"
}
```

### Candidate 30

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[8].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[8].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:17.763",
  "id": 2547,
  "name": "杭州"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:17.810",
  "id": 2551,
  "name": "宁波"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:17.787",
  "id": 2549,
  "name": "湖州"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:17.680",
  "id": 2539,
  "name": "嘉兴"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:17.897",
  "id": 2558,
  "name": "舟山"
}
```

### Candidate 31

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[9].children`
- Total path: `not inferred`
- Confidence score: `20`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[9].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:18.089",
  "id": 2574,
  "name": "合肥"
}
```

Sample 2:

```json
{
  "updated_at": "2023-04-22T08:46:18.201",
  "id": 2584,
  "name": "芜湖"
}
```

Sample 3:

```json
{
  "updated_at": "2023-04-22T08:46:18.210",
  "id": 2585,
  "name": "蚌埠"
}
```

Sample 4:

```json
{
  "updated_at": "2023-04-22T08:46:17.991",
  "id": 2566,
  "name": "淮南"
}
```

Sample 5:

```json
{
  "updated_at": "2023-04-22T08:46:17.978",
  "id": 2565,
  "name": "马鞍山"
}
```

### Candidate 32

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[29].children`
- Total path: `not inferred`
- Confidence score: `16`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[29].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:23.167",
  "id": 3024,
  "name": "香港特别行政区"
}
```

### Candidate 33

- Request: `POST https://hr.vivo.com/api/social/webSite/portal/entityItem/tree`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data[30].children`
- Total path: `not inferred`
- Confidence score: `16`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://hr.vivo.com/api/social/webSite/portal/entityItem/tree",
  "method": "POST",
  "list_path": "data[30].children",
  "field_map": {
    "position_key": "id",
    "title": "name",
    "updated_at": "updated_at"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "entity_code": "location_code_list",
    "company_id": 0,
    "group_id": 0
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
  "updated_at": "2023-04-22T08:46:22.861",
  "id": 2998,
  "name": "澳门特别行政区"
}
```

## Target P14

- Company: `大疆创新`
- Company type: `民企`
- Official-source evidence: `https://careers.dji.com/zh-CN/campus`
- Entry page: `https://careers.dji.com/zh-CN/campus/hot-jobs`
- Final page: `https://careers.dji.com/zh-CN/campus/hot-jobs`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P15

- Company: `宁德时代`
- Company type: `民企`
- Official-source evidence: `https://www.catl.com/`
- Entry page: `https://talent.catl.com/`
- Final page: `https://talent.catl.com/social-recruitment/catlhr/96144/#/`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P16

- Company: `吉利控股`
- Company type: `民企`
- Official-source evidence: `https://campus.geely.com/`
- Entry page: `https://campus.geely.com/`
- Final page: `https://campus.geely.com/campus-recruitment/geely/78436/#/`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P17

- Company: `美的集团`
- Company type: `民企`
- Official-source evidence: `https://www.midea.com.cn/zh/careers`
- Entry page: `https://careers.midea.com/schoolOut/post?type=2`
- Final page: `https://careers.midea.com/schoolOut/post?type=2`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://iop.midea.com/robot/noLogin/session/init/session`
- Response: `200` / `application/json`
- Candidate list path: `data.wsMessageVOS`
- Total path: `not inferred`
- Confidence score: `13`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, host, lang, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, timezone, user-agent, x-requested-with` (values redacted)
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
  "endpoint": "https://iop.midea.com/robot/noLogin/session/init/session",
  "method": "POST",
  "list_path": "data.wsMessageVOS",
  "field_map": {
    "position_key": "channelCode",
    "title": "userName",
    "location": "knowledgeRegion",
    "raw_text": "content",
    "updated_at": "timestamp"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "userName": "IOP_TOURISTS_1787742258379_LY3E",
    "channelCode": "campus",
    "skillCode": "ROBOT_SKILL_GROUP_IpuN_39790179296",
    "endPoint": "PC",
    "wsSessionId": "IOP_WS_JuJy_33742266771",
    "userNickName": "",
    "isNew": true,
    "skillId": ""
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
  "channelCode": "campus",
  "knowledgeRegion": null,
  "messageSourceType": "IOP",
  "msgReturnType": null,
  "terminateMsgType": null,
  "timestamp": "2026-08-26 19:04:27",
  "type": "WELCOME",
  "userName": "IOP_TOURISTS_1787742258379_LY3E"
}
```

### Candidate 2

- Request: `GET https://iop.midea.com/robot/questionBank/noLogin/component?iopDomainName=campus&userName=IOP_TOURISTS_1787742257952_NUjt`
- Response: `200` / `application/json`
- Candidate list path: `data`
- Total path: `not inferred`
- Confidence score: `13`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, host, lang, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://iop.midea.com/robot/questionBank/noLogin/component",
  "method": "GET",
  "list_path": "data",
  "field_map": {
    "position_key": "componentCode",
    "title": "displayName",
    "application_url": "componentUrl",
    "updated_at": "beginDate"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "iopDomainName": "campus",
    "userName": "IOP_TOURISTS_1787742257952_NUjt"
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
  "beginDate": null,
  "componentCode": "BHmZCHFfykNWYelLlk",
  "componentIconType": 0,
  "componentType": "customerservice",
  "componentUrl": "",
  "displayName": "智能客服"
}
```

Sample 2:

```json
{
  "beginDate": null,
  "componentCode": "wOboBAXNPOKvOXzlMa",
  "componentIconType": 0,
  "componentType": "advice",
  "componentUrl": "",
  "displayName": "我要建议"
}
```

### Candidate 3

- Request: `GET https://careers.midea.com/backend/school/position/common/project/list?status=1&projectTypes=1%2C2%2C9%2C5&employementCategories=1%2C4&_ihr_log_trackId=6ed16460-a798-4023-8aa5-330e0fb7332b`
- Response: `200` / `application/json`
- Candidate list path: `data`
- Total path: `not inferred`
- Confidence score: `10`
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
  "endpoint": "https://careers.midea.com/backend/school/position/common/project/list",
  "method": "GET",
  "list_path": "data",
  "field_map": {
    "position_key": "projectRuleId",
    "title": "projectRuleName",
    "updated_at": "graduationStartDate",
    "is_valid": "status"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "status": "1",
    "projectTypes": "1,2,9,5",
    "employementCategories": "1,4",
    "_ihr_log_trackId": "6ed16460-a798-4023-8aa5-330e0fb7332b"
  },
  "success": {
    "path": "code",
    "expect": "0"
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "projectRuleId": "4286dfd5-d9e8-4146-8f8c-98093833a81b",
  "projectRuleName": "日常实习生招聘通道",
  "status": 1,
  "projectType": "9",
  "graduationStartDate": 1767196800000
}
```

## Target P18

- Company: `顺丰`
- Company type: `民企`
- Official-source evidence: `https://campus-static.sf-express.com/`
- Entry page: `https://campus.sf-express.com/`
- Final page: `https://campus.sf-express.com/#/homePage`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P19

- Company: `比亚迪`
- Company type: `民企`
- Official-source evidence: `https://job.byd.com/portal/mobile/school-home`
- Entry page: `https://job.byd.com/portal/mobile/school-home`
- Final page: `https://job.byd.com/portal/pc/#/school/home`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://job.byd.com/portal/api/portal-api/position/schedule/query-list`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.data`
- Total path: `data.totalNum`
- Confidence score: `25`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, lang, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://job.byd.com/portal/api/portal-api/position/schedule/query-list",
  "method": "POST",
  "list_path": "data.data",
  "field_map": {
    "position_key": "id",
    "title": "schoolName",
    "location": "city",
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
  "body": {
    "page": {
      "pageSize": 6,
      "pageIndex": 1
    }
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "page.pageIndex",
    "size_param": "page.pageSize",
    "page_size": 6,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "data.totalNum",
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
  "city": "重庆市",
  "id": "1836715397852745731",
  "meetingType": "00282",
  "schoolName": "西南大学",
  "status": "00111",
  "updateTime": null
}
```

Sample 2:

```json
{
  "city": "西安市",
  "id": "1836715397856940033",
  "meetingType": "00282",
  "schoolName": "西北农林科技大学",
  "status": "00111",
  "updateTime": null
}
```

Sample 3:

```json
{
  "city": "无锡市",
  "id": "1836715397852745730",
  "meetingType": "00282",
  "schoolName": "江南大学",
  "status": "00111",
  "updateTime": null
}
```

Sample 4:

```json
{
  "city": "雅安市",
  "id": "1836715397848551426",
  "meetingType": "00282",
  "schoolName": "四川农业大学",
  "status": "00111",
  "updateTime": null
}
```

Sample 5:

```json
{
  "city": "上海市",
  "id": "1836715397848551425",
  "meetingType": "00282",
  "schoolName": "华东理工大学",
  "status": "00111",
  "updateTime": null
}
```

### Candidate 2

- Request: `POST https://job.byd.com/portal/api/portal-api/other-info/notice/query-list`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.data`
- Total path: `data.totalNum`
- Confidence score: `21`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, cookie, host, lang, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://job.byd.com/portal/api/portal-api/other-info/notice/query-list",
  "method": "POST",
  "list_path": "data.data",
  "field_map": {
    "position_key": "id",
    "title": "noticeEnName",
    "application_url": "noticeUrl",
    "updated_at": "updateTime",
    "is_valid": "delStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "pageSize": 3,
    "pageIndex": 1
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "pageIndex",
    "size_param": "pageSize",
    "page_size": 3,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "data.totalNum",
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
  "delStatus": 1,
  "id": "12",
  "noticeEnName": null,
  "noticeUrl": "https://mp.weixin.qq.com/s/vhFFMMRRa7KBK0jWKBTY0g",
  "relatedSchoolTopic": null,
  "updateTime": null
}
```

### Candidate 3

- Request: `GET https://job.byd.com/portal/api/portal-api/material/getMaterial?ids=81038%2C810313%2C810314`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.810313`
- Total path: `not inferred`
- Confidence score: `18`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, cookie, host, lang, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://job.byd.com/portal/api/portal-api/material/getMaterial",
  "method": "GET",
  "list_path": "data.810313",
  "field_map": {
    "position_key": "id",
    "title": "fileName",
    "application_url": "fileUrl",
    "updated_at": "updateTime",
    "is_valid": "delStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "ids": "81038,810313,810314"
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
  "delStatus": 1,
  "fileName": "美琪-24届-浙江大学",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/学长学姐有话说/260812/07f429d87fd74f6aa4da6b9c5d34442f.jpg",
  "id": "260801",
  "updateTime": null
}
```

Sample 2:

```json
{
  "delStatus": 1,
  "fileName": "Albert-23届-西安交通大学",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/学长学姐有话说/260812/f352696182dd46f4821335f7b84924a5.jpg",
  "id": "260802",
  "updateTime": null
}
```

Sample 3:

```json
{
  "delStatus": 1,
  "fileName": "卡子-25届-北京大学",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/学长学姐有话说/260812/978df6b5945e472690e119359ee2c144.jpg",
  "id": "260803",
  "updateTime": null
}
```

Sample 4:

```json
{
  "delStatus": 1,
  "fileName": "Jessie-23届-清华大学",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/学长学姐有话说/260812/1c3dea3656eb41ceb1398c8ee510d407.jpg",
  "id": "260804",
  "updateTime": null
}
```

Sample 5:

```json
{
  "delStatus": 1,
  "fileName": "黄港-24届-中国科学院大学",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/学长学姐有话说/260812/07788c990ee14f4d939bc039907f3fb1.jpg",
  "id": "260805",
  "updateTime": null
}
```

### Candidate 4

- Request: `GET https://job.byd.com/portal/api/portal-api/material/getMaterial?ids=81038%2C810313%2C810314`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.810314`
- Total path: `not inferred`
- Confidence score: `17`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, cookie, host, lang, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://job.byd.com/portal/api/portal-api/material/getMaterial",
  "method": "GET",
  "list_path": "data.810314",
  "field_map": {
    "position_key": "id",
    "title": "fileName",
    "application_url": "fileUrl",
    "updated_at": "updateTime",
    "is_valid": "delStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "ids": "81038,810313,810314"
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
  "delStatus": 1,
  "fileName": "清华大学未央书院一行走进比亚迪深圳总部礼宾楼展厅",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/OPENDAY/260812/9d131554529a453bab977375d7313223.jpg",
  "id": "260811",
  "updateTime": null
}
```

Sample 2:

```json
{
  "delStatus": 1,
  "fileName": "北京大学走进迪空间——开启医学×科技的跨界新视野",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/OPENDAY/260812/7b12398404184b319b4a6059dd126d57.jpg",
  "id": "260808",
  "updateTime": null
}
```

Sample 3:

```json
{
  "delStatus": 1,
  "fileName": "中南大学·比亚迪探营活动圆满举办，深度感知中国智造脉搏",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/OPENDAY/260812/9f20b7ffca0a4eb284bfc4b3bc762c2c.jpg",
  "id": "260810",
  "updateTime": null
}
```

Sample 4:

```json
{
  "delStatus": 1,
  "fileName": "安徽大学成功举办“非遗皖韵 智汇科创”2025年国际青年夏令营",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/OPENDAY/260812/9cd45eb37a344023bc91f25acc6af84d.jpg",
  "id": "260809",
  "updateTime": null
}
```

### Candidate 5

- Request: `GET https://job.byd.com/portal/api/portal-api/material/getMaterial?ids=81038%2C810313%2C810314`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.81038`
- Total path: `not inferred`
- Confidence score: `15`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, cookie, host, lang, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://job.byd.com/portal/api/portal-api/material/getMaterial",
  "method": "GET",
  "list_path": "data.81038",
  "field_map": {
    "position_key": "id",
    "title": "fileName",
    "application_url": "fileUrl",
    "updated_at": "updateTime",
    "is_valid": "delStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "ids": "81038,810313,810314"
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
  "delStatus": 1,
  "fileName": "校招顶部大图",
  "fileUrl": "https://ess-cdn.byd.com/招聘/门户/国内英文版/校园招聘/校招顶部banner/260812/1c965d01028e42ffbfedeba56421b086.png",
  "id": "30",
  "updateTime": null
}
```

Sample 2:

```json
{
  "delStatus": 1,
  "fileName": "校招banner-博士后",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E6%8B%9B%E8%81%98%E7%AE%80%E7%AB%A0//260723/ca5373d656a44d7aa827c69d8b1983db.png",
  "id": "31",
  "updateTime": null
}
```

## Target P20

- Company: `理想汽车`
- Company type: `民企`
- Official-source evidence: `https://www.lixiang.com/`
- Entry page: `https://www.lixiang.com/employ/campus/list.html`
- Final page: `https://www.lixiang.com/employ/campus/list.html?fromJob=1`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://api-web.lixiang.com/osd-hr-recruitment-website/v1/recruit/school/job-page?page=1&page_size=10`
- Response: `200` / `application/json`
- Candidate list path: `data.items`
- Total path: `data.total_pages`
- Confidence score: `40`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, x-chj-metadata, x-chj-sourceurl, x-chj-traceid` (values redacted)
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
  "endpoint": "https://api-web.lixiang.com/osd-hr-recruitment-website/v1/recruit/school/job-page",
  "method": "GET",
  "list_path": "data.items",
  "field_map": {
    "position_key": "id",
    "title": "title",
    "location": "location_title"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "page": "1",
    "page_size": "10"
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "page",
    "size_param": "page_size",
    "page_size": 10,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "data.total_pages",
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
  "location_title": "北京",
  "id": 18450,
  "title": "高速选址运营实习生"
}
```

Sample 2:

```json
{
  "location_title": "上海",
  "id": 18451,
  "title": "充电网络工程供应管理实习生"
}
```

Sample 3:

```json
{
  "location_title": "北京",
  "id": 18452,
  "title": "电力大客户实习生"
}
```

Sample 4:

```json
{
  "location_title": "北京",
  "id": 18459,
  "title": "充电网络规划实习生"
}
```

Sample 5:

```json
{
  "location_title": "北京",
  "id": 19125,
  "title": "间接采购实习生"
}
```

### Candidate 2

- Request: `GET https://api-web.lixiang.com/osd-hr-recruitment-website/v1/recruit/job/location?hire_mode=2`
- Response: `200` / `application/json`
- Candidate list path: `data.items`
- Total path: `not inferred`
- Confidence score: `13`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-type, cookie, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, x-chj-metadata, x-chj-sourceurl, x-chj-traceid` (values redacted)
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
  "endpoint": "https://api-web.lixiang.com/osd-hr-recruitment-website/v1/recruit/job/location",
  "method": "GET",
  "list_path": "data.items",
  "field_map": {
    "title": "name",
    "location": "city_list"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "hire_mode": "2"
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
  "name": "山东",
  "city_list": [
    {
      "code": "371000",
      "level": 2,
      "name": "威海",
      "en": "WeiHaiShi"
    },
    {
      "code": "371500",
      "level": 2,
      "name": "聊城",
      "en": "LiaoChengShi"
    },
    {
      "code": "370800",
      "level": 2,
      "name": "济宁",
      "en": "JiNingShi"
    },
    {
      "code": "371600",
      "level": 2,
      "name": "滨州",
      "en": "BinZhouShi"
    },
    {
      "code": "371300",
      "level": 2,
      "name": "临沂",
      "en": "LinYiShi"
    },
    {
      "code": "371700",
      "level": 2,
      "name": "菏泽",
      "en": "HeZeShi"
    },
    {
      "code": "370200",
      "level": 2,
      "name": "青岛",
      "en": "QingDaoShi"
    },
    {
      "code": "370700",
      "level": 2,
      "name": "潍坊",
      "en": "WeiFangShi"
    },
    {
      "code": "370300",
      "level": 2,
      "name": "淄博",
      "en": "ZiBoShi"
    },
    {
      "code": "371100",
      "level": 2,
      "name": "日照",
      "en": "RiZhaoShi"
    },
    {
      "code": "370900",
      "level": 2,
      "name": "泰安",
      "en": "TaiAnShi"
    },
    {
      "code": "370100",
      "level": 2,
      "name": "济南",
      "en": "JiNanShi"
    }
  ]
}
```

Sample 2:

```json
{
  "name": "福建",
  "city_list": [
    {
      "code": "350800",
      "level": 2,
      "name": "龙岩",
      "en": "LongYanShi"
    },
    {
      "code": "350100",
      "level": 2,
      "name": "福州",
      "en": "FuZhouShi"
    },
    {
      "code": "350500",
      "level": 2,
      "name": "泉州",
      "en": "QuanZhouShi"
    },
    {
      "code": "350200",
      "level": 2,
      "name": "厦门",
      "en": "XiaMenShi"
    }
  ]
}
```

Sample 3:

```json
{
  "name": "河南",
  "city_list": [
    {
      "code": "410100",
      "level": 2,
      "name": "郑州",
      "en": "ZhengZhouShi"
    }
  ]
}
```

Sample 4:

```json
{
  "name": "河北",
  "city_list": [
    {
      "code": "130600",
      "level": 2,
      "name": "保定",
      "en": "BaoDingShi"
    },
    {
      "code": "130100",
      "level": 2,
      "name": "石家庄",
      "en": "ShiJiaZhuangShi"
    }
  ]
}
```

Sample 5:

```json
{
  "name": "重庆",
  "city_list": [
    {
      "code": "500100",
      "level": 2,
      "name": "重庆",
      "en": "ChongQingShi"
    }
  ]
}
```

## Target S01

- Company: `国家电网有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.sgcc.com.cn/`
- Entry page: `https://zhaopin.sgcc.com.cn/`
- Final page: `https://zhaopin.sgcc.com.cn/`
- Page status: `412`
- Outcome: skipped
- Reason: 入口页返回 HTTP 412，已跳过

## Target S02

- Company: `中国移动通信集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://job.10086.cn/`
- Entry page: `https://job.10086.cn/personal/job/`
- Final page: `https://job.10086.cn/personal/job/`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://service.govwza.cn/api/services/Accessibility/Configuration/GetAll?appid=e4634471b17a7f059a81d47613d67632&timestamp=1787742393439&domain=job.10086.cn&referer=https%3A%2F%2Fjob.10086.cn%2Fpersonal%2Fjob%2F&mainversion=4`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `result.golbalElems`
- Total path: `not inferred`
- Confidence score: `18`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-type, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
- Replay verdict: **不可接入** — 最简合规头未返回等效非空候选列表
- Suspicious URL/header/query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |
| 完整头 + Cookie（基线） | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉疑似签名头 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 去掉 Cookie | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 同时去掉两者 | 200 | yes | HTTP 200，候选列表路径仍存在且非空 |
| 最简合规头 | 200 | no | HTTP 200，候选列表路径不存在 |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://service.govwza.cn/api/services/Accessibility/Configuration/GetAll",
  "method": "GET",
  "list_path": "result.golbalElems",
  "field_map": {
    "title": "title",
    "location": "placeholder"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "appid": "e4634471b17a7f059a81d47613d67632",
    "timestamp": "1787742393439",
    "domain": "job.10086.cn",
    "referer": "https://job.10086.cn/personal/job/",
    "mainversion": "4"
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
  "title": "",
  "placeholder": null
}
```

Sample 2:

```json
{
  "title": null,
  "placeholder": null
}
```

Sample 3:

```json
{
  "title": "",
  "placeholder": null
}
```

Sample 4:

```json
{
  "title": "",
  "placeholder": null
}
```

Sample 5:

```json
{
  "title": "",
  "placeholder": null
}
```

## Target S03

- Company: `中国电信集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.chinatelecom.com.cn/ct/zp/`
- Entry page: `https://job.chinatelecom.com.cn/wt/TELE/web/index?brandCode=1`
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

## Target S04

- Company: `中国联合网络通信集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.chinaunicom.com.cn/46/menu01/528/column06`
- Entry page: `https://zglt.zhaopin.com/`
- Final page: `https://zglt.zhaopin.com/`
- Page status: `200`
- Outcome: skipped
- Reason: 页面无可见内容且未捕获 JSON 响应，可能被无头浏览器拦截

## Target S05

- Company: `中国石油天然气集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.cnpc.com.cn/frontapp/`
- Entry page: `https://zhaopin.cnpc.com.cn/web/index.html`
- Final page: `https://zhaopin.cnpc.com.cn/web/index.html`
- Page status: `412`
- Outcome: skipped
- Reason: 入口页返回 HTTP 412，已跳过

## Target S06

- Company: `中国石油化工集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.sinopecgroup.com/group/rsbd/index.shtml`
- Entry page: `https://job.sinopec.com/app/`
- Final page: `https://job.sinopec.com/app/#/`
- Page status: `200`
- Outcome: skipped
- Reason: 页面无可见内容且未捕获 JSON 响应，可能被无头浏览器拦截

## Target S07

- Company: `中国海洋石油集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.cnooc.com.cn/col/col661/index.html`
- Entry page: `https://cnooc.zhaopin.com/job/index.html`
- Final page: `https://cnooc.zhaopin.com/job/index.html`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target S08

- Company: `中国中车集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.crrcgc.cc/`
- Entry page: `https://sp.wintalent.cn/CRRC/homeMobile/index.html`
- Final page: `https://sp.wintalent.cn/CRRC/homeMobile/index.html`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://crrc.hotjob.cn/wecruit/suite/dynamic/list/SU64d47c466202cc36e27a52d4?iSaJAx=isAjax&request_locale=zh_CN`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.dynamicDetail`
- Total path: `not inferred`
- Confidence score: `16`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-length, content-type, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://crrc.hotjob.cn/wecruit/suite/dynamic/list/SU64d47c466202cc36e27a52d4",
  "method": "POST",
  "list_path": "data.dynamicDetail",
  "field_map": {
    "position_key": "key",
    "title": "title",
    "updated_at": "times"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {}
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "times": "2026年04月09日",
  "title": "中国中车2026年来华留学生招聘公告",
  "type": "richText",
  "key": 1775714637360
}
```

Sample 2:

```json
{
  "times": "2025年09月13日",
  "title": "中国中车集团有限公司2026全球招聘公告\t",
  "type": "richText",
  "key": 1757737698955
}
```

Sample 3:

```json
{
  "times": "2025年09月30日",
  "title": "中车数智科技（雄安）有限公司2026校园招聘公告\t",
  "type": "richText",
  "key": 1759200175150
}
```

Sample 4:

```json
{
  "times": "2025年09月30日",
  "title": "中车信息技术有限公司2026校园招聘公告\t",
  "type": "richText",
  "key": 1759200160082
}
```

Sample 5:

```json
{
  "times": "2025年09月25日",
  "title": "中车国际有限公司2026校园招聘公告",
  "type": "richText",
  "key": 1758946807882
}
```

## Target S09

- Company: `中国航天科技集团有限公司`
- Company type: `央国企`
- Official-source evidence: `http://www.spacechina.com/`
- Entry page: `https://career.spacechina.com/`
- Final page: `—`
- Page status: `None`
- Outcome: skipped
- Reason: 浏览器捕获失败：Page.goto: net::ERR_CONNECTION_CLOSED at https://career.spacechina.com/ Call log: - navigating to "https://career.spacechina.com/", waiting until "domcontentloaded"

## Target S10

- Company: `中国航空工业集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.avic.com/`
- Entry page: `https://avic.zhiye.com/campus`
- Final page: `https://avic.zhiye.com/404?errorpath=%2Fcampus`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target F01

- Company: `微软中国`
- Company type: `外资`
- Official-source evidence: `https://www.microsoft.com/zh-cn/aprd/recruitment`
- Entry page: `https://careers.microsoft.com/v2/global/en/locations/beijing.html`
- Final page: `https://careers.microsoft.com/v2/global/en/locations/beijing.html`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target F02

- Company: `亚马逊中国`
- Company type: `外资`
- Official-source evidence: `https://www.amazon.jobs/zh/locations/beijing-CHINA`
- Entry page: `https://www.amazon.jobs/en/search?country%5B%5D=CHN&result_limit=10`
- Final page: `https://www.amazon.jobs/en/search?country%5B%5D=CHN&result_limit=10`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://www.amazon.jobs/en/search.json?normalized_country_code%5B%5D=CHN&radius=24km&facets%5B%5D=normalized_country_code&facets%5B%5D=normalized_state_name&facets%5B%5D=normalized_city_name&facets%5B%5D=location&facets%5B%5D=business_category&facets%5B%5D=category&facets%5B%5D=schedule_type_id&facets%5B%5D=employee_class&facets%5B%5D=normalized_location&facets%5B%5D=job_function_id&facets%5B%5D=is_manager&facets%5B%5D=is_intern&offset=0&result_limit=10&sort=relevant&latitude=&longitude=&loc_group_id=&loc_query=&base_query=&city=&country=&region=&county=&query_options=`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `jobs`
- Total path: `facets.category_facet[12].Finance & Accounting`
- Confidence score: `65`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, cookie, host, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent` (values redacted)
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
  "endpoint": "https://www.amazon.jobs/en/search.json",
  "method": "GET",
  "list_path": "jobs",
  "field_map": {
    "position_key": "id",
    "title": "title",
    "location": "city",
    "raw_text": "description",
    "application_url": "url_next_step",
    "updated_at": "posted_date"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {
    "normalized_country_code[]": "CHN",
    "radius": "24km",
    "facets[]": [
      "normalized_country_code",
      "normalized_state_name",
      "normalized_city_name",
      "location",
      "business_category",
      "category",
      "schedule_type_id",
      "employee_class",
      "normalized_location",
      "job_function_id",
      "is_manager",
      "is_intern"
    ],
    "offset": "0",
    "result_limit": "10",
    "sort": "relevant",
    "latitude": "",
    "longitude": "",
    "loc_group_id": "",
    "loc_query": "",
    "base_query": "",
    "city": "",
    "country": "",
    "region": "",
    "county": "",
    "query_options": ""
  },
  "pagination_candidates": {
    "offset": "0"
  },
  "total_path": "facets.category_facet[12].Finance & Accounting"
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "city": "Beijing",
  "id": "59828880-6a04-4595-adc4-d1f5fd309b70",
  "is_intern": null,
  "job_schedule_type": "full-time",
  "posted_date": "August 13, 2026",
  "title": "Database Specialist SA",
  "url_next_step": "https://account.amazon.jobs/jobs/10500629/apply"
}
```

Sample 2:

```json
{
  "city": "Shanghai",
  "id": "f8729c17-b287-4dbd-8a35-bb21ba86145a",
  "is_intern": null,
  "job_schedule_type": "full-time",
  "posted_date": "August 26, 2026",
  "title": "Manager, Sales, AGL Sales ",
  "url_next_step": "https://account.amazon.jobs/jobs/10515155/apply"
}
```

Sample 3:

```json
{
  "city": "Shanghai",
  "id": "026e38a8-ea22-4d85-9bc7-baabc169abe7",
  "is_intern": null,
  "job_schedule_type": "full-time",
  "posted_date": "August 14, 2026",
  "title": "Mechanical Process Engineer, Product Engineering",
  "url_next_step": "https://account.amazon.jobs/jobs/10502498/apply"
}
```

Sample 4:

```json
{
  "city": "Shenzhen",
  "id": "3f0236a1-df39-44a5-a77c-b6223d5af44a",
  "is_intern": null,
  "job_schedule_type": "full-time",
  "posted_date": "May 26, 2026",
  "title": "Sr. Hardware Development Engineer, Centralized Electrical Engineer (CEE) - Devices",
  "url_next_step": "https://account.amazon.jobs/jobs/10430478/apply"
}
```

Sample 5:

```json
{
  "city": "Guangzhou",
  "id": "fa3a9e27-68e9-4a08-a7ca-0e7cd75af6dd",
  "is_intern": null,
  "job_schedule_type": "full-time",
  "posted_date": "June 26, 2026",
  "title": "Customer Acq Executive",
  "url_next_step": "https://account.amazon.jobs/jobs/10459715/apply"
}
```

## Target F03

- Company: `IBM 中国`
- Company type: `外资`
- Official-source evidence: `https://www.ibm.com/cn-zh/careers/search`
- Entry page: `https://www.ibm.com/cn-zh/careers/search`
- Final page: `https://www.ibm.com/cn-zh/careers/search`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://cm-api-v4.contact-module.ibm.com/api/v4/client-info/lookup`
- Response: `200` / `application/json`
- Candidate list path: `regionsAndLanguages.data`
- Total path: `not inferred`
- Confidence score: `24`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `:authority, :method, :path, :scheme, accept, accept-encoding, content-length, content-type, origin, priority, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, x-correlation-id, x-origin` (values redacted)
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
  "endpoint": "https://cm-api-v4.contact-module.ibm.com/api/v4/client-info/lookup",
  "method": "POST",
  "list_path": "regionsAndLanguages.data",
  "field_map": {
    "title": "languageNameDefault",
    "location": "regionCode"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "contactInformationBundleKey": {
      "languageCode": "zh",
      "regionCode": "CN",
      "focusArea": "Miscellaneous - Careers"
    },
    "textTranslationBundleKey": {
      "languageCode": "zh",
      "regionCode": "CN",
      "focusArea": "Miscellaneous - Careers",
      "variation": "Miscellaneous - Careers"
    },
    "regionsAndLanguagesForLocale": {
      "languageCode": "local",
      "regionCode": "local",
      "focusArea": "Miscellaneous - Careers",
      "variation": "Miscellaneous - Careers"
    },
    "schedulingInformationKey": {
      "languageCode": "zh",
      "regionCode": "CN",
      "focusArea": "Miscellaneous - Careers"
    },
    "digitalEnablersKey": {
      "languageCode": "zh",
      "regionCode": "CN"
    }
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "languageNameDefault": "English",
  "regionCode": "AD"
}
```

Sample 2:

```json
{
  "languageNameDefault": "French (Français)",
  "regionCode": "AD"
}
```

Sample 3:

```json
{
  "languageNameDefault": "English",
  "regionCode": "AF"
}
```

Sample 4:

```json
{
  "languageNameDefault": "English",
  "regionCode": "AM"
}
```

Sample 5:

```json
{
  "languageNameDefault": "English",
  "regionCode": "AQ"
}
```

## Target F04

- Company: `西门子中国`
- Company type: `外资`
- Official-source evidence: `https://www.siemens.com/zh-cn/company/jobs/`
- Entry page: `https://jobs.siemens.com.cn/siemens/position/index?recruitmentType=INTERNSHIPRECRUITMENT`
- Final page: `—`
- Page status: `None`
- Outcome: skipped
- Reason: 浏览器捕获失败：Page.goto: net::ERR_CONNECTION_CLOSED at https://jobs.siemens.com.cn/siemens/position/index?recruitmentType=INTERNSHIPRECRUITMENT Call log: - navigating to "https://jobs.siemens.com.cn/siemens/position/index?recruitmentType=INTERNSHIPRECRUITMENT", waiting until "domcontentloaded"

## Target F05

- Company: `博世中国`
- Company type: `外资`
- Official-source evidence: `https://www.bosch.com.cn/careers/`
- Entry page: `https://www.bosch.com.cn/careers/job-offers/`
- Final page: `https://www.bosch.com.cn/careers/job-offers/`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target F06

- Company: `苹果中国`
- Company type: `外资`
- Official-source evidence: `https://www.apple.com/careers/us/work-at-apple/locations/shanghai.html`
- Entry page: `https://jobs.apple.com/en-us/search?location=china-CHNC&page=1`
- Final page: `https://jobs.apple.com/en-us/search?location=china-CHNC&page=1`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target B01

- Company: `中国工商银行`
- Company type: `银行`
- Official-source evidence: `https://www.icbc.com.cn/ICBCLtd/%E8%81%8C%E4%B8%9A%E5%8F%91%E5%B1%95/%E4%BA%BA%E6%89%8D%E6%8B%9B%E8%81%98/`
- Entry page: `https://job.icbc.com.cn/`
- Final page: `https://job.icbc.com.cn/pc/index.html#/main/home`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://job.icbc.com.cn/icbc/trmo/announ/qryAnnounList`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.dataList`
- Total path: `data.total`
- Confidence score: `47`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, host, loginway, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, userid, x-forwared-for, zoneflag, zoneno` (values redacted)
- Replay verdict: **不可接入** — 最简合规头未返回等效非空候选列表
- Suspicious URL/header/query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |
| 完整头 + Cookie（基线） | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/announ/qryAnnounList (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |
| 去掉疑似签名头 | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/announ/qryAnnounList (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |
| 去掉 Cookie | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/announ/qryAnnounList (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |
| 同时去掉两者 | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/announ/qryAnnounList (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |
| 最简合规头 | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/announ/qryAnnounList (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://job.icbc.com.cn/icbc/trmo/announ/qryAnnounList",
  "method": "POST",
  "list_path": "data.dataList",
  "field_map": {
    "position_key": "announId",
    "title": "title",
    "raw_text": "content",
    "updated_at": "publishTime",
    "is_valid": "announStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "public": {
      "call_app": "F-TRM"
    },
    "private": {
      "page": 1,
      "pageSize": 4,
      "projectType": "R00301"
    }
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "private.page",
    "size_param": "private.pageSize",
    "page_size": 4,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "data.total",
  "success": {
    "path": "retCode",
    "expect": "0"
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "announId": "00000000000010276003",
  "projectType": "R00301",
  "projectTypeStr": null,
  "title": "中国工商银行2026年度春季校园招聘笔试考生须知",
  "publishTime": "2026-04-14 19:05:38",
  "announStatus": "R01401",
  "announType": "R40302"
}
```

Sample 2:

```json
{
  "announId": "00000000000010212007",
  "projectType": "R00301",
  "projectTypeStr": null,
  "title": "中国工商银行广州分行2026年度春季校园招聘公告",
  "publishTime": "2026-03-12 16:52:23",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

Sample 3:

```json
{
  "announId": "00000000000010213009",
  "projectType": "R00301",
  "projectTypeStr": null,
  "title": "中国工商银行河北雄安分行2026年度春季校园招聘公告",
  "publishTime": "2026-03-12 16:52:23",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

Sample 4:

```json
{
  "announId": "00000000000010216005",
  "projectType": "R00301",
  "projectTypeStr": null,
  "title": "中国工商银行业务研发中心2026年度春季校园招聘公告",
  "publishTime": "2026-03-12 16:52:23",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

### Candidate 2

- Request: `POST https://job.icbc.com.cn/icbc/trmo/announ/qryAnnounList`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.dataList`
- Total path: `data.total`
- Confidence score: `47`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, host, loginway, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, userid, x-forwared-for, zoneflag, zoneno` (values redacted)
- Replay verdict: **未重放** — 共享端点预算只允许一个完整五级重放梯度；该过滤变体已保留但未发出请求
- Suspicious URL/header/query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://job.icbc.com.cn/icbc/trmo/announ/qryAnnounList",
  "method": "POST",
  "list_path": "data.dataList",
  "field_map": {
    "position_key": "announId",
    "title": "title",
    "raw_text": "content",
    "updated_at": "publishTime",
    "is_valid": "announStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "public": {
      "call_app": "F-TRM"
    },
    "private": {
      "page": 1,
      "pageSize": 4,
      "projectType": "R00302"
    }
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "private.page",
    "size_param": "private.pageSize",
    "page_size": 4,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "data.total",
  "success": {
    "path": "retCode",
    "expect": "0"
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "announId": "00000000000010602003",
  "projectType": "R00302",
  "projectTypeStr": null,
  "title": "中国工商银行北京市分行2026年社会招聘公告",
  "publishTime": "2026-07-21 13:32:53",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

Sample 2:

```json
{
  "announId": "00000000000010538003",
  "projectType": "R00302",
  "projectTypeStr": null,
  "title": "中国工商银行江西省分行2026年社会招聘公告",
  "publishTime": "2026-06-26 09:19:24",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

Sample 3:

```json
{
  "announId": "03000000000010436005",
  "projectType": "R00302",
  "projectTypeStr": null,
  "title": "中国工商银行天津市分行2026年社会招聘公告",
  "publishTime": "2026-06-02 08:39:33",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

Sample 4:

```json
{
  "announId": "00000000000010458003",
  "projectType": "R00302",
  "projectTypeStr": null,
  "title": "中国工商银行2026年海外人才招聘启事",
  "publishTime": "2026-06-01 17:58:05",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

### Candidate 3

- Request: `POST https://job.icbc.com.cn/icbc/trmo/announ/qryAnnounList`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.dataList`
- Total path: `data.total`
- Confidence score: `47`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, host, loginway, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, userid, x-forwared-for, zoneflag, zoneno` (values redacted)
- Replay verdict: **未重放** — 共享端点预算只允许一个完整五级重放梯度；该过滤变体已保留但未发出请求
- Suspicious URL/header/query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://job.icbc.com.cn/icbc/trmo/announ/qryAnnounList",
  "method": "POST",
  "list_path": "data.dataList",
  "field_map": {
    "position_key": "announId",
    "title": "title",
    "raw_text": "content",
    "updated_at": "publishTime",
    "is_valid": "announStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "public": {
      "call_app": "F-TRM"
    },
    "private": {
      "page": 1,
      "pageSize": 4,
      "projectType": "R00303"
    }
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "private.page",
    "size_param": "private.pageSize",
    "page_size": 4,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "data.total",
  "success": {
    "path": "retCode",
    "expect": "0"
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "announId": "00000000000010462015",
  "projectType": "R00303",
  "projectTypeStr": null,
  "title": "中国工商银行2026年星令营暑期实习公告",
  "publishTime": "2026-06-05 08:37:57",
  "announStatus": "R01403",
  "announType": "R40302"
}
```

Sample 2:

```json
{
  "announId": "00000000000010455007",
  "projectType": "R00303",
  "projectTypeStr": null,
  "title": "中国工商银行湖北省分行2026年星令营暑期实习公告",
  "publishTime": "2026-06-05 08:37:57",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

Sample 3:

```json
{
  "announId": "00000000000010455015",
  "projectType": "R00303",
  "projectTypeStr": null,
  "title": "中国工商银行苏州分行2026年星令营暑期实习公告",
  "publishTime": "2026-06-05 08:37:57",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

Sample 4:

```json
{
  "announId": "00000000000010456005",
  "projectType": "R00303",
  "projectTypeStr": null,
  "title": "中国工商银行数据中心2026年星令营暑期实习公告",
  "publishTime": "2026-06-05 08:37:57",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

### Candidate 4

- Request: `POST https://job.icbc.com.cn/icbc/trmo/post/qryPostType`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.dataList`
- Total path: `not inferred`
- Confidence score: `22`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, content-length, content-type, host, loginway, origin, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, user-agent, userid, x-forwared-for, zoneflag, zoneno` (values redacted)
- Replay verdict: **不可接入** — 最简合规头未返回等效非空候选列表
- Suspicious URL/header/query/body paths: `none`

#### Replay verification

| Level | HTTP | Equivalent non-empty list | Note |
| --- | ---: | :---: | --- |
| 完整头 + Cookie（基线） | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/post/qryPostType (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |
| 去掉疑似签名头 | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/post/qryPostType (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |
| 去掉 Cookie | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/post/qryPostType (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |
| 同时去掉两者 | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/post/qryPostType (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |
| 最简合规头 | — | no | request failed: HTTPSConnectionPool(host='job.icbc.com.cn', port=443): Max retries exceeded with url: /icbc/trmo/post/qryPostType (Caused by SSLError(SSLError(1, '[SSL: UNSAFE_LEGACY_RENEGOTIATION_DISABLED] unsafe legacy renegotiation disabled (_ssl.c:1032)'))) |

#### Parser configuration draft

The draft contains observed/inferred API fields only. Human review must add batch metadata and confirm campus scope.

```json
{
  "endpoint": "https://job.icbc.com.cn/icbc/trmo/post/qryPostType",
  "method": "POST",
  "list_path": "data.dataList",
  "field_map": {
    "position_key": "postTypeId",
    "title": "postName",
    "raw_text": "description",
    "updated_at": "lstModiTime",
    "is_valid": "postTypeStatus"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "public": {
      "call_app": "F-TRM"
    },
    "private": {}
  },
  "success": {
    "path": "retCode",
    "expect": "0"
  }
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "postTypeId": "D00001",
  "recruitType": "R00301",
  "postName": "星辰管培生",
  "postTypeStatus": "R01701",
  "lstModiTime": "2022-10-12 17:23:52"
}
```

Sample 2:

```json
{
  "postTypeId": "D00003",
  "recruitType": "R00301",
  "postName": "科技菁英",
  "postTypeStatus": "R01701",
  "lstModiTime": "2022-10-12 17:23:52"
}
```

Sample 3:

```json
{
  "postTypeId": "D00002",
  "recruitType": "R00301",
  "postName": "专业英才",
  "postTypeStatus": "R01701",
  "lstModiTime": "2022-10-12 17:23:52"
}
```

Sample 4:

```json
{
  "postTypeId": "D00004",
  "recruitType": "R00301",
  "postName": "客户经理",
  "postTypeStatus": "R01701",
  "lstModiTime": "2022-10-12 17:23:52"
}
```

Sample 5:

```json
{
  "postTypeId": "D00005",
  "recruitType": "R00301",
  "postName": "客服经理",
  "postTypeStatus": "R01701",
  "lstModiTime": "2022-10-12 17:23:52"
}
```

## Target B02

- Company: `中国建设银行`
- Company type: `银行`
- Official-source evidence: `https://www.ccb.com/cn/recruit/index.html`
- Entry page: `https://job.ccb.com/cn/job/index.html`
- Final page: `https://job1.ccb.com/cn/job/index.html`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target B03

- Company: `中国农业银行`
- Company type: `银行`
- Official-source evidence: `https://www.abchina.com.cn/cn/`
- Entry page: `https://career.abchina.com.cn/build/index.html`
- Final page: `https://career.abchina.com.cn/build/index.html#/`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target B04

- Company: `中国银行`
- Company type: `银行`
- Official-source evidence: `https://www.boc.cn/aboutboc/bi4/`
- Entry page: `https://www.boc.cn/aboutboc/bi4/`
- Final page: `https://www.boc.cn/aboutboc/bi4/`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target B05

- Company: `交通银行`
- Company type: `银行`
- Official-source evidence: `https://job.bankcomm.com/`
- Entry page: `https://job.bankcomm.com/`
- Final page: `https://job.bankcomm.com/#/`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target J01

- Company: `上汽大众汽车有限公司`
- Company type: `中外合资`
- Official-source evidence: `https://www.csvw.com/`
- Entry page: `https://csvw.zhiye.com/campus`
- Final page: `https://csvw.zhiye.com/campus`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target J02

- Company: `一汽-大众汽车有限公司`
- Company type: `中外合资`
- Official-source evidence: `https://www.faw-vw.com/home`
- Entry page: `https://www.faw-vw.com/home`
- Final page: `https://www.faw-vw.com/home`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://www.faw-vw.com/api/v0.1/service/gateway/cms-mgmt/vehicle/getVehicleSeriesInfo`
- Response: `200` / `application/json`
- Candidate list path: `data`
- Total path: `not inferred`
- Confidence score: `23`
- Shared endpoint replay budget: `5 / 6`
- Captured request header names: `accept, accept-encoding, connection, cookie, host, language, referer, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform, sec-fetch-dest, sec-fetch-mode, sec-fetch-site, tenant-id, user-agent, x-xsrf-token` (values redacted)
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
  "endpoint": "https://www.faw-vw.com/api/v0.1/service/gateway/cms-mgmt/vehicle/getVehicleSeriesInfo",
  "method": "GET",
  "list_path": "data",
  "field_map": {
    "position_key": "pictureId",
    "title": "vehicleSeriesName",
    "raw_text": "detailsUrl",
    "application_url": "subscribeUrl",
    "updated_at": "updatedBy"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "params": {}
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "vehicleSeriesName": "ID. AURA T6",
  "vehicleType": "ID.系列",
  "vehicleTypeCode": "ID",
  "subscribeUrl": "https://vw.faw-vw.com/#/CarDetails?vsid=29&car_series=ID&car_model=ID.+AURA+T6&entrance_tap=eJ64Wv07yQZPT2PDjxQaxYs0CYbWrdgCqRVDY7u/9RdBfA0mKtV8mJ1XnqbDcSdC&entrance_page=03vxR4e0JMgb6rm8OhMvxw==&car_type=4&car_three_code=NEW+ID",
  "pictureId": "07f614f7-1d82-4b23-8398-93a1329fd4db",
  "updatedBy": "SYSTEM_ADMIN_BE_00000001"
}
```

Sample 2:

```json
{
  "vehicleSeriesName": "Q4 e-tron",
  "vehicleType": "e-tron系列",
  "vehicleTypeCode": "e-tron Series",
  "subscribeUrl": "https://www.audi.cn/zh/q4_etron_testdrive.html",
  "pictureId": "ca677761-8f38-4c7a-bf72-069a38d02ed8",
  "updatedBy": "SYSTEM_ADMIN_BE_00000001"
}
```

Sample 3:

```json
{
  "vehicleSeriesName": "VS8",
  "vehicleType": "SUV",
  "vehicleTypeCode": "SUV",
  "subscribeUrl": "https://jetta.faw-vw.com/#/test-drive?modelCode=39",
  "pictureId": "cf594adc-c662-406d-bb42-4e8d1f5f39fe",
  "updatedBy": "SYSTEM_ADMIN_BE_00000001"
}
```

Sample 4:

```json
{
  "vehicleSeriesName": "捷达",
  "vehicleType": "轿车",
  "vehicleTypeCode": "Sedan",
  "subscribeUrl": null,
  "pictureId": "f0246d10-840b-4c7a-b2b0-082c52b24e8f",
  "updatedBy": "SYSTEM_ADMIN_BE_00000001"
}
```

Sample 5:

```json
{
  "vehicleSeriesName": "探岳L",
  "vehicleType": "SUV",
  "vehicleTypeCode": "SUV",
  "subscribeUrl": "https://vw.faw-vw.com/#/IndexSix?tapPath=Lv1fTWA7TFCHnlM2F4jO7q0EXG/JLNP8Fc6jmKGCav//YdfOhextvBm5/fiz65cc&submit=Lv1fTWA7TFCHnlM2F4jO7nFiWW5IxUW/47d/dUCBwNPqB0lxsshXnQEe0MGOUJzr&page=UBX9XxPtib5wg/tlLN5E1A==&modelName=%E5%85%A8%E6%96%B0%E6%8E%A2%E5%B2%B3L&modelCode=21",
  "pictureId": "0fd3c483-86e0-4aff-a094-9289df8239c5",
  "updatedBy": "SYSTEM_ADMIN_BE_00000001"
}
```

## Target J03

- Company: `广汽丰田汽车有限公司`
- Company type: `中外合资`
- Official-source evidence: `https://www.gac-toyota.com.cn/`
- Entry page: `https://gac-toyota.zhiye.com/campus/`
- Final page: `https://gac-toyota.zhiye.com/campus/`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target J04

- Company: `东风日产乘用车公司`
- Company type: `中外合资`
- Official-source evidence: `https://www.dongfeng-nissan.com.cn/about/recruit`
- Entry page: `https://www.dongfeng-nissan.com.cn/about/recruit/campus`
- Final page: `https://www.dongfeng-nissan.com.cn/about/recruit/campus`
- Page status: `200`

### Capture notes

- `GET https://pv.sohu.com/cityjson?ie=utf-8` / `200` — JSON body could not be retained: Expecting value: line 1 column 1 (char 0)
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target I01

- Company: `中国信息通信研究院`
- Company type: `事业单位`
- Official-source evidence: `https://www.caict.ac.cn/zpxx/`
- Entry page: `https://www.hotjob.cn/wt/caict/web/index/webPosition210!getPostListByConditionShowPic`
- Final page: `https://www.hotjob.cn/wt/caict/web/index/webPosition210!getPostListByConditionShowPic`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target I02

- Company: `中国科学院计算技术研究所`
- Company type: `事业单位`
- Official-source evidence: `https://www.ict.cas.cn/rczp/`
- Entry page: `https://www.ict.cas.cn/rczp/`
- Final page: `—`
- Page status: `None`
- Outcome: skipped
- Reason: 浏览器捕获失败：Page.goto: net::ERR_CERT_AUTHORITY_INVALID at https://www.ict.cas.cn/rczp/ Call log: - navigating to "https://www.ict.cas.cn/rczp/", waiting until "domcontentloaded"

## Target I03

- Company: `中国标准化研究院`
- Company type: `事业单位`
- Official-source evidence: `https://www.cnis.ac.cn/ynbm/rlzyb/rczp/`
- Entry page: `https://www.cnis.ac.cn/ynbm/rlzyb/rczp/`
- Final page: `https://www.cnis.ac.cn/ynbm/rlzyb/rczp/`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target N01

- Company: `中国汽车工业协会`
- Company type: `社会机构`
- Official-source evidence: `https://www.caam.org.cn/`
- Entry page: `https://www.caam.org.cn/chn/8/cate_81/list_1.html`
- Final page: `—`
- Page status: `None`
- Outcome: skipped
- Reason: 浏览器捕获失败：Page.goto: net::ERR_CONNECTION_CLOSED at https://www.caam.org.cn/chn/8/cate_81/list_1.html Call log: - navigating to "https://www.caam.org.cn/chn/8/cate_81/list_1.html", waiting until "domcontentloaded"

## Target N02

- Company: `中国红十字会总会`
- Company type: `社会机构`
- Official-source evidence: `https://www.redcross.org.cn/careers.html`
- Entry page: `https://www.redcross.org.cn/careers.html`
- Final page: `https://www.redcross.org.cn/careers.html`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.
