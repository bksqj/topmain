"""Generic pagination helpers for inline lists longer than 5 items."""
from __future__ import annotations

from dataclasses import dataclass

PAGE_SIZE = 5


@dataclass
class Page:
    items: list  # slice of items on this page
    page: int  # 1-based
    total_pages: int
    start_index: int  # 1-based index of first item on the page


def paginate(items: list, page: int, page_size: int = PAGE_SIZE) -> Page:
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    return Page(
        items=items[start : start + page_size],
        page=page,
        total_pages=total_pages,
        start_index=start + 1,
    )
