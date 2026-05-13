# 📅 School Planner

A clean, interactive school planner built with Python. This app uses Natural Language Processing to make adding assignments as easy as typing a sentence.

## 🚀 Features
- **NL Input:** Add events like "Math Quiz Friday at 10am."
- **Interactive Calendar:** View all your tasks in a beautiful, stretched calendar layout.
- **Auto-Cleanup:** Old events are automatically removed to keep your schedule fresh.
- **Hover Details:** Hover over any event to see full details instantly.

## 🛠️ Tech Stack
- **Language:** [Python](https://www.python.org/)
- **Environment:** [uv](https://github.com/astral-sh/uv)
- **Frontend:** [Streamlit](https://streamlit.io/)
- **Parsing:** `dateparser`

## 📦 Installation & Usage
1. Make sure you have `uv` installed.
2. Clone this repo: `git clone https://github.com/[YOUR_USERNAME]/school-planner.git`
3. Install dependencies and run:
   ```bash
   uv run streamlit run app.py