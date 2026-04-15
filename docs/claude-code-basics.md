# Claude Code Basics

How Claude Code works with our collective's repository structure.

---

## What is Claude Code?

Claude Code is a way to work with Claude directly in your project folder. Instead of copy-pasting context into a chat window, Claude reads files from your folder and understands your project automatically.

---

## How It Works With Our Repo

When you open Claude Code in your project folder (`projects/[your-name]/`), Claude:

1. **Reads your `CLAUDE.md`** — this is your persistent context
2. **Sees your files** — everything in your folder is accessible
3. **Can create and edit files** — Claude can write code, documents, whatever you need
4. **Remembers the session** — within a session, Claude has continuity

---

## The CLAUDE.md File

This is the most important file in your project folder. It tells Claude:
- Who you are
- What you're working on
- How you like to work
- Any specific instructions or preferences

### Example CLAUDE.md

```markdown
# My Claude Context

## About Me
Robin, educator and AI enthusiast. Part of the Feminist AI Craft Collective.

## Current Project
Exploring how to use Claude for lesson planning in adult education.

## How I Work
- I prefer explanations before code
- I learn best with examples
- Please check my understanding before moving on

## Values
- Accessibility matters
- Plain language over jargon
- Process over perfection

## Current Goals
- [ ] Create a reusable lesson plan template
- [ ] Build a skill for generating discussion questions
- [ ] Document what I learn for the collective
```

---

## Working With Claude Code

### Starting a session

1. Open your terminal
2. Navigate to your project folder:
   ```bash
   cd feminist-ai-craft-collective/projects/[your-name]
   ```
3. Launch Claude Code (method depends on your setup)

### During a session

- Ask Claude questions about your files
- Have Claude create new files
- Iterate on ideas together
- Claude can read anything in your folder

### Ending a session

- Important context should go in `CLAUDE.md`
- Working files stay in `workspace/`
- Reusable context goes in `context/`

---

## Your Folder Structure

```
projects/[your-name]/
├── CLAUDE.md          # Your persistent context (Claude reads this first)
├── context/           # Additional context files
│   ├── background.md  # Deeper background info
│   └── preferences.md # Detailed preferences
└── workspace/         # Your working files
    ├── experiments/   # Things you're trying
    └── outputs/       # Things Claude created
```

---

## Tips for Good CLAUDE.md Files

### Do:
- Update it as your focus changes
- Include your current goals
- Mention your preferences and values
- Add relevant background

### Don't:
- Put secrets or API keys
- Make it too long (1-2 pages max)
- Include things that change every session

---

## Using Shared Resources

The collective maintains shared contexts and skills in the `shared/` folder:

```
shared/
├── contexts/     # Prompts and personas anyone can use
├── skills/       # Reusable SKILL.md files
└── templates/    # Starter files
```

You can reference these in your CLAUDE.md:
```markdown
## Resources I Use
- See `../../shared/contexts/thoughtful-educator.md` for my base persona
```

Or copy them into your own folder to customize.

---

## Sharing What You Learn

When you create something useful:

1. **Keep it in your folder first** — test and refine
2. **Consider sharing** — could others use this?
3. **Post in Discussions** — describe what you made
4. **Move to shared/** — if others want it, add it to the collective resources

---

## Troubleshooting

### Claude doesn't seem to know my context
- Make sure you're in the right folder
- Check that CLAUDE.md exists and isn't empty
- Try explicitly asking Claude to read your CLAUDE.md

### Claude made a file I didn't want
- Just delete it: `rm filename`
- Or ask Claude to delete it

### I want Claude to forget something
- Remove it from CLAUDE.md
- Start a new session

---

*Claude Code turns your project folder into a collaborative workspace. Your CLAUDE.md is the handshake.*
