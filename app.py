from __future__ import annotations

import calendar
import subprocess
import sys
import atexit
from collections import defaultdict
from datetime import date, datetime, timedelta
from html import escape

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from planner import Event, add_event, load_events, save_events, purge_expired_events


@st.cache_resource
def start_telegram_bot():
    """Launch the Telegram bot as a background process exactly once."""
    process = subprocess.Popen([sys.executable, "bot.py"])
    atexit.register(process.terminate)
    return process


APP_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700;800&display=swap');

:root {
    --ink: #f8fbff;
    --muted: #a8b3cf;
    --panel: rgba(10, 15, 32, 0.82);
    --panel-strong: rgba(14, 21, 43, 0.94);
    --line: rgba(140, 160, 255, 0.22);
    --cyan: #35f6ff;
    --pink: #ff4fd8;
    --lime: #69ff97;
    --yellow: #ffe66d;
    --red: #ff5d73;
    --blue: #4aa8ff;
    --purple: #a879ff;
}

html, body, [class*="css"] {
    font-family: 'Lexend', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 12% 8%, rgba(53, 246, 255, 0.22), transparent 32%),
        radial-gradient(circle at 88% 14%, rgba(255, 79, 216, 0.2), transparent 28%),
        linear-gradient(135deg, #070912 0%, #111735 48%, #07111d 100%);
    color: var(--ink);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(8, 12, 28, 0.96), rgba(13, 24, 46, 0.94));
    border-right: 1px solid var(--line);
    padding-top: 2rem;
}

.block-container {
    max-width: 1480px;
    padding: 1.75rem 2.25rem 3rem;
}

.planner-hero {
    border: 1px solid var(--line);
    border-radius: 18px;
    background:
        linear-gradient(135deg, rgba(53, 246, 255, 0.12), rgba(255, 79, 216, 0.1)),
        rgba(8, 12, 28, 0.72);
    box-shadow: 0 24px 80px rgba(0, 0, 0, 0.34);
    margin-bottom: 0.5rem;
    padding: 1.35rem 1.5rem;
    text-align: center;
}

.hero-emoji {
    font-size: 3.6rem;
    line-height: 1;
    margin-bottom: 0.35rem;
    text-shadow: 0 0 26px rgba(53, 246, 255, 0.65);
}

.planner-hero h1 {
    color: var(--ink);
    font-size: clamp(2rem, 4vw, 3.6rem);
    font-weight: 800;
    letter-spacing: 0;
    margin: 0;
}

.planner-hero p {
    color: var(--muted);
    font-size: 1rem;
    margin: 0.55rem auto 0;
    max-width: 720px;
}

h1, h2, h3, h4, label, p, span, div {
    font-family: 'Lexend', sans-serif;
}

h2, h3 {
    color: var(--ink);
}

/* --- THE GIANT "SEARCH ENGINE" INPUT --- */
/* Target ONLY the main search bar so we don't break manual forms */
div[data-testid="stTextInput"]:has(input[aria-label="Add a school event"]) {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

div[data-testid="stTextInput"]:has(input[aria-label="Add a school event"]) label {
    display: none;
}

input[aria-label="Add a school event"] {
    background: rgba(10, 15, 32, 0.95);
    border: 2px solid rgba(53, 246, 255, 0.4);
    border-radius: 24px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(53, 246, 255, 0.1);
    color: var(--ink);
    font-size: 1.4rem;
    line-height: 1.6;
    padding: 1.2rem 1.5rem;
    min-height: 5rem;
    text-align: center;
    transition: all 250ms ease;
}

input[aria-label="Add a school event"]:focus {
    border-color: var(--pink);
    box-shadow: 0 0 0 4px rgba(255, 79, 216, 0.15), 0 0 40px rgba(255, 79, 216, 0.35);
    transform: translateY(-2px) scale(1.01);
}

input[aria-label="Add a school event"]::placeholder {
    color: rgba(168, 179, 207, 0.5);
    font-weight: 400;
}
/* --------------------------------------- */

.stButton > button {
    background: linear-gradient(135deg, rgba(53, 246, 255, 0.18), rgba(255, 79, 216, 0.16));
    border: 1px solid rgba(53, 246, 255, 0.42);
    border-radius: 12px;
    color: var(--ink);
    font-weight: 800;
    transition: transform 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
}

.stButton > button:hover {
    border-color: var(--pink);
    box-shadow: 0 0 24px rgba(255, 79, 216, 0.24);
    color: var(--ink);
    transform: scale(1.035);
}

[data-testid="stMetric"],
[data-testid="stAlert"],
details {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 16px;
    box-shadow: 0 16px 44px rgba(0, 0, 0, 0.24);
}

/* Dashboard Metric Tweaks */
[data-testid="stMetric"] {
    padding: 1rem 1.5rem;
    text-align: center;
    border-color: rgba(53, 246, 255, 0.2);
}

details {
    margin-bottom: 0.65rem;
    overflow: hidden;
    transition: transform 140ms ease, border-color 140ms ease, box-shadow 140ms ease;
}

details:hover {
    border-color: rgba(53, 246, 255, 0.45);
    box-shadow: 0 18px 52px rgba(53, 246, 255, 0.12);
    transform: translateY(-2px) scale(1.006);
}

details summary {
    color: var(--ink);
    font-weight: 700;
}

.calendar-title {
    color: var(--ink);
    margin: 1.5rem 0 0.85rem;
    text-align: center;
    text-shadow: 0 0 18px rgba(53, 246, 255, 0.34);
}

.calendar-shell {
    width: 100%;
    margin: 0.5rem 0 2rem;
    overflow: visible;
}

.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 0.7rem;
    overflow: visible;
}

