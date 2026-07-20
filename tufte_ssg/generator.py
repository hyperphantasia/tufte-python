#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# File name: generator.py
# Author: brkln (github.com/hyperphantasia)
# Location: 445.523236,-122.681730
# Date created: 2026-07-10
# Version = "1.0"
# License = "MIT License"
# =============================================================================
"""Site building and rendering pipeline for the static site generator.

This module loads content, renders markdown and templates, writes output
files, and copies static assets into the built site directory.
"""
# =============================================================================

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import jinja2

from . import content as content_mod
from . import markdown_render
from .config import load_config
from .shortcodes import expand_shortcodes

MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def dateformat(value: datetime | None, fmt: str = "%B %-d, %Y") -> str:
    """Format a datetime for display.

    Args:
        value: Datetime to format, or None.
        fmt: Unused format string parameter kept for Jinja compatibility.

    Returns:
        A human-readable date string, or an empty string if value is None.
    """
    if value is None:
        return ""
    return f"{MONTHS[value.month - 1]} {value.day}, {value.year}"


def rfc822(value: datetime | None) -> str:
    """Format a datetime as an RFC 822 timestamp.

    Args:
        value: Datetime to format, or None.

    Returns:
        An RFC 822 formatted timestamp in UTC.
    """
    if value is None:
        value = datetime.utcnow()
    return value.strftime("%a, %d %b %Y %H:%M:%S +0000")


