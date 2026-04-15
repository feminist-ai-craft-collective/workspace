# Git for Humans

Git can feel intimidating, but you only need to know a handful of commands for our workflow. Think of it like a shared Dropbox that tracks every change.

---

## The Mental Model

Imagine a shared notebook:
- **Repository (repo)** = the whole notebook
- **Clone** = making your own copy to write in
- **Pull** = getting pages others have added
- **Commit** = stapling your new pages together with a note
- **Push** = putting your pages back in the shared notebook

---

## The Only Commands You Need

### First time setup (do once)

```bash
# Tell Git who you are
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Get the repo
git clone https://github.com/feminist-ai-craft-collective/feminist-ai-craft-collective.git
```

### Every time you start working

```bash
cd feminist-ai-craft-collective
git pull
```

This gets any changes others made since your last session.

### When you're done working

```bash
git add .
git commit -m "Describe what you did"
git push
```

That's it. Three commands.

---

## What Those Commands Actually Do

| Command | What it does |
|---------|-------------|
| `git pull` | Downloads changes from GitHub to your computer |
| `git add .` | Stages all your changes (the `.` means "everything") |
| `git commit -m "message"` | Saves your staged changes with a description |
| `git push` | Uploads your commits to GitHub |

---

## Helpful Commands

```bash
# See what files you've changed
git status

# See the history of changes
git log --oneline

# Undo changes to a file (before committing)
git checkout -- filename

# See what's different
git diff
```

---

## Common Problems and Fixes

### "I got an error when I tried to push"

Usually means someone else pushed changes. Fix:
```bash
git pull
# If there's a conflict, ask for help in Discussions
git push
```

### "I accidentally edited a file I shouldn't have"

```bash
git checkout -- path/to/file
```

### "I want to undo my last commit"

```bash
git reset --soft HEAD~1
```
Your changes are still there, just uncommitted.

### "Everything is broken and I want to start over"

Nuclear option — re-clone:
```bash
cd ..
rm -rf feminist-ai-craft-collective
git clone https://github.com/feminist-ai-craft-collective/feminist-ai-craft-collective.git
```

---

## Golden Rules

1. **Pull before you push** — always
2. **Commit often** — small, frequent commits are easier to understand
3. **Write clear messages** — "Updated my context file" is better than "stuff"
4. **Ask for help** — we're all learning

---

## Glossary

- **Repository (repo)**: The project folder and all its history
- **Clone**: Copy a repo to your computer
- **Commit**: A saved snapshot of changes
- **Push**: Send your commits to GitHub
- **Pull**: Get commits from GitHub
- **Branch**: A parallel version (we mostly just use `main`)
- **Merge conflict**: When two people edited the same lines (rare if you stay in your folder)

---

*You don't need to understand Git deeply. You just need to pull, commit, push.*
