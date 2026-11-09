# ev-infra

`render.yaml` here describes every Render service Empowered Vote runs: 27
services and 2 environment groups in workspace `tea-d69tn76mcj7s738vmt10`.
It is a Render Blueprint ([spec](https://render.com/docs/blueprint-spec)).

**Status: LINKED.** Since 2026-11-07 this file is Render Blueprint
`exs-dbn7hgjrjlhs739nnekg` (branch `main`, file `render.yaml`, auto-sync on),
under ev-cto decision 0037. Every merge to `main` syncs to Render. This repo is
public: it holds no secret values.

## Working with it

- **This file is the source of truth.** Change Render only through a PR here.
  A sync overwrites any dashboard edit that conflicts with this file, so a
  quick fix made in the dashboard is silently undone later.
- **Env var values stay in the dashboard.** Every env var is listed by name
  with `sync: false`. Render keeps the value already set and never reads one
  from here. Never put a value in this file. To add a variable, add its name
  here with `sync: false`, then set the value in the dashboard.
- **Retiring a service:** remove it here and merge, then delete it in the
  dashboard. Order matters: a service deleted in the dashboard but still in
  this file is **recreated** on the next sync. Removing it from the file alone
  does not delete it, and it does not trigger a sync either: Render counts a
  removal as "no changes", so no sync runs and the Blueprint keeps listing the
  service until it is deleted. Once it is out of the file on `main`, deleting
  it is safe (seen with `civic-spaces-slice-assignment`, #4, 2026-11-09).
- **Renaming a service:** Render matches services by name. Rename in the
  dashboard and here in the same change, or the sync creates a new service.

## Layout

- `projects` → `Empowered Vote` → `Production`: the 20 services that sit in
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

- **Suspended state.** Three services are suspended: `focused-communities`,
  `empowered-validation-quests`, `civic-trivia-backend`. Check Render's change
  preview to confirm a sync does not resume or redeploy them.
- **Env var values and secret files** (by design).
- **Static site build plan** (`starter` on all 15 static sites; it is the
  default).
- **Web service build cache** (`no-cache`), failure notifications
  (`default`) and open ports (detected by Render).
- **`www.empowered.vote`.** Render adds the `www` redirect itself when the
  apex `empowered.vote` is listed, so the file lists only the apex.

## How it was linked (2026-11-07)

Render's preview showed "associate" for all 28 services and both env groups,
and one change: on-the-record's start command set to empty (a static site
never runs one). After the first sync, `scripts/check-live.py` matched live
Render on every checked field, and the four suspended services stayed
suspended.

The preview is the safety check for every future change too: on a PR here,
anything beyond the intended setting is a reason to stop.
