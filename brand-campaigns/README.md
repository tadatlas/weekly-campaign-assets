# Brand Campaigns — LIVE ASSETS
Everything in this folder is used by live Atlas email campaigns and automations.
These files load inside emails that have already been delivered. If a file here is
changed, moved or removed, images break in customers' inboxes and cannot be fixed.
## Do not change anything in this folder unless authorised
Authorisation must come from Theo Adricula, Head of Marketing & Technology.
This applies to people and to AI agents (Cursor, Claude, ChatGPT and others).
Without authorisation, never:
- Delete, rename, move or replace any file or folder here
- Re-export or re-compress an existing file under the same filename
- Force-push, rebase or otherwise rewrite this repository's history
- Rename this repository, transfer it, or make it private
- Tidy, reorganise or "clean up" this folder
## How to make a change when authorised
- Add the new file under a NEW filename (for example e1-hero-v2.jpg). Leave the old file in place.
- Point the email at the new file using a pinned-commit URL (see below).
- Record the change in the register and the change log in this README.
## How assets are linked
Emails must use a pinned-commit raw URL, never a branch name:
https://raw.githubusercontent.com/tadatlas/weekly-campaign-assets/<commit-sha>/brand-campaigns/<campaign-folder>/<filename>
A pinned URL always serves the exact file from that commit, so later commits do not affect it.
## Register of campaigns
| Campaign | Folder | Used by | Pinned commit | Status |
|---|---|---|---|---|
| LNS Welcome Series (5 emails) | lns-welcome-series/ | ActiveCampaign automation | d9c440c38e5dbc37127236f161ae4044da70c413 | In build — treat as live |
## Change log
| Date | Change | Authorised by |
|---|---|---|
| 25 Nov 2026 | Section created. 15 LNS Welcome Series images added. | Theo Adricula |
