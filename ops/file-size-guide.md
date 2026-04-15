# File Size Guide

Git is designed for code and text, not large files. Here's how to keep the repo healthy.

---

## Size Limits

| Size | Guidance |
|------|----------|
| < 1 MB | ✅ Perfect, commit freely |
| 1-10 MB | ⚠️ Think twice — is it necessary? |
| 10-50 MB | ❌ Avoid — find an alternative |
| 50+ MB | 🚫 GitHub will warn or block |
| 100+ MB | 🚫 GitHub will reject the push |

---

## What Belongs in Git

✅ **Yes:**
- Markdown files (`.md`)
- Text files (`.txt`)
- Small config files (`.json`, `.yaml`)
- Small scripts (`.py`, `.sh`, `.js`)
- Small images for documentation (< 500 KB)

❌ **No:**
- Video files
- Audio files
- Large images
- Datasets (`.csv` over 1 MB)
- Database files
- Archives (`.zip`, `.tar`)
- Model weights

---

## Check Before You Commit

Find large files in your folder:
```bash
find . -size +1M -type f
```

See what's staged and how big:
```bash
git status
ls -lh path/to/file
```

---

## Alternatives for Large Files

### Images
- Compress them first (tools: TinyPNG, ImageOptim)
- Resize to what you actually need
- Link to external hosting if decorative

### Datasets
- Host on Google Drive, Dropbox, or Hugging Face
- Include a link in your README
- Include a small sample in the repo

### Videos
- Host on YouTube (unlisted), Vimeo, or Loom
- Link in your documentation

### Large outputs
- Keep them local in a folder named `private/` (auto-ignored)
- Share via other means if needed

---

## If the Repo Gets Bloated

Signs of trouble:
- `git clone` takes a long time
- Your `.git` folder is huge
- GitHub shows warnings

Recovery is painful — prevention is easier. Ask in Discussions if you need help.

---

*Text is tiny. Everything else adds up fast.*
