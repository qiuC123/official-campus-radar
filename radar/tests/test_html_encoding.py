import codecs
from unittest.mock import patch

from django.test import SimpleTestCase

from radar.services.html_encoding import decode_html


class HtmlEncodingTests(SimpleTestCase):
    def test_unlabelled_utf8_does_not_use_optional_charset_detector(self):
        markup = "<title>2027校园招聘</title><p>秋招岗位</p>"
        with patch("bs4.dammit.EncodingDetector.__init__", side_effect=AssertionError("no guessing")):
            self.assertEqual(decode_html(markup.encode()), markup)

    def test_declared_and_undeclared_legacy_chinese(self):
        cases = (
            ("<title>校园招聘</title>", "gbk", "text/html; charset=GBK"),
            ('<meta charset="gb2312"><title>校园招聘</title>', "gb2312", ""),
            ('<meta http-equiv="Content-Type" content="text/html; charset=gbk"><p>秋招</p>', "gbk", ""),
            ("<p>校园招聘</p>", "gb18030", ""),
            ("<p>café</p>", "iso-8859-1", "text/html; charset=iso-8859-1"),
        )
        for markup, encoding, header in cases:
            with self.subTest(encoding=encoding, header=header):
                self.assertEqual(decode_html(markup.encode(encoding), header), markup)

    def test_explicit_http_charset_precedes_meta(self):
        markup = '<meta charset="utf-8"><title>校园招聘</title>'
        self.assertEqual(decode_html(markup.encode("gbk"), "text/html; charset=gbk"), markup)

    def test_bad_or_incompatible_declaration_falls_back_without_loss(self):
        markup = "<p>校园招聘</p>"
        for label in ("unknown-charset", "ascii"):
            self.assertEqual(decode_html(markup.encode(), f"text/html; charset={label}"), markup)

    def test_bom_precedes_conflicting_declaration(self):
        markup = "<title>校园招聘</title>"
        for body in (codecs.BOM_UTF8 + markup.encode(), markup.encode("utf-16"), markup.encode("utf-32")):
            self.assertEqual(decode_html(body, "text/html; charset=gbk"), markup)

    def test_undecodable_input_is_not_silently_replaced(self):
        with self.assertRaises(ValueError):
            decode_html(b"\xff")
