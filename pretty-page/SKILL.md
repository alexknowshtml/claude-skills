---
name: pretty-page
description: Convert markdown to a beautifully styled, shareable HTML page and upload to S3-compatible storage
---

# /pretty-page — Convert Markdown to Styled HTML Page

Convert markdown content into a beautifully styled, shareable HTML page using the JFDI design system (Risograph-inspired aesthetic). Renders locally and uploads to any S3-compatible host.


## Usage

```
/pretty-page <file-path-or-inline-content> [--title "Page Title"] [--slug custom-slug] [--nav '<JSON>'] [--wide]
```

**`--wide`** — widens the content column from 720px to 1100px. Use for table-heavy pages so wide tables render without horizontal scrolling.


## What It Does

1. Takes markdown content (file path or inline text)
2. Converts to styled HTML using `render.py` and `template.html`
3. Uploads to S3-compatible storage via `upload.py`
4. Returns a shareable public URL


## When to Use

Instead of posting raw `.md` files or sending markdown attachments, use this to create a readable, styled page that anyone can open in a browser.

Good for:
- Meeting notes with action item checklists
- Analysis reports
- Research summaries
- Blog post drafts for review
- Any markdown content that needs to be shared and read comfortably
- System architecture docs with interactive animations


## Source Sync Guardrails

**The MD is always the source of truth. The pretty-page is a rendered artifact.**

1. **MD-first workflow** — If the user asks to update content on a pretty-page, always write the change to the source `.md` first, then regenerate.
2. **Regenerate = overwrite** — The upload always uses the same slug derived from the source file, so regenerating overwrites the previous version at the same URL.
3. **Never guess URL slugs** — When adding links to source `.md` files, always verify URLs exist before writing them.


## Setup

Install the Python dependency:

```bash
pip install boto3
```

Set these environment variables (add to your `.env` or shell profile):

```bash
# Required
export S3_BUCKET=your-bucket-name
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Optional — for non-AWS providers (DO Spaces, Cloudflare R2, Backblaze B2)
export S3_ENDPOINT_URL=https://nyc3.digitaloceanspaces.com
export AWS_DEFAULT_REGION=nyc3

# Optional — prefix for uploaded files (default: "pretty-page/")
export S3_PREFIX=public/

# Optional — override public URL base (e.g. your CDN domain)
export S3_PUBLIC_BASE_URL=https://cdn.yourdomain.com
```


## Template

The template uses the JFDI design system:

- **Fonts:** Fraunces (headings) + DM Sans (body) + DM Mono (code)
- **Colors:** Cream paper (#F7F3ED), dark ink (#1C1C1C), red (#E63946), blue (#457B9D), yellow (#F4A261), green (#2A9D8F)
- **Features:** Paper noise texture, offset box-shadows on blockquotes, styled code blocks, responsive layout


## Interactive Features

### Checkboxes with localStorage
Markdown `- [ ]` and `- [x]` render as styled, clickable HTML checkboxes. State persists in browser localStorage (keyed by page title slug).

A notice appears under each h2 section containing checkboxes: "Checkbox changes are stored locally on your device, not synced with other devices or people."

### Copy as Markdown
Floating button in the top-right corner copies the full raw markdown source to clipboard. Shows "Copied!" feedback with green styling for 2 seconds.

### Table of Contents (Auto & Manual)
- **Auto-TOC:** Pages with 4+ headings automatically get a collapsible "On this page" TOC generated from all h2/h3/h4 headings
- **Manual TOC:** If the markdown starts with a metadata block containing anchor links (`#section-name`), the auto-TOC is suppressed and the manual version is used instead
- **Collapsible:** Both auto and manual TOCs are collapsible with a `[+]`/`[-]` toggle — starts open, state persists in localStorage

### Floating Sidebar TOC
On wide-screen displays (>1300px), a fixed sidebar TOC appears on the left side of pages with 4+ h2 headings. It highlights the active section as you scroll.

### Collapsible h3 Sections
All h3 headings are collapsible — click the heading to toggle the section. State persists in localStorage.

### Sticky Nav Bar
Pass `--nav` with a JSON array of `{label, url, active}` objects to add a fixed nav bar:

```bash
NAV='[{"label":"Home","url":"https://example.com/","active":true},{"label":"Docs","url":"https://example.com/docs"}]'
python3 render.py source.md --nav "$NAV"
```

### Heading Anchors
All h2/h3/h4 headings get slug-based `id` attributes for in-page linking. `scroll-margin-top` provides breathing room when jumping to anchors.

### Metadata Box
Consecutive `**Bold:**` lines at the start of content are wrapped in a styled `.metadata` div. First line renders slightly larger for visual hierarchy. Lists following bold labels are included in the box.


## Blockquote Cards (Person/Item Cards)

Use blockquotes to create visually distinct cards — great for staff rosters, contact profiles, or any list of items that need their own box.

**Pattern — header + bullets + connections paragraph:**
```markdown
> **Name** — Title
> - Career stop 1
> - Career stop 2 (current role)
> - Education
>
> *Connections:* Cross-reference notes as prose here.
```

**How it renders:**
- First line (`**Name** — Title`) → styled as a `card-header` (1.1em, semi-bold)
- Bullet lines → rendered as `<ul><li>` list
- Blank `>` line separates paragraphs within the same card
- Blank line (no `>`) between cards creates separate blockquote boxes


## Horizontal Rules and Back-to-Top Links

Every `---` in the markdown generates a styled `back-to-top` link + `<hr>` in the rendered HTML on archive-style pages (3+ HRs). **Use `---` sparingly** — only between major `##` sections.


## Output Filename Behavior

The render script derives its output filename from the document's H1 slug. Use `--slug` to control the name:

```bash
python3 render.py source.md --slug my-slug
# → writes /tmp/pretty-page-my-slug.html
```


## Raw HTML Passthrough & Gmail-Style Email Cards

Block-level lines starting with an HTML tag (`<div ...>`, `</div>`, etc.) pass through render.py unchanged, enabling template components to be embedded directly in markdown sources.

The template ships CSS for a Gmail-style email card (`.gmail-card`):

```html
<div class="gmail-card">
<div class="gmail-header">
<div class="gmail-subject">Subject line here</div>
<div class="gmail-meta">
<div class="gmail-avatar">A</div>
<div class="gmail-sender-info">
<div class="gmail-sender-name">Sender Name</div>
<div class="gmail-sender-email">sender@example.com</div>
<div class="gmail-to">to Recipient</div>
</div>
<div class="gmail-date">Apr 7, 2026</div>
</div>
</div>
<div class="gmail-body">
<p>Body paragraphs as HTML.</p>
</div>
</div>
```

**Rules:** every line of the block must start with `<` (passthrough is line-based); body content must be pre-converted to HTML (`<p>`, `<ul>/<li>`, `<a>`).


## Interactive Animations

For system documentation, architecture explanations, or any page where the **sequence or timing** is the point, you can add interactive JS animations. These are hand-authored in HTML rather than generated from markdown — build the page as a standalone `.html` file, use the JFDI design system CSS variables (`--paper`, `--ink`, `--red`, `--blue`, `--yellow`, `--green`) and fonts, then upload directly.

**Key JS rule:** All choreographed animations use `async/await` + `const sleep = ms => new Promise(r => setTimeout(r, ms))`. Never callback chains.


## Footer Customization

The footer is set in `render.py`:

```python
html = html.replace('{{FOOTER}}', 'Prepared by <a href="https://example.com">Your Name</a>')
```

Edit this line to personalize the footer for your deployment.


## Implementation

1. Read the markdown content (from file path or inline)
2. Use `render.py` to convert markdown to HTML using `template.html`
3. The script handles: markdown-to-HTML conversion, frontmatter stripping, checkbox rendering, heading ID generation, metadata block detection, raw HTML passthrough, and raw markdown embedding
4. **NEVER redirect stdout to the output file.** The script writes the HTML itself and prints the output path to stdout. Correct invocation:
   ```bash
   python3 render.py source.md --slug my-slug
   # Script writes to /tmp/pretty-page-my-slug.html and prints that path
   ```
5. **Link-check before upload** — Extract all markdown URLs and verify them:
   ```bash
   grep -oP 'https?://[^)"\s]+' file.md | sort -u | while read url; do
     code=$(curl -s -o /dev/null -w "%{http_code}" -L --max-time 10 "$url")
     echo "$code $url"
   done
   ```
6. Use `upload.py` to upload and get a public URL
7. Return the URL
