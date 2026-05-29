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
    /* WARM MATTE PALETTE (Espresso / Cozy) */
    --warm0: #2a2725; /* Main background - Deep Warm Brown */
    --warm1: #36322f; /* Lighter background / Panels */
    --warm2: #45403c; /* Hover states / Selections */
    --warm3: #58524d; /* Borders / Line dividers */
    
    --warm4: #a8a198; /* Sub-text / Muted text */
    --warm5: #dcd5c9; /* Standard text */
    --warm6: #f4ece0; /* Bright text / Headings - Cream */
    
    /* Warm Accents */
    --warm-accent: #c98a6c; /* Primary Focus / Copper */
    
    /* Category Colors */
    --warm-ex: #c67a73; /* Muted Terracotta (Exams) */
    --warm-gn: #d4a76a; /* Mustard (General) */
    --warm-cl: #9ba87d; /* Olive/Sage (Clubs) */
    --warm-pr: #b394a4; /* Dusty Mauve (Projects) */
    --warm-hw: #82939f; /* Muted Slate (Homework) */

    --panel: var(--warm1);
    --panel-strong: var(--warm2);
    --line: var(--warm3);
    --ink: var(--warm6);
    --muted: var(--warm4);
}

html, body, [class*="css"] {
    font-family: 'Lexend', sans-serif;
}

.stApp {
    background: var(--warm0);
    color: var(--ink);
}

[data-testid="stSidebar"] {
    background: var(--warm1);
    border-right: 1px solid var(--line);
    padding-top: 2rem;
}

.block-container {
    max-width: 1480px;
    padding: 1.5rem 2rem 2rem;
}

.planner-hero {
    border: 1px solid var(--line);
    border-radius: 12px;
    background: var(--panel);
    margin-bottom: 0.5rem;
    padding: 1.2rem;
    text-align: center;
}

.hero-emoji {
    font-size: 2.8rem;
    line-height: 1;
    margin-bottom: 0.2rem;
}

.planner-hero h1 {
    color: var(--ink);
    font-size: clamp(1.8rem, 3vw, 2.6rem);
    font-weight: 700;
    letter-spacing: -0.5px;
    margin: 0;
}

.planner-hero p {
    color: var(--muted);
    font-size: 0.95rem;
    margin: 0.5rem auto 0;
    max-width: 720px;
}

h1, h2, h3, h4, label, p, span, div {
    font-family: 'Lexend', sans-serif;
}

h2, h3 {
    color: var(--ink);
    font-weight: 600;
}

/* --- THE GIANT "SEARCH ENGINE" INPUT --- */
div[data-testid="stTextInput"]:has(input[aria-label="Add a school event"]) {
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
}

div[data-testid="stTextInput"]:has(input[aria-label="Add a school event"]) label {
    display: none;
}

input[aria-label="Add a school event"] {
    background: var(--warm1);
    border: 2px solid var(--warm3);
    border-radius: 12px;
    color: var(--ink);
    font-size: 1.15rem;
    line-height: 1.5;
    padding: 1rem 1.2rem;
    min-height: 4.5rem;
    text-align: center;
    transition: all 150ms ease;
    box-shadow: none; /* Flat design */
}

input[aria-label="Add a school event"]:focus {
    border-color: var(--warm-accent);
    background: var(--warm2);
    outline: none;
}

input[aria-label="Add a school event"]::placeholder {
    color: var(--warm3);
    font-weight: 400;
}
/* --------------------------------------- */

.stButton > button {
    background: var(--warm1);
    border: 1px solid var(--warm3);
    border-radius: 8px;
    color: var(--warm5);
    font-weight: 500;
    transition: all 150ms ease;
}

.stButton > button:hover {
    border-color: var(--warm-accent);
    background: var(--warm2);
    color: var(--warm6);
}

[data-testid="stMetric"],
[data-testid="stAlert"],
details {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 12px;
}

[data-testid="stMetric"] {
    padding: 0.85rem 1rem;
    text-align: center;
}

details {
    margin-bottom: 0.65rem;
    overflow: hidden;
    transition: all 150ms ease;
}

details:hover {
    border-color: var(--warm-accent);
    background: var(--panel-strong);
}

details summary {
    color: var(--warm5);
    font-weight: 600;
}

.calendar-title {
    color: var(--ink);
    margin: 0.8rem 0 0.4rem;
    text-align: center;
    font-size: 1.6rem;
}

.calendar-shell {
    width: 100%;
    margin: 0.25rem 0 1.5rem;
    overflow: visible;
}

.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 0.35rem;
    overflow: visible;
}

.calendar-weekday {
    color: var(--warm4);
    font-size: 0.8rem;
    font-weight: 600;
    text-align: center;
    text-transform: uppercase;
}

.calendar-day {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 10px;
    /* REDUCED HEIGHT VERY SLIGHTLY */
    min-height: clamp(100px, 11vh, 150px); 
    padding: 0.5rem;
    overflow: visible;
    position: relative;
}

