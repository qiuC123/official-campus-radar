# Recruitment API discovery report

Generated: `2026-08-27T12:53:58+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target P03-C09

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
- Candidate row count: `9`
- Total path: `not inferred`
- Reported total: `None`
- Confidence score: `27`
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
    "is_valid": "classify.status"
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
  "classify.status": 0,
  "itemId": 3771,
  "itemName": "Technology",
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
  "classify.status": 0,
  "itemId": 3770,
  "itemName": "Sales",
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
  "classify.status": 0,
  "itemId": 7873,
  "itemName": "Service Class",
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
  "classify.status": 0,
  "itemId": 3768,
  "itemName": "Supply Chain",
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
  "classify.status": 0,
  "itemId": 3769,
  "itemName": "Finance",
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
- Candidate row count: `3`
- Total path: `not inferred`
- Reported total: `None`
- Confidence score: `25`
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
    "is_valid": "classify.status"
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
  "classify.status": 0,
  "itemId": 13104,
  "itemName": "Inaccurte recommendations and large deviation",
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
  "classify.status": 0,
  "itemId": 13106,
  "itemName": "Slow response and poor user expirence",
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
  "classify.status": 0,
  "itemId": 13108,
  "itemName": "no practical help",
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
- Candidate row count: `1`
- Total path: `not inferred`
- Reported total: `None`
- Confidence score: `23`
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
    "updated_at": "creationDate",
    "is_valid": "classify.status"
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
  "classify.status": 0,
  "itemId": 13433,
  "itemAttr1": null,
  "itemAttr2": null,
  "itemAttr3": null,
  "itemAttr4": null,
  "itemAttr5": null,
  "itemAttr6": null
}
```

## Target P06-C09

- Company: `百度`
- Company type: `民企`
- Official-source evidence: `https://talent.baidu.com/external/baidu/campus.html`
- Entry page: `https://talent.baidu.com/jobs/campus`
- Final page: `about:blank`
- Page status: `200`
- Outcome: skipped
- Reason: 页面无可见内容且未捕获 JSON 响应，可能被无头浏览器拦截

## Target P09-C09

- Company: `小米`
- Company type: `民企`
- Official-source evidence: `https://campus.hr.xiaomi.com/`
- Entry page: `https://hr.xiaomi.com/campus/list/0-0-0`
- Final page: `https://hr.xiaomi.com/campus/list/0-0-0`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P10-C09

- Company: `网易`
- Company type: `民企`
- Official-source evidence: `https://campus.163.com/`
- Entry page: `https://campus.163.com/app/job/position?id=76`
- Final page: `https://campus.163.com/app/job/position?id=76`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target P16-C09

