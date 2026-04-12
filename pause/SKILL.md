---
description: Save session state and generate a return prompt (quick or full mode)
---

# Pause Command

You are helping the user pause their current work session and prepare to return later.

## Mode Detection

**Detect mode from user's message:**
- "quick pause" / "pause quick" / `/pause --quick` → **QUICK MODE**
- "pause" / `/pause` (without "quick") → **FULL MODE**

---

## QUICK MODE (Fast, Local Only)

**When to use:** Short breaks, switching contexts, multiple pauses per day

**Workflow:**
1. **Check for changes:** Run `git status --short` (faster than full status)
2. **Commit locally if needed:** Commit with message "Quick pause: {brief context}"
3. **Skip push:** Don't push to remote (saves time)
4. **Generate minimal prompt:** Just essentials for quick resume

**Quick Prompt Template:**
```
Resume: [one-line task description]
Next: [single next step]
Files: [1-2 key files with paths]
```

**Example Quick Output:**

**Message 1:**
```
Resume: /pause optimization - implementing two-mode support
Next: Test both quick and full modes, measure performance
Files: .claude/commands/pause.md
```

**Message 2:**
Changes committed locally. Use "pause" (full mode) before long breaks to push to remote.

---

## FULL MODE (Detailed, Pushed to Remote)

**When to use:** End of day, long breaks, want complete backup

**Workflow:**
1. **File issues for remaining work:** Create tickets/tasks for anything needing follow-up
2. **Check for uncommitted work:** Run `git status`
3. **Commit and push:** Full git workflow
4. **Generate detailed prompt:** Complete context for thorough resume

**Full Prompt Template:**
```
Resume work on [project/task]. Context:
- Current status: [where they left off]
- Completed: [what's done]
- Next steps: [what to do when returning]
- Files involved: [key files with paths]
- Pending proposals/questions: [anything proposed but not yet responded to — capture VERBATIM, not summarized]
- Conversational tone: [focused? frustrated? brainstorming? debugging? This helps the next session match the user's headspace]

Key Learnings (patterns worth repeating):
1. [First learning - specific pattern or decision that should carry forward]
2. [Second learning - if applicable]
3. [Third learning - if applicable]
```

**When to include Key Learnings:**
- Multi-session projects where patterns emerged
- Decisions that should be remembered (e.g., "always verify before archiving")
- Gotchas or anti-patterns discovered
- Workflow patterns that worked well

**Checkpoint Quality Rules:**

Before finalizing the resume prompt, apply the **Amnesia Test**: read the prompt back and ask yourself — *"If I woke up with ONLY this, could I seamlessly continue the conversation?"* If the answer is no, add more detail.

**Banned content in resume prompts:**
- Vague summaries like "discussed dashboard stuff" or "worked on various things"
- "No active task" / "Idle" without explaining what you're waiting for
- Omitting pending proposals — these are the #1 casualty of session breaks
- Anything you'd be embarrassed to read back after losing all context

**Example Full Output:**

**Message 1:**
```
Resume work on Scripts Cleanup Project. Context:
- Current status: Phase 2 complete, starting Phase 3
- Completed: 59 scripts archived, 11 deleted, documentation updated
- Next steps: Create scripts inventory SOP, update skill-creation-workflow.md
- Files involved: personal-data/projects/system/scripts-cleanup/tasks.md
- Pending proposals/questions: "Should we keep the deprecated webhook-relay.sh as a reference, or archive it with the rest?" — awaiting decision
- Conversational tone: Focused, methodical. Batch-approving archives quickly.

Key Learnings (patterns worth repeating):
1. Verification pattern: Always grep for script references in .claude/, docs/, scripts/ BEFORE archiving
2. Fallback safety: Scripts with command fallbacks are safe to archive - behavior unchanged
3. Documentation drift: Update reference docs immediately when archiving
```

**Message 2:**
All changes committed and pushed. Session ready to resume.

---

## Git Workflow

### Quick Mode
```bash
# Check if there are changes (fast check)
git status --short

# If changes exist, commit locally only
git add .
git commit -m "Quick pause: [brief context from conversation]"

# Skip push in quick mode
```

### Full Mode
```bash
git add <changed-files>
git commit -m "[Detailed commit message]"
git pull --rebase
git push
git status  # MUST show "up to date with origin"
```

**Critical:** Work is NOT complete until `git push` succeeds.

---

## Performance Targets

**Quick Mode:**
- Target: <3 seconds end-to-end
- Skips: git push, detailed context analysis
- Keeps: Local commit, minimal prompt

**Full Mode:**
- Target: <8 seconds end-to-end
- Includes: Full git workflow, detailed prompt
- Safest: Changes pushed to remote

---

## Output Format

**Always follow this structure:**

1. **Generate the resume prompt** (quick or full format)
2. **Wrap in a code block:** Use standard markdown code blocks — the Claude Code UI auto-copies the first code block and shows a copy button
3. **Show status:** Brief message about git operations

**Use this exact format for the resume prompt:**

~~~
```
Resume work on [project/task]. Context:
- Current status: [where they left off]
- Completed: [what's done]
- Next steps: [what to do when returning]
- Files involved: [key files with paths]
- Pending proposals/questions: [verbatim — anything proposed but unanswered]
- Conversational tone: [user's headspace — focused, frustrated, brainstorming, etc.]

Key Learnings (patterns worth repeating):
1. [Learning that should carry forward to next session]
2. [Additional learnings if applicable]
```
~~~

**After the code block, add:** "✅ Resume prompt ready. [git status message]"

---

## Mode Recommendations

**Show mode recommendation in Message 2 when appropriate:**

- If quick mode used 3+ times without full pause → "Consider running full pause to push changes to remote."
- If full mode used in middle of day → "For quick context switches, try 'quick pause' next time."

---

## Natural Language Triggers

These phrases should trigger this command via intent detection (if configured):

- "quick pause" → Quick mode
- "pause quick" → Quick mode
- "pause" → Full mode
- "save my work" → Full mode
- "brb" → Quick mode (be right back)

---

## Example Scenarios

### Scenario 1: Quick Context Switch
**User:** "quick pause"\
**Mode:** QUICK\
**Git:** Commit locally, skip push\
**Prompt:** Minimal (3 lines)\
**Time:** ~2 seconds

### Scenario 2: End of Day
**User:** "pause"\
**Mode:** FULL\
**Git:** Commit + push\
**Prompt:** Detailed (5-7 lines)\
**Time:** ~6 seconds

### Scenario 3: Emergency Context Switch
**User:** "brb"\
**Mode:** QUICK\
**Git:** Commit locally, skip push\
**Prompt:** Minimal\
**Time:** ~2 seconds
