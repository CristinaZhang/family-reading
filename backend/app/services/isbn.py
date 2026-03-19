from __future__ import annotations

import re


_ISBN_RE = re.compile(r"[^0-9Xx]")


def normalize_isbn(raw: str) -> str:
    s = _ISBN_RE.sub("", (raw or "").strip())
    s = s.upper()
    return s


def _isbn10_checkdigit(body9: str) -> str:
    total = 0
    for i, ch in enumerate(body9, start=1):
        total += i * int(ch)
    r = total % 11
    return "X" if r == 10 else str(r)


def _isbn13_checkdigit(body12: str) -> str:
    total = 0
    for i, ch in enumerate(body12):
        n = int(ch)
        total += n if i % 2 == 0 else 3 * n
    r = (10 - (total % 10)) % 10
    return str(r)


def is_valid_isbn10(isbn10: str) -> bool:
    s = normalize_isbn(isbn10)
    if len(s) != 10:
        return False
    if not re.fullmatch(r"\d{9}[\dX]", s):
        return False
    return _isbn10_checkdigit(s[:9]) == s[9]


def is_valid_isbn13(isbn13: str) -> bool:
    s = normalize_isbn(isbn13)
    if len(s) != 13 or not s.isdigit():
        return False
    return _isbn13_checkdigit(s[:12]) == s[12]


def to_isbn13(isbn: str) -> str:
    s = normalize_isbn(isbn)
    if len(s) == 13 and is_valid_isbn13(s):
        return s
    if len(s) == 10 and is_valid_isbn10(s):
        body12 = "978" + s[:9]
        return body12 + _isbn13_checkdigit(body12)
    raise ValueError("Invalid ISBN")

