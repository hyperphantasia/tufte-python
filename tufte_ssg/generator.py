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
files, and copies static assets into the built site directory. Supports
incremental builds through caching.
"""
# =============================================================================

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import jinja2

from . import cache as cache_mod
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
    # %-d isn't portable (fails on some libc); build it by hand instead.
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

    def __init__(self, root: Path) -> None:
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

    # -- content pipeline --------------------------------------------------

    def _render_body(self, doc: content_mod.Document) -> None:
        """Render a document's markdown body and excerpt to HTML.

        Expands shortcodes and converts markdown in the same order Jekyll
        does (Liquid, then Kramdown).

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
        """Discover posts/pages and compute their URLs.

        Cheap operation that just parses front matter and filenames.
        Does NOT run shortcode expansion or Markdown conversion, so it's
        safe to call this unconditionally even during an incremental build.
        """
        self.posts = content_mod.discover_posts(self.content_dir / "posts")
        self.pages = content_mod.discover_pages(self.content_dir / "pages")

        for post in self.posts:
            post.url = self._permalink_for(post)

        for page in self.pages:
            page.url = f"/{page.slug}/"

    # -- layout chain --------------------------------------------------

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

    # -- site-wide template context --------------------------------------------------

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

    # -- output helpers --------------------------------------------------

    def _output_file_for(self, url_path: str) -> Path:
        """Compute the output file path for a given URL path.

        Args:
            url_path: Site-relative URL path.

        Returns:
            The filesystem path where this URL's output should be written.
        """
        if url_path == "/":
            return self.out_dir / "index.html"
        return self.out_dir / url_path.strip("/") / "index.html"

    def _write(self, url_path: str, html: str) -> None:
        """Write rendered HTML to the output directory.

        Args:
            url_path: Site-relative URL path.
            html: HTML content to write.
        """
        out_file = self._output_file_for(url_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(html, encoding="utf-8")

    def render_documents(self, cache: dict, force: bool) -> dict[str, dict]:
        """Render (or reuse from cache) every post/page.

        A document is re-rendered (the expensive shortcode+Markdown pass)
        only if `force` is set, its source file's mtime changed, it's new,
        or its output file has gone missing (otherwise its previously-
        rendered HTML is reused both for its own page and for the index/
        feed, which need every post's content regardless of what changed
        this run).

        Args:
            cache: The persisted cache dict from a previous build.
            force: If True, force re-render of all documents.

        Returns:
            The new per-document cache entries to persist.
        """
        cached_docs = cache.get("docs", {})
        new_cache: dict[str, dict] = {}
        rendered_count = 0
        skipped_count = 0

        for doc in self.posts + self.pages:
            key = str(doc.source_path.relative_to(self.root))
            mtime = doc.source_path.stat().st_mtime
            out_file = self._output_file_for(doc.url)
            cached = cached_docs.get(key)

            needs_render = (
                force
                or cached is None
                or cached.get("mtime") != mtime
                or cached.get("url") != doc.url
                or not out_file.exists()
            )

            if needs_render:
                self._render_body(doc)
                html = self.render_through_layout(
                    doc.layout, doc.content_html, doc)
                self._write(doc.url, html)
                rendered_count += 1
            else:
                doc.content_html = cached["content_html"]
                doc.excerpt_html = cached["excerpt_html"]
                skipped_count += 1

            new_cache[key] = {
                "mtime": mtime,
                "url": doc.url,
                "content_html": doc.content_html,
                "excerpt_html": doc.excerpt_html,
            }

        # Source files that existed last build but are gone now -- remove
        # their stale output rather than leaving orphaned pages on disk.
        removed_keys = set(cached_docs) - set(new_cache)
        for key in removed_keys:
            old_url = cached_docs[key].get("url")
            if not old_url:
                continue
            stale_file = self._output_file_for(old_url)
            if stale_file.exists():
                shutil.rmtree(stale_file.parent, ignore_errors=True)

        print(
            f"Rendered {rendered_count} page(s), reused {skipped_count} unchanged, removed {len(removed_keys)} stale.")
        return new_cache

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

    # -- static assets --------------------------------------------------

    TOGGLE_CAPABLE_THEMES = {"solarized", "dracula",
                             "solarized-rainbow", "solAArized",
                             "selenized","selenized-bw"}

    def _theme_name(self) -> str:
        """Return the configured theme name."""
        return self.config["theme"]

    def _copy_file_if_newer(self, src: Path, dst: Path) -> None:
        """Copy a file only if the destination is missing, older, or differs in size.

        Args:
            src: Source file path.
            dst: Destination file path.
        """
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime and dst.stat().st_size == src.stat().st_size:
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    def _copytree_incremental(self, src_dir: Path, dst_dir: Path) -> None:
        """Copy a directory tree, only touching new or changed files.

        Like shutil.copytree(dirs_exist_ok=True), but only copies files
        that are new or changed, and removes files under dst_dir that no
        longer exist under src_dir. For large asset trees (image-heavy
        blogs especially) this avoids re-copying everything on every build.

        Args:
            src_dir: Source directory path.
            dst_dir: Destination directory path.
        """
        dst_dir.mkdir(parents=True, exist_ok=True)
        src_files = set()
        for src_file in src_dir.rglob("*"):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(src_dir)
            src_files.add(rel)
            self._copy_file_if_newer(src_file, dst_dir / rel)

        for dst_file in dst_dir.rglob("*"):
            if not dst_file.is_file():
                continue
            rel = dst_file.relative_to(dst_dir)
            if rel not in src_files:
                dst_file.unlink()

    def copy_static(self) -> None:
        """Copy static assets into the output directory."""
        fonts_src = self.static_dir / "fonts"
        img_src = self.static_dir / "img"
        css_src = self.static_dir / "css"
        js_src = self.static_dir / "js"
        if fonts_src.exists():
            self._copytree_incremental(fonts_src, self.out_dir / "fonts")
        if img_src.exists():
            self._copytree_incremental(
                img_src, self.out_dir / "assets" / "img")
        if js_src.exists():
            self._copytree_incremental(js_src, self.out_dir / "js")
        if css_src.exists():
            # Copy everything except the themes/ folder -- only the
            # selected theme (below) ships in the built output.
            css_out = self.out_dir / "css"
            css_out.mkdir(parents=True, exist_ok=True)
            for item in css_src.iterdir():
                if item.name == "themes":
                    continue
                if item.is_file():
                    self._copy_file_if_newer(item, css_out / item.name)
                else:
                    self._copytree_incremental(item, css_out / item.name)

        theme_name = self._theme_name()
        theme_src = self.static_dir / "css" / "themes" / f"{theme_name}.css"
        if not theme_src.exists():
            available = sorted(p.stem for p in (
                self.static_dir / "css" / "themes").glob("*.css"))
            raise FileNotFoundError(
                f"config.yml sets theme: {theme_name!r}, but static/css/themes/{theme_name}.css "
                f"doesn't exist. Available themes: {', '.join(available)}"
            )
        self._copy_file_if_newer(theme_src, self.out_dir / "css" / "theme.css")

    # -- top-level build --------------------------------------------------

    def build(self, force: bool = False) -> None:
        """Build the site.

        By default this is incremental: a post/page is only re-rendered if
        its source file changed, is new, or its output is missing. Editing
        a template, config.yml, or the generator's own code invalidates
        everything and triggers a full rebuild automatically. Pass
        force=True to always do a full rebuild regardless (if you
        don't trust the cache for some reason). A fresh checkout (no _site/,
        no cache file, as in CI) always does a full build too, since
        there's nothing to reuse.

        Args:
            force: If True, force a full rebuild regardless of cache state.
        """
        cache = cache_mod.load(self.root)
        current_global_mtime = cache_mod.global_mtime(self.root)
        full_rebuild = (
            force
            or not self.out_dir.exists()
            or cache["global_mtime"] != current_global_mtime
        )

        if full_rebuild and self.out_dir.exists():
            shutil.rmtree(self.out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)

        if full_rebuild:
            reason = "forced" if force else (
                "no previous build" if not cache["docs"] else "templates/config/code changed")
            print(f"Full rebuild ({reason}).")
            cache = cache_mod.empty()

        self.load_content()
        new_doc_cache = self.render_documents(cache, force=full_rebuild)

        self.build_index()
        self.build_feed()
        self.copy_static()

        cache_mod.save(self.root, new_doc_cache)
