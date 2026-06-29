# Free footbags.com stock checker 🛒🔔

Watches the **entire [footbags.com](https://footbags.com) store** and **emails + texts you**
the moment *any* product flips from sold-out back to in-stock. Runs entirely on
GitHub Actions — no server, no monthly cost.

## How it works

- `config.json` — the store to watch (already set to footbags.com).
- `check.py` — reads the store's public `products.json` (reliable per-variant stock
  flag) and decides what's in stock.
- `.github/workflows/check.yml` — runs the check every 15 min via GitHub's free cron.
- `state.json` — auto-created; remembers what was already in stock so you only get
  alerted on the *change*, not every run. (The first run just records a baseline and
  sends no alerts.)

Texting is free via AT&T's **email-to-SMS gateway** — no Twilio needed.

---

## Setup (one time, ~10 minutes)

### 1. Make a Gmail App Password
Alerts are sent from a Gmail account using an **App Password** (a special 16-char
password, not your normal login):

1. Go to https://myaccount.google.com/security and turn on **2-Step Verification**
   (required before app passwords are available).
2. Go to https://myaccount.google.com/apppasswords
3. Type a name like `footbag-bot`, click **Create**, and copy the 16-character code
   it shows (looks like `abcd efgh ijkl mnop` — you can drop the spaces).

> Tip: a throwaway Gmail just for this bot keeps things tidy.

### 2. Your AT&T text address
Your phone number `5551234567` becomes this email address:

```
5551234567@txt.att.net
```

Sending an email there arrives on your phone as a text. (AT&T also offers
`@mms.att.net` for picture/longer messages — `txt` is fine here.)

### 3. Push this folder to a new GitHub repo
```bash
cd stock-checker
git init
git add .
git commit -m "footbags stock checker"
git branch -M main
git remote add origin https://github.com/YOU/footbag-checker.git
git push -u origin main
```

### 4. Add your secrets
In the repo: **Settings → Secrets and variables → Actions → New repository secret**.
Add these three (names must match exactly):

| Secret name           | Value                                                   |
|-----------------------|---------------------------------------------------------|
| `GMAIL_USER`          | `youremail@gmail.com`                                   |
| `GMAIL_APP_PASSWORD`  | the 16-char app password from step 1                    |
| `ALERT_TO`            | `youremail@gmail.com, 5551234567@txt.att.net`           |

`ALERT_TO` is a comma-separated list — your real email **and** your AT&T text
address, so you get both an email and a text.

### 5. Turn it on / test it
Go to the **Actions** tab. If prompted, click **"I understand my workflows, enable
them."** Then open **stock-check → Run workflow** to run it by hand.

- The **first** run just records which products are currently in stock (no alerts).
- After that, every 15 min it compares against the baseline and alerts you on
  anything newly back in stock.

**To prove alerts work end-to-end:** after the first run finishes, delete the
`state.json` file in the repo (or edit it to set one currently-in-stock item to
`false`), then run the workflow again — you should get an email + text within a
minute.

---

## Notes
- GitHub's cron is best-effort; `*/15` can run a few minutes late under load. Want it
  faster (e.g. every 5 min) or slower? Edit the `cron:` line in
  `.github/workflows/check.yml`.
- Free GitHub Actions minutes are unlimited for **public** repos and generous for
  private ones — every-15-min checks stay well within the free tier.
- This watches the whole store. If you'd rather only be alerted for *specific*
  footbags, say the word and I'll add a filter.