- Company: `吉利控股`
- Company type: `民企`
- Official-source evidence: `https://campus.geely.com/`
- Entry page: `https://campus.geely.com/campus-recruitment/geely/98148#/`
- Final page: `https://campus.geely.com/campus-recruitment/geely/98148#/`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://campus.geely.com/api/extension-server/extension/list-by-org?orgId=geely`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.extensions[0].apps`
- Candidate row count: `4`
- Total path: `not inferred`
- Reported total: `None`
- Confidence score: `12`
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
  "endpoint": "https://campus.geely.com/api/extension-server/extension/list-by-org",
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
    "orgId": "geely"
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
  "name": "tdAtsWebAggregationGeelySocial",
  "config.locations": [
    {
      "slot": "offer-form",
      "client": [
        "hr-web"
      ]
    }
  ]
}
```

Sample 2:

```json
{
  "name": "tdAtsWebAggregationGeelyAiExport",
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

Sample 3:

```json
{
  "name": "tdAtsWebAggregationGeelyBackAdjustment",
  "config.locations": [
    {
      "slot": "candidate-detail-button",
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
  "name": "tdAtsWebAggregationGeelyJobShow",
  "config.locations": [
    {
      "slot": "job-recruitment-website",
      "client": [
        "hr-web"
      ]
    }
  ]
}
```

## Target P17-C09

- Company: `美的集团`
- Company type: `民企`
- Official-source evidence: `https://careers.midea.com/`
- Entry page: `https://careers.midea.com/schoolOut/post?type=2`
- Final page: `https://careers.midea.com/schoolOut/post?type=2`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://iop.midea.com/robot/noLogin/session/init/session`
- Response: `200` / `application/json`
- Candidate list path: `data.wsMessageVOS`
- Candidate row count: `1`
- Total path: `not inferred`
- Reported total: `None`
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
    "application_url": "content.aiLinkThinkBOS",
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
    "userName": "IOP_TOURISTS_1787806381818_2kvZ",
    "channelCode": "campus",
    "skillCode": "ROBOT_SKILL_GROUP_IpuN_39790179296",
    "endPoint": "PC",
    "wsSessionId": "IOP_WS_hSlw_39806384426",
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
  "content.aiLinkThinkBOS": [
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "招聘流程是什么样的？投递多久能有反馈？如何知道我的招聘进展？",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250812000135455662KDG"
    },
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "流程结束后还能再投别的岗位吗？",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250813000136763993KDG"
    },
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "如何进行网申投递简历？有什么注意事项吗？",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250812000135471375KDG"
    },
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "我投递简历的时候出现系统故障无法投递，需要怎么解决？",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250812000135448345KDG"
    },
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "投递简历时可以选择几个岗位志愿？",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250812000135471443KDG"
    },
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "从筛选简历，到笔试，再到面试，每个步骤的通过比例是多少？",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250812000135464642KDG"
    },
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "什么时候收到笔试通知？什么时候进行面试？通知的形式是什么？",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250812000135464497KDG"
    },
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "什么岗位需要做AI面试？什么时候收到AI面试通知？通知的形式是什么？",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250812000135456397KDG"
    },
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "面试分几轮",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250812000135449054KDG"
    },
    {
      "classifyId": "2008",
      "classifyName": "猜你想问",
      "question": "薪资水平是否与面试结果相关？",
      "questionId": "ROBOT_SKILL_GROUP_IpuN_39790179296#FQ30KP20250812000135464937KDG"
    }
  ],
  "knowledgeRegion": null,
  "messageSourceType": "IOP",
  "msgReturnType": null,
  "terminateMsgType": null,
  "timestamp": "2026-08-27 12:53:05",
  "type": "WELCOME",
  "userName": "IOP_TOURISTS_1787806381818_2kvZ"
}
```

### Candidate 2

- Request: `GET https://iop.midea.com/robot/questionBank/noLogin/component?iopDomainName=campus&userName=IOP_TOURISTS_1787806381401_h8O0`
- Response: `200` / `application/json`
- Candidate list path: `data`
- Candidate row count: `2`
- Total path: `not inferred`
- Reported total: `None`
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
    "userName": "IOP_TOURISTS_1787806381401_h8O0"
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

- Request: `GET https://careers.midea.com/backend/school/position/common/project/list?status=1&projectTypes=1%2C2%2C9%2C5&employementCategories=1%2C4&_ihr_log_trackId=049591ba-d8a3-4ed6-98d6-86729df4f323`
- Response: `200` / `application/json`
- Candidate list path: `data`
- Candidate row count: `1`
- Total path: `not inferred`
- Reported total: `None`
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
    "_ihr_log_trackId": "049591ba-d8a3-4ed6-98d6-86729df4f323"
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
  "employementCategory": 4,
  "status": 1,
  "projectType": "9",
  "graduationStartDate": 1767196800000
}
```

## Target P19-C09

- Company: `比亚迪`
- Company type: `民企`
- Official-source evidence: `https://job.byd.com/portal/mobile/school-home`
- Entry page: `https://job.byd.com/portal/pc/`
- Final page: `https://job.byd.com/portal/pc/#/home`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `GET https://job.byd.com/portal/api/portal-api/material/getMaterial?ids=81031%2C81034%2C81032%2C81033`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.81032`
- Candidate row count: `8`
- Total path: `not inferred`
- Reported total: `None`
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
  "list_path": "data.81032",
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
    "ids": "81031,81034,81032,81033"
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
  "fileName": "员工食堂",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E5%91%98%E5%B7%A5%E7%A6%8F%E5%88%A9/1%E5%91%98%E5%B7%A5%E9%A3%9F%E5%A0%82%20Employee%20Cafeteria.jpg",
  "id": "2",
  "updateTime": null
}
```

Sample 2:

```json
{
  "delStatus": 1,
  "fileName": "员工宿舍",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E5%91%98%E5%B7%A5%E7%A6%8F%E5%88%A9/2%E5%91%98%E5%B7%A5%E5%AE%BF%E8%88%8D%20%20Employee%20Dormitory.jpg",
  "id": "3",
  "updateTime": null
}
```

Sample 3:

```json
{
  "delStatus": 1,
  "fileName": "园区云巴",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E5%91%98%E5%B7%A5%E7%A6%8F%E5%88%A9/3%E5%9B%AD%E5%8C%BA%E4%BA%91%E5%B7%B4Campus%20SkyRail.jpg",
  "id": "4",
  "updateTime": null
}
```

