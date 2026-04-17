#!/usr/bin/env python3
"""Convert markdown to styled HTML using the pretty-page template."""
import sys
import re
import os

def md_to_html(md_text):
    """Simple markdown to HTML converter."""
    lines = md_text.split('\n')
    html_parts = []
    in_list = False
    list_type = None  # 'ul', 'ol', or 'checklist'
    in_code_block = False
    code_lines = []
    in_blockquote = False
    bq_lines = []

    def flush_blockquote():
        nonlocal in_blockquote, bq_lines
        if in_blockquote:
            content = '\n'.join(bq_lines)
            # Split on double newlines first
            paras = [p.strip() for p in content.split('\n\n') if p.strip()]
            result_lines = []
            for p in paras:
                sublines = p.split('\n')
                non_empty = [sl for sl in sublines if sl.strip()]
                # Check if this paragraph is entirely list items (- or *)
                if non_empty and all(re.match(r'^[\-\*]\s+', sl.strip()) for sl in non_empty):
                    result_lines.append('<ul>')
                    for sl in non_empty:
                        item_text = re.sub(r'^[\-\*]\s+', '', sl.strip())
                        result_lines.append(f'<li>{inline_format(item_text)}</li>')
                    result_lines.append('</ul>')
                # Check if first line is a header and remaining lines are all list items
                elif (len(non_empty) > 1
                      and not re.match(r'^[\-\*]\s+', non_empty[0].strip())
                      and all(re.match(r'^[\-\*]\s+', sl.strip()) for sl in non_empty[1:])):
                    result_lines.append(f'<p class="card-header">{inline_format(non_empty[0].strip())}</p>')
                    result_lines.append('<ul>')
                    for sl in non_empty[1:]:
                        item_text = re.sub(r'^[\-\*]\s+', '', sl.strip())
                        result_lines.append(f'<li>{inline_format(item_text)}</li>')
                    result_lines.append('</ul>')
                # If paragraph has multiple lines with bold labels, split them
                elif len(sublines) > 1 and all(re.match(r'\*\*[^*]+\*\*', sl.strip()) for sl in sublines if sl.strip()):
                    for sl in sublines:
                        if sl.strip():
                            result_lines.append(f'<p>{inline_format(sl.strip())}</p>')
                else:
                    stripped_p = p.strip()
                    if stripped_p.startswith('*Sources:') or stripped_p.startswith('*Verified:'):
                        result_lines.append(f'<p class="card-meta">{inline_format(stripped_p)}</p>')
                    else:
                        result_lines.append(f'<p>{inline_format(p)}</p>')
            inner = ''.join(result_lines)
            html_parts.append(f'<blockquote>{inner}</blockquote>')
            in_blockquote = False
            bq_lines = []

    def flush_list():
        nonlocal in_list, list_type
        if in_list:
            tag = 'ol' if list_type == 'ol' else 'ul'
            html_parts.append(f'</{tag}>')
            in_list = False
            list_type = None

    i = 0
    while i < len(lines):
        line = lines[i]

        if line.strip().startswith('```'):
            if in_code_block:
                html_parts.append(f'<pre><code>{chr(10).join(code_lines)}</code></pre>')
                code_lines = []
                in_code_block = False
            else:
                flush_list()
                flush_blockquote()
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_lines.append(line.replace('<', '&lt;').replace('>', '&gt;'))
            i += 1
            continue

        if line.strip().startswith('>'):
            flush_list()
            if not in_blockquote:
                in_blockquote = True
            bq_lines.append(re.sub(r'^>\s*', '', line))
            i += 1
            continue
        elif in_blockquote and line.strip() == '':
            flush_blockquote()
            i += 1
            continue
        elif in_blockquote:
            flush_blockquote()

        if line.strip() == '---' or line.strip() == '***':
            flush_list()
            html_parts.append('<hr>')
            i += 1
            continue

        heading_match = re.match(r'^(#{1,4})\s+(.*)', line)
        if heading_match:
            flush_list()
            level = len(heading_match.group(1))
            raw_text = heading_match.group(2)
            text = inline_format(raw_text)
            slug = re.sub(r'[^a-z0-9]+', '-', raw_text.lower()).strip('-')
            html_parts.append(f'<h{level} id="{slug}">{text}</h{level}>')
            i += 1
            continue

        stripped = line.strip()

        checkbox_match = re.match(r'^[\-\*]\s+\[([ xX])\]\s+(.*)', stripped)
        if checkbox_match:
            if list_type != 'checklist':
                flush_list()
                html_parts.append('<ul class="checklist">')
                in_list = True
                list_type = 'checklist'
            checked = 'checked' if checkbox_match.group(1).lower() == 'x' else ''
            text = inline_format(checkbox_match.group(2))
            html_parts.append(f'<li class="check-item"><label><input type="checkbox" {checked}><span>{text}</span></label></li>')
            i += 1
            continue

        list_match = re.match(r'^[\-\*]\s+(.*)', stripped)
        if list_match:
            if list_type != 'ul':
                flush_list()
                html_parts.append('<ul>')
                in_list = True
                list_type = 'ul'
            html_parts.append(f'<li>{inline_format(list_match.group(1))}</li>')
            i += 1
            continue

        num_match = re.match(r'^\d+\.\s+(.*)', stripped)
        if num_match:
            if list_type != 'ol':
                flush_list()
                html_parts.append('<ol>')
                in_list = True
                list_type = 'ol'
            html_parts.append(f'<li>{inline_format(num_match.group(1))}</li>')
            i += 1
            continue

        if stripped == '':
            # If in an ordered list, look ahead to see if the next non-blank line
            # is also a numbered item — if so, don't flush (keeps list numbering continuous)
            if list_type == 'ol':
                j = i + 1
                while j < len(lines) and lines[j].strip() == '':
                    j += 1
                if j < len(lines) and re.match(r'^\d+\.\s+', lines[j].strip()):
                    i += 1
                    continue
            flush_list()
            i += 1
            continue

        flush_list()

        if i + 1 < len(lines) and re.match(r'^\|[\-\s\|:]+\|$', lines[i + 1].strip()):
            table_html = parse_table(lines, i)
            if table_html:
                html_parts.append(table_html[0])
                i = table_html[1]
                continue

        html_parts.append(f'<p>{inline_format(line)}</p>')
        i += 1

    flush_list()
    flush_blockquote()

    return '\n'.join(html_parts)


