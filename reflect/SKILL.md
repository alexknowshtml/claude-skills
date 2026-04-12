---
description: Session retrospective - analyze what happened, find friction, auto-implement quick wins, publish report
---

You are performing a session retrospective to extract learnings and suggest system improvements.

**This is NOT `/eod` or `/pause`.** Those handle day-ending and session-saving mechanics. `/reflect` is a learning loop that analyzes the current session for ways to improve your Claude Code setup itself.

## What This Does

1. Reads the current session transcript
2. Identifies friction points, struggles, workarounds, repeated patterns, and discoveries
3. Produces a report with specific, actionable improvement suggestions
4. Auto-implements quick wins (memory updates, one-liner SOP additions) with your approval
5. Presents the full report in readable format

## Architecture: Opus Subagent Delegation

The analysis phase (Step 2) runs on **Opus** via a subagent for better pattern recognition, deeper synthesis, and sharper memory drafts. The main session (any model) handles transcript loading (Step 1) and implementation (Steps 3-4).

```
Main session (Sonnet):  Load transcripts → delegate to Opus → implement quick wins → publish
Opus subagent:          Analyze patterns → check overlap → generate report
```

## Execution

**IMPORTANT:** Execute immediately. No acknowledgment, no explaining what you're about to do.

---

### Step 1: Load Session Transcript

Get the current session transcript from disk.

```bash
# Update this path to match your Claude Code project directory
# Claude Code stores sessions in ~/.claude/projects/<project-slug>/
SESSION_DIR="$HOME/.claude/projects/<your-project-slug>"

# Find the main session (most recently modified)
LATEST_JSONL=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | head -1)
echo "Main session: $LATEST_JSONL"
wc -l "$LATEST_JSONL"
```

Read the session file, extracting user messages and assistant text (skip raw tool results):

```bash
extract_session() {
  local FILE="$1"
  echo "=== $(basename $FILE) ==="
  # User messages
  jq -r 'select(.type == "user") | select(.message.content | type == "string") | "USER: " + .message.content' "$FILE" 2>/dev/null
  # Assistant text blocks only
  jq -r 'select(.type == "assistant") | .message.content[]? | select(.type == "text") | "ASSISTANT: " + .text' "$FILE" 2>/dev/null
}

extract_session "$LATEST_JSONL"
```

**If a JSONL is very large (1000+ lines),** focus on:
- All user messages (these are the primary signal)
- Assistant text that contains reasoning, decisions, or corrections
- Tool use results that show errors or retries

---

### Step 2: Spawn Opus Subagent for Analysis

Delegate the heavy analysis work to an Opus subagent. Pass it:
1. The extracted transcript content from Step 1
2. The analysis framework (categories, dedup rules, report template)
3. Existing system context (commands, skills, memory files)

**Before spawning**, gather the overlap context the agent will need:

```bash
# Existing commands
ls .claude/commands/*.md 2>/dev/null | head -30
# Existing skills (if using skill directories)
ls .claude/skills/*/SKILL.md 2>/dev/null | head -30
# Memory files (if using auto-memory)
ls ~/.claude/projects/<your-project-slug>/memory/ 2>/dev/null
```

**Spawn the Agent** with `model: "opus"` and `subagent_type: "general-purpose"`:

```
Agent({
  description: "Opus reflect analysis",
  model: "opus",
  prompt: `You are performing a session retrospective analysis. Your job is to analyze transcripts, identify patterns and friction, and produce a structured improvement report.

DO NOT implement any changes. DO NOT write any files. Only produce the report as text output.

## Transcript Data
{paste extracted user messages and assistant text from Step 1}

## Existing System Context
Commands: {list}
Skills: {list}
Memory files: {list}

## Analysis Framework

Review the transcripts looking for these categories. DEDUP RULE: Each issue belongs in exactly one section — the most relevant one.

### A. Friction Points
- Tool failures or retries
- Wrong approaches that had to be corrected
- Missing information that required extra lookups
- Commands or skills that didn't exist but should have
- Manual steps that could be automated

### B. Struggles and Corrections
- Misunderstandings of intent
- Wrong file paths or API usage
- Incorrect assumptions
- "No, I meant..." moments

### C. Repeated Patterns
- Similar queries run in different contexts
- Workflows that follow the same structure
- Lookups that could be cached

### D. Discoveries
- How a system actually works vs. assumption
- New capabilities found
- Edge cases or gotchas

### E. Skill/Command Gaps
- Requests that required long ad-hoc workflows
- Multi-step processes that could be a /command

### F. Documentation Gaps
- Outdated or incomplete SOPs
- Missing cross-references
- Tribal knowledge that should be written down

## Report Template

Produce the report in EXACTLY this format:

# Session Retrospective - {DATE}

