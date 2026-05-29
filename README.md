# 📅 My School Planner

A high-end, interactive school planner built with Python and Streamlit. This app combines a sleek, cyberpunk-inspired desktop dashboard with an automated Telegram bot, allowing you to manage your schedule seamlessly from your computer or your phone.

## 🚀 Features
- **Natural Language Parsing:** Add events effortlessly. Just type "Math Quiz Friday at 10am" and the app figures out the date, time, and category.
- **Telegram Bot Integration:** Text your planner on the go! Send a message from your phone, and it instantly syncs to your desktop dashboard.
- **Automated Daily Reminders:** The bot proactively sends a push notification to your phone at 5:30 PM EST with tomorrow's schedule.
- **Advanced Dashboard UI:** Features a neon-styled persistent sidebar, smart-wrapping calendar pills, and a real-time quick stats HUD.
- **Auto-Sync & Cleanup:** Old events are automatically purged, and the dashboard silently refreshes in the background so you never have to hit "reload".
- **Manual Escape Hatch:** A built-in advanced form for highly specific scheduling needs.

## 🛠️ Tech Stack
- **Language:** [Python](https://www.python.org/)
- **Environment & Packaging:** [uv](https://github.com/astral-sh/uv)
- **Frontend UI:** [Streamlit](https://streamlit.io/)
- **NLP & Parsing:** `dateparser`
- **Bot Engine & Scheduling:** `python-telegram-bot[job-queue]`
- **Background Refresh:** `streamlit-autorefresh`

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/](https://github.com/)[YOUR_USERNAME]/school-planner.git
   cd school-planner