def inline_format(text):
    """Apply inline formatting."""
    # Strip trailing backslash (markdown line continuation)
    text = re.sub(r'\\$', '', text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width:100%;height:auto;border-radius:4px;margin:1rem 0;">', text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    # Auto-link bare URLs not already inside an anchor or img tag
    text = re.sub(r'(?<!href=")(?<!src=")(?<!">)(https?://[^\s<>"]+)', r'<a href="\1">\1</a>', text)
    return text


def parse_table(lines, start):
    """Parse a markdown table starting at line index."""
    header = lines[start].strip()
    if not header.startswith('|'):
        return None

    cells = [c.strip() for c in header.split('|')[1:-1]]
    sep_idx = start + 1

    html = '<table><thead><tr>'
    for cell in cells:
        html += f'<th>{inline_format(cell)}</th>'
    html += '</tr></thead><tbody>'

    i = sep_idx + 1
    while i < len(lines) and lines[i].strip().startswith('|'):
        row_cells = [c.strip() for c in lines[i].strip().split('|')[1:-1]]
        html += '<tr>'
        for cell in row_cells:
            html += f'<td>{inline_format(cell)}</td>'
        html += '</tr>'
        i += 1

    html += '</tbody></table>'
    return (html, i)


def build_nav_html(nav_items):
    """Build sticky nav bar HTML from a list of {label, url, active} dicts."""
    if not nav_items:
        return ''
    links = []
    for item in nav_items:
        cls = ' class="active"' if item.get('active') else ''
        links.append(f'<a href="{item["url"]}"{cls}>{item["label"]}</a>')
    return f'<nav class="sticky-nav">{" ".join(links)}</nav>\n<div class="nav-spacer"></div>'


def render(md_path, title=None, slug=None, nav=None):
    """Render markdown file to HTML using the template."""
    with open(md_path) as f:
        md_text = f.read()

    # Strip frontmatter
    if md_text.startswith('---'):
        parts = md_text.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            md_text = parts[2].strip()
            if not title:
                title_match = re.search(r'title:\s*["\']?(.+?)["\']?\s*$', frontmatter, re.MULTILINE)
                if title_match:
                    title = title_match.group(1)

    # Preserve raw HTML blocks (iframes, embeds) from markdown processing
    html_block_placeholders = {}
    html_block_counter = [0]
    def preserve_html_block(match):
        key = f'__HTML_BLOCK_{html_block_counter[0]}__'
        html_block_placeholders[key] = match.group(0)
        html_block_counter[0] += 1
        return key
    md_text = re.sub(r'<iframe\b[^>]*>.*?</iframe>', preserve_html_block, md_text, flags=re.DOTALL)
    md_text = re.sub(r'<video\b[^>]*>.*?</video>', preserve_html_block, md_text, flags=re.DOTALL)
    md_text = re.sub(r'<audio\b[^>]*>.*?</audio>', preserve_html_block, md_text, flags=re.DOTALL)
    md_text = re.sub(r'<details\b[^>]*>.*?</details>', preserve_html_block, md_text, flags=re.DOTALL)
    md_text = re.sub(r'<span\b[^>]*>.*?</span>', preserve_html_block, md_text, flags=re.DOTALL)
    md_text = re.sub(r'<div\b[^>]*>.*?</div>', preserve_html_block, md_text, flags=re.DOTALL)

    # Always strip first h1 from content (template renders its own title)
    h1_match = re.match(r'^#\s+(.+)', md_text)
    if h1_match:
        if not title:
            title = h1_match.group(1)
        md_text = md_text[h1_match.end():].strip()

    if not title:
        title = 'Untitled'

    if not slug:
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    content_html = md_to_html(md_text)

    # Wrap pre-section metadata in a styled block
    # Detect consecutive <p><strong>Label:</strong>...</p> lines at the start of content
    lines = content_html.split('\n')
    meta_lines = []
    in_meta = True
    in_meta_list = False
    for line in lines:
        if in_meta and line.startswith('<p><strong>') and '</strong>' in line and line.endswith('</p>'):
            meta_lines.append(line)
            in_meta_list = False
        elif in_meta and (line.startswith('<ul>') or line.startswith('<ul ')):
            meta_lines.append(line)
            in_meta_list = True
        elif in_meta_list and (line.startswith('<li>') or line.startswith('</ul>')):
            meta_lines.append(line)
            if line.startswith('</ul>'):
                in_meta_list = False
        elif not in_meta_list:
            break
        else:
            break
    has_manual_toc = False
    if meta_lines:
        meta_block = '\n'.join(meta_lines)
        rest = '\n'.join(lines[len(meta_lines):])
        # Check if the metadata block contains anchor links (manual TOC)
        has_manual_toc = 'href="#' in meta_block
        # Wrap in collapsible details if it has a TOC
        if has_manual_toc:
            # Extract the first line as the summary, rest as collapsible content
            first_line = meta_lines[0]
            remaining = '\n'.join(meta_lines[1:])
            content_html = f'<div class="metadata"><details class="toc-collapse" open><summary>{first_line}</summary>{remaining}</details></div>\n{rest}'
        else:
            content_html = f'<div class="metadata">{meta_block}</div>\n{rest}'
    else:
        rest = content_html

    # Auto-generate TOC if no manual one exists and page has 4+ headings
    if not has_manual_toc:
        heading_pattern = re.compile(r'<h([234]) id="([^"]+)">(.+?)</h\1>')
        headings = heading_pattern.findall(content_html)
        if len(headings) >= 4:
            # Build nested <ul> structure so bullets indent properly
            toc_parts = []
            current_level = 2
            for level, hid, text in headings:
                level = int(level)
                clean = re.sub(r'<[^>]+>', '', text)
                if level > current_level:
                    # Open nested lists for each level deeper
                    for _ in range(level - current_level):
                        toc_parts.append('<ul>')
                elif level < current_level:
                    # Close nested lists for each level shallower
                    for _ in range(current_level - level):
                        toc_parts.append('</li></ul>')
                else:
                    # Same level — close previous <li> if not the first item
                    if toc_parts:
                        toc_parts.append('</li>')
                toc_parts.append(f'<li><a href="#{hid}">{clean}</a>')
                current_level = level
            # Close any remaining open tags
            toc_parts.append('</li>')
            for _ in range(current_level - 2):
                toc_parts.append('</ul></li>')
            toc_inner = '\n'.join(toc_parts)
            toc_html = f'<div class="metadata"><details class="toc-collapse" open><summary><p><strong>On this page:</strong></p></summary><ul class="auto-toc">\n{toc_inner}\n</ul></details></div>\n'
            content_html = toc_html + content_html

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html')
    with open(template_path) as f:
        template = f.read()

    # Embed raw markdown for copy-to-clipboard
    import html as html_mod
    raw_md_escaped = html_mod.escape(md_text)

    # Restore preserved HTML blocks (iframes, embeds)
    # Reverse order so outer blocks (which contain inner placeholders) are restored first,
    # then inner placeholders get resolved in subsequent iterations
    for key, original_html in reversed(list(html_block_placeholders.items())):
        content_html = content_html.replace(f'<p>{key}</p>', original_html)
        content_html = content_html.replace(key, original_html)

    html = template.replace('{{TITLE}}', title)
    html = html.replace('{{NAV}}', build_nav_html(nav) if nav else '')
    html = html.replace('{{CONTENT}}', content_html)
    html = html.replace('{{RAW_MARKDOWN}}', raw_md_escaped)
    footer = os.environ.get('PRETTY_PAGE_FOOTER', '')
    html = html.replace('{{FOOTER}}', footer)

    output_path = f'/tmp/pretty-page-{slug}.html'
    with open(output_path, 'w') as f:
        f.write(html)

    print(output_path)
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: render.py <markdown-file> [--title 'Title'] [--slug slug]", file=sys.stderr)
        sys.exit(1)

    import json as json_mod

    md_path = sys.argv[1]
    title = None
    slug = None
    nav = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--title' and i + 1 < len(sys.argv):
            title = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--slug' and i + 1 < len(sys.argv):
            slug = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--nav' and i + 1 < len(sys.argv):
            nav = json_mod.loads(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    render(md_path, title, slug, nav)
