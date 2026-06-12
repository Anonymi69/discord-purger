# Discord DM Purger

A clean, privacy-focused tool to delete your own Discord DMs quickly and efficiently.

---

## ⚠️ Disclaimer

Use this tool **at your own risk**.

Automating actions on Discord may violate Discord's Terms of Service.
The author is **not responsible** for any account restrictions, bans, data loss, or other consequences resulting from the use of this project.

---

## 🔐 How Authentication Works

This version **does not extract, scan, or auto-detect tokens** in any way.

When you open the app, you are presented with a login screen where you manually paste your own Discord user token. The token is:

- Always masked on screen (never shown in plaintext)
- Blocked from being copied or cut via keyboard or right-click
- Validated directly against Discord's API before the app proceeds
- Never stored, logged, or written to disk

---

## 🚀 Installation & Usage

### Requirements

- **Python 3.10 or newer** — [Download Python](https://www.python.org/downloads/)
- An internet connection

> There are no prebuilt executables or releases. You run the tool directly from source using Python.

---

### 1. Clone the repository

```bash
git clone https://github.com/Anonymi69/discord-purger.git
```
```bash
cd discord-purger
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

> Dependencies (`PyQt6`, `requests`, `Pillow`) are also auto-installed on first run if missing.

### 3. Run the program

```bash
python main.py
```

---

## 🖥️ How to Use

1. **Get your token** — Open Discord in a browser, open DevTools (`F12`), go to the Network tab, send any message, and find the `Authorization` header in the request.
2. **Paste it** into the token field on the login screen and click **Validate & Continue**.
3. Once validated, your account info and DM list will load automatically.
4. **Select** the conversations you want to purge (individually or all at once).
5. Set a **delay** between deletions (default 0.8s — lower values increase rate-limit risk).
6. Click **▶ Start Purge** and monitor the activity log.

---

## 📽️ Video Tutorial

<!-- Paste your video below — drag and drop an .mp4 into this file on GitHub, or paste a link -->

---

## 📌 Notes

- Only your own messages are deleted — you cannot delete messages sent by others.
- Deleted messages cannot be recovered.
- Using very low delay values increases the chance of being rate-limited by Discord.
- The activity log shows every deletion in real time.

---

## ⭐ Support

If you find this project useful, consider giving it a star on GitHub.
