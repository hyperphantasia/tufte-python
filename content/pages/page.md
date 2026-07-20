---
layout: post
title: Page
---

{% newthought 'Tufte-Python' %} mirrors Jekyll's own conventions: it provides for posts and pages.

## Posts

Posts are for recurring pieces of similar content such as might be found in a typical blog entry. Post content lives in a folder named `"content/posts"` and files are created in this folder{% sidenote 1 'Yes, a page like this one and its `"layout: post"` set in the front matter has the same structure as a post.' %}. They are named with a date prepended to the title of the post. For instance `content/posts/2004-02-24-this-is-a-post.md` is a perfectly valid post filename.

Posts will always have a section above the content itself consisting of YAML [front matter](https://jekyllrb.com/docs/front-matter/), which is metadata about the post. A post title must always be *present* for the post to be processed properly.

```
---
title: Some Title
date: 2004-02-24 10:18:00
---
## Content

Markdown formatted content *here*.
```

## Pages

Page material is more suited to static, non-recurring types of content. Pages are Markdown documents with YAML front matter that live in `"content/pages"` and are converted to standalone content, such as this Page or the [About](https://hyperphantasia.github.io/tufte-python/about/) page.
