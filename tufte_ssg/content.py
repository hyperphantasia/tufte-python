#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# File name: content.py
# Author: brkln (github.com/hyperphantasia)
# Location: 445.523236,-122.681730
# Date created: 2026-07-10
# Version = "1.0"
# License = "MIT License"
# =============================================================================
"""Discovers and parses posts/pages from the content/ directory.

Each post/page is a markdown file with a YAML front matter header, exactly
like a Jekyll post:

    ---
    title: "My post"
    date: 2026-07-13 09:36:04
    categories: python css
    ---
    Body text here...

Posts live in content/posts/ and are named YYYY-MM-DD-slug.md (same
convention as Jekyll's _posts). 
Pages live in content/pages/ and are named slug.md.
"""
# =============================================================================

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?(.*)", re.DOTALL)
POST_FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$")
EXCERPT_SEPARATOR = "<!--more-->"


def slugify(value: str) -> str:
    """Convert a string into a URL-friendly slug.

    Args:
        value: Input text.

    Returns:
        A lowercase slug containing only letters, numbers, and hyphens.
    """
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


@dataclass
class Document:
    """A single post or page."""

    source_path: Path
    metadata: dict[str, Any]
    raw_body: str
    slug: str
    date: datetime | None = None
    is_post: bool = False
    url: str = ""  # site-relative URL, WITHOUT baseurl (e.g. "/about/")
    excerpt_raw: str = field(default="")
    content_html: str = field(default="")
    excerpt_html: str = field(default="")

    @property
    def title(self) -> str:
        """Return the document title."""
        return self.metadata.get("title", self.slug)

    @property
    def layout(self) -> str:
        """Return the layout name for this document."""
        return self.metadata.get("layout", "post" if self.is_post else "page")

    @property
    def nav_exclude(self) -> bool:
        """Return whether this document should be excluded from navigation."""
        return bool(self.metadata.get("nav_exclude", False))

    @property
    def categories(self) -> list[str]:
        """Return the document categories as a list of strings."""
        return _as_list(self.metadata.get("categories"))

    @property
    def tags(self) -> list[str]:
        """Return the document tags as a list of strings."""
        return _as_list(self.metadata.get("tags"))

    @property
    def draft(self) -> bool:
        """Return whether this document is marked as a draft."""
        return bool(self.metadata.get("draft", False))


def _as_list(value: Any) -> list[str]:
    """Normalize a metadata value into a list of strings.

    Args:
        value: A scalar, list, or None.

    Returns:
        A list of strings.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return str(value).split()


def _parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML front matter from the markdown body.

    Args:
        text: Full document text.

    Returns:
        A tuple of (metadata dictionary, body text).
    """
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    body = m.group(2)
    return meta, body


def load_post(path: Path) -> Document:
    """Load a markdown post from disk.

    Args:
        path: Path to the post file.

    Returns:
        A parsed post document.
    """
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_front_matter(text)

    m = POST_FILENAME_RE.match(path.name)
    if m:
        year, month, day, slug = m.groups()
        file_date = datetime(int(year), int(month), int(day))
    else:
        file_date = None
        slug = path.stem

    date = meta.get("date", file_date)
    if isinstance(date, str):
        date = _parse_date_str(date)
    if isinstance(date, datetime) is False and date is not None:
        date = datetime(date.year, date.month, date.day)
    if date is None:
        date = file_date or datetime.now()

    excerpt_raw = body.split(EXCERPT_SEPARATOR, 1)[
        0] if EXCERPT_SEPARATOR in body else _first_paragraph(body)

    return Document(
        source_path=path,
        metadata=meta,
        raw_body=body,
        slug=slugify(meta.get("slug", slug)),
        date=date,
        is_post=True,
        excerpt_raw=excerpt_raw,
    )


def load_page(path: Path) -> Document:
    """Load a markdown page from disk.

    Args:
        path: Path to the page file.

    Returns:
        A parsed page document.
    """
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_front_matter(text)
    slug = slugify(meta.get("slug", path.stem))
    date = meta.get("date")
    if isinstance(date, str):
        date = _parse_date_str(date)
    return Document(
        source_path=path,
        metadata=meta,
        raw_body=body,
        slug=slug,
        date=date,
        is_post=False,
    )


def _parse_date_str(value: str) -> datetime:
    """Parse a date string using supported formats.

    Args:
        value: Date string.

    Returns:
        Parsed datetime.

    Raises:
        ValueError: If the string does not match a supported format.
    """
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {value!r}")


def _first_paragraph(body: str) -> str:
    """Extract the first paragraph from markdown text.

    Args:
        body: Markdown body text.

    Returns:
        The first paragraph, or an empty string if none exists.
    """
    stripped = body.strip()
    parts = re.split(r"\n\s*\n", stripped, maxsplit=1)
    return parts[0] if parts else ""


def discover_posts(posts_dir: Path) -> list[Document]:
    """Discover, load, filter, and sort posts.

    Args:
        posts_dir: Directory containing post markdown files.

    Returns:
        Posts sorted by descending date, excluding drafts.
    """
    docs = [load_post(p) for p in sorted(posts_dir.glob("*.md"))]
    docs = [d for d in docs if not d.draft]
    docs.sort(key=lambda d: d.date, reverse=True)
    return docs


def discover_pages(pages_dir: Path) -> list[Document]:
    """Discover and load pages.

    Args:
        pages_dir: Directory containing page markdown files.

    Returns:
        A list of parsed page documents.
    """
    if not pages_dir.exists():
        return []
    return [load_page(p) for p in sorted(pages_dir.glob("*.md"))]
