from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class BookMetaPayload:
    isbn13: str
    title: str
    authors: list[str]
    publisher: Optional[str] = None
    pub_date: Optional[str] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    categories: list[str] | None = None
    raw: dict[str, Any] | None = None


class BookProvider:
    def resolve(self, isbn13: str) -> BookMetaPayload:
        raise NotImplementedError


class PlaceholderProvider(BookProvider):
    """
    MVP 占位 provider：返回最小元数据，方便端到端跑通。
    后续可替换为真实的 ISBN 数据源（比如自建/第三方 API）。
    """

    def resolve(self, isbn13: str) -> BookMetaPayload:
        raw = {"provider": "placeholder", "isbn13": isbn13}
        return BookMetaPayload(
            isbn13=isbn13,
            title=f"Unknown Title ({isbn13})",
            authors=[],
            publisher=None,
            pub_date=None,
            cover_url=None,
            summary=None,
            categories=[],
            raw=raw,
        )


def dumps_raw(raw: dict[str, Any] | None) -> str | None:
    if raw is None:
        return None
    return json.dumps(raw, ensure_ascii=False)