**Session focus:** {1-sentence summary}\
**Duration:** {approximate}\
**Key files touched:** {list}

---

## Friction Points Found

### {Friction Point 1}
- **What happened:** {Specific description}
- **Impact:** {How much time/effort was wasted}
- **Suggested fix:** {Concrete improvement}
- **Type:** {memory | skill | command | sop | agent | code}
- **Breaking change?** {Yes/No}
- **Effort:** {Small | Medium | Large}
- **Auto-implement?** {Yes — memory/sop update | No — needs review}

---

## Corrections Made (Learning Opportunities)

### {Correction 1}
- **User said:** "{Quote or paraphrase}"
- **What was wrong:** {What was incorrect}
- **Root cause:** {Why}
- **Prevention:** {How to avoid}
- **Type:** {memory | sop | skill | prompt-update}
- **Auto-implement?** {Yes | No}

---

## New Patterns Worth Capturing

### {Pattern 1}
- **Pattern:** {Description}
- **Frequency this session:** {count}
- **Suggested action:** {Add to memory | Create skill | Update SOP | Create command}
- **Draft content:** {Exact text/code to add}
- **Auto-implement?** {Yes | No}

---

## Skill/Command Suggestions

### {Suggestion 1}: /command-name
- **Trigger:** {When invoked}
- **What it does:** {Brief description}
- **Based on:** {Session evidence}
- **Effort:** {Small | Medium | Large}
- **Priority:** {Should exist now | Nice to have | Someday}

---

## Memory Updates

### {Memory 1}
- **File:** {filename.md}
- **Content:** {Exact frontmatter + body to write}
- **Replaces:** {Existing entry, if any}
- **Auto-implement?** Yes

---

## Documentation Gaps

### {Gap 1}
- **What's missing:** {Description}
- **Where it should go:** {File path}
- **Draft content:** {Content}
- **Auto-implement?** {Yes | No}

---

## Summary

**COUNTING RULE:** Count distinct actionable items only. A memory that fixes a friction point is ONE item. Auto-implemented + Needs approval must sum to total.

**Total actionable improvements:** {count} ({count} auto-implemented + {count} needs approval)

Breakdown by type:
- Memory/SOP updates: {count} (auto-implemented)
- New skills/commands: {count} (needs approval if non-trivial)
- Documentation fixes: {count}

**Top 3 highest-impact improvements:**
1. {Most impactful}
2. {Second}
3. {Third}
`
})
```

The Opus agent returns the full report as text. Save it to a variable for the next steps.

---

### Step 3: Auto-Implement Quick Wins

Using the Opus agent's report, implement any items marked `Auto-implement? Yes`:
- Memory file additions or updates (no breaking changes, purely additive)
- One-liner SOP additions (appending a note to an existing file)
- Fixing an obviously wrong reference in a doc

**Rules for auto-implementation:**
- Only implement if confidence is high (the need is unambiguous from the transcript)
- Write the change, then append it to the "Quick Wins Auto-Implemented" section of the report
- Do NOT auto-implement: new skills, new commands, changes to core system files, anything that could break existing behavior

For each auto-implemented item, apply the change and note it in the report.

---

### Step 4: Save Report + Present Summary

1. **Save the full report** to a retrospectives or insights directory:
   ```bash
   DATE=$(date +"%Y-%m-%d")
   SESSION_SHORT=$(basename "$LATEST_JSONL" .jsonl | cut -c1-8)
   TOPIC_SLUG="<1-3-word-description>"  # e.g. "email-triage", "auth-refactor"
   OUTFILE="personal-data/insights/${DATE}-${SESSION_SHORT}-${TOPIC_SLUG}.md"
   ```

2. **Present the report** — render as markdown, open in browser, or use your preferred viewer.

3. **Show a summary** with:
   - What the session accomplished
   - How many improvements found
   - What was auto-implemented
   - What needs approval

---

## What This Command Does NOT Do

- Does not commit or push (that's `/pause` or manual)
- Does not update task status (that's `/eod`)
- Does not save session state for resumption (that's `/pause`)
- Does not auto-implement anything with breaking changes or meaningful risk

## Guidelines

- **Be honest about struggles.** The point is to learn, not to look good.
- **Be specific.** "Improve error handling" is useless. "Add retry logic to Gmail API calls because it failed 3 times this session" is useful.
- **Prioritize by impact.** A fix that prevents daily friction matters more than a nice-to-have.
- **Draft actual content.** Don't say "add a memory entry about X" — write the exact entry.
- **Check for existing solutions first.** The system is large. Something might already exist.
- **Non-breaking by default.** If a change could break existing behavior, explicitly call it out and describe the migration path.
- **Minimum viable report.** If the session was straightforward with no friction, say so. Don't invent problems. A report that says "Clean session, no improvements needed" is a valid outcome.
