from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

from dateparser import parse
from dateparser.search import search_dates


EVENTS_FILE = Path("events.json")


@dataclass
class Event:
    title: str
    date: str
    time: str | None
    category: str


def load_events() -> list[Event]:
    """Load saved events from events.json, ignoring malformed records safely."""
    if not EVENTS_FILE.exists():
        return []

    try:
        with EVENTS_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(data, list):
        return []

    events: list[Event] = []
    for item in data:
        event = _event_from_dict(item)
        if event is not None:
            events.append(event)

    return sorted(events, key=_sort_key)


def save_events(events: list[Event]) -> None:
    """Save events to events.json in chronological order."""
    sorted_event_data = [asdict(event) for event in sorted(events, key=_sort_key)]
    temporary_file = EVENTS_FILE.with_suffix(".json.tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(sorted_event_data, file, indent=2)

    temporary_file.replace(EVENTS_FILE)

def purge_expired_events() -> int:
    """Remove events older than today. Returns count of removed events."""
    events = load_events()
    today = date.today().isoformat()
    current_events = [e for e in events if e.date >= today]
    removed = len(events) - len(current_events)
    if removed:
        save_events(current_events)
    return removed


def parse_event(raw_text: str) -> Event:
    """Parse a natural-language event into a structured Event."""
    cleaned_text = raw_text.strip()
    if not cleaned_text:
        raise ValueError("Please type an event with a date or time.")

    parser_settings: dict[str, Any] = {
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": datetime.now(),
        "RETURN_AS_TIMEZONE_AWARE": False,
    }
    parsed_dates = search_dates(
        cleaned_text,
        settings=parser_settings,
    )

    if not parsed_dates:
        raise ValueError("I could not find a date or time in that event.")

    matched_text, searched_datetime = parsed_dates[0]
    # search_dates can preserve the phrase but miss the explicit time, so re-parse it.
    parsed_datetime = parse(matched_text, settings=parser_settings) or searched_datetime
    title = _clean_title(cleaned_text, matched_text)
    category = _guess_category(cleaned_text)

    return Event(
        title=title,
        date=parsed_datetime.date().isoformat(),
        time=_event_time(parsed_datetime, matched_text),
        category=category,
    )


def add_event(raw_text: str) -> Event:
    """Parse a natural-language event, save it, and return the new event."""
    event = parse_event(raw_text)
    purge_expired_events()
    events = load_events()
    events.append(event)
    save_events(events)
    return event


def _event_from_dict(item: Any) -> Event | None:
    if not isinstance(item, dict):
        return None

    title = item.get("title")
    event_date = item.get("date")
    event_time = item.get("time")
    category = item.get("category")

    if not isinstance(title, str) or not isinstance(event_date, str):
        return None
    if event_time is not None and not isinstance(event_time, str):
        return None
    if not isinstance(category, str):
        category = "General"

    try:
        date.fromisoformat(event_date)
        if event_time is not None:
            datetime.strptime(event_time, "%H:%M")
    except ValueError:
        return None

    return Event(
        title=title.strip() or "Untitled event",
        date=event_date,
        time=event_time,
        category=category.strip() or "General",
    )


def display_events(events: list[Event] | None = None) -> None:
    """Print events grouped by Today, This Week, and Later."""
    events = load_events() if events is None else sorted(events, key=_sort_key)
    if not events:
        print("No events saved yet.")
        return

    today = date.today()
    end_of_week = today + timedelta(days=6 - today.weekday())
    groups: dict[str, list[Event]] = {
        "Today": [],
        "This Week": [],
        "Later": [],
    }
    overdue: list[Event] = []

    for event in events:
        event_date = date.fromisoformat(event.date)
        if event_date < today:
            overdue.append(event)
        elif event_date == today:
            groups["Today"].append(event)
        elif event_date <= end_of_week:
            groups["This Week"].append(event)
        else:
            groups["Later"].append(event)

    if overdue:
        _print_group("Overdue", overdue)

    for heading, grouped_events in groups.items():
        _print_group(heading, grouped_events)


def _clean_title(raw_text: str, matched_text: str) -> str:
    title = raw_text.replace(matched_text, "", 1)
    title = re.sub(
        r"\b(due|on|at|by|for|next|this|today|tomorrow|yesterday)\b",
        " ",
        title,
        flags=re.IGNORECASE,
    )
    title = re.sub(r"\s+", " ", title).strip(" ,.-")
    return title or "Untitled event"


def _guess_category(raw_text: str) -> str:
    text = raw_text.lower()
    category_keywords = {
        "Test": ("test", "exam", "quiz", "midterm", "final"),
        "Assignment": ("homework", "essay", "paper", "worksheet", "assignment", "due"),
        "Project": ("project", "presentation", "lab", "report"),
        "Activity": ("practice", "game", "club", "meeting", "rehearsal"),
    }

    for category, keywords in category_keywords.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "General"


def _event_time(parsed_datetime: datetime, matched_text: str) -> str | None:
    has_time = re.search(
        r"\b(\d{1,2}:\d{2}|\d{1,2}\s*(am|pm)|noon|midnight)\b",
        matched_text,
        flags=re.IGNORECASE,
    )
    if not has_time or parsed_datetime.time() == time.min:
        return None
    return parsed_datetime.strftime("%H:%M")


def _sort_key(event: Event) -> tuple[str, str]:
    return event.date, event.time or "23:59"


def _print_group(heading: str, events: list[Event]) -> None:
    print(f"\n{heading}")
    print("-" * len(heading))

    if not events:
        print("  No events.")
        return

    for event in events:
        event_date = date.fromisoformat(event.date).strftime("%a, %b %d")
        event_time = f" at {event.time}" if event.time else ""
        print(f"  {event_date}{event_time} | {event.category} | {event.title}")


def main() -> None:
    print("Study Planner")
    print("Type an event, 'list' to view events, or 'quit' to exit.")

    while True:
        raw_text = input("\n> ").strip()

        if not raw_text:
            continue

        command = raw_text.lower()
        if command in {"quit", "exit"}:
            break
        if command == "list":
            display_events()
            continue

        try:
            event = add_event(raw_text)
        except ValueError as error:
            print(error)
            continue

        event_time = f" at {event.time}" if event.time else ""
        print(f"Saved: {event.title} on {event.date}{event_time} [{event.category}]")


if __name__ == "__main__":
    main()
