#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# File name: markdown_render.py
# Author: brkln (github.com/hyperphantasia)
# Location: 445.523236,-122.681730
# Date created: 2026-07-10
# Version = "1.0"
# License = "MIT License"
# =============================================================================
"""Wraps Python-Markdown with extensions chosen to match kramdown's
behaviour reasonably closely: fenced code blocks, tables, footnotes,
smart quotes, and auto-generated header ids (used e.g. by
`<h2 id="epigraphs">` style anchors in the original theme)."""
# =============================================================================

from __future__ import annotations

import html
import re

import markdown

_EXTENSIONS = [
    "extra",
    "sane_lists",
    "smarty",
    "toc",
    "codehilite",
]

_EXTENSION_CONFIGS = {
    "codehilite": {
        "css_class": "highlight",
        "guess_lang": False,
    },
    "toc": {
        "marker": "",
        "permalink": False,
    },
}

# Raw math delimiters MathJax is configured to scan for (see
# templates/partials/head.html). None of these are meaningful to
# Python-Markdown, so left alone it treats their contents as ordinary
# paragraph text which means Markdown's own inline rules (backslash
# escaping, emphasis, smart quotes...) mangle LaTeX before MathJax ever
# sees it. `\\` becomes `\`, and a stray pair of `*` (e.g. `\beta^{*}`
# used twice) gets consumed as <em> markup. To avoid this, math regions
# are stashed out before conversion and restored verbatim afterward, the
# same way shortcodes.py protects code spans from shortcode expansion.
_MATH_PATTERNS = [
    re.compile(r"\$\$.*?\$\$", re.DOTALL),   # $$ ... $$
    re.compile(r"\\\[.*?\\\]", re.DOTALL),   # \[ ... \]
    re.compile(r"\\\(.*?\\\)", re.DOTALL),   # \( ... \)
]

# Code (fenced blocks and inline spans) must be walled off before the math
# patterns above ever run. Those patterns match "next $$ ... next $$" with no
# awareness of Markdown structure, so a literal `$$` shown as documentation
# inside backticks (e.g. "raw `$$...$$` delimiters" or a fenced ```text
# example) is indistinguishable to them from a real opening/closing pair. The
# regex then pairs that stray `$$` with the next real one it finds
# (a paragraph or more later) and stashes the entire span between
# them (blank lines, fences, and any real math in between included) as a
# single "math" chunk. That collapses multiple paragraphs into one and can
# make real math nearby disappear into the bogus chunk. Since Markdown
# already leaves code spans/blocks verbatim on its own, we don't need math
# protection to reach inside them at all. Easiest fix is to hide code from
# the math patterns entirely, then put it back unchanged before conversion.
_FENCE_PATTERN = re.compile(r"^([ \t]*)(`{3,}|~{3,})[^\n]*\n.*?^\1\2[ \t]*$",
                             re.DOTALL | re.MULTILINE)
_CODE_SPAN_PATTERN = re.compile(r"(`+)(?:(?!\1).)+?\1", re.DOTALL)


def _protect_code(text: str) -> tuple[str, list[str]]:
    stash: list[str] = []

    def stash_it(m: re.Match) -> str:
        stash.append(m.group(0))
        return f"\x01CODE{len(stash) - 1}\x01"

    text = _FENCE_PATTERN.sub(stash_it, text)
    text = _CODE_SPAN_PATTERN.sub(stash_it, text)
    return text, stash


def _restore_code(text: str, stash: list[str]) -> str:
    for i, chunk in enumerate(stash):
        text = text.replace(f"\x01CODE{i}\x01", chunk)
    return text


def _protect_math(text: str) -> tuple[str, list[str]]:
    stash: list[str] = []

    def stash_it(m: re.Match) -> str:
        stash.append(m.group(0))
        return f"\x00MATH{len(stash) - 1}\x00"

    code_hidden, code_stash = _protect_code(text)
    for pattern in _MATH_PATTERNS:
        code_hidden = pattern.sub(stash_it, code_hidden)
    text = _restore_code(code_hidden, code_stash)
    return text, stash


def _restore_math(html_text: str, stash: list[str]) -> str:
    for i, chunk in enumerate(stash):
        # Escape &/</> for HTML safety (e.g. bare `<` in "a < b"); MathJax
        # still sees the literal characters once the browser decodes the
        # entities, same as it would for any other HTML text node.
        html_text = html_text.replace(
            f"\x00MATH{i}\x00", html.escape(chunk, quote=False))
    return html_text


def make_renderer() -> markdown.Markdown:
    return markdown.Markdown(extensions=_EXTENSIONS, extension_configs=_EXTENSION_CONFIGS)


def render(text: str) -> str:
    protected, stash = _protect_math(text)
    md = make_renderer()
    html_out = md.convert(protected)
    return _restore_math(html_out, stash)
