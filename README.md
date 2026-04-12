# Claude Skills

A curated collection of Claude Code skills for professional AI-assisted workflows.

These are battle-tested skills from a real production setup. Each one is a reusable prompt with full tool access — copy it into your project and it becomes a `/command` in any Claude Code session.

## What's a Skill?

Skills are markdown files that live in `.claude/skills/<name>/SKILL.md` (or `.claude/commands/<name>.md` for simpler setups). They act as reusable, parameterized prompts with access to all Claude Code tools. Drop one in and invoke it with `/name`.

## Skills

| Skill | Description |
|-------|-------------|
| [/reflect](./reflect/) | Session retrospective — find friction, capture learnings, auto-implement quick wins |
| [/pause](./pause/) | Save session state and generate a return prompt (quick or full mode) |

## Installation

Each skill lives in its own directory. Copy the folder into your project:

```bash
# As a skill (recommended)
cp -r reflect /your-project/.claude/skills/reflect

# Or as a simple command
cp reflect/SKILL.md /your-project/.claude/commands/reflect.md
```

Then invoke it in Claude Code with `/reflect`.

## Customization

Each `SKILL.md` has placeholder values (marked with `<angle-brackets>`) for paths and project-specific config. Replace these before using.

## More

More skills added as they're polished and generalized. Built by [@alexknowshtml](https://github.com/alexknowshtml).
