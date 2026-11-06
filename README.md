# ev-infra

`render.yaml` here describes every Render service Empowered Vote runs: 28
services and 2 environment groups in workspace `tea-d69tn76mcj7s738vmt10`.
It is a Render Blueprint ([spec](https://render.com/docs/blueprint-spec)).

**Status: DRAFT, not linked.** No Blueprint exists in Render yet, so today
this file changes nothing. Render's dashboard is still the source of truth.
Linking the Blueprint needs its own founder approval, under ev-cto decision
0037. This repo is public: it holds no secret values.

## Once it is linked

- **This file is the source of truth.** Change Render only through a PR here.
  A sync overwrites any dashboard edit that conflicts with this file, so a
  quick fix made in the dashboard is silently undone later.
- **Env var values stay in the dashboard.** Every env var is listed by name
  with `sync: false`. Render keeps the value already set and never reads one
  from here. Never put a value in this file. To add a variable, add its name
  here with `sync: false`, then set the value in the dashboard.
- **Retiring a service:** remove it here, merge, let the sync finish, then
  delete it in the dashboard. A service deleted in the dashboard but still in
  this file is **recreated** on the next sync. Removing it from the file alone
  does not delete it.
- **Renaming a service:** Render matches services by name. Rename in the
  dashboard and here in the same change, or the sync creates a new service.

## Layout

- `projects` → `Empowered Vote` → `Production`: the 21 services that sit in
  that Render project today.
- Top-level `services`: the 7 `ev-jobs-*` cron jobs. They belong to no
  project on Render, and this file keeps it that way.
- `envVarGroups`: `ev-jobs-shared` (linked to all 7 crons) and
  `EV-NoServices` (linked to nothing).
- Each service names its own `repo:` and `branch:`, so one file covers all
  ten app repos.

## Checking the file against live Render

```bash
uv run scripts/check-live.py render.yaml
```

It reads the API key from `~/.render/cli.yaml` (never printed), re-fetches
every service, and compares repo, branch, root dir, auto-deploy, build
filter, build/start commands, publish path, plan, region, schedule, instance
count, health check, previews, subdomain policy, routes, headers, custom
domains, env var **names**, env group links and project membership. It never
reads env var values.

```bash
render blueprints validate render.yaml
```

checks the file against Render's schema and the workspace.

## What this file cannot hold

These live settings have no Blueprint field. Render keeps them as they are,
but they are invisible here:

- **Suspended state.** Four services are suspended: `focused-communities`,
  `civic-spaces-slice-assignment`, `empowered-validation-quests`,
  `civic-trivia-backend`. Check Render's change preview to confirm the first
  sync does not resume or redeploy them.
- **Env var values and secret files** (by design).
- **Static site build plan** (`starter` on all 15 static sites; it is the
  default).
- **Web service build cache** (`no-cache`), failure notifications
  (`default`) and open ports (detected by Render).
- **`www.empowered.vote`.** Render adds the `www` redirect itself when the
  apex `empowered.vote` is listed, so the file lists only the apex.

## Before linking

1. Push this repo, then create the Blueprint in Render pointing at it.
2. Read Render's change preview. Every service should show as adopting an
   existing resource with **no** setting changes. Stop if it shows any
   creation, deletion, or setting change.
3. Approve the first sync only after that check.
