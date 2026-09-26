# Weekly Campaign Assets

Story-format images (1080 × 1920) for the **Campaign assets** carousel on the Atlas iQ For You page. This repo is public so the images can be served through the free jsDelivr CDN. The Campaign Assets database in Notion holds the links.

## What's here

The files in the top level are the **Lower North Shore open homes set for Saturday 27 June 2026**:

- `00.png` — cover slide ("This Weekend's Open Homes")
- `01.png` to `10.png` — one slide per property

## How to link to an image

Use the jsDelivr link, not the GitHub page link:

```
https://cdn.jsdelivr.net/gh/tadatlas/weekly-campaign-assets@main/<file name>
```

For example: `https://cdn.jsdelivr.net/gh/tadatlas/weekly-campaign-assets@main/01.png`

## Adding a new week

Give each week its own folder instead of overwriting `00.png` to `10.png`. Overwritten files can take up to 12 hours to update (jsDelivr caches them), and any old link in Notion would silently show the new image.

Folder name: `YYYY-MM-DD-region`, using the open-home date. For example:

```
2026-07-04-lower-north-shore/00.png
2026-07-04-lower-north-shore/01.png
```

Link: `https://cdn.jsdelivr.net/gh/tadatlas/weekly-campaign-assets@main/2026-07-04-lower-north-shore/01.png`

To upload on github.com:

1. On your computer, make a folder with the week's name and put the images in it.
2. Open this repo on github.com and click **Add file → Upload files**.
3. Drag the **whole folder** in (not just the images). GitHub keeps the folder name.
4. Write a short note (e.g. `Add 4 July LNS open homes`), keep **Commit directly to the main branch** selected and click **Commit changes**.
5. Paste the new links into the Campaign Assets database in Notion.

## House rules

1. **Don't rename, move or delete files that Notion still links to.** The carousel shows a blank card the moment a linked file changes.
2. **Remove old weeks only after their Notion rows are archived.**
3. **Keep each file under 20 MB.** jsDelivr won't serve anything larger.
