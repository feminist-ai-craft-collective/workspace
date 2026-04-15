# Shared Skills

Reusable SKILL.md files that define capabilities Claude can use across projects.

---

## What's a Skill?

A skill is a structured file that teaches Claude how to do something specific — like a recipe. It includes:
- When to use this skill
- What inputs it needs
- Step-by-step instructions
- Examples

---

## How to Use

Reference a skill in your CLAUDE.md:
```markdown
## Skills Available
- Lesson planning: `../../shared/skills/lesson-planning/SKILL.md`
```

Or copy the skill folder to your project and customize.

---

## How to Contribute

1. Build and test the skill in your project first
2. Document it clearly — someone else should be able to use it
3. Post in Discussions to share
4. Add it here when it's ready

---

## Skill Structure

```
skill-name/
├── SKILL.md       # The main skill definition
├── examples/      # Example inputs and outputs
└── README.md      # Human-readable explanation
```

---

*This folder is empty to start — your skills will fill it.*
