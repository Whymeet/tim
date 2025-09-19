# VK Ads Report Automation

This project creates screenshots of VK posts and statistics of the related advertising groups and compiles them into a Word report.

## Requirements

- Python 3.8+
- Google Chrome installed (Playwright launches the desktop browser via the `chrome` channel).
  The scripts reuse the local profile stored in `.playwright-profile` to keep the browser looking human and reduce captcha prompts.

Install Python dependencies:

```bash
pip install -r requirements.txt
playwright install
```

`playwright install` downloads the browsers required for headless execution.

## Authentication

Before running the main script you must authenticate in VK and save the session cookies. Run:

```bash
python vk_auth.py
```

A browser window will open. Log into your VK account (complete 2FA if needed) and navigate to `https://ads.vk.com/hq/dashboard/ad_groups`. After the page loads press **Enter** in the terminal. The script will save your session to `vk_storage.json`.

## Running the script

After authentication simply run:

```bash
python main.py
```

The program reads `posts.xlsx`, takes screenshots of the posts and group statistics and generates a report `Отчет.docx`. All images are stored inside the `assets/` directory.

### Input file

`posts.xlsx` must contain the name of a group in the first column and the links to VK posts in the subsequent columns.

### Output

- `assets/` – folder with screenshots of each post and VK Ads group statistics.
- `Отчет.docx` – generated Word report containing the screenshots.

