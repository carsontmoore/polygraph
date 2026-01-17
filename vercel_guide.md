# Vercel Deployment Guide & Gotchas

A running list of Vercel-specific concepts, configuration, and lessons learned while deploying Polygraph.

---

## Core Concepts

### How Vercel Deployment Works

```
Your Repo → Vercel pulls code → Runs build → Serves output
                                    ↓
                            Needs to know:
                            1. Where is the code? (Root Directory)
                            2. What framework? (Framework Preset)
                            3. How to build? (Build Command)
                            4. Where's the output? (Output Directory)
```

### Framework Presets

Vercel has built-in presets for common frameworks. Each preset knows:
- What build command to run
- Where output files go
- How to serve the app

| Framework | Build Command | Output Directory |
|-----------|---------------|------------------|
| Next.js | `npm run build` | `.next` |
| React (CRA) | `npm run build` | `build` |
| Static/HTML | (none) | `public` |
| Vue | `npm run build` | `dist` |

**Key lesson:** If Vercel guesses the wrong framework, it looks for output in the wrong place → 404 errors.

---

## Project Configuration

### Root Directory

When your frontend code isn't at the repo root:

```
polygraph/              ← Repo root
├── backend/            ← Python API
├── frontend/           ← Next.js app (this is what Vercel needs)
│   ├── package.json
│   ├── src/
│   └── ...
└── README.md
```

**Setting:** Settings → General (or Git) → Root Directory → `frontend`

Without this, Vercel tries to build from repo root, can't find `package.json`, and fails.

---

### Build & Development Settings

Location: Settings → Build & Development Settings

| Setting | What It Does | Next.js Value |
|---------|--------------|---------------|
| Framework Preset | Tells Vercel how to build/serve | **Next.js** |
| Build Command | Command to compile your app | `npm run build` (or blank) |
| Output Directory | Where build artifacts go | Leave blank (preset knows) |
| Install Command | How to install dependencies | `npm install` (or blank) |

**Key lesson:** Explicitly select the Framework Preset rather than relying on auto-detection.

---

### Environment Variables

Location: Settings → Environment Variables

Variables are injected at build time. For Next.js:
- `NEXT_PUBLIC_*` variables are exposed to the browser
- Other variables are server-side only

```
NEXT_PUBLIC_API_URL=https://your-api.railway.app
```

**Key lesson:** After adding/changing env vars, you must redeploy for changes to take effect.

---

## Common Errors & Fixes

### Error: "No output directory named public found"

**Cause:** Vercel thinks it's a static site, looking for `public/` folder
**Fix:** Set Framework Preset to "Next.js" explicitly

### Error: 404 on deployed site

**Possible causes:**
1. Wrong Root Directory (not pointing to frontend code)
2. Wrong Framework Preset (looking for wrong output folder)
3. Build failed silently (check deployment logs)

### Error: API calls failing on deployed site

**Cause:** Frontend is calling `localhost:8000` which doesn't exist in production
**Fix:** Set `NEXT_PUBLIC_API_URL` environment variable to your deployed backend URL

---

## Deployment Checklist

Before deploying a monorepo (frontend + backend together):

- [ ] Set Root Directory to frontend folder path
- [ ] Select correct Framework Preset (Next.js)
- [ ] Add environment variables (especially API URL)
- [ ] Verify build command is correct
- [ ] Check deployment logs if something fails

---

## Vercel CLI (Alternative to Dashboard)

You can also deploy via command line:

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy from frontend directory
cd frontend
vercel

# Follow prompts - it asks for settings interactively
```

Sometimes easier than navigating the dashboard UI.

---

## Useful Links

- [Vercel Next.js Documentation](https://vercel.com/docs/frameworks/nextjs)
- [Environment Variables](https://vercel.com/docs/environment-variables)
- [Monorepo Configuration](https://vercel.com/docs/monorepos)
- [Build & Development Settings](https://vercel.com/docs/projects/project-configuration)

---

*This document is updated as new deployment lessons are learned.*