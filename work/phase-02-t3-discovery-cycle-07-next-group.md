# Recruitment API discovery report

Generated: `2026-08-27T12:24:55+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target P12-C07

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
- Candidate row count: `10`
- Total path: `data.total`
- Reported total: `239`
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
- Candidate row count: `11`
- Total path: `not inferred`
- Reported total: `None`
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

## Target P08-C07

- Company: `美团`
- Company type: `民企`
- Official-source evidence: `https://zhaopin.meituan.com/`
- Entry page: `https://job.meituan.com/web/campus`
- Final page: `https://job.meituan.com/web/campus`
- Page status: `200`

### Capture notes

- `POST https://catfront.dianping.com/pbbatchts?v=1&sdk=1.13.0&pageId=owl-32accbd6-179c-adc8-da04-5316-1787804595067&p=com.sankuai.recruitment.official.website` / `200` — Request body omitted: unavailable as UTF-8 text
- `POST https://catfront.dianping.com/pbbatchts?v=1&sdk=1.13.0&pageId=owl-32accbd6-179c-adc8-da04-5316-1787804595067&p=com.sankuai.recruitment.official.website` / `200` — Request body omitted: unavailable as UTF-8 text
- `POST https://catfront.dianping.com/pbbatchts?v=1&sdk=1.13.0&pageId=owl-32accbd6-179c-adc8-da04-5316-1787804595067&p=com.sankuai.recruitment.official.website` / `200` — Request body omitted: unavailable as UTF-8 text
- `POST https://catfront.dianping.com/pbbatchts?v=1&sdk=1.13.0&pageId=owl-32accbd6-179c-adc8-da04-5316-1787804595067&p=com.sankuai.recruitment.official.website` / `200` — Request body omitted: unavailable as UTF-8 text
- `POST https://catfront.dianping.com/pbbatchts?v=1&sdk=1.13.0&pageId=owl-32accbd6-179c-adc8-da04-5316-1787804595067&p=com.sankuai.recruitment.official.website` / `200` — Request body omitted: unavailable as UTF-8 text
- `POST https://catfront.dianping.com/pbbatchts?v=1&sdk=1.13.0&pageId=owl-32accbd6-179c-adc8-da04-5316-1787804595067&p=com.sankuai.recruitment.official.website` / `200` — Request body omitted: unavailable as UTF-8 text
- `POST https://catfront.dianping.com/pbbatchts?v=1&sdk=1.13.0&pageId=owl-32accbd6-179c-adc8-da04-5316-1787804595067&p=com.sankuai.recruitment.official.website` / `200` — Request body omitted: unavailable as UTF-8 text
- `POST https://catfront.dianping.com/pbbatchts?v=1&sdk=1.13.0&pageId=owl-32accbd6-179c-adc8-da04-5316-1787804595067&p=com.sankuai.recruitment.official.website` / `200` — Request body omitted: unavailable as UTF-8 text
- `POST https://catfront.dianping.com/pbbatchts?v=1&sdk=1.13.0&pageId=owl-32accbd6-179c-adc8-da04-5316-1787804595067&p=com.sankuai.recruitment.official.website` / `200` — Request body omitted: unavailable as UTF-8 text
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://job.meituan.com/api/official/job/getJobList`
- Response: `200` / `application/json`
- Candidate list path: `data.list`
- Candidate row count: `10`
- Total path: `data.page.totalPage`
- Reported total: `57`
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
    "title": "name",
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
    "u_query_id": "6dd23e48564efdb3aeabc32093fac65c",
    "r_query_id": "178780459568670203468"
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
  "jobUnionId": "3763421415",
  "name": "大模型算法实习生",
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
    },
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

Sample 2:

```json
{
  "jobUnionId": "4669976027",
  "name": "海外AI开发者社区运营实习生（Longcat大模型）",
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

Sample 3:

```json
{
  "jobUnionId": "4555593816",
  "name": "Agent算法实习生",
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
    },
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

Sample 4:

```json
{
  "jobUnionId": "4306214875",
  "name": "Agent开发实习生（AI 产品方向）",
  "jobType": "2",
  "jobStatus": "000",
  "cityList": [
    {
      "code": null,
      "name": "成都市",
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
  "jobUnionId": "4709354699",
  "name": "导购产品实习生",
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

## Target F02-C07

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
- Candidate row count: `10`
- Total path: `facets.category_facet[12].Finance & Accounting`
- Reported total: `6`
- Confidence score: `93`
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
    "updated_at": "team.updated_at"
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
  "business_category": "advertising",
  "city": "Shanghai",
  "id": "9f45f0a6-27ba-423d-8015-728ab1eaf0c5",
  "is_intern": null,
  "job_category": "Marketing & PR",
  "job_schedule_type": "full-time",
  "title": "Sr. Brand Marketing Manager, Amazon Ads CN Brand Marketing ",
  "url_next_step": "https://account.amazon.com/jobs/3201456/apply",
  "team.business_category_id": null,
  "team.updated_at": null,
  "team.image_content_type": null,
  "team.thumbnail_content_type": null
}
```

Sample 2:

```json
{
  "business_category": "retail",
  "city": "Shenzhen",
  "id": "4321b3df-fa05-437a-bc36-3fac09902038",
  "is_intern": null,
  "job_category": "Project/Program/Product Management--Non-Tech",
  "job_schedule_type": "full-time",
  "title": "Ecommerce Operations Manager, Amazon Private Brands Global Sourcing",
  "url_next_step": "https://account.amazon.jobs/jobs/10516415/apply",
  "team.business_category_id": null,
  "team.updated_at": null,
  "team.image_content_type": null,
  "team.thumbnail_content_type": null
}
```

Sample 3:

```json
{
  "business_category": "transportation-and-logistics",
  "city": "Shenzhen",
  "id": "dd66fb60-4793-4f06-911b-5be1c97a6692",
  "is_intern": null,
  "job_category": "Administrative Support",
  "job_schedule_type": "full-time",
  "title": "Sales Operation Intern, SalesOps Team",
  "url_next_step": "https://account.amazon.jobs/jobs/10516357/apply",
  "team.business_category_id": null,
  "team.updated_at": null,
  "team.image_content_type": null,
  "team.thumbnail_content_type": null
}
```

Sample 4:

```json
{
  "business_category": "aws",
  "city": "Beijing",
  "id": "a9583c9a-5928-4817-8d7e-7aa1dabe1900",
  "is_intern": null,
  "job_category": "Sales, Advertising, & Account Management",
  "job_schedule_type": "full-time",
  "title": "BD Manager, Gaming North",
  "url_next_step": "https://account.amazon.jobs/jobs/10515913/apply",
  "team.business_category_id": null,
  "team.updated_at": null,
  "team.image_content_type": null,
  "team.thumbnail_content_type": null
}
```

Sample 5:

```json
{
  "business_category": "alexa-and-amazon-devices",
  "city": "Shenzhen",
  "id": "10f0faf0-e640-4b40-b2bc-8eacdb9defc3",
  "is_intern": null,
  "job_category": "Hardware Development",
  "job_schedule_type": "full-time",
  "title": "HW Safety Compliance Engineer ",
  "url_next_step": "https://account.amazon.jobs/jobs/10515809/apply",
  "team.business_category_id": null,
  "team.updated_at": null,
  "team.image_content_type": null,
  "team.thumbnail_content_type": null
}
```

## Target B01-C07

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
- Candidate row count: `4`
- Total path: `data.total`
- Reported total: `38`
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
  "announId": "00000000000010213003",
  "projectType": "R00301",
  "projectTypeStr": null,
  "title": "中国工商银行青岛市分行2026年度春季校园招聘公告",
  "publishTime": "2026-03-12 16:52:23",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

Sample 3:

```json
{
  "announId": "00000000000010213011",
  "projectType": "R00301",
  "projectTypeStr": null,
  "title": "中国工商银行吉林省分行2026年度春季校园招聘公告",
  "publishTime": "2026-03-12 16:52:23",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

Sample 4:

```json
{
  "announId": "00000000000010216009",
  "projectType": "R00301",
  "projectTypeStr": null,
  "title": "中国工商银行宁夏分行2026年度春季校园招聘公告",
  "publishTime": "2026-03-12 16:52:23",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

### Candidate 2

- Request: `POST https://job.icbc.com.cn/icbc/trmo/announ/qryAnnounList`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.dataList`
- Candidate row count: `4`
- Total path: `data.total`
- Reported total: `9`
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
- Candidate row count: `4`
- Total path: `data.total`
- Reported total: `45`
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
  "announId": "00000000000010455009",
  "projectType": "R00303",
  "projectTypeStr": null,
  "title": "中国工商银行广西分行2026年星令营暑期实习公告",
  "publishTime": "2026-06-05 08:37:57",
  "announStatus": "R01401",
  "announType": "R40301"
}
```

### Candidate 4

- Request: `POST https://job.icbc.com.cn/icbc/trmo/post/qryPostType`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.dataList`
- Candidate row count: `24`
- Total path: `not inferred`
- Reported total: `None`
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
  "lstModiTime": "2022-10-12 17:23:39"
}
```

Sample 2:

```json
{
  "postTypeId": "D00003",
  "recruitType": "R00301",
  "postName": "科技菁英",
  "postTypeStatus": "R01701",
  "lstModiTime": "2022-10-12 17:23:39"
}
```

Sample 3:

```json
{
  "postTypeId": "D00002",
  "recruitType": "R00301",
  "postName": "专业英才",
  "postTypeStatus": "R01701",
  "lstModiTime": "2022-10-12 17:23:39"
}
```

Sample 4:

```json
{
  "postTypeId": "D00004",
  "recruitType": "R00301",
  "postName": "客户经理",
  "postTypeStatus": "R01701",
  "lstModiTime": "2022-10-12 17:23:39"
}
```

Sample 5:

```json
{
  "postTypeId": "D00005",
  "recruitType": "R00301",
  "postName": "客服经理",
  "postTypeStatus": "R01701",
  "lstModiTime": "2022-10-12 17:23:39"
}
```
