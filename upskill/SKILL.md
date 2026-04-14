---
description: Scan current session for skills that need creating or updating, then apply changes
---

You are performing an automated skill maintenance pass based on what happened in the current session.

**Execute immediately.** No preamble, no acknowledgment.

## What This Does

Scans the current session transcript to find:
1. **Stale skills** — skills that were used but contain outdated info (wrong URLs, old versions, missing artifacts, resolved questions still marked open)
2. **New skill candidates** — repeated multi-step workflows that don't have a skill yet
3. **Session index gaps** — skills that were used but their session index wasn't updated

## Execution

### Step 1: Load Session Transcript

```bash
# Update this path to match your Claude Code project directory
# Claude Code stores sessions in ~/.claude/projects/<project-slug>/
SESSION_DIR="$HOME/.claude/projects/<your-project-slug>"

LATEST_JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
echo "Session: $LATEST_JSONL"
wc -l "$LATEST_JSONL"
```

Extract user messages and assistant tool calls (skill invocations, file writes, URLs generated):

```bash
# User messages (what was asked)
jq -r 'select(.type == "user") | select(.message.content | type == "string") | .message.content' "$LATEST_JSONL" 2>/dev/null | head -200

# Skills invoked
jq -r 'select(.type == "assistant") | .message.content[]? | select(.type == "tool_use") | select(.name == "Skill") | .input.skill' "$LATEST_JSONL" 2>/dev/null | sort -u

# Files written or edited
jq -r 'select(.type == "assistant") | .message.content[]? | select(.type == "tool_use") | select(.name == "Write" or .name == "Edit") | .input.file_path' "$LATEST_JSONL" 2>/dev/null | sort -u

# URLs in assistant output
jq -r 'select(.type == "assistant") | .message.content[]? | select(.type == "text") | .text' "$LATEST_JSONL" 2>/dev/null | grep -oP 'https?://[^\s)>"]+' | sort -u
```

### Step 2: Identify Touched Skills

From the signals above, determine which skills were active:
- Skills explicitly invoked via the Skill tool
- Skills whose project files were modified (match file paths to skill project directories)
- Skills whose triggers match topics discussed in user messages

For each identified skill, read its SKILL.md and session index.

### Step 3: Spawn Opus Subagent for Analysis

Delegate the diff analysis to Opus. Pass it:
- The extracted session signals (user messages, files touched, URLs generated, skills invoked)
- The current content of each touched skill's SKILL.md
- The current content of each touched skill's session index (if it has one)

```
Agent({
  description: "Opus upskill analysis",
  model: "opus",
  subagent_type: "general-purpose",
  prompt: `You are analyzing a session transcript to find skill maintenance needed.

DO NOT implement changes. Only produce a structured report.

## Session Signals
{paste extracted signals}

## Existing Skills Touched
{paste each SKILL.md content}

## Session Indexes
{paste each session index}

## Analysis Tasks

### A. Stale Content Detection
For each touched skill, compare its SKILL.md against what actually happened:
- URLs that were generated or changed (new uploads, new pretty-pages)
- Version references that changed (e.g. "v9" → "v10")
- Artifacts created or modified (new files, new scripts, new documents)
- Questions marked "open" that were resolved during the session
- New people, tools, or workflows discovered
- Incorrect or outdated descriptions

### B. Session Index Updates
For each skill with a session index, check if this session should be added.
Draft the session entry with date, session ID, and summary.

### C. New Skill Candidates
Look for multi-step workflows in the session that:
- Took 5+ tool calls to complete
- Don't map to any existing skill
- Would be repeatable in future sessions
- Involve domain-specific knowledge that Claude wouldn't have by default

For each candidate, draft:
- Suggested skill name
- Trigger phrases
- What the skill would contain
- Why it's worth creating (frequency estimate)

### D. Trigger Gaps
Look for user messages that SHOULD have activated a skill but didn't because the trigger list is missing a keyword.

## Output Format

Return EXACTLY this structure:

# Upskill Report

## Skills to Update

### {skill-name}
**Changes needed:**
- {specific change 1 with exact old → new text}
- {specific change 2}

**Session index entry to add:**
\`\`\`json
{exact JSON entry}
\`\`\`

## New Skill Candidates

### {suggested-skill-name}
- **Purpose:** {what it does}
- **Triggers:** {list}
- **Based on:** {what happened in session}
- **Priority:** {Now | Soon | Someday}

## Trigger Updates

### {skill-name}
- **Add trigger:** "{phrase}" — because {reason}

## No Changes Needed
{List any touched skills that are already up to date}
`
})
```

The Opus agent returns the full report as text.

### Step 4: Apply Changes

Using the Opus report, apply each update:

1. **Skill file edits** — Edit each SKILL.md with the specific changes identified
2. **Session index updates** — Append new entries to session index files
3. **Trigger additions** — Add missing triggers to skill frontmatter
4. **New skills** — For candidates marked "Now", present them for approval before creating

**Rules:**
- Apply stale-content fixes and session index updates immediately (low risk, high value)
- Present new skill candidates for user approval before creating
- Never delete content from a SKILL.md — only add or update

### Step 5: Commit and Report

```bash
SESSION_SHORT=$(basename "$LATEST_JSONL" .jsonl | head -c 8)
git add .claude/skills/
git commit -m "upskill: update skills from session $SESSION_SHORT"
git push
```

Present a summary to the user:
- How many skills were scanned
- How many needed updates (and what changed)
- Any new skill candidates (with approval buttons if applicable)

## What This Does NOT Do

- Does not analyze friction or session quality (that's `/reflect`)
- Does not save session state (that's `/pause`)
- Does not create slash commands (that's `/create-skill`)
- Only touches `.claude/skills/` — never modifies commands, SOPs, or memory

## When to Run

- End of any session that involved project-specific work
- After resolving open questions or creating new artifacts
- When you want Claude to proactively identify skill gaps from what just happened
