#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# File name: shortcodes.py
# Author: brkln (github.com/hyperphantasia)
# Location: 445.523236,-122.681730
# Date created: 2026-07-10
# Version = "1.0"
# License = "MIT License"
# =============================================================================
"""Port of tufte-jekyll's custom Liquid tags (_plugins/*.rb) to plain-text
shortcodes that are expanded b e f o r e Markdown conversion, exactly like
Jekyll expands Liquid tags before handing the result to Kramdown.

Supported shortcodes (same names/argument order as the original theme so
existing tufte-jekyll posts can be dropped in with no changes):

    {% newthought 'text' %}
    {% sidenote 'id' 'text' %}
    {% marginnote 'id' 'text' %}
    {% marginfigure 'id' 'path/to/img' 'caption' %}
    {% maincolumn 'path/to/img' 'caption' %}
    {% fullwidth 'path/to/img' 'caption' %}
    {% epigraph 'text' 'author' 'citation' %}
    {% math %} ... {% endmath %}      (block LaTeX, MathJax)
    {% m %} ... {% em %}              (inline LaTeX, MathJax)

Fenced/inline code spans are protected from expansion so that shortcode
syntax can still be shown literally in a code block.
"""
# =============================================================================

from __future__ import annotations

import re
import shlex
from typing import Callable, Protocol


class MarkdownRenderer(Protocol):
    """Callable Markdown renderer used for inline shortcode content."""

    def __call__(self, text: str) -> str: ...


ResolveImage = Callable[[str], str]
ShortcodeHandler = Callable[[list[str], ResolveImage, MarkdownRenderer], str]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CODE_FENCE_RE = re.compile(r"(```.*?```|~~~.*?~~~)", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"(`[^`\n]+`)")


