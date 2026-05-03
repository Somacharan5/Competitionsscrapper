# Setup Guide — Xads Competition Scraper

## Prerequisites

- Python 3.11+
- GitHub account (for free automation)
- Google account
- Anthropic API key (get from console.anthropic.com)

---

## Step 1 — Get Your Anthropic API Key

1. Go to https://console.anthropic.com
2. Create account / log in
3. Click **API Keys** → **Create Key**
4. Copy the key (starts with `sk-ant-`)
5. Save it — you'll add it to GitHub secrets later

---

## Step 2 — Set Up Google Sheets Access

### 2a. Create a Google Cloud Project
1. Go to https://console.cloud.google.com
2. Create a new project: "Xads Scraper"
3. Enable **Google Sheets API**: APIs & Services → Library → Search "Sheets" → Enable
4. Enable **Google Drive API**: Same, search "Drive" → Enable

### 2b. Create a Service Account
1. APIs & Services → Credentials → Create Credentials → Service Account
2. Name: `xads-scraper-bot`
3. Click **Done**
4. Click the service account → **Keys** tab → **Add Key** → JSON
5. Download the JSON file
6. Rename it to `service_account.json`
7. Put it in `credentials/` folder (this folder is gitignored)

### 2c. Note the Service Account Email
From the JSON file, copy the `client_email` field. It looks like:
`xads-scraper-bot@xads-scraper-xxxxx.iam.gserviceaccount.com`

---

## Step 3 — Run One-Time Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_ORG/xads-scraper.git
cd xads-scraper

# Install dependencies
pip install -r requirements.txt

# Copy env template
cp .env.example .env

# Edit .env — fill in only these (SHEET_ID is already pre-filled):
# ANTHROPIC_API_KEY=sk-ant-...
# GOOGLE_CREDENTIALS_PATH=credentials/service_account.json
# SMTP_EMAIL=your@gmail.com
# SMTP_PASSWORD=your-app-password

# Run one-time setup (connects to your existing sheet, adds tabs + headers)
python setup.py
```

Your Sheet ID (`14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E`) is already hardcoded — no need to configure it.

The setup script will:
- Open your existing blank Google Sheet
- Create "Competitions" and "Jobs & Placement" tabs with correct headers and formatting
- Print success confirmation

---

## Step 4 — Share Your Sheet with the Service Account

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E
2. Click **Share** (top right)
3. Paste the service account email from your `service_account.json` file (the `client_email` field — looks like `xads-scraper-bot@project-id.iam.gserviceaccount.com`)
4. Give it **Editor** access
5. Uncheck "Notify people" → click **Share**

This is the only manual step. Everything else is automated.

---

## Step 5 — Test Manually

```bash
# Add SHEET_ID to your .env file
# Then run:
python src/scraper.py
```

Check your Google Sheet — it should populate with competitions!

---

## Step 6 — Set Up GitHub Actions (Automated Every 3 Days)

### 6a. Push to GitHub
```bash
git add .
git commit -m "Initial setup"
git push origin main
```

### 6b. Add GitHub Secrets
Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `GOOGLE_CREDENTIALS_JSON` | The FULL content of `credentials/service_account.json` (paste the whole JSON) |
| `SMTP_EMAIL` | Your Gmail address |
| `SMTP_PASSWORD` | Your Gmail App Password (not your regular password) |
| `NOTIFY_EMAILS` | `soma.charan@mastersunion.org,Hitesh.kalwani@mastersunion.org` |

> **Note**: `SHEET_ID` is hardcoded as `14jJYhpdoDqQAYXzLequShRY4yaT1PQ_jTT6pjK4DV_E` — no secret needed for it.

### 6c. Get Gmail App Password
1. Go to https://myaccount.google.com
2. Security → 2-Step Verification (enable if not already)
3. Search "App passwords" → Create new
4. Select "Mail" → "Other" → Name it "Xads Scraper"
5. Copy the 16-character password

---

## Step 7 — Trigger First GitHub Actions Run

Go to your GitHub repo → **Actions** → **Competition Scraper** → **Run workflow**

Watch it run. Check your Google Sheet and email after ~5 minutes.

---

## After That — Fully Automated

The scraper will now automatically run every 3 days (at 6 AM UTC) and:
1. Search the web for new competitions using Claude AI
2. Filter out expired and duplicate ones
3. Update your Google Sheet
4. Send you an email with new findings

---

## Manually Run Anytime

```bash
python src/scraper.py
```

Or trigger from GitHub Actions → Run workflow.

---

## Cost Estimate

- **Anthropic API**: ~$0.50-2.00 per run (runs every 3 days = ~$5-20/month)
- **GitHub Actions**: Free (well within free tier)
- **Google Sheets API**: Free
- **Gmail SMTP**: Free

Total: ~$5-20/month depending on how many searches you run.
