from __future__ import annotations

import json
import httpx
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


class RealBookProvider(BookProvider):
    """
    真实的ISBN数据源实现，使用Open Library API获取书籍信息
    """

    def resolve(self, isbn13: str) -> BookMetaPayload:
        try:
            # 调用Open Library API获取书籍信息
            response = httpx.get(
                f"https://openlibrary.org/isbn/{isbn13}.json",
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()

            # 解析响应数据
            title = data.get("title", f"Unknown Title ({isbn13})")

            # 解析作者信息
            authors = []
            for author in data.get("authors", []):
                if isinstance(author, dict) and "name" in author:
                    authors.append(author["name"])
                elif isinstance(author, dict) and "key" in author:
                    # 尝试获取作者名称
                    try:
                        author_response = httpx.get(
                            f"https://openlibrary.org{author['key']}.json",
                            timeout=5.0
                        )
                        author_response.raise_for_status()
                        author_data = author_response.json()
                        if "name" in author_data:
                            authors.append(author_data["name"])
                    except Exception:
                        pass

            # 解析出版商信息
            publisher = None
            publishers = data.get("publishers", [])
            if publishers:
                if isinstance(publishers[0], dict) and "name" in publishers[0]:
                    publisher = publishers[0]["name"]
                elif isinstance(publishers[0], str):
                    publisher = publishers[0]

            pub_date = data.get("publish_date")
            cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn13}-M.jpg"

            # 解析简介
            summary = None
            if "description" in data:
                if isinstance(data["description"], dict) and "value" in data["description"]:
                    summary = data["description"]["value"]
                elif isinstance(data["description"], str):
                    summary = data["description"]

            # 解析分类
            categories = []
            for subject in data.get("subjects", []):
                if isinstance(subject, dict) and "name" in subject:
                    categories.append(subject["name"])
                elif isinstance(subject, str):
                    categories.append(subject)

            return BookMetaPayload(
                isbn13=isbn13,
                title=title,
                authors=authors,
                publisher=publisher,
                pub_date=pub_date,
                cover_url=cover_url,
                summary=summary,
                categories=categories,
                raw=data
            )
        except Exception as e:
            # 失败时返回占位数据
            raw = {"provider": "real", "isbn13": isbn13, "error": str(e)}
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