.calendar-day.today {
    background: var(--warm2);
    border-color: var(--warm-accent);
}

.calendar-day.today .day-number {
    align-items: center;
    background: var(--warm-accent);
    border-radius: 6px;
    color: var(--warm0);
    display: inline-flex;
    height: 1.6rem;
    justify-content: center;
    width: 1.6rem;
}

.calendar-day.muted-day {
    background: rgba(54, 50, 47, 0.4); /* Faded Warm1 */
    border-color: transparent;
}

.calendar-day.muted-day .day-number {
    color: var(--warm3);
}

.day-number {
    color: var(--warm5);
    font-size: 0.9rem;
    font-weight: 700;
    line-height: 1;
    margin-bottom: 0.3rem;
}

/* MATTE WARM PILLS */
.calendar-event {
    border: 1px solid transparent;
    border-radius: 6px;
    color: var(--warm5);
    cursor: default;
    font-size: 0.78rem;
    line-height: 1.3;
    margin-top: 0.3rem;
    padding: 0.3rem 0.4rem;
    position: relative;
    transition: all 100ms ease;
    z-index: 1;
}

.calendar-event:hover {
    z-index: 20;
}

.event-time {
    color: var(--warm4);
    display: block;
    font-size: 0.7rem;
    font-weight: 600;
    margin-bottom: 0.1rem;
}

.event-title {
    display: -webkit-box;
    -webkit-line-clamp: 2; 
    -webkit-box-orient: vertical;
    overflow: hidden;
    white-space: normal; 
    word-wrap: break-word;
}

.event-tooltip {
    background: var(--warm1);
    border: 1px solid var(--warm3);
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(42, 39, 37, 0.8);
    color: var(--warm5);
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
    background: var(--warm1);
    border-left: 1px solid var(--warm3);
    border-top: 1px solid var(--warm3);
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
    color: var(--warm-accent);
    font-size: 0.9rem;
    font-weight: 700;
    margin-bottom: 0.35rem;
}

/* Category Warm Matte Variations */
.calendar-event.homework { 
    background: rgba(130, 147, 159, 0.15); 
    border-left: 3px solid var(--warm-hw); 
}
.calendar-event.homework:hover { background: rgba(130, 147, 159, 0.25); }

.calendar-event.exams { 
    background: rgba(198, 122, 115, 0.15); 
    border-left: 3px solid var(--warm-ex); 
}
.calendar-event.exams:hover { background: rgba(198, 122, 115, 0.25); }

.calendar-event.clubs { 
    background: rgba(155, 168, 125, 0.15); 
    border-left: 3px solid var(--warm-cl); 
}
.calendar-event.clubs:hover { background: rgba(155, 168, 125, 0.25); }

.calendar-event.projects { 
    background: rgba(179, 148, 164, 0.15); 
    border-left: 3px solid var(--warm-pr); 
}
.calendar-event.projects:hover { background: rgba(179, 148, 164, 0.25); }

.calendar-event.general { 
    background: rgba(212, 167, 106, 0.15); 
    border-left: 3px solid var(--warm-gn); 
}
.calendar-event.general:hover { background: rgba(212, 167, 106, 0.25); }

.more-events {
    color: var(--warm4);
    font-size: 0.72rem;
    font-weight: 600;
    margin-top: 0.3rem;
}

@media (max-width: 760px) {
    .block-container { padding-left: 0.75rem; padding-right: 0.75rem; }
    .planner-hero { padding: 1rem; }
    .calendar-grid { gap: 0.28rem; }
    .calendar-day { min-height: 90px; padding: 0.25rem; }
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

            for event in day_events[:4]: # Show max 4 events per day in smaller boxes
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

            extra_event_count = len(day_events) - 4
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

    events = load_events()
    purge_expired_events()
    events = load_events()

    # ---------------------------------------------------------
    # LAYOUT REDESIGN: Two-Column Split (Adjusted ratio)
    # ---------------------------------------------------------
    left_col, right_col = st.columns([1, 2.0], gap="large")

    with left_col:
        # 1. COMMAND CENTER (Hero + Input + Manual Escape Hatch)
        st.markdown(
            """
            <header class="planner-hero">
                <div class="hero-emoji">📅</div>
                <h1>My School Planner</h1>
                <p>Clean, warm-matte planning for assignments, exams, projects, and after-school life.</p>
            </header>
            """,
            unsafe_allow_html=True,
        )

        st.text_input(
            "Add a school event",
            key="event_input",
            placeholder="Try: 'Math Quiz next Friday at 10am'",
            on_change=handle_event_submit,
        )
        
        # --- ESCAPE HATCH: The manual entry form ---
        with st.expander("⚙️ Advanced Add (Manual Entry)", expanded=False):
            with st.form("manual_add_form", clear_on_submit=True):
                # Inputs are stacked vertically to fit the narrow left column perfectly
                manual_title = st.text_input("Event Title", placeholder="e.g., Chemistry Lab")
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

        st.divider()

        # 2. QUICK STATS
        render_quick_stats(events)

    with right_col:
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