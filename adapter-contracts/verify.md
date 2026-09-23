# adapter-contract — verify

Contract a local `verify` adapter must provide.

## Required frontmatter

```yaml
---
name: <local-name>                        # not the plugin skill's name (POLICY §3.2)
extends: production-quality-ready:verify
contract: production-quality-ready/CONTRACTS.md
allowed-tools: Read, Glob, Grep, Bash
---
```

## Required body sections

1. **Launch the app** — concrete command, with a check that the binary
   is newer than the sources.
2. **Path of output artifacts** — where the app writes.
3. **Specific traps** — cross-reference `drive-app-window` for
   Win32/WebView2; the adapter writes only this project's traps.
4. **Pilot projects** — small projects opened quickly for smoke tests.

## What the adapter does NOT

- Write the window harness — that's `drive-app-window`.
- Write what to semantically verify — that's the universal `verify`
  rule + the owners of the audited themes.
