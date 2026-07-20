---
layout: post
title:  "Edge Cases"
date:   2026-07-09 15:04:01
categories: post
---

Some edge cases {% marginnote 'mn-id-1' 'For the source article, see [Harmon](https://clayh53.github.io/tufte-jekyll/articles/20/Edge-Cases).' %}and cautionary examples on using Markdown for writing content using this theme. In particular, list syntax can really knot things up.
<!--more-->

### MathJax and ">", "<", "&" characters inside blocks

MathJax renders block-style expressions inside a `$$ ... $$` pair straight from the raw page text. the Markdown pass doesn't touch what's between them, so there's no risk of the parser mangling special characters before MathJax ever sees them.

This code:

```latex
$$
  D = \left(\begin{matrix}
  1 & -1 & & & & \\
  &    & \cdots &   & \\
  &    &        & 1 & -1
 \end{matrix}
 \right)
$$
```
yields this:

$$
D = \left(\begin{matrix}
  1 & -1 & & & & \\
  &    & \cdots &   & \\
  &    &        & 1 & -1
\end{matrix}
\right)
$$

Other examples from the [wikia Tex reference](http://latex.wikia.com/wiki/Matrix_environments):

$$
\begin{matrix}
\alpha& \beta^{*}\\
\gamma^{*}& \delta
\end{matrix}
$$


$$
\begin{bmatrix}
\alpha& \beta^{*}\\
\gamma^{*}& \delta
\end{bmatrix}
$$

$$
\begin{Bmatrix}
\alpha& \beta^{*}\\
\gamma^{*}& \delta
\end{Bmatrix}
$$

$$
\begin{vmatrix}
\alpha& \beta^{*}\\
\gamma^{*}& \delta
\end{vmatrix}
$$

$$
\begin{Vmatrix}
\alpha& \beta^{*}\\
\gamma^{*}& \delta
\end{Vmatrix}
$$

$$
\begin{Vmatrix}
\alpha& \beta^{*}\\
\gamma^{*}& \delta
\end{Vmatrix}
$$

Note that inline matrices need a bit of extra care, for example [here](https://en.wikibooks.org/wiki/LaTeX/Mathematics#Matrices_in_running_text):

To not increase leading in a portion of text, a matrix in text must be set smaller: $$ \bigl(\begin{smallmatrix}a & b \\ c & d\end{smallmatrix} \bigr) $$ The way this inline matrix is written is: `$$ \bigl(\begin{smallmatrix}a & b \\ c & d\end{smallmatrix} \bigr) $$`

## Edge Case 1: list formatting

### No blank lines between Markdown list items

The issue arises when sidenotes and marginnotes are put into list items. As mentioned in the main documentation page, **lists can be problematic** not only for semantic clarity, but also because they can create formatting issues. For example:

### Example

+ Split Bregman iteration {% sidenote 1 'Goldstein, T. and Osher, S. (2009). The split Bregman method for l1-regularized problems. SIAM J. Img. Sci., 2:323-343.' %}
+ Dykstra's alternating projection algorithm {% sidenote 2 'Dykstra, R. L. (1983). An algorithm for restricted least squares regression. J. Amer. Statist. Assoc., 78(384):837-842.' %}
+ Proximal point algorithm applied to the dual
+ Numerous applications in statistics and machine learning: lasso, gen. lasso, graphical lasso, (overlapping) group lasso, ...
+ Embraces distributed computing for big data {% sidenote 3 'Boyd, S., Parikh, N., Chu, E., Peleato, B., and Eckstein, J. (2011). Distributed optimization and statistical learning via the alternating direction method of multipliers. Found. Trends Mach. learn., 3(1):1-122.' %}

### Why this matters

Notice how the sidenotes display properly, but the fact that sidenotes have more display 'volume' than the list items themselves causes a horizontal mismatch between the sidenote item's number and its corresponding list item.

Please note that there must be *no blank lines between your list items*. This isn't specific to any one Markdown parser. It's standard Markdown behavior (this theme's Python-Markdown behaves the same way Kramdown, Python-Markdown's own `extra` extension, and most other implementations do): a blank line between list items switches a list from "tight" to "loose", and loose lists wrap each item's content in its own `<p>` tag. If you have a list, and you put a blank line between the items like this:

```text
  + list item 1

  + list item 2
```

It will create an html tag structure like this:

```text
<ul>
   <li>
      <p>list item 1</p>
  </li>
  <li>
      <p>list item 2</p>
   </li>
</ul>
```
Which *totally* goofs up the layout CSS.

However, if your Markdown is this:

```text
    + list item 1
    + list item 2
```

It will create a tag structure like this:

```text
<ul>
   <li>list item 1</li>
   <li>list item 2</li>
</ul>
```

Here is the same content as above, with a blank line separating the list items. Notice how the sidenotes get squashed into the main content area:


### Remarks on ADMM version 2 - **one blank line** between Markdown list items

Related algorithms

+ Split Bregman iteration {% sidenote 1 'Goldstein, T. and Osher, S. (2009). The split Bregman method for l1-regularized problems. SIAM J. Img. Sci., 2:323-343.' %}

+ Dykstra's alternating projection algorithm {% sidenote 2 'Dykstra, R. L. (1983). An algorithm for restricted least squares regression. J. Amer. Statist. Assoc., 78(384):837-842.' %}

+ Proximal point algorithm applied to the dual

+ Numerous applications in statistics and machine learning: lasso, gen. lasso, graphical lasso, (overlapping) group lasso, ...
<br>
<br>
<br>
<br>

## Edge Case 2: shortcode quoting

This Python port is actually *less* fiddly than the Jekyll original it grew from. Jekyll's Liquid tags are parsed before Markdown ever runs, with no concept of a Markdown code span. If you wanted to *show* a shortcode's literal syntax inside backticks (rather than have it expand), you had to wrap it in an escaping trick just to stop Liquid from touching it. Tufte-python's shortcode expander, explicitly skips over fenced and inline code spans before it looks for anything to expand (see `tufte_ssg/shortcodes.py`), so code spans containing shortcode-like syntax just work, with no escaping trick needed. Every code span you've seen throughout this site's sample posts is proof of that.

The other half of the puzzle is arguments *with* real quote characters in them, like an `<a href="...">` tag embedded in a caption. Shortcode arguments are parsed the same forgiving way a Unix shell parses a quoted command line (via Python's `shlex`): wrap an argument in double quotes and a backslash-escaped `\"` inside it becomes a literal `"`, and an apostrophe inside it (like Tufte'**s**) needs no special handling at all, since it isn't the character being used to delimit the argument. So this:

```text
{% fullwidth "assets/img/rhino.png" "Tufte's pet rhino (via <a href=\"//www.edwardtufte.com/tufte/\">Edward Tufte</a>)" %}
```

produces the following image with a link in its caption, apostrophe and all, with none of the "escaping the escapes" gymnastics the original needed:

{% fullwidth "assets/img/rhino.png" "Tufte's pet rhino (via <a href=\"//www.edwardtufte.com/tufte/\">Edward Tufte</a>)" %}
