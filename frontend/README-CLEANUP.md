# AdCraft AI Frontend (cleaned)

This folder contains the cleaned React + Vite + TypeScript frontend source.

## Install and run

```bash
npm ci
npm run typecheck
npm run build
npm run dev
```

## Deploy on Render

- Root Directory: `frontend` (if deploying from the repository root)
- Build Command: `npm ci && npm run build`
- Publish Directory: `dist`
- Add the frontend API configuration required by your app/backend.
- Add a Static Site rewrite: Source `/*`, Destination `/index.html`, Action `Rewrite`.

## What was hardened

- Campaign section editors now handle missing/null section objects and arrays.
- Dashboard and common list summaries tolerate missing API arrays.
- This does not replace backend/API verification; unexpected response shapes should still be investigated.
