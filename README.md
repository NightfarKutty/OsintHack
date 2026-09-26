# ⚡ OsintHack — Phone Number OSINT Utility

A terminal-based Open Source Intelligence (OSINT) tool built for Python environments (including Termux and Linux). It parses international phone number metadata, checks carrier details, generates search dorks, and queries external APIs.

---

## 🛠️ Features

* 🌐 **Global Number Parsing:** Extracts E.164 formatting, country codes, national numbers, and timezones using Google's `libphonenumber`.
* 📡 **Carrier & Line Type:** Identifies carrier names and line classifications (Mobile, Fixed Line, VoIP, Toll-Free).
* 🔎 **OSINT Footprint Dorks:** Automatically generates search engine queries (Google, Bing, DuckDuckGo) for public data verification.
* 🔗 **Direct Messenger Protocol Links:** Provides direct chat URIs for WhatsApp, Telegram, and Viber.
* 📊 **API Integration:** Supports NumVerify API for supplemental verification data.
* 💾 **JSON Reporting:** Automatically exports session results into structured JSON files.

---

## 📥 Installation

### 1. Termux Setup

```bash
# Update system packages
pkg update && pkg upgrade -y

# Install dependencies
pkg install python git -y

# Clone the repository
git clone [https://github.com/NightfarKutty/OsintHack.git](https://github.com/NightfarKutty/OsintHack.git)
cd OsintHack

# Install Python requirements
pip install -r requirements.txt

# Run Kutty Hacker Page
python kuttyhacker.py