.calendar-weekday {
    color: var(--cyan);
    font-size: 0.84rem;
    font-weight: 800;
    text-align: center;
    text-transform: uppercase;
}

.calendar-day {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 16px;
    box-shadow: 0 18px 52px rgba(0, 0, 0, 0.24);
    min-height: clamp(150px, 16vh, 220px);
    padding: 0.65rem;
    overflow: visible;
    position: relative;
}

.calendar-day.today {
    background: linear-gradient(135deg, rgba(53, 246, 255, 0.16), rgba(255, 79, 216, 0.1)), var(--panel-strong);
    border-color: var(--cyan);
    box-shadow:
        inset 0 0 0 3px var(--cyan),
        0 0 34px rgba(53, 246, 255, 0.3),
        0 18px 52px rgba(0, 0, 0, 0.28);
}

.calendar-day.today .day-number {
    align-items: center;
    background: linear-gradient(135deg, var(--cyan), var(--pink));
    border-radius: 999px;
    color: #06111f;
    display: inline-flex;
    height: 1.85rem;
    justify-content: center;
    width: 1.85rem;
}

.calendar-day.muted-day {
    background: rgba(8, 12, 28, 0.46);
    color: #66708b;
}

.day-number {
    color: var(--ink);
    font-size: 0.95rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 0.6rem;
}

/* SMART WRAPPING PILLS */
.calendar-event {
    background: rgba(74, 168, 255, 0.16);
    border: 1px solid rgba(74, 168, 255, 0.2);
    border-left: 4px solid var(--blue);
    border-radius: 12px;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.2);
    color: var(--ink);
    cursor: default;
    font-size: 0.82rem;
    line-height: 1.35;
    margin-top: 0.4rem;
    padding: 0.45rem 0.55rem;
    position: relative;
    transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
    z-index: 1;
}

.calendar-event:hover {
    border-color: rgba(255, 255, 255, 0.4);
    box-shadow: 0 0 26px rgba(53, 246, 255, 0.18), 0 16px 40px rgba(0, 0, 0, 0.28);
    transform: translateY(-2px) scale(1.025);
    z-index: 20;
}

.event-time {
    color: var(--muted);
    display: block;
    font-size: 0.72rem;
    font-weight: 800;
    margin-bottom: 0.15rem;
}

.event-title {
    display: -webkit-box;
    -webkit-line-clamp: 2; /* Allow up to 2 lines of text */
    -webkit-box-orient: vertical;
    overflow: hidden;
    white-space: normal; /* Allow text wrapping */
    word-wrap: break-word;
}

