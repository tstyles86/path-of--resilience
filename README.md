# Path of Resilience

The Path of Resilience — Travis coaching and booking website.

## Claude Code Skills

This repository includes custom [Claude Code skills](https://docs.anthropic.com/en/docs/claude-code/skills) for working on the site.

### Installation

**macOS / Linux**
```bash
cp -r skills/* ~/.claude/skills/
```

**Windows (PowerShell)**
```powershell
Copy-Item -Recurse skills\* $env:USERPROFILE\.claude\skills\
```

### Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| Site Review | `/site-review` | Audit all pages for content, UX, links, accessibility, and performance |
| Update Copy | `/update-copy <section>` | Rewrite or refine website copy to match the brand voice |
| Add Section | `/add-section <description>` | Scaffold a new HTML section using the existing navy/gold design system |
