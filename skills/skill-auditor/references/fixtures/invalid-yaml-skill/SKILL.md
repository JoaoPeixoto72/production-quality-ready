---
name: invalid-yaml-skill
description: Audit product X — with a colon-space in the middle: like this. Use for demonstrating a real YAML failure the regex-based checker will miss.
version: 1.0.0
allowed-tools: Read
---

# invalid-yaml-skill

Fixture. The `description:` above contains `: ` (colon + space) inside an
unquoted string. A real `yaml.safe_load` treats it as the start of a nested
key and rejects the frontmatter; a regex-based reader accepts it.

This is the exact defect that shipped in five production plugin
descriptions until §1.b of the linter was added.

Point the linter at this SKILL.md directly and expect a Blocker with reason
"frontmatter is not valid YAML (§1.b)".
