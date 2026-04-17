---
name: pretty-page
description: Convert markdown to a beautifully styled, shareable HTML page and upload to S3-compatible storage
---

# /pretty-page — Convert Markdown to Styled HTML Page

Convert markdown content into a beautifully styled, shareable HTML page using the Good Neighbors design system (Risograph-inspired aesthetic). Renders locally and uploads to any S3-compatible host.

## Usage

```
/pretty-page <file-path-or-inline-content> [--title "Page Title"] [--slug custom-slug] [--nav '<JSON>']
```

## What It Does

1. Takes markdown content (file path or inline text)
2. Converts to styled HTML using `render.py` and `template.html`
3. Uploads to S3-compatible storage via `upload.py`
4. Returns a shareable public URL

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

The template uses the Good Neighbors design system:

- **Fonts:** Fraunces (headings) + DM Sans (body) + DM Mono (code)
- **Colors:** Cream paper (#F7F3ED), dark ink (#1C1C1C), red (#E63946), blue (#457B9D), yellow (#F4A261), green (#2A9D8F)
- **Features:** Paper noise texture, offset box-shadows on blockquotes, styled code blocks, responsive layout

## Interactive Features

### Checkboxes with localStorage
Markdown `- [ ]` and `- [x]` render as styled, clickable HTML checkboxes. State persists in browser localStorage (keyed by page title slug).

### Copy as Markdown
Floating button copies the full raw markdown source to clipboard.

### Table of Contents (Auto & Manual)
- **Auto-TOC:** Pages with 4+ headings automatically get a collapsible "On this page" TOC
- **Manual TOC:** If markdown starts with a metadata block containing anchor links (`#section-name`), the auto-TOC is suppressed and the manual version is used
- Both are collapsible with a `[+]`/`[-]` toggle, state persists in localStorage

### Sticky Nav Bar
Pass `--nav` with a JSON array of `{label, url, active}` objects to add a fixed nav bar:

```bash
NAV='[{"label":"Home","url":"https://example.com/","active":true},{"label":"Docs","url":"https://example.com/docs"}]'
python3 render.py source.md --nav "$NAV"
```

### Heading Anchors
All h2/h3/h4 headings get slug-based `id` attributes for in-page linking.

### Metadata Box
Consecutive `**Bold:**` lines at the start of content are wrapped in a styled `.metadata` div.

### Blockquote Cards
Use blockquotes to create visually distinct cards — great for profiles or structured content:

```markdown
> **Name** — Title
> - Career stop 1
> - Career stop 2 (current role)
>
> *Notes:* Cross-reference prose here.
```

## Implementation

When this skill is invoked:

1. Read the markdown content (from file path or inline)
2. Run:
   ```bash
   python3 .claude/skills/pretty-page/render.py <file.md> [--title "Title"] [--slug slug] [--nav '<JSON>']
   ```
   This writes output to `/tmp/pretty-page-{slug}.html` and prints the path.
3. Upload:
   ```bash
   python3 .claude/skills/pretty-page/upload.py /tmp/pretty-page-{slug}.html
   ```
   This prints the public URL.
4. Return the URL to the user.

**Link-check before upload** — extract all URLs from the source and verify them:

```bash
grep -oP 'https?://[^)"\s]+' file.md | sort -u | while read url; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -L --max-time 10 "$url")
  echo "$code $url"
done
```
Flag any 404s and fix them in the source `.md` before uploading.

## Source Sync Guardrails

**The MD is always the source of truth. The pretty-page is a rendered artifact.**

- When generating from a file path, embed a source attribution comment in the HTML after `<body>`: `<!-- pretty-page source: /path/to/source.md -->`
- When the user asks to update content, write the change to the source `.md` first, then regenerate.
- Regenerating always overwrites the previous version at the same slug URL.

## When to Use

Instead of posting raw `.md` files as attachments, use this to create a readable, styled page anyone can open in a browser.

Good for:
- Meeting notes with action item checklists
- Analysis reports and research summaries
- Meeting prep documents
- Blog post drafts for review
- Any markdown content that needs to be shared comfortably