class Site:
    """Build and render a static site from content and templates."""

    def __init__(self, root: Path):
        """Initialize a site builder.

        Args:
            root: Project root directory.
        """
        self.root = root
        self.config = load_config(root / "config.yml")
        self.out_dir = root / "_site"
        self.content_dir = root / "content"
        self.templates_dir = root / "templates"
        self.static_dir = root / "static"

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self.env.filters["dateformat"] = dateformat
        self.env.filters["rfc822"] = rfc822

        self.posts: list[content_mod.Document] = []
        self.pages: list[content_mod.Document] = []

    def _render_body(self, doc: content_mod.Document) -> None:
        """Render a document's markdown body and excerpt to HTML.

        Args:
            doc: Document to render.
        """
        baseurl = self.config["baseurl"]

        def md(text: str) -> str:
            return markdown_render.render(text)

        expanded = expand_shortcodes(doc.raw_body.replace(
            content_mod.EXCERPT_SEPARATOR, ""), baseurl, md)
        doc.content_html = markdown_render.render(expanded)

        expanded_excerpt = expand_shortcodes(doc.excerpt_raw, baseurl, md)
        doc.excerpt_html = markdown_render.render(expanded_excerpt)

    def _permalink_for(self, doc: content_mod.Document) -> str:
        """Build the permalink URL for a document.

        Args:
            doc: Document to generate a permalink for.

        Returns:
            A site-relative URL ending in a trailing slash.
        """
        pattern = doc.metadata.get("permalink", self.config["permalink"])
        short_year = doc.date.strftime("%y") if doc.date else ""
        year = doc.date.strftime("%Y") if doc.date else ""
        month = doc.date.strftime("%m") if doc.date else ""
        day = doc.date.strftime("%d") if doc.date else ""
        url = pattern.format(short_year=short_year, year=year,
                             month=month, day=day, slug=doc.slug, title=doc.slug)
        if not url.startswith("/"):
            url = "/" + url
        if not url.endswith("/"):
            url += "/"
        return url

    def load_content(self) -> None:
        """Discover, load, and render all content documents."""
        self.posts = content_mod.discover_posts(self.content_dir / "posts")
        self.pages = content_mod.discover_pages(self.content_dir / "pages")

        for post in self.posts:
            post.url = self._permalink_for(post)
            self._render_body(post)

        for page in self.pages:
            page.url = f"/{page.slug}/"
            self._render_body(page)

    LAYOUT_TEMPLATE_FILES = {
        "post": "post.html",
        "page": "page.html",
        "full-width": "full-width.html",
        "default": "base.html",
    }
    LAYOUT_PARENTS = {
        "post": "default",
        "page": "default",
        "full-width": None,
        "default": None,
    }

    def render_through_layout(self, layout_name: str, content_html: str, page_ctx: Any, extra: dict | None = None) -> str:
        """Render content through a layout chain.

        Args:
            layout_name: Starting layout name.
            content_html: HTML content to inject.
            page_ctx: Page context passed to templates.
            extra: Additional template context.

        Returns:
            Rendered HTML string.

        Raises:
            ValueError: If the layout name is unknown.
        """
        name = layout_name
        html = content_html
        ctx_base = {"site": self.site_context(), "page": page_ctx,
                    "now": datetime.utcnow()}
        if extra:
            ctx_base.update(extra)
        while name is not None:
            template_file = self.LAYOUT_TEMPLATE_FILES.get(name)
            if template_file is None:
                raise ValueError(f"Unknown layout '{name}'")
            tmpl = self.env.get_template(template_file)
            html = tmpl.render(content=html, **ctx_base)
            name = self.LAYOUT_PARENTS.get(name)
        return html

    def nav_items(self) -> list[dict]:
        """Return navigation items for the site."""
        items = [{"title": self.config["index_title"], "url": "/"}]
        for p in self.pages:
            if not p.nav_exclude:
                items.append({"title": p.title, "url": p.url})
        return items

    def site_context(self) -> dict:
        """Build the global template context for the site."""
        cfg = self.config
        theme_name = self._theme_name()
        return {
            "title": cfg["title"],
            "subtitle": cfg["subtitle"],
            "author": cfg["author"],
            "email": cfg["email"],
            "description": cfg["description"],
            "url": cfg["url"],
            "baseurl": cfg["baseurl"],
            "options": cfg["options"],
            "social": cfg["social"],
            "badge_image": cfg["badge_image"],
            "nav_items": self.nav_items(),
            "theme": theme_name,
            "theme_supports_toggle": theme_name in self.TOGGLE_CAPABLE_THEMES,
        }

    def _write(self, url_path: str, html: str) -> None:
        """Write rendered HTML to the output directory.

        Args:
            url_path: Site-relative URL path.
            html: HTML content to write.
        """
        if url_path == "/":
            out_file = self.out_dir / "index.html"
        else:
            out_file = self.out_dir / url_path.strip("/") / "index.html"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html, encoding="utf-8")

    def build_posts(self) -> None:
        """Render and write all posts."""
        for post in self.posts:
            html = self.render_through_layout(
                post.layout, post.content_html, post)
            self._write(post.url, html)

    def build_pages(self) -> None:
        """Render and write all pages."""
        for page in self.pages:
            html = self.render_through_layout(
                page.layout, page.content_html, page)
            self._write(page.url, html)

    def build_index(self) -> None:
        """Render and write the home page."""
        tmpl = self.env.get_template("index.html")
        index_page = {
            "title": self.config["index_title"], "url": "/", "date": None}
        listing_html = tmpl.render(
            posts=self.posts, site=self.site_context(), page=index_page)
        html = self.render_through_layout(
            "full-width", listing_html, index_page)
        self._write("/", html)

    def build_feed(self) -> None:
        """Render and write the RSS feed."""
        tmpl = self.env.get_template("feed.xml")
        xml = tmpl.render(posts=self.posts,
                          site=self.site_context(), now=datetime.utcnow())
        out_file = self.out_dir / "feed.xml"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(xml, encoding="utf-8")

    TOGGLE_CAPABLE_THEMES = {"solarized",
                             "solAArized", "solarized-rainbow", "dracula"}

    def _theme_name(self) -> str:
        """Return the configured theme name."""
        return self.config["theme"]

    def copy_static(self) -> None:
        """Copy static assets into the output directory."""
        fonts_src = self.static_dir / "fonts"
        img_src = self.static_dir / "img"
        css_src = self.static_dir / "css"
        js_src = self.static_dir / "js"
        if fonts_src.exists():
            shutil.copytree(fonts_src, self.out_dir /
                            "fonts", dirs_exist_ok=True)
        if img_src.exists():
            shutil.copytree(img_src, self.out_dir /
                            "assets" / "img", dirs_exist_ok=True)
        if js_src.exists():
            shutil.copytree(js_src, self.out_dir / "js", dirs_exist_ok=True)
        if css_src.exists():
            css_out = self.out_dir / "css"
            css_out.mkdir(parents=True, exist_ok=True)
            for item in css_src.iterdir():
                if item.name == "themes":
                    continue
                if item.is_file():
                    shutil.copy2(item, css_out / item.name)
                else:
                    shutil.copytree(item, css_out / item.name,
                                    dirs_exist_ok=True)

        theme_name = self._theme_name()
        theme_src = self.static_dir / "css" / "themes" / f"{theme_name}.css"
        if not theme_src.exists():
            available = sorted(p.stem for p in (
                self.static_dir / "css" / "themes").glob("*.css"))
            raise FileNotFoundError(
                f"config.yml sets theme: {theme_name!r}, but static/css/themes/{theme_name}.css "
                f"doesn't exist. Available themes: {', '.join(available)}"
            )
        shutil.copy2(theme_src, self.out_dir / "css" / "theme.css")

    def build(self, clean: bool = True) -> None:
        """Build the full site.

        Args:
            clean: If true, delete the existing output directory first.
        """
        if clean and self.out_dir.exists():
            shutil.rmtree(self.out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        self.load_content()
        self.build_posts()
        self.build_pages()
        self.build_index()
        self.build_feed()
        self.copy_static()
