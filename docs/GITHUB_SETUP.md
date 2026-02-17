# 🚀 GitHub Setup & Deployment Guide

Complete guide for uploading this project to GitHub with best security practices.

## ✅ Fast Path (Your Current Status)

Use this when the repository already exists and is empty.

- GitHub repo: `https://github.com/0xwaya/ceo-agent-system.git`
- GitHub login: already configured

```bash
# 1) From project root
cd /Users/pc/code/langraph

# 2) Initialize git only if needed
git init

# 3) Stage and commit
git add .
git commit -m "Initial commit: CEO Agent Executive AI System"

# 4) Ensure main branch
git branch -M main

# 5) Configure remote safely (works whether origin exists or not)
git remote add origin https://github.com/0xwaya/ceo-agent-system.git 2>/dev/null || \
git remote set-url origin https://github.com/0xwaya/ceo-agent-system.git

# 6) First push
git push -u origin main
```

If `git commit` reports "nothing to commit", run `git status` and continue with remote + push.

## Pre-Upload Security Checklist

### ✅ Verify No Sensitive Files

```bash
# Check for .env files (should not exist in repo)
ls -la | grep "\.env$"

# Clean up temporary files
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -delete
rm -f *.log server.log

# Verify .gitignore is comprehensive
cat .gitignore | grep -E "(\.env|secret|credential|key)"
```

### ✅ Review .env.example

Ensure `.env.example` has:

- ✅ Placeholder values only
- ✅ No real API keys
- ✅ Clear comments for each variable

```bash
# Good example in .env.example:
SECRET_KEY=change-this-to-secure-random-string-in-production

# BAD (never do this):
SECRET_KEY=sk-actual-secret-key-xyz123
```

### ✅ Security Files Created

- [x] `LICENSE` - MIT License
- [x] `SECURITY.md` - Security policy
- [x] `CONTRIBUTING.md` - Contribution guidelines
- [x] `.gitignore` - Comprehensive ignore file

## Step 1: Initialize Git Repository

```bash
# Navigate to project
cd /Users/pc/code/langraph

# Initialize git (if not already done)
git init

# Check status
git status
```

## Step 2: Create .gitattributes (Optional)

For better Git handling:

```bash
cat > .gitattributes << EOF
# Auto detect text files and perform LF normalization
* text=auto

# Python files
*.py text eol=lf
*.pyx text eol=lf

# Shell scripts
*.sh text eol=lf
*.bash text eol=lf

# Windows scripts
*.bat text eol=crlf
*.cmd text eol=crlf
*.ps1 text eol=crlf

# Documentation
*.md text
*.txt text
*.rst text

# Binary files
*.png binary
*.jpg binary
*.jpeg binary
*.gif binary
*.ico binary
*.pdf binary
*.zip binary
*.tar.gz binary
EOF
```

## Step 3: Stage and Commit Files

```bash
# Add all files (respecting .gitignore)
git add .

# Verify what will be committed
git status

# IMPORTANT: Verify no .env files are staged!
git status | grep -E "(\.env$|secret|credential|\.key)"

# If any sensitive files appear, remove them:
# git reset HEAD path/to/sensitive/file

# Create initial commit
git commit -m "Initial commit: CEO Agent Executive AI System v2.0

- Multi-agent orchestration system
- Flask backend with SocketIO
- React-based admin dashboard
- Comprehensive logging and validation
- Security best practices implemented
- Documentation and API reference"
```

## Step 4: Create GitHub Repository

> Skip this step if your repository already exists (for you: `0xwaya/ceo-agent-system`).

### Via GitHub Web Interface

1. Go to https://github.com/new
2. Repository name: `ceo-agent-system` (or your preferred name)
3. Description: `🤖 Executive AI System - Multi-agent orchestration platform with CEO/CFO decision-making, admin dashboard, and real-time monitoring`
4. **Visibility**:
   - Public (recommended for portfolio)
   - Private (if containing proprietary logic)
5. **DO NOT** initialize with README (we have one)
6. Click "Create repository"

### Via GitHub CLI (Alternative)

```bash
# Install GitHub CLI if not installed
# macOS: brew install gh
# Windows: winget install gh

# Login
gh auth login

# Create repository
gh repo create ceo-agent-system --public --source=. --remote=origin --description="Executive AI System - Multi-agent orchestration platform"
```

