#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# File name: cache.py
# Author: brkln (github.com/hyperphantasia)
# Location: 445.523236,-122.681730
# Date created: 2026-07-10
# Version = "1.0"
# License = "MIT License"
# =============================================================================
"""On-disk cache for incremental builds.

Lets Site.build() skip re-rendering documents whose source file hasn't
changed since the last build. The cache is invalidated wholesale (forcing
a full rebuild) whenever anything that could affect every page changes:
a template, config.yml, or the generator's own Python source. That's
deliberately conservative: it costs one full rebuild after a template
edit, but guarantees stale output never ships silently. Individual posts/
pages are otherwise only re-rendered when their own file's mtime has moved,
or their expected output file has gone missing (self-healing if _site/ was
hand-edited).
"""
# =============================================================================

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CACHE_VERSION = 2
CACHE_FILENAME = ".tufte_cache.json"


def empty() -> dict[str, Any]:
    """Create a fresh, empty cache dictionary.

    Returns:
        A new cache dict with current version and no stored documents.
    """
    return {"version": CACHE_VERSION, "global_mtime": 0.0, "docs": {}}


def global_mtime(root: Path) -> float:
    """Compute the latest mtime across global build inputs.

    Returns the most recent modification time of any file that could affect
    how every page renders: templates, config.yml, and the generator's
    own source code.

    Args:
        root: Project root directory.

    Returns:
        The latest mtime (seconds since epoch) across all global inputs,
        or 0.0 if no files are found.
    """
    latest = 0.0
    for p in (root / "config.yml", root / "templates", root / "tufte_ssg"):
        if p.is_file():
            latest = max(latest, p.stat().st_mtime)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    latest = max(latest, f.stat().st_mtime)
    return latest


def load(root: Path) -> dict[str, Any]:
    """Load the cache from disk, or return an empty cache if not found.

    If the cache file doesn't exist, is corrupted, or has an incompatible
    version, silently returns an empty cache to trigger a full rebuild.

    Args:
        root: Project root directory.

    Returns:
        The persisted cache dict, or an empty cache if loading fails.
    """
    cache_file = root / CACHE_FILENAME
    if not cache_file.exists():
        return empty()
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return empty()
    if not isinstance(data, dict) or data.get("version") != CACHE_VERSION:
        return empty()
    data.setdefault("docs", {})
    data.setdefault("global_mtime", 0.0)
    return data


def save(root: Path, docs: dict[str, dict]) -> None:
    """Persist the cache to disk.

    Args:
        root: Project root directory.
        docs: Per-document cache entries (keyed by source file path).
    """
    cache_file = root / CACHE_FILENAME
    payload = {
        "version": CACHE_VERSION,
        "global_mtime": global_mtime(root),
        "docs": docs,
    }
    cache_file.write_text(json.dumps(payload), encoding="utf-8")


def clear(root: Path) -> None:
    """Remove the cache file from disk.

    Args:
        root: Project root directory.
    """
    cache_file = root / CACHE_FILENAME
    if cache_file.exists():
        cache_file.unlink()
