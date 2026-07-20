"""Configuration loading for the site generator.
This module loads `config.yml`, merges it with defaults, and
 appliesenvironment-variable overrides for local development and deployment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULTS: dict[str, Any] = {
    "title": "Tufte-Python",
    "subtitle": "Content-centric minimalist blogging",
    "author": "Your Name",
    "email": "you@example.com",
    "description": "A Tufte-styled static site, generated with Python",
    "url": "",
    "baseurl": "",
    "permalink": "/articles/{year}/{slug}/",
    "index_title": "blog",
    "badge_image": "assets/img/python_simple_blog_logo.png",
    "theme": "solarized",
    "options": {
        "mathjax": True,
        "lato_font_load": True,
        "justify_text": False,
    },
    "social": [],
}


def load_config(path: Path) -> dict[str, Any]:
    """Load and merge site configuration from YAML and environment overrides.

    Args:
        path: Path to the configuration file.

    Returns:
        A merged configuration dictionary containing defaults, file values,
        and environment-variable overrides.
    """
    data: dict[str, Any] = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    merged = dict(DEFAULTS)
    merged.update({k: v for k, v in data.items() if k != "options"})
    merged["options"] = {**DEFAULTS["options"], **(data.get("options") or {})}

    # Allow overriding on the command line for local preview, e.g.:
    #   TUFTE_BASEURL="" python build.py --serve
    if "TUFTE_BASEURL" in os.environ:
        merged["baseurl"] = os.environ["TUFTE_BASEURL"]
    if "TUFTE_URL" in os.environ:
        merged["url"] = os.environ["TUFTE_URL"]

    # normalize: no trailing slash on baseurl/url
    merged["baseurl"] = merged["baseurl"].rstrip("/")
    merged["url"] = merged["url"].rstrip("/")
    return merged
