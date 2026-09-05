"""Deterministic HTML decoding, independent of optional charset detectors."""

import codecs
from email.message import Message

from bs4.dammit import EncodingDetector


def decode_html(body: bytes, content_type: str = "") -> str:
    # BOM takes precedence, including UTF-32 before the overlapping UTF-16 BOM.
    for marker, encoding in (
        (codecs.BOM_UTF32_LE, "utf-32"),
        (codecs.BOM_UTF32_BE, "utf-32"),
        (codecs.BOM_UTF16_LE, "utf-16"),
        (codecs.BOM_UTF16_BE, "utf-16"),
        (codecs.BOM_UTF8, "utf-8-sig"),
    ):
        if body.startswith(marker):
            return body.decode(encoding, errors="strict")

    header = Message()
    header["content-type"] = content_type
    encodings = (
        header.get_content_charset(),
        EncodingDetector.find_declared_encoding(body, is_html=True),
        "utf-8",
        "gb18030",
    )
    for encoding in dict.fromkeys(encodings):
        if not encoding:
            continue
        try:
            return body.decode(encoding, errors="strict")
        except (LookupError, UnicodeError):
            continue
    raise ValueError("official HTML cannot be decoded without replacement characters")
