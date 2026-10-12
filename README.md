# Rates & Banks: NL vs UK

A website that compares how ECB and Bank of England interest rate changes affected eight Dutch and UK banks from 2021 onward.

- **Central bank rates update by themselves every day.** A free GitHub Action downloads the latest rates from the ECB and Bank of England data feeds and republishes the site.
- **Bank figures are updated by hand,** because banks publish them as press releases and PDFs. That takes about 10 minutes, 1–2 times a year (see below).

## What's in this folder

| File | What it does |
|---|---|
| `index.html` | The website |
| `data/policy_rates.csv` | ECB and BoE rates, rewritten automatically every day |
| `data/bank_results.csv` | Bank figures, which you edit |
| `data/sources.csv` | The source list shown at the bottom of the site |
| `data/meta.json` | When the rates were last checked (shown in the footer) |
| `scripts/update_rates.py` | The script that downloads the rates |
| `.github/workflows/update.yml` | Runs the script every day at 06:17 UTC and publishes the site |

## One-time setup (about 10 minutes)

1. Create a free account at **github.com** if you don't have one.
2. Click **+** (top right) → **New repository**. Name it, for example, `rates-and-banks`. Choose **Public**. Click **Create repository**.
3. On the new repository page, click **uploading an existing file**. Drag in **everything inside this folder** (including the `.github` folder; on a Mac, press Cmd+Shift+. in Finder to see hidden folders). Click **Commit changes**.
   - If the `.github` folder doesn't upload, create the file by hand: **Add file → Create new file**, type the name `.github/workflows/update.yml`, paste in the contents of that file, and commit.
4. Go to **Settings → Pages**. Under **Build and deployment → Source**, choose **GitHub Actions**.
5. Go to **Settings → Actions → General → Workflow permissions**. Choose **Read and write permissions** and save.
6. Go to the **Actions** tab. Click **Update rates and publish site → Run workflow**.
7. After 1–2 minutes the run turns green. Your site is live at
   `https://<your-username>.github.io/rates-and-banks/`

From then on it runs every day by itself. You don't need to do anything.

### Checking it works

- In the **Actions** tab, each daily run should be green.
- The site's footer says when the rates were last checked.
- If a download ever fails, the script keeps the last good data, so the site never breaks. The footer then says "latest check failed".

## Updating the bank figures (after each results season)

Banks publish full-year results in February. When they're out:

1. In GitHub, open `data/bank_results.csv` and click the pencil icon (Edit).
2. Add one row per bank for the new year, in the same format as the existing rows:
   ```
   ING,Netherlands,2026,EUR,14900,13.5,ROE,1.38,6400,Net result
   ```
   Columns: bank, country, year, currency, net interest income (millions), return on equity (%), return measure, net interest margin (%, leave empty if not reported), net profit (millions), profit basis.
3. Optionally, add the press release links to `data/sources.csv`.
4. Click **Commit changes**. The site republishes within about 2 minutes.

The charts, headline numbers and most of the text update automatically with the new year. Reread the "Key findings" text in `index.html` afterwards. Some sentences describe what happened (for example, which banks dipped in 2024) and may need a small edit.

## Notes

- Rates come from the ECB Data Portal (series `FM.D.U2.EUR.4F.KR.DFR.LEV`) and the Bank of England database (series `IUDBEDR`).
- GitHub can pause scheduled runs in repositories with no activity for 60 days. The daily run commits the "last checked" time, which counts as activity. If runs ever stop, click **Run workflow** once to restart them.
