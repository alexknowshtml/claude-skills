# /publish-oss — Publish an Internal Tool as Open Source

Interactive checklist for publishing an internal tool, adapter, or script to GitHub and npm cleanly — scanning for private references, building dist, and publishing with token auth.

## When to Use

- User wants to open-source a script, adapter, or package from a monorepo
- User says "publish this as OSS", "put this on npm", "open source this", "create a public package"

## What It Does

1. **Scan for private references** — find internal tool names, private packages, and internal URLs
2. **Identify replacements** — map private tools to their public equivalents and flag for user review
3. **Verify public docs** — confirm every CLI tool referenced in docs is publicly installable
4. **Ensure GitHub repo** — check if standalone repo exists; create it if not
5. **Build dist** — run the build step and verify dist/ is present
6. **Bump version** — increment patch version correctly for monorepo context
7. **Publish to npm** — use granular access token (no login required)
8. **Sync monorepo** — copy back to monorepo if publishing from standalone repo, or push standalone from monorepo
9. **Commit and push** — both repos

## Private Reference Patterns to Scan

These patterns indicate internal-only tools that public users cannot access:

```bash
# Scan command — run from the package directory
# Customize these patterns to match your own private tool names
grep -rn \
  -e "localhost:[0-9]" \
  -e "your-internal-tool" \
  -e "your-org-internal" \
  -e "/home/yourname" \
  README* CONTRIBUTING* docs/ *.md 2>/dev/null
```

**Common replacements:**
| Private | Public replacement |
|---------|-------------------|
| Internal CLI wrappers | Public npm package equivalent |
| Internal API endpoints | Document the env var approach instead |
| Internal localhost URLs | Remove entirely — internal only |
| Hardcoded home paths | Use `~` or env vars |

## Step-by-Step Execution

### Step 1 — Identify the package

Ask for the package path if not provided. Confirm:
- Package name and version from `package.json`
- Whether a standalone GitHub repo already exists
- Target npm scope (scoped `@user/pkg` or unscoped `my-package`)

### Step 2 — Scan for private references

Run the grep scan above (customized for your private patterns). For each match:
- Show the file, line number, and matched text
- Propose the public replacement
- Ask for confirmation before making changes

### Step 3 — Fix private references

Apply agreed replacements. Re-run scan to confirm clean.

### Step 4 — Verify publicly installable tools in docs

Extract all CLI commands from README/CONTRIBUTING:
```bash
grep -oP '`[a-z][a-z-]+\s' README.md | sort -u
```

For each CLI tool found, confirm it can be installed from npm/homebrew/public source. Flag any that are internal.

### Step 5 — GitHub repo

Check if standalone repo exists:
```bash
gh repo view <your-github-username>/<repo-name> 2>&1 | head -3
```

If missing, create:
```bash
gh repo create <your-github-username>/<repo-name> \
  --public \
  --description "Description here" \
  --clone=false
cd <package-dir>
git remote add standalone git@github.com:<your-github-username>/<repo-name>.git
git subtree push --prefix=<monorepo-path> standalone main
```

If exists, push latest:
```bash
git subtree push --prefix=<monorepo-path> standalone main
# OR if standalone was the source: git push standalone main
```

### Step 6 — Build dist

```bash
cd <package-dir>
bun run build  # or tsc --outDir dist
ls dist/       # verify dist exists and is non-empty
```

### Step 7 — Bump version

**Always use `--no-git-tag-version` in a monorepo:**
```bash
cd <package-dir>
npm version patch --no-git-tag-version
# Then manually commit:
git add package.json
git commit -m "bump <package-name> to $(jq -r .version package.json)"
```

### Step 8 — Publish to npm

**Credential check first:**
```bash
npm whoami 2>/dev/null || echo "NOT LOGGED IN"
```

If not logged in, fetch the granular access token:
```bash
# Check if token is already in npmrc
cat ~/.npmrc 2>/dev/null | grep registry.npmjs.org

# If missing, user needs to generate one:
# npmjs.com → Profile → Access Tokens → Generate New Token → Granular Access Token
# Then: npm set //registry.npmjs.org/:_authToken=npm_YOUR_TOKEN
```

Publish:
```bash
cd <package-dir>
npm publish --access public
```

### Step 9 — Sync and push

```bash
# Add to git, commit, push monorepo
git add <package-dir>
git commit -m "chore: publish <package-name> v<version> to npm"
git push origin main

# Sync standalone repo
git subtree push --prefix=<monorepo-path> standalone main
```

### Step 10 — Verify

```bash
# Check npm page is live
curl -s https://registry.npmjs.org/<package-name>/latest | jq '{name, version, description}'

# Check GitHub
gh repo view <your-github-username>/<repo-name> --json name,description,url
```

Return both URLs to the user.

## After Publishing

Always return:
- **npm:** `https://www.npmjs.com/package/<package-name>`
- **GitHub:** `https://github.com/<your-github-username>/<repo-name>`
- **Install command:** `npm install <package-name>`

## Common Gotchas

- `npm version patch` fails on dirty working tree → always use `--no-git-tag-version`
- npm login doesn't work on headless server → use granular access token
- `bun install` not `npm install` for monorepo subdirectory packages
- `npm publish` with passkey 2FA → granular token bypasses this entirely
- git subtree push fails if standalone repo has commits not in monorepo → use `git subtree push --prefix=... standalone main --squash` as fallback