## Step 5: Push to GitHub

```bash
# Add or update remote
git remote add origin https://github.com/0xwaya/ceo-agent-system.git 2>/dev/null || \
git remote set-url origin https://github.com/0xwaya/ceo-agent-system.git

# Set main branch
git branch -M main

# Push to GitHub
git push -u origin main
```

Optional verification:

```bash
git remote -v
git branch --show-current
```

## Step 6: Configure Repository Settings

### Enable Security Features

1. **Settings** → **Security** → **Code security and analysis**
   - ✅ Enable Dependency graph
   - ✅ Enable Dependabot alerts
   - ✅ Enable Dependabot security updates

### Add Topics

Go to **About** section and add topics:

```
ai
multi-agent
langchain
langgraph
flask
socketio
python
ceo
automation
orchestration
executive-ai
```

### Create Branch Protection Rules

**Settings** → **Branches** → **Add rule**

- Branch name pattern: `main`
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date

## Step 7: Add Repository Badges

Edit README.md and add badges at the top:

```markdown
# 👔 CEO Agent - Executive AI System

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green)
![License](https://img.shields.io/badge/license-MIT-blue)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)
![Maintenance](https://img.shields.io/badge/Maintained-Yes-green)
```

## Step 8: GitHub Actions Status

This project already includes a workflow at `.github/workflows/code-quality.yml`.

Current checks include:

- Black formatting check
- Flake8 lint check
- Dashboard smoke rendering check (`tools/smoke_dashboard_render.py`)
- Pytest suite (`pytest -q`)

No additional CI file is required for first upload.

## Step 9: Add .env.example to Repository

Verify `.env.example` is safe:

```bash
# Should be in repository
cat .env.example

# Should NOT be in repository
ls -la | grep "^\.env$"  # Should return nothing
```

## Step 10: Create Release

```bash
# Tag the release
git tag -a v2.0.0 -m "Release v2.0.0 - Production-ready multi-agent system"

# Push tag
git push origin v2.0.0
```

Then on GitHub:
1. Go to **Releases** → **Create a new release**
2. Choose tag: v2.0.0
3. Release title: `v2.0.0 - Production Release`
4. Add release notes

## Ongoing Maintenance

### Before Each Commit

```bash
# Always check for sensitive files
git status | grep -iE "(secret|credential|key|\.env$)"

# Use git diff to review changes
git diff

# Commit with descriptive message
git commit -m "feat(agents): add new marketing capabilities"
git push
```

### Regular Security Audits

```bash
# Update dependencies
pip install --upgrade pip
pip-review --auto  # or pip install pip-review

# Security audit
pip install safety
safety check

# Update requirements
pip freeze > requirements.txt
```

### Keep Documentation Updated

- Update README.md for new features
- Update CHANGELOG.md for each release
- Update ARCHITECTURE.md for structural changes

## Troubleshooting

### Accidentally Committed .env file

```bash
# Remove from git but keep locally
git rm --cached .env

# Commit the removal
git commit -m "chore: remove .env from version control"

# Push
git push

# Important: Consider .env data compromised
# Rotate all API keys and secrets immediately!
```

### Large Files Issue

```bash
# GitHub has 100MB file limit
# Check file sizes
find . -type f -size +50M

# Use Git LFS for large files
git lfs install
git lfs track "*.csv"
git lfs track "data/*"
```

### Fix Commit History (Advanced)

```bash
# Rewrite history to remove sensitive file
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch path/to/sensitive/file" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: rewrites history)
git push origin --force --all
```

## Security Best Practices Summary

✅ **DO:**
- Use `.env.example` with placeholders
- Keep `.env` in `.gitignore`
- Rotate secrets if accidentally committed
- Enable GitHub security features
- Review all commits before pushing
- Use branch protection rules

❌ **DON'T:**
- Commit API keys or secrets
- Push `.env` files
- Hard-code credentials in code
- Ignore security warnings
- Skip code reviews
- Disable .gitignore

## Support

If you have questions:
- Open an issue on GitHub
- Check CONTRIBUTING.md
- Review SECURITY.md

---

**Ready to upload? Run through the checklist above, then follow Steps 1-10!**
