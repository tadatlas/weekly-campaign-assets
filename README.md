# Weekly Campaign Assets

Images and videos for Atlas campaigns: the weekly OFI email, Instagram stories, the **Campaign assets** carousel on the Atlas iQ For You page and the Founding Director's Edit. This repo is public so the files can be served through the free jsDelivr CDN. Emails and the Campaign Assets database in Notion link to them.

## What's here

| Folder | What's in it |
| --- | --- |
| `ofi/<ddmonyyyy>/` | One folder per Saturday OFI send: the email HTML and its launchpad tile images. E.g. `ofi/07nov2026/` |
| `stories/<region>-<ddmonyyyy>/` | Story assets per region and week (`lns`, `sh`, `byb`): cover, property cards, open-time `tabs/`, `stills/` and `videos/` |
| `templates/ofi-weekly-edm/` | The weekly all-regions OFI email template: build script, base, example week and QA. See its README |
| `founding-directors-edit/` | Founding Director's Edit cover photos (`<yyyy-mm>/`) and Stone logos (`brand/`) |
| Top level `00.png`–`10.png` | The first set: Lower North Shore open homes, Saturday 27 June 2026 (`00` is the cover, `01`–`10` one per property) |

## How to link to a file

Use the jsDelivr link, not the GitHub page link:

```
https://cdn.jsdelivr.net/gh/tadatlas/weekly-campaign-assets@main/<path>
```

Spaces in a path become `%20`. For example:

```
https://cdn.jsdelivr.net/gh/tadatlas/weekly-campaign-assets@main/ofi/07nov2026/tile-lns.jpg
```

## Adding a new week

Make new folders that follow the patterns above, using the Saturday's date (e.g. `stories/lns-14nov2026/`). Don't reuse or overwrite an older week's files. jsDelivr caches files for up to 12 hours, and any email or Notion row still linking to the old file would quietly show the new one.

To upload on github.com:

1. On your computer, make the folder with the right name and put the files in it.
2. Open the parent folder in this repo on github.com (e.g. `stories/`) and click **Add file → Upload files**.
3. Drag the **whole folder** in. GitHub keeps the folder name.
4. Write a short note (e.g. `Add LNS 14 Nov stories`), keep **Commit directly to the main branch** selected and click **Commit changes**.

## House rules

1. **Don't rename, move or delete files that an email or Notion still links to.** The image disappears the moment the file changes.
2. **Remove old weeks only once nothing links to them.**
3. **Keep each file under 20 MB.** jsDelivr won't serve anything larger. Two story videos in `stories/sh-07nov2026/videos/` are over this (`SH_By_Appointment_Sat7Nov.mp4`, 44 MB, and `SH_OFI_Cover_Sat7Nov.mp4`, 25 MB), so share those from Canva or Dropbox instead of linking to them here.
