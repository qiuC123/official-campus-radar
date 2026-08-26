# Recruitment API discovery report

Generated: `2026-08-27T00:06:00+08:00`

> Development-only evidence. A discovered endpoint is not an integrated source; samples require human review to confirm campus recruitment.

## Target J03-FAMILY

- Company: `广汽丰田汽车有限公司`
- Company type: `中外合资`
- Official-source evidence: `https://www.gac-toyota.com.cn/`
- Entry page: `https://gac-toyota.zhiye.com/campus/`
- Final page: `https://gac-toyota.zhiye.com/campus/`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target I01-FAMILY

- Company: `中国信息通信研究院`
- Company type: `事业单位`
- Official-source evidence: `https://www.caict.ac.cn/zpxx/`
- Entry page: `https://www.hotjob.cn/wt/caict/web/index/webPosition210!getPostListByConditionShowPic`
- Final page: `https://www.hotjob.cn/wt/caict/web/index/webPosition210!getPostListByConditionShowPic`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.

## Target S08-FAMILY

- Company: `中国中车集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.crrcgc.cc/`
- Entry page: `https://wecruit.hotjob.cn/SU64d480906202cc36e27a5fd8/mc/position/campus`
- Final page: `https://wecruit.hotjob.cn/SU64d480906202cc36e27a5fd8/mc/position/campus`
- Page status: `200`

### Capture notes

- `POST https://wecruit.hotjob.cn/wecruit/isLogin/SU64d480906202cc36e27a5fd8?iSaJAx=isAjax&request_locale=zh_CN` / `200` — JSON body could not be retained: Response.body: Protocol error (Network.getResponseBody): No resource with given identifier found Response body is not available for a response that was navigated away from. Read response.body() before triggering any navigation.
- `GET https://wecruit.hotjob.cn/wecruit/suite/config/SU64d480906202cc36e27a5fd8?iSaJAx=isAjax&request_locale=zh_CN` / `200` — JSON body could not be retained: Response.body: Target page, context or browser has been closed
- Outcome: candidate endpoints observed

Candidate APIs below are discovery facts, not integration claims.

### Candidate 1

- Request: `POST https://wecruit.hotjob.cn/wecruit/positionInfo/listPosition/SU64d480906202cc36e27a5fd8?iSaJAx=isAjax&request_locale=zh_CN`
- Response: `200` / `application/json;charset=UTF-8`
- Candidate list path: `data.pageForm.pageData`
- Total path: `data.pageForm.totalPage`
- Confidence score: `46`
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
  "endpoint": "https://wecruit.hotjob.cn/wecruit/positionInfo/listPosition/SU64d480906202cc36e27a5fd8",
  "method": "POST",
  "list_path": "data.pageForm.pageData",
  "field_map": {
    "position_key": "postId",
    "title": "postName",
    "location": "workPlaceStr",
    "updated_at": "publishDate"
  },
  "batch": {
    "identity_key": "__REVIEW_REQUIRED__",
    "title": "__REVIEW_REQUIRED__",
    "official_page_url": "__REVIEW_REQUIRED__",
    "recruitment_type": "__REVIEW_REQUIRED__",
    "target_audience": "__REVIEW_REQUIRED__"
  },
  "body": {},
  "total_path": "data.pageForm.totalPage"
}
```

#### Job samples (raw key values)

Sample 1:

```json
{
  "postType": "0/1227/111201",
  "recruitType": 1,
  "publishDate": "2026-08-24 16:31:16",
  "workPlaceStr": "无锡市",
  "postId": "6a8c015b1ad6db7cf834c7e7",
  "postTypeName": "市场营销、管理类",
  "postName": "市场投标报价岗"
}
```

Sample 2:

```json
{
  "postType": "0/1227/103402",
  "recruitType": 1,
  "publishDate": "2026-08-24 15:59:08",
  "workPlaceStr": "成都市",
  "postId": "6a8bf9d14315481304cda9b9",
  "postTypeName": "电子信息、计算机类",
  "postName": "数字化工程师"
}
```

Sample 3:

```json
{
  "postType": "0/1227/103403",
  "recruitType": 1,
  "publishDate": "2026-08-24 15:57:21",
  "workPlaceStr": "成都市",
  "postId": "68bfe060778ced4f3930fa53",
  "postTypeName": "材料类",
  "postName": "焊接工艺师"
}
```

Sample 4:

```json
{
  "postType": "0/1227/103403",
  "recruitType": 1,
  "publishDate": "2026-08-24 15:55:45",
  "workPlaceStr": "成都市",
  "postId": "68bfd80a720ec0268293e91d",
  "postTypeName": "材料类",
  "postName": "化工工艺师"
}
```

Sample 5:

```json
{
  "postType": "0/1227/103401",
  "recruitType": 1,
  "publishDate": "2026-08-24 15:48:23",
  "workPlaceStr": "成都市、重庆市、昆明市",
  "postId": "68bfe05f778ced4f3930fa4c",
  "postTypeName": "电气、自动化类",
  "postName": "检修（售后）工程师(电气、自动化类)"
}
```

## Target S04-FAMILY

- Company: `中国联合网络通信集团有限公司`
- Company type: `央国企`
- Official-source evidence: `https://www.chinaunicom.com.cn/46/menu01/528/column06`
- Entry page: `https://zglt.zhaopin.com/scjobs/index.html`
- Final page: `https://zglt.zhaopin.com/scjobs/index.html`
- Page status: `200`
- Outcome: no candidate job API detected

No endpoint discovery is claimed for this target.
