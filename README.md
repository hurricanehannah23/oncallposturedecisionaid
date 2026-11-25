# On-Call Posture Decision Aid

A 45th Weather Squadron threat outlook for KSC and CCSFS, for weekend and holiday on-call decisions. It uses the METCON threat matrix rows and scoring (without Marine & coastal): Lightning, Surface winds, Winds aloft (≤400 ft), Severe / hail, Heavy rain / flooding, Temperature and Tropical. Each one is rated None, Low, Moderate or High for each day in the window. The page then recommends a posture: **on call** (nothing above Low), **on call: heightened** (a Moderate), or **stay staffed** (a High).

An **Hourly timing** view applies the same thresholds hour by hour for every threat, with a posture row and a list of each Moderate and High period. Each threat tab has its own timing strip.

Cells start from the data. Click a cell to raise it, Shift-click to lower it, and right-click to hand it back to the data. Overrides and notes are saved in each browser.

## What's in the repo

| File | What it does |
|---|---|
| `index.html` | The whole dashboard: one page, no build step. |
| `scripts/fetch_data.py` | Downloads the NWS grid forecast, NWS forecast text, NWS alerts, GFS winds at 262/394 ft (Open-Meteo), SPC Day 1–8 outlooks, NHC active storms and the NWS Melbourne discussion into `data/*.json`. Standard library only. |
| `.github/workflows/deploy.yml` | Every 30 minutes (and on every push) it runs the script and deploys the page plus `data/` to GitHub Pages. |

The page reads `data/*.json` when those files are less than 3 hours old. If a file is missing or stale, it calls that API directly. The data isn't committed to the repo; it's built fresh on each deploy, so the history stays small.

## Set up

1. Create a repo (public, or private if your plan includes Pages for private repos) and upload these files, keeping the `.github/workflows` folder.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. **Actions → Refresh data and deploy → Run workflow** for the first deploy. The page URL shows on the run's summary.

## Faster or more reliable refreshes

GitHub can run scheduled jobs late. To trigger refreshes yourself, the way the ops dashboard does with cron-job.org:

- Create a fine-grained personal access token limited to this repo with **Actions: Read and write**.
- In cron-job.org, send `POST https://api.github.com/repos/OWNER/REPO/actions/workflows/deploy.yml/dispatches` with the following.
  - Headers: `Authorization: Bearer <token>`, `Accept: application/vnd.github+json`
  - Body: `{"ref":"main"}`

## Changing the rules

The thresholds are listed on the page under **How it's scored**. To change them, edit `DEF` near the top of the script in `index.html` (and the matching text in the How it's scored panel). Sites are in `SITES`, both in `index.html` and in `scripts/fetch_data.py`.
