import base64
import json
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

from django.test import SimpleTestCase

from radar.services.application_pages import (
    BATCH_APPLICATION_URLS,
    configured_batch_application_url,
)


class BatchApplicationPageTests(SimpleTestCase):
    def test_all_current_formal_batch_identities_have_exact_job_pages(self):
        expected = {
            "OPPO": {
                "phase-02:p12": (
                    "https://careers.oppo.com/university/oppo/campus/post"
                    "?recruitType=Graduate"
                ),
            },
            "vivo": {
                "phase-02:p13": (
                    "https://hr-campus.vivo.com/jobs?1=%5B%7B%22id%22%3A%222%22"
                    "%2C%22label%22%3A%22%E7%A7%8B%E5%AD%A3%E6%A0%A1%E5%9B%AD"
                    "%E6%8B%9B%E8%81%98%22%7D%5D"
                ),
            },
            "中国电信集团有限公司": {
                "phase-02:s03": (
                    "https://job.chinatelecom.com.cn/wt/TELE/web/index"
                    "?brandCode=1#/postinquiry?data="
                    "eyJrZXkiOjU4MTYxNywidHlwZSI6IjEiLCJyZWNydWl0UHJvamVjdCI6IiIs"
                    "InJlY3J1aXRQcm9qZWN0TmFtZSI6IiJ9"
                ),
            },
            "中国联合网络通信集团有限公司": {
                "phase-02:s04": "https://zglt.zhaopin.com/scjobs/index.html",
            },
            "京东": {
                "official-project:jd:plan:56": "https://campus.jd.com/#/jobs?selProjects=56",
                "official-project:jd:plan:57": "https://campus.jd.com/#/jobs?selProjects=57",
                "official-project:jd:plan:58": "https://campus.jd.com/#/jobs?selProjects=58",
            },
            "大疆创新": {
                "official-project:dji:tuojiangzhe:2027": (
                    "https://apply.careers.dji.com/campus-recruitment/dji/143359"
                    "?locale=zh-CN#/jobs"
                ),
                "official-project:dji:digital-management:2027": (
                    "https://apply.careers.dji.com/campus-recruitment/dji/143359"
                    "?locale=zh-CN#/jobs?keyword="
                    "%E6%95%B0%E5%AD%97%E7%AE%A1%E7%90%86"
                    "&page=1&anchorName=jobsList"
                ),
            },
            "宁德时代": {
                "phase-02:p15": "https://app.mokahr.com/campus-recruitment/catlhr/148948#/jobs",
            },
            "拼多多": {
                "phase-02:p11": "https://careers.pddglobalhr.com/campus/grad",
            },
            "比亚迪": {
                "phase-02:p19": "https://job.byd.com/portal/pc/#/school/schoolPositionList",
            },
            "百度": {
                "phase-02:p06": "https://talent.baidu.com/jobs/list?recruitType=GRADUATE",
            },
            "美团": {
                "official-project:meituan:special:6": "https://zhaopin.meituan.com/web/position?hiringType=2_6",
                "official-project:meituan:special:8": "https://zhaopin.meituan.com/web/longcat",
                "official-project:meituan:special:3": "https://zhaopin.meituan.com/web/beidou",
            },
            "腾讯": {
                "official-project:tencent:project:1": "https://join.qq.com/post.html?query=p_1",
                "official-project:tencent:project:2": "https://join.qq.com/post.html?query=p_2",
                "official-project:tencent:projects:4-12": "https://join.qq.com/post.html?query=p_104",
                "official-project:tencent:project:14": "https://join.qq.com/post.html?query=p_14",
                "official-project:tencent:project:20": "https://join.qq.com/post.html?query=p_20",
                "official-project:tencent:project:9": "https://join.qq.com/post.html?query=p_9",
            },
            "顺丰": {
                "phase-02:p18": "https://campus.sf-express.com/#/positionList",
            },
        }

        self.assertEqual(BATCH_APPLICATION_URLS, expected)
        identities = [
            identity
            for company_mapping in BATCH_APPLICATION_URLS.values()
            for identity in company_mapping
        ]
        self.assertEqual(len(identities), 23)
        self.assertEqual(len(set(identities)), 23)

    def test_telecom_job_page_preserves_the_beijing_company_context(self):
        url = BATCH_APPLICATION_URLS["中国电信集团有限公司"]["phase-02:s03"]
        route, separator, query = urlparse(url).fragment.partition("?")

        self.assertEqual(route, "/postinquiry")
        self.assertEqual(separator, "?")
        payload = json.loads(
            base64.b64decode(parse_qs(query)["data"][0]).decode("utf-8")
        )
        self.assertEqual(payload, {
            "key": 581617,
            "type": "1",
            "recruitProject": "",
            "recruitProjectName": "",
        })

    def test_url_must_match_company_identity_and_source_host(self):
        source = SimpleNamespace(
            source_url="https://talent.baidu.com/api/jobs",
            organization=SimpleNamespace(name="百度"),
        )
        self.assertEqual(
            configured_batch_application_url(source, "phase-02:p06"),
            "https://talent.baidu.com/jobs/list?recruitType=GRADUATE",
        )
        self.assertIsNone(
            configured_batch_application_url(source, "phase-02:unknown")
        )
        wrong_host = SimpleNamespace(
            source_url="https://untrusted.example/api/jobs",
            organization=SimpleNamespace(name="百度"),
        )
        self.assertIsNone(
            configured_batch_application_url(wrong_host, "phase-02:p06")
        )
