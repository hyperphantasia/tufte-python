---
title: "A Quiet Place for Notes"
date: 2024-08-19 13:30:00
categories: notes
tags: [python, writing, design]
---

A personal blog does not need to compete with an application dashboard.

It can give ideas room to breathe and place useful context close to the paragraph that needs it.

<!--more-->

This section appears only after the visitor opens the full article. It is meant to showcase examples shown in this freeCodeCamp News [tutorial](ADD_LINK).
<br>
<br>

## Newthougths

Use the `newthought` shortcode to introduce a new section or changes in the argument:

{% newthought 'A new thought begins here' %}. Keep in mind that a good layout should make reading easier.
<br>
<br>

## Sidenotes

Sidenote {% sidenote 'note-1' 'This is a sidenote. It appears beside the main text on wide screens and becomes part of the reading flow on smaller screens.' %}

<br>

You can enrich notes with Markdown:

Sidenote {% sidenote 'note-2' 'This note includes **bold text** and a [link](https://en.wikipedia.org/wiki/Hyperphantasia).' %}

<br>

A marginnote is not a sidenote, see the difference: {% marginnote 'margin-note' 'A margin note does not use the same numbered-note treatment as a sidenote.' %}

<br>
<br>

## Margin Figures

{% marginfigure 'figure-1' 'assets/img/2024-08-fCC-News-tutorial/Cuisin.JPG' 'A quiet place to read and write.' %}

To place figures in the margin, use the `marginfigure` shortcode (note that it takes three [parameters](https://hyperphantasia.github.io/tufte-python/articles/2026/tufte-style-python-blog/#margin-figures) that *must* be enclosed in quotes):

Margin figures help establish a visual hierarchy. The main text represents the primary argument while the margin figures supports or illustrates data.
<br>
<br>
<br>

## Main Columns Figures

The `maincolumn` is meant for figures that should be constrained to the main column. 
<br>
<br>

{% maincolumn 'assets/img/2024-08-fCC-News-tutorial/Picasso.png' 'Nature morte à la tête antique, *[Pablo Picasso (1925)](https://www.centrepompidou.fr/fr/ressources/oeuvre/cxxXG6j)*' %}
<br>

## Full Width Figures

For information rich material, it is important to display a full-width image or figure. These figures will expand beyond the main column to fit within the larger part of the viewport.
<br>
<br>

{% fullwidth 'assets/img/2024-08-fCC-News-tutorial/Magdalena-Bay.JPG' 'Magdalena-Bay, *[François Biard (1841)](https://collections.louvre.fr/en/ark:/53355/cl010065799)*' %}
<br>
<br>

# Epigraphs

Epigraphs are short quotations placed at the beginning of a chapter to suggest its theme and set the tone.

{% epigraph 'The details are not the details. They make the design.' 'Charles Eames' 'A commonly cited design principle' %}

They function like this:

{% epigraph 'A short quotation.' 'Author Name' 'Book or article title' %}
<br>

## Mathematical notation

If activated, this theme loads MathJax to render both inline and block-level mathematical notation.

$$ 
\int_0^1 x^2\,dx = \frac{1}{3}
$$

The result is: $$ 1/3 $$
<br>
<br>

## Tables

Tables are a big thing !
<br>
<br>

| Format | Best use |
| --- | --- |
| Sidenote | Supporting context |
| Margin figure | Small visual |
| Full-width figure | Wide diagram |

[tufte-python](github.com/hyperphantasia/tufte-python) provides a broad range of [possibilities](https://hyperphantasia.github.io/tufte-python/articles/2026/tufte-style-python-blog/).
<br>
<br>

## Code snippets

```python
print("See you soon !")
```

That's it! More examples are available in this [post](https://hyperphantasia.github.io/tufte-python/articles/2026/tufte-style-python-blog/) and in this [one](https://hyperphantasia.github.io/tufte-python/articles/2026/edge-cases/). Also, do not forget to check the project's [Readme](https://github.com/hyperphantasia/tufte-python/blob/main/README.md).
