# ccpv Hooks

The original ECC hook runtime is intentionally not copied into this plugin because it includes session persistence, compaction, continuous learning, cost tracking, desktop notifications, and broader process automation.

This plugin keeps only low-intrusion hooks:

- block clearly destructive Bash commands
- remind after stack-relevant edits that backend, frontend, database, Docker, security, and test contracts may need verification

The standard `hooks/hooks.json` is discovered by Claude Code by convention and is not declared in `.claude-plugin/plugin.json`.