def _split_args(raw: str) -> list[str]:
    """Split shortcode arguments using shell-like quoting rules.

    Args:
        raw: Raw argument string from the shortcode tag.

    Returns:
        Parsed arguments, falling back to whitespace splitting if quotes
        are unbalanced.
    """
    lexer = shlex.shlex(raw, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return raw.split()


def _inline_markdown(md_render: MarkdownRenderer, text: str) -> str:
    """Render inline Markdown and strip wrapping paragraph tags.

    Args:
        md_render: Markdown rendering function.
        text: Markdown fragment to render.

    Returns:
        Rendered HTML without outer `<p>` tags.
    """
    html = md_render(text).strip()
    html = re.sub(r"^<p>", "", html)
    html = re.sub(r"</p>$", "", html)
    return html


# ---------------------------------------------------------------------------
# Protecting code spans while rewrite shortcodes
# ---------------------------------------------------------------------------


def _protect_code(text: str) -> tuple[str, list[str]]:
    """Temporarily replace code spans and fences with placeholders.

    Args:
        text: Input text.

    Returns:
        A tuple of (protected text, stash of original code chunks).
    """
    stash: list[str] = []

    def stash_it(m: re.Match[str]) -> str:
        stash.append(m.group(0))
        return f"\x00CODE{len(stash) - 1}\x00"

    text = _CODE_FENCE_RE.sub(stash_it, text)
    text = _INLINE_CODE_RE.sub(stash_it, text)
    return text, stash


def _restore_code(text: str, stash: list[str]) -> str:
    """Restore placeholders created by `_protect_code`.

    Args:
        text: Text containing placeholders.
        stash: Original code chunks.

    Returns:
        Text with placeholders restored.
    """
    for i, chunk in enumerate(stash):
        text = text.replace(f"\x00CODE{i}\x00", chunk)
    return text


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

_SINGLE_TAG_RE = re.compile(r"\{%\s*([a-zA-Z_]+)\s*(.*?)\s*%\}")
_MATH_BLOCK_RE = re.compile(
    r"\{%\s*math\s*%\}(.*?)\{%\s*endmath\s*%\}", re.DOTALL)
_MATH_INLINE_RE = re.compile(r"\{%\s*m\s*%\}(.*?)\{%\s*em\s*%\}", re.DOTALL)


def expand_shortcodes(text: str, baseurl: str, md_render: MarkdownRenderer) -> str:
    """Expand tufte-python shortcodes in text.

    Args:
        text: Source text containing shortcodes.
        baseurl: Base URL prefix for relative image paths.
        md_render: Markdown renderer for inline caption/note content.

    Returns:
        Text with shortcodes replaced by HTML.
    """
    text, stash = _protect_code(text)

    def is_remote(path: str) -> bool:
        """Return True if the path is an absolute/remote URL."""
        return path.startswith(("http://", "https://", "//"))

    def resolve_img(path: str) -> str:
        """Resolve an image path against the site's baseurl."""
        return path if is_remote(path) else f"{baseurl}/{path}"

    text = _MATH_BLOCK_RE.sub(
        lambda m: f'<div class="mathblock"><script type="math/tex; mode=display">{m.group(1)}</script></div>',
        text,
    )
    text = _MATH_INLINE_RE.sub(
        lambda m: f'<span>&#8203;<script type="math/tex">{m.group(1)}</script></span>',
        text,
    )

    def dispatch(m: re.Match[str]) -> str:
        """Dispatch a shortcode tag to its handler."""
        name, raw_args = m.group(1), m.group(2)
        if name not in _HANDLERS:
            return m.group(0)
        args = _split_args(raw_args)
        return _HANDLERS[name](args, resolve_img, md_render)

    text = _SINGLE_TAG_RE.sub(dispatch, text)
    return _restore_code(text, stash)


# ---------------------------------------------------------------------------
# Individual tag handlers: ports of _plugins/*.rb
# ---------------------------------------------------------------------------


def _h_newthought(args: list[str], resolve_img: ResolveImage, md_render: MarkdownRenderer) -> str:
    """Render a `newthought` shortcode."""
    text = args[0] if args else ""
    return f"<span class='newthought'>{text}</span>"


def _h_sidenote(args: list[str], resolve_img: ResolveImage, md_render: MarkdownRenderer) -> str:
    """Render a `sidenote` shortcode."""
    sid, text = args[0], args[1]
    text = _inline_markdown(md_render, text)
    return (
        f"<label for='{sid}' class='margin-toggle sidenote-number'></label>"
        f"<input type='checkbox' id='{sid}' class='margin-toggle'/>"
        f"<span class='sidenote'>{text}</span>"
    )


def _h_marginnote(args: list[str], resolve_img: ResolveImage, md_render: MarkdownRenderer) -> str:
    """Render a `marginnote` shortcode."""
    sid, text = args[0], args[1]
    text = _inline_markdown(md_render, text)
    return (
        f"<label for='{sid}' class='margin-toggle'>&#8853;</label>"
        f"<input type='checkbox' id='{sid}' class='margin-toggle'/>"
        f"<span class='marginnote'>{text}</span>"
    )


def _h_marginfigure(args: list[str], resolve_img: ResolveImage, md_render: MarkdownRenderer) -> str:
    """Render a `marginfigure` shortcode."""
    sid, path, caption = args[0], args[1], args[2]
    caption = _inline_markdown(md_render, caption)
    return (
        f"<label for='{sid}' class='margin-toggle'>&#8853;</label>"
        f"<input type='checkbox' id='{sid}' class='margin-toggle'/>"
        f"<span class='marginnote'><img class='fullwidth' src='{resolve_img(path)}'/><br>{caption}</span>"
    )


def _h_maincolumn(args: list[str], resolve_img: ResolveImage, md_render: MarkdownRenderer) -> str:
    """Render a `maincolumn` shortcode."""
    path, caption = args[0], args[1]
    caption = _inline_markdown(md_render, caption)
    return f"<figure><img src='{resolve_img(path)}'/><figcaption class='maincolumn-figure'>{caption}</figcaption></figure>"


def _h_fullwidth(args: list[str], resolve_img: ResolveImage, md_render: MarkdownRenderer) -> str:
    """Render a `fullwidth` shortcode."""
    path, caption = args[0], args[1]
    caption = _inline_markdown(md_render, caption)
    return f"<figure class='fullwidth'><img src='{resolve_img(path)}'/><figcaption>{caption}</figcaption></figure>"


def _h_epigraph(args: list[str], resolve_img: ResolveImage, md_render: MarkdownRenderer) -> str:
    """Render an `epigraph` shortcode."""
    text, author, citation = args[0], args[1], args[2]
    return (
        f"<div class='epigraph'><blockquote><p>{text}</p>"
        f"<footer>{author}, <cite>{citation}</cite></footer></blockquote></div>"
    )


_HANDLERS: dict[str, ShortcodeHandler] = {
    "newthought": _h_newthought,
    "sidenote": _h_sidenote,
    "marginnote": _h_marginnote,
    "marginfigure": _h_marginfigure,
    "maincolumn": _h_maincolumn,
    "fullwidth": _h_fullwidth,
    "epigraph": _h_epigraph,
}
