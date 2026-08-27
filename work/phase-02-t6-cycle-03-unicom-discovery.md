# Recruitment API discovery report

Generated: `2026-08-27T17:39:34+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target 1

- Company: `—`
- Company type: `—`
- Official-source evidence: `—`
- Entry page: `https://zglt.zhaopin.com/scjobs/index.html`
- Final page: `https://zglt.zhaopin.com/scjobs/index.html`
- Page status: `200`
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://fe.zhaopin.com/grace/api/dsc/search-job-list`
- Response: `200` / `application/json; charset=utf-8`
- Candidate list path: `data.jobList`
- Candidate row count: `11`
- Total path: `data.pageInfo.totalNum`
- Reported total: `2704`
- Confidence score: `188`
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
  "endpoint": "https://fe.zhaopin.com/grace/api/dsc/search-job-list",
  "method": "POST",
  "list_path": "data.jobList",
  "field_map": {
    "title": "job.title",
    "location": "job.cityName",
    "raw_text": "job.detail",
    "application_url": "job.url",
    "updated_at": "job.modifiedTime"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {
    "orgNumbers": [
      "105347"
    ],
    "jobSource": 2,
    "pageIndex": 1,
    "pageSize": 11,
    "orgDepartmentIds": [],
    "workRegionIds": "",
    "jobTypes": "",
    "priorityMajors": "",
    "customTags": "",
    "campusParentDepartmentIds": ""
  },
  "pagination": {
    "mode": "page_index",
    "page_param": "pageIndex",
    "size_param": "pageSize",
    "page_size": 11,
    "start_page": 1,
    "max_pages": 10
  },
  "total_path": "data.pageInfo.totalNum",
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
  "company.bestEmployerType": 0,
  "company.campusOrgName": "中国联通河南省分公司",
  "company.campusOrgShortName": "",
  "company.campusParentDepartment": null,
  "job.cityName": "郑州",
  "job.employmentType": 5,
  "job.jobType": 3000300090000,
  "job.jobTypeName": "通信项目经理",
  "job.modifiedTime": 1787823383313,
  "job.positionSourceType": 2,
  "job.salaryType": 1,
  "job.title": "AI FDE工程师",
  "job.url": "https://xiaoyuan.zhaopin.com/job/CC145093010J40891012705"
}
```

Sample 2:

```json
{
  "company.bestEmployerType": 0,
  "company.campusOrgName": "中国联通河南省分公司",
  "company.campusOrgShortName": "",
  "company.campusParentDepartment": null,
  "job.cityName": "郑州",
  "job.employmentType": 5,
  "job.jobType": 3000300090000,
  "job.jobTypeName": "通信项目经理",
  "job.modifiedTime": 1787820576145,
  "job.positionSourceType": 2,
  "job.salaryType": 1,
  "job.title": "人工智能解决方案经理",
  "job.url": "https://xiaoyuan.zhaopin.com/job/CC145093010J40891013105"
}
```

Sample 3:

```json
{
  "company.bestEmployerType": 0,
  "company.campusOrgName": "中国联通河南省分公司",
  "company.campusOrgShortName": "",
  "company.campusParentDepartment": null,
  "job.cityName": "郑州",
  "job.employmentType": 5,
  "job.jobType": 3000300090000,
  "job.jobTypeName": "通信项目经理",
  "job.modifiedTime": 1787820563490,
  "job.positionSourceType": 2,
  "job.salaryType": 1,
  "job.title": "人工智能交付经理",
  "job.url": "https://xiaoyuan.zhaopin.com/job/CC145093010J40891013005"
}
```

Sample 4:

```json
{
  "company.bestEmployerType": 0,
  "company.campusOrgName": "中国联通河南省分公司",
  "company.campusOrgShortName": "",
  "company.campusParentDepartment": null,
  "job.cityName": "郑州",
  "job.employmentType": 5,
  "job.jobType": 20000200210000,
  "job.jobTypeName": "网络信息安全工程师",
  "job.modifiedTime": 1787820552064,
  "job.positionSourceType": 2,
  "job.salaryType": 1,
  "job.title": "安全服务工程师",
  "job.url": "https://xiaoyuan.zhaopin.com/job/CC145093010J40891012905"
}
```

Sample 5:

```json
{
  "company.bestEmployerType": 0,
  "company.campusOrgName": "中国联通河南省分公司",
  "company.campusOrgShortName": "",
  "company.campusParentDepartment": null,
  "job.cityName": "郑州",
  "job.employmentType": 5,
  "job.jobType": 3000300090000,
  "job.jobTypeName": "通信项目经理",
  "job.modifiedTime": 1787820538483,
  "job.positionSourceType": 2,
  "job.salaryType": 1,
  "job.title": "云原生交付工程师",
  "job.url": "https://xiaoyuan.zhaopin.com/job/CC145093010J40891012805"
}
```
