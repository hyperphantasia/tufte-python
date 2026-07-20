#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# File name: build.py
# Author: brkln
# Location: 445.523236,-122.681730
# Date created: 2026-07-10
# Version = "1.0"
# License = "MIT License"
# Listening = Il Gioco Di Giosue - Nicola Piovani
# =============================================================================
"""Build (and optionally serve) the site.

Usage:
    python build.py                     # build once into _site/ (uses config.yml's real baseurl)
    python build.py --serve             # build + serve at :8000 (baseurl blanked out for local links)
    python build.py --serve --watch     # also rebuild automatically on file changes
    python build.py --serve --production-urls  # serve with the real baseurl, to sanity-check it before deploying
"""
# =============================================================================

from __future__ import annotations

import argparse
import functools
import http.server
import os
import socketserver
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from tufte_ssg import Site  # noqa: E402


def _mtime_fingerprint(root: Path) -> float:
    """Return the most recent modification time under the site inputs.

    Args:
        root: Project root directory.

    Returns:
        The latest modification timestamp found in `content`, `templates`,
        `static`, or `config.yml`.
    """
    latest = 0.0
    for base in ("content", "templates", "static", "config.yml"):
        p = root / base
        if p.is_file():
            latest = max(latest, p.stat().st_mtime)
        elif p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    latest = max(latest, f.stat().st_mtime)
    return latest


def build(root: Path) -> Site:
    """Build the site for the given project root.

    Args:
        root: Project root directory.

    Returns:
        The built `Site` instance.
    """
    site = Site(root)
    site.build()
    print(f"Built site into {site.out_dir}")
    return site


class _BaseurlHandler(http.server.SimpleHTTPRequestHandler):
    """Serve a site under a base URL path.

    This serves `directory` under `baseurl` (for example, "/reponame") and
    returns 404 for anything outside that prefix. It mirrors GitHub Pages
    project-site behavior so production URLs can be tested locally.
    """

    baseurl: str = ""  # set via functools.partial before use

    def translate_path(self, path: str) -> str:
        """Translate a URL path into a local filesystem path.

        Args:
            path: Requested URL path.

        Returns:
            A filesystem path string resolved by the parent handler.
        """
        parsed = path.split("?", 1)[0].split("#", 1)[0]
        if self.baseurl:
            if parsed == self.baseurl or parsed.startswith(self.baseurl + "/"):
                path = "/" + parsed[len(self.baseurl):].lstrip("/")
            else:
                path = "/__404__"
        return super().translate_path(path)


def serve(root: Path, port: int, watch: bool, production_urls: bool) -> None:
    """Build and serve the site, optionally rebuilding on changes.

    Args:
        root: Project root directory.
        port: TCP port to bind.
        watch: If true, rebuild when source files change.
        production_urls: If true, serve under the configured base URL path.
    """
    if not production_urls and "TUFTE_BASEURL" not in os.environ:
        os.environ["TUFTE_BASEURL"] = ""

    site = build(root)
    baseurl = site.config["baseurl"]

    if production_urls and baseurl:
        handler_cls = type("_Handler", (_BaseurlHandler,),
                           {"baseurl": baseurl})
        handler = functools.partial(handler_cls, directory=str(site.out_dir))
    else:
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler, directory=str(site.out_dir))

    httpd = socketserver.TCPServer(("", port), handler)
    print(f"Serving http://localhost:{port} (Ctrl+C to stop)")
    if production_urls and baseurl:
        print(
            f"(mounted under {baseurl!r} to match the real deployment -- try http://localhost:{port}{baseurl}/)")
    elif not production_urls:
        print("(using an empty baseurl for local preview -- pass --production-urls to test the real one)")

    if not watch:
        httpd.serve_forever()
        return

    import threading

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    last = _mtime_fingerprint(root)
    try:
        while True:
            time.sleep(1)
            current = _mtime_fingerprint(root)
            if current != last:
                last = current
                print("Change detected, rebuilding...")
                try:
                    build(root)
                except Exception as exc:  # noqa: BLE001
                    print(f"Build failed: {exc}")
    except KeyboardInterrupt:
        pass
    finally:
        httpd.shutdown()


def main() -> None:
    """Parse CLI arguments and run the requested action."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true",
                        help="serve the built site over HTTP")
    parser.add_argument("--watch", action="store_true",
                        help="rebuild automatically on file changes (implies --serve)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--production-urls",
        action="store_true",
        help="use the real baseurl from config.yml while serving, instead of blanking it out for local preview",
    )
    args = parser.parse_args()

    root = Path(__file__).parent

    if args.serve or args.watch:
        serve(root, args.port, args.watch, args.production_urls)
    else:
        build(root)


if __name__ == "__main__":
    main()
