# Getting Started

Welcome to the Feminist AI Craft Collective! This guide will help you set up your workspace and start collaborating.

---

## Step 1: Get the Repository

### If you don't have Git installed

**Mac:** Open Terminal and type `git --version`. If it's not installed, you'll be prompted to install it.

**Windows:** Download [Git for Windows](https://git-scm.com/download/win) and install with default options.

### Clone the repo

```bash
cd ~/Documents  # or wherever you keep projects
git clone https://github.com/feminist-ai-craft-collective/feminist-ai-craft-collective.git
cd feminist-ai-craft-collective
```

---

## Step 2: Create Your Project Folder

```bash
mkdir -p projects/[your-name]
mkdir -p projects/[your-name]/context
mkdir -p projects/[your-name]/workspace
touch projects/[your-name]/CLAUDE.md
```

Replace `[your-name]` with your identifier (e.g., your first name or username).

---

## Step 3: Set Up Your CLAUDE.md

This file tells Claude who you are and what you're working on when you open Claude Code in your folder.

Open `projects/[your-name]/CLAUDE.md` and add something like:

```markdown
# Project Context

## Who I Am
[Your name], member of the Feminist AI Craft Collective.

## What I'm Working On
[Describe your current focus or experiment]

## My Preferences
- [How you like Claude to communicate]
- [Any specific approaches or values]

## Current Goals
- [ ] [Goal 1]
- [ ] [Goal 2]
```

---

## Step 4: Open Claude Code

1. Open Claude Code (desktop app or CLI)
2. Navigate to your project folder: `projects/[your-name]/`
3. Claude will automatically read your `CLAUDE.md` for context

---

## Step 5: Push Your Changes

Once you've created your folder:

```bash
git add .
git commit -m "Add project folder for [your-name]"
git push
```

---

## You're Ready!

- Work in your `projects/[your-name]/` folder freely
- Pull before each session: `git pull`
- Push when you're done: `git add . && git commit -m "message" && git push`
- Ask questions in GitHub Discussions

---

## Next Steps

- Read [Claude Code Basics](claude-code-basics.md) to understand the workflow
- Check out `shared/` for collective resources
- Introduce yourself in Discussions!

---

*Learn by doing and do better.*
