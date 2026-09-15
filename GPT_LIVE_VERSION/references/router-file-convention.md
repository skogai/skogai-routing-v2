---
title: router-file-convention
type: note
permalink: skogai-routing/gpt-live-version/references/router-file-convention
---

# Router file convention

A v1 SkogAI router contains YAML frontmatter followed by exactly one `<routes>` block.

```markdown
---
permalink: project/skogai
type: router
---

<routes>

- @docs/ - project documentation
- src/ - implementation files to inspect when relevant

</routes>
```

Rules:

- Require `type: router`.
- Allow an optional nonempty `permalink`.
- Reject other frontmatter fields in v1.
- Put opening and closing tags on separate lines without attributes.
- Allow blank lines inside `<routes>`.
- Make every nonblank line inside the block a nonempty Markdown list entry.
- Allow either `@`-links or plain paths. Loading behavior belongs to the host agent; this convention only records routes.
- Reject additional standalone XML blocks.
- Do not infer or implement other document types.