Sample 4:

```json
{
  "delStatus": 1,
  "fileName": "健身器材",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E5%91%98%E5%B7%A5%E7%A6%8F%E5%88%A9/4%E5%81%A5%E8%BA%AB%E5%99%A8%E6%9D%90%20Fitness%20Equipment.jpg",
  "id": "5",
  "updateTime": null
}
```

Sample 5:

```json
{
  "delStatus": 1,
  "fileName": "专题培训",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E5%91%98%E5%B7%A5%E7%A6%8F%E5%88%A9/5%E4%B8%93%E9%A2%98%E5%9F%B9%E8%AE%AD%20Specialized%20Training.jpg",
  "id": "8",
  "updateTime": null
}
```

### Candidate 2

- Request: `GET https://job.byd.com/portal/api/portal-api/material/getMaterial?ids=81031%2C81034%2C81032%2C81033`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.81034`
- Candidate row count: `6`
- Total path: `not inferred`
- Reported total: `None`
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
  "list_path": "data.81034",
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
    "ids": "81031,81034,81032,81033"
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
  "fileName": "电子-精密制造",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/6.jpg",
  "id": "13",
  "updateTime": null
}
```

Sample 2:

```json
{
  "delStatus": 1,
  "fileName": "电池-刀片电池",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/5.jpg",
  "id": "14",
  "updateTime": null
}
```

Sample 3:

```json
{
  "delStatus": 1,
  "fileName": "汽车-DMI",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/4.jpg",
  "id": "15",
  "updateTime": null
}
```

Sample 4:

```json
{
  "delStatus": 1,
  "fileName": "云巴-智能轨道交通系统",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/3.jpg",
  "id": "16",
  "updateTime": null
}
```

Sample 5:

```json
{
  "delStatus": 1,
  "fileName": "半导体-IGBT",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/2.jpg",
  "id": "17",
  "updateTime": null
}
```

### Candidate 3

- Request: `GET https://job.byd.com/portal/api/portal-api/material/getMaterial?ids=81031%2C81034%2C81032%2C81033`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.81033`
- Candidate row count: `4`
- Total path: `not inferred`
- Reported total: `None`
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
  "list_path": "data.81033",
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
    "ids": "81031,81034,81032,81033"
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
  "fileName": "元旦晚会",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E5%91%98%E5%B7%A5%E6%B4%BB%E5%8A%A8/%E5%85%83%E6%97%A6%E6%99%9A%E4%BC%9A.jpg",
  "id": "9",
  "updateTime": null
}
```

Sample 2:

```json
{
  "delStatus": 1,
  "fileName": "家庭欢乐月",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E5%91%98%E5%B7%A5%E6%B4%BB%E5%8A%A8/%E5%AE%B6%E5%BA%AD%E6%AC%A2%E4%B9%90%E6%9C%88.jpg",
  "id": "10",
  "updateTime": null
}
```

Sample 3:

```json
{
  "delStatus": 1,
  "fileName": "空巢青年社交趴",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E5%91%98%E5%B7%A5%E6%B4%BB%E5%8A%A8/%E7%A9%BA%E5%B7%A2%E9%9D%92%E5%B9%B4%E7%A4%BE%E4%BA%A4%E8%B6%B4.jpg",
  "id": "11",
  "updateTime": null
}
```

Sample 4:

```json
{
  "delStatus": 1,
  "fileName": "迪厂音乐节",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E5%91%98%E5%B7%A5%E6%B4%BB%E5%8A%A8/%E8%BF%AA%E5%8E%82%E9%9F%B3%E4%B9%90%E8%8A%82.jpg",
  "id": "12",
  "updateTime": null
}
```

### Candidate 4

- Request: `GET https://job.byd.com/portal/api/portal-api/material/getMaterial?ids=81031%2C81034%2C81032%2C81033`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.81031`
- Candidate row count: `1`
- Total path: `not inferred`
- Reported total: `None`
- Confidence score: `14`
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
  "list_path": "data.81031",
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
    "ids": "81031,81034,81032,81033"
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
  "fileName": "中国青年，一路向前",
  "fileUrl": "https://ess-cdn.byd.com/%E6%8B%9B%E8%81%98/%E9%97%A8%E6%88%B7/%E5%9B%BD%E5%86%85%E8%8B%B1%E6%96%87%E7%89%88/%E9%A6%96%E9%A1%B5/%E9%A1%B6%E9%83%A8%E8%A7%86%E9%A2%91/Who%20is%20byd%20241210.mp4",
  "id": "2001",
  "updateTime": null
}
```
