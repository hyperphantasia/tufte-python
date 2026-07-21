---
layout: full-width
title: About
---

{% newthought 'Tufte-Python' %} is a Python port of the original [tufte-jekyll](https://github.com/clayh53/tufte-jekyll) theme, which itself is a natural extension of the work done by [Edward Tufte](https://github.com/edwardtufte/tufte-css) and his collaborators on GitHub. They created a CSS file that allows web writers to use the same simple and elegant [style](https://ctan.math.washington.edu/tex-archive/macros/latex/contrib/tufte-latex/sample-handout.pdf) available from Tufte's published materials.

This port swaps out Ruby, Jekyll, and Liquid for Python, [Jinja2](https://jinja.palletsprojects.com/), and [Python-Markdown](https://python-markdown.github.io/) while keeping the same look and content-authoring [shortcodes](https://hyperphantasia.github.io/tufte-python/articles/2026/tufte-style-python-blog) (sidenotes, margin notes, epigraphs, and so on) the Jekyll version implements.

It also includes popular color themes like [Solarized](https://ethanschoonover.com/solarized/) (the default), [Dracula](https://github.com/dracula/dracula-theme), and several [Gradianto](https://github.com/thvardhan/Gradianto) variants. They can be selected in the `config.yml` file. Most themes are accessible and come along with a dark mode that follows system preferences with a manual switch available.

Note that this is a full-width layout. This was set with `"layout: full-width"` in the YAML front matter for this page located in `about.md`. In this layout style, sidenote and marginnote do not display.