.event-tooltip {
    background: #070912;
    border: 1px solid rgba(53, 246, 255, 0.4);
    border-radius: 14px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.38), 0 0 28px rgba(53, 246, 255, 0.16);
    color: var(--ink);
    font-size: 0.82rem;
    left: 50%;
    line-height: 1.45;
    max-width: min(280px, 75vw);
    min-width: 220px;
    opacity: 0;
    padding: 0.75rem 0.85rem;
    pointer-events: none;
    position: absolute;
    top: calc(100% + 0.55rem);
    transform: translate(-50%, -0.25rem);
    transition: opacity 120ms ease, transform 120ms ease;
    visibility: hidden;
    white-space: normal;
    z-index: 100;
}

.event-tooltip::before {
    background: #070912;
    border-left: 1px solid rgba(53, 246, 255, 0.4);
    border-top: 1px solid rgba(53, 246, 255, 0.4);
    content: "";
    height: 0.65rem;
    left: 50%;
    position: absolute;
    top: -0.36rem;
    transform: translateX(-50%) rotate(45deg);
    width: 0.65rem;
}

.calendar-event:hover .event-tooltip {
    opacity: 1;
    transform: translate(-50%, 0);
    visibility: visible;
}

.tooltip-title {
    color: var(--cyan);
    font-size: 0.9rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
}

.calendar-event.homework { background: rgba(74, 168, 255, 0.18); border-left-color: var(--blue); }
.calendar-event.exams { background: rgba(255, 93, 115, 0.18); border-left-color: var(--red); }
.calendar-event.clubs { background: rgba(105, 255, 151, 0.15); border-left-color: var(--lime); }
.calendar-event.projects { background: rgba(168, 121, 255, 0.18); border-left-color: var(--purple); }
.calendar-event.general { background: rgba(255, 230, 109, 0.14); border-left-color: var(--yellow); }

.more-events {
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 800;
    margin-top: 0.35rem;
}

@media (max-width: 760px) {
    .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
    .planner-hero { padding: 1rem; }
    .calendar-grid { gap: 0.28rem; }
    .calendar-day { min-height: 112px; padding: 0.35rem; }
    .calendar-event { font-size: 0.7rem; }
    .event-tooltip { min-width: 190px; }
}
</style>
"""


def sorted_events(events: list[Event]) -> list[Event]:
    return sorted(events, key=lambda event: (event.date, event.time or "23:59"))


def upcoming_events(events: list[Event]) -> list[Event]:
    today = date.today()
    return [
        event
        for event in sorted_events(events)
        if date.fromisoformat(event.date) >= today
    ]


def events_due_this_week(events: list[Event]) -> list[Event]:
    today = date.today()
    end_of_week = today + timedelta(days=6 - today.weekday())
    return [
        event
        for event in events
        if today <= date.fromisoformat(event.date) <= end_of_week
    ]


def events_by_date(
    events: list[Event],
    visible_dates: set[date] | None = None,
) -> dict[date, list[Event]]:
    grouped_events: dict[date, list[Event]] = defaultdict(list)
    for event in events:
        event_day = date.fromisoformat(event.date)
        if visible_dates is None or event_day in visible_dates:
            grouped_events[event_day].append(event)
    return grouped_events


def format_event_date(event: Event) -> str:
    event_date = date.fromisoformat(event.date)
    date_text = event_date.strftime("%a, %b %d")
    if event.time:
        display_time = datetime.strptime(event.time, "%H:%M").strftime("%I:%M %p")
        return f"{date_text} at {display_time.lstrip('0')}"
    return date_text


def format_event_time(event: Event, compact: bool = False) -> str:
    if not event.time:
        return "" if compact else "All day"
    return datetime.strptime(event.time, "%H:%M").strftime("%I:%M %p").lstrip("0")


def calendar_month_offset(current_month: date, month_delta: int) -> date:
    month_index = current_month.month - 1 + month_delta
    year = current_month.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def category_css_class(category: str) -> str:
    normalized = category.strip().lower()
    if normalized in {"assignment", "homework"}:
        return "homework"
    if normalized in {"test", "exam", "exams", "quiz"}:
        return "exams"
    if normalized in {"activity", "club", "clubs", "meeting", "practice"}:
        return "clubs"
    if normalized in {"project", "presentation", "lab", "report"}:
        return "projects"
    return "general"


def delete_event(index_to_delete: int) -> None:
    events = load_events()
    updated_events = [
        event for index, event in enumerate(events) if index != index_to_delete
    ]
    save_events(sorted_events(updated_events))
    st.rerun()


def clear_events() -> None:
    save_events([])
    st.rerun()


def handle_event_submit() -> None:
    raw_text = st.session_state.get("event_input", "").strip()
    if not raw_text:
        return

    try:
        event = add_event(raw_text)
    except ValueError as error:
        st.session_state.error_message = str(error)
    else:
        date_str = format_event_date(event)
        time_str = format_event_time(event)
        time_display = f" at **{time_str}**" if event.time else ""
        st.session_state.success_message = (
            f"✨ Saved: **{event.title}** for **{date_str}**{time_display} "
            f"under **[{event.category}]**."
        )

    st.session_state.event_input = ""


def render_event_card(event: Event, original_index: int) -> None:
    with st.expander(f"{event.title} - {format_event_date(event)}"):
        st.write(f"**Category:** {event.category}")
        st.write(f"**Date:** {event.date}")
        st.write(f"**Time:** {format_event_time(event)}")

        if st.button("Delete", key=f"delete-{original_index}", type="secondary", use_container_width=True):
            delete_event(original_index)


def render_quick_stats(events: list[Event]) -> None:
    today = date.today()
    upcoming = upcoming_events(events)
    due_this_week = events_due_this_week(events)
    overdue = [event for event in events if date.fromisoformat(event.date) < today]

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Upcoming Events", len(upcoming))
    with col2:
        st.metric("Due This Week", len(due_this_week))
    with col3:
        if overdue:
            st.error(f"⚠️ {len(overdue)} Overdue")
        else:
            st.metric("Overdue", "0")


def render_calendar(events: list[Event]) -> None:
    if "calendar_month" not in st.session_state:
        today = date.today()
        st.session_state.calendar_month = date(today.year, today.month, 1)

    current_month: date = st.session_state.calendar_month
    previous_column, title_column, today_column, next_column = st.columns(
        [1, 4, 1, 1],
        vertical_alignment="center",
    )

    with previous_column:
        if st.button("‹", key="calendar-previous", help="Previous month"):
            st.session_state.calendar_month = calendar_month_offset(current_month, -1)
            st.rerun()

    with title_column:
        st.markdown(
            f"<h3 class='calendar-title'>{current_month.strftime('%B %Y')}</h3>",
            unsafe_allow_html=True,
        )

    with today_column:
        if st.button("Today", key="calendar-today"):
            today = date.today()
            st.session_state.calendar_month = date(today.year, today.month, 1)
            st.rerun()

    with next_column:
        if st.button("›", key="calendar-next", help="Next month"):
            st.session_state.calendar_month = calendar_month_offset(current_month, 1)
            st.rerun()

    month_days = calendar.Calendar(firstweekday=6).monthdatescalendar(
        current_month.year,
        current_month.month,
    )
    visible_dates = {day for week in month_days for day in week}
    grouped_events = events_by_date(sorted_events(events), visible_dates)
    weekday_names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    calendar_html = ["<div class='calendar-shell'><div class='calendar-grid'>"]
    for weekday in weekday_names:
        calendar_html.append(f"<div class='calendar-weekday'>{weekday}</div>")

    today = date.today()
    for week in month_days:
        for day in week:
            classes = ["calendar-day"]
            if day.month != current_month.month:
                classes.append("muted-day")
            if day == today:
                classes.append("today")

            calendar_html.append(f"<div class='{' '.join(classes)}'>")
            calendar_html.append(f"<div class='day-number'>{day.day}</div>")

            day_events = grouped_events.get(day, [])

            for event in day_events[:5]:
                category_class = category_css_class(event.category)
                event_title = escape(event.title)
                # Use compact=True to hide "All day" and save vertical space in the pills
                event_time = escape(format_event_time(event, compact=True))
                event_category = escape(event.category)
                
                time_html = f"<span class='event-time'>{event_time}</span>" if event_time else ""
                
                calendar_html.append(
                    "<div "
                    f"class='calendar-event {category_class}'"
                    ">"
                    f"{time_html}"
                    f"<span class='event-title'>{event_title}</span>"
                    "<div class='event-tooltip' role='tooltip'>"
                    f"<div class='tooltip-title'>{event_title}</div>"
                    f"<div><strong>Time:</strong> {escape(format_event_time(event))}</div>"
                    f"<div><strong>Category:</strong> {event_category}</div>"
                    "</div>"
                    "</div>"
                )

            extra_event_count = len(day_events) - 5
            if extra_event_count > 0:
                calendar_html.append(
                    f"<div class='more-events'>+{extra_event_count} more</div>"
                )

            calendar_html.append("</div>")

    calendar_html.append("</div></div>")
    st.markdown("".join(calendar_html), unsafe_allow_html=True)


def main() -> None:
    # Refresh the page automatically every 5000 milliseconds
    st_autorefresh(interval=5000, limit=None, key="planner_autorefresh")

    # Start the bot automatically in the background
    start_telegram_bot()
    
    st.set_page_config(page_title="My Planner", page_icon="📅", layout="wide", initial_sidebar_state="expanded")

    st.markdown(APP_THEME_CSS, unsafe_allow_html=True)

    # 1. COMMAND CENTER (Hero + Input + Manual Escape Hatch)
    st.markdown(
        """
        <header class="planner-hero">
            <div class="hero-emoji">📅</div>
            <h1>My School Planner</h1>
            <p>Neon-powered planning for assignments, exams, projects, and after-school life.</p>
        </header>
        """,
        unsafe_allow_html=True,
    )

    st.text_input(
        "Add a school event",
        key="event_input",
        placeholder="Try: 'Math Quiz next Friday at 10am' or 'Read Chapter 4 tonight'",
        on_change=handle_event_submit,
    )
    
    # --- NEW ESCAPE HATCH: The manual entry form ---
    with st.expander("⚙️ Advanced Add (Manual Entry)", expanded=False):
        with st.form("manual_add_form", clear_on_submit=True):
            col_title, col_cat = st.columns([2, 1])
            with col_title:
                manual_title = st.text_input("Event Title", placeholder="e.g., Chemistry Lab")
            with col_cat:
                manual_category = st.selectbox("Category", ["Assignment", "Test", "Project", "Activity", "General"])
                
            col_date, col_time = st.columns(2)
            with col_date:
                manual_date = st.date_input("Date")
            with col_time:
                manual_time = st.time_input("Time (Optional)", value=None)
                
            submitted = st.form_submit_button("Save Event", type="primary", use_container_width=True)
            
            if submitted:
                if not manual_title.strip():
                    st.error("Please enter an event title.")
                else:
                    time_str = manual_time.strftime("%H:%M") if manual_time else None
                    new_event = Event(
                        title=manual_title.strip(),
                        date=manual_date.isoformat(),
                        time=time_str,
                        category=manual_category
                    )
                    
                    events_list = load_events()
                    events_list.append(new_event)
                    save_events(events_list)
                    
                    time_display = f" at **{time_str}**" if time_str else ""
                    st.session_state.success_message = (
                        f"✨ Saved manually: **{new_event.title}** for **{manual_date.strftime('%a, %b %d')}**"
                        f"{time_display} under **[{new_event.category}]**."
                    )
                    st.rerun()
    # -----------------------------------------------

    if "success_message" in st.session_state:
        st.success(st.session_state.pop("success_message"))
    if "error_message" in st.session_state:
        st.error(st.session_state.pop("error_message"))

    events = load_events()
    purge_expired_events()
    events = load_events()

    # 2. QUICK STATS
    render_quick_stats(events)
    st.divider()

    # 3. CALENDAR
    render_calendar(events)

    # 4. PERSISTENT SIDEBAR
    with st.sidebar:
        st.markdown("### 📋 Upcoming Events")
        upcoming = upcoming_events(events)

        if not upcoming:
            st.info("No upcoming events yet. You're all caught up!")
        else:
            today = date.today()
            indexed_events = list(enumerate(events))
            upcoming_indexed_events = sorted(
                indexed_events, key=lambda item: (item[1].date, item[1].time or "23:59")
            )

            for original_index, event in upcoming_indexed_events:
                if date.fromisoformat(event.date) < today:
                    continue
                render_event_card(event, original_index)
                
        st.divider()
        if events and st.button("🗑️ Clear All Events", type="primary", use_container_width=True):
            clear_events()


if __name__ == "__main__":
    main()