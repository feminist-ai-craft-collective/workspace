# Contributing to the Collective

Welcome! This guide is for everyone, regardless of technical background.

---

## The Golden Rules

1. **Work in your own folder** — `projects/[your-name]/` is your space
2. **Pull before you push** — always get the latest changes first
3. **No secrets** — never commit passwords, API keys, or private data
4. **Ask in Discussions** — when in doubt, ask before changing shared files

---

## Your Daily Workflow

### Starting your session

```bash
cd feminist-ai-craft-collective
git pull
```

This grabs any changes others have made.

### When you're done working

```bash
git add .
git commit -m "Brief description of what you did"
git push
```

That's it! Your changes are now shared.

---

## What Goes Where

| Folder | What belongs there | Who can edit |
|--------|-------------------|--------------|
| `projects/[your-name]/` | Your experiments, contexts, work-in-progress | You |
| `shared/contexts/` | Prompts useful to everyone | Anyone (discuss first) |
| `shared/skills/` | Reusable SKILL.md files | Anyone (discuss first) |
| `docs/` | Guides and documentation | Anyone (discuss first) |

---

## Before You Commit

Run through the [secrets checklist](ops/secrets-check.md):

- [ ] No API keys?
- [ ] No passwords?
- [ ] No private file paths?
- [ ] No files over 10MB?

---

## Need Help?

- **Confused about Git?** See [Git for Humans](docs/git-for-humans.md)
- **Question about Claude?** See [Claude Code Basics](docs/claude-code-basics.md)
- **Stuck?** Post in GitHub Discussions — we're all learning together

---

*Learn by doing and do better.*
