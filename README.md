# Claude Skills

A curated collection of Claude Code slash commands for professional AI-assisted workflows.

These are battle-tested commands from a real production setup. Each one is designed to be copied into your own `.claude/commands/` directory and customized for your environment.

## What's a Claude Skill?

Claude Code supports custom slash commands — markdown files in `.claude/commands/` that act as reusable prompts with full tool access. Drop one in, and `/command-name` becomes available in any session.

## Skills

| Skill | Description |
|-------|-------------|
| [/reflect](./reflect.md) | Session retrospective — find friction, capture learnings, auto-implement quick wins |
| [/pause](./pause.md) | Save session state and generate a return prompt (quick or full mode) |

## Installation

Copy any skill file into your project's `.claude/commands/` directory:

```bash
cp reflect.md /your-project/.claude/commands/reflect.md
```

Then invoke it in Claude Code with `/reflect`.

## Customization

Each skill has a `## Configuration` section at the top. Replace the placeholder values with your own paths and preferences before using.

## More

More skills added as they're polished and generalized. Built by [@alexknowshtml](https://github.com/alexknowshtml).
