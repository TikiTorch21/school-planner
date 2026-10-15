import os
import logging
from collections import defaultdict
from datetime import date, datetime, timedelta, time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from planner import Event, add_event, load_events, purge_expired_events

load_dotenv()
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found! Make sure you have a .env file with your token.")


# ==========================================
# 🎨 SHARED FORMATTING HELPERS
# ==========================================

CATEGORY_ICONS = {
    "Test": "🚨",
    "Assignment": "📝",
    "Project": "🛠️",
    "Activity": "🏆",
    "General": "📌",
}

def format_12hr_time(time_str: str | None) -> str:
    """Convert '14:30' to '2:30 PM'."""
    if not time_str:
        return ""
    dt = datetime.strptime(time_str, "%H:%M")
    return dt.strftime("%I:%M %p").lstrip("0")

def format_event_line(event: Event) -> str:
    """Format a single event consistently across all bot commands."""
    icon = CATEGORY_ICONS.get(event.category, "📌")
    time_badge = f" • `{format_12hr_time(event.time)}`" if event.time else ""
    return f"  {icon} {event.title}{time_badge}"

def format_friendly_date(target_date: date, today: date) -> str:
    """Turn raw dates into scannable headers with relative day counts."""
    delta = (target_date - today).days
    date_str = target_date.strftime("%a, %b %d")
    
    if delta == 0:
        return f"🔥 *Today — {date_str}*"
    if delta == 1:
        return f"📌 *Tomorrow — {date_str}*"
    if 1 < delta <= 6:
        return f"🗓️ *{target_date.strftime('%A, %b %d')}* _(in {delta} days)_"
    return f"🗓️ *{date_str}* _(in {delta} days)_"


# ==========================================
# 🤖 BOT COMMANDS & JOBS
# ==========================================

async def daily_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check tomorrow's schedule at 5:30 PM and send a proactive message."""
    if not MY_CHAT_ID:
        logging.warning("Daily reminder skipped: MY_CHAT_ID is not set in .env.")
        return

    events = load_events()
    tomorrow = date.today() + timedelta(days=1)
    tomorrow_events = [e for e in events if e.date == tomorrow.isoformat()]

    if not tomorrow_events:
        return

    lines = [f"🔔 *Heads Up! Schedule for tomorrow ({tomorrow.strftime('%a, %b %d')}):*\n"]
    lines.extend(format_event_line(e) for e in tomorrow_events)

    await context.bot.send_message(chat_id=MY_CHAT_ID, text="\n".join(lines), parse_mode="Markdown")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with instructions."""
    welcome_text = (
        "👋 *Welcome to your School Planner Bot!*\n\n"
        "Text me an event like `'History essay due next Friday at 3pm'` "
        "and I'll add it to your calendar.\n\n"
        "*Commands:*\n"
        "📅 /today — See what is due today\n"
        "🔮 /upcoming — View your grouped schedule\n"
        "📊 /stats — Quick overview\n"
        "🔑 /my_id — Get your Chat ID for daily reminders\n"
        "🆘 /help — Command cheat sheet"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the command cheat sheet."""
    help_text = (
        "🛠️ *Planner Commands*\n\n"
        "• Type naturally to add an event\n"
        "• /today — Events due today\n"
        "• /upcoming — Next 12 scheduled events\n"
        "• /stats — Quick dashboard numbers\n\n"
        "*Category Icons:*\n"
        "🚨 Test  |  📝 Assignment  |  🛠️ Project\n"
        "🏆 Activity  |  📌 General"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def get_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Give the user their Chat ID for the .env file."""
    user_id = update.effective_chat.id
    msg = (
        f"Your unique Chat ID is: `{user_id}`\n\n"
        "Add this to your `.env` file:\n"
        f"`MY_CHAT_ID={user_id}`\n\n"
        "Restart the app to activate daily 5:30 PM reminders!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display events due today."""
    events = load_events()
    today_str = date.today().isoformat()
    today_events = [e for e in events if e.date == today_str]

    if not today_events:
        await update.message.reply_text("🎉 *All caught up!* Nothing scheduled for today.", parse_mode="Markdown")
        return

    lines = [f"🔥 *Due Today ({date.today().strftime('%a, %b %d')}):*\n"]
    lines.extend(format_event_line(e) for e in today_events)
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def upcoming_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display upcoming events grouped cleanly by date."""
    purge_expired_events()
    events = load_events()
    
    if not events:
        await update.message.reply_text("📭 Your planner is completely empty!", parse_mode="Markdown")
        return

    today = date.today()
    grouped: dict[date, list[Event]] = defaultdict(list)
    for e in events[:12]:
        grouped[date.fromisoformat(e.date)].append(e)

    lines = ["🔮 *Upcoming Schedule*\n"]
    for event_date, day_events in grouped.items():
        lines.append(format_friendly_date(event_date, today))
        lines.extend(format_event_line(e) for e in day_events)
        lines.append("")  # Blank line between dates

    if len(events) > 12:
        lines.append(f"_...and {len(events) - 12} more on your dashboard._\n")

    lines.append("─" * 18)
    lines.append("_🚨 Test  📝 HW  🛠️ Proj  🏆 Club  📌 Gen_")

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show quick metrics mirroring the Streamlit app."""
    events = load_events()
    today = date.today()
    end_of_week = today + timedelta(days=6 - today.weekday())
    
    upcoming_count = sum(1 for e in events if date.fromisoformat(e.date) >= today)
    due_this_week = sum(1 for e in events if today <= date.fromisoformat(e.date) <= end_of_week)
    overdue_count = sum(1 for e in events if date.fromisoformat(e.date) < today)
    
    overdue_line = (
        f"⚠️ Overdue Events: *{overdue_count}*"
        if overdue_count > 0
        else "✨ Overdue Events: *0* (Great job!)"
    )

    text = (
        "📊 *Quick Stats*\n\n"
        f"🗓️ Upcoming Events: *{upcoming_count}*\n"
        f"🎯 Due This Week: *{due_this_week}*\n"
        f"{overdue_line}"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process natural language to add events."""
    user_text = update.message.text
    try:
        event = add_event(user_text)
        icon = CATEGORY_ICONS.get(event.category, "📌")
        friendly_date = date.fromisoformat(event.date).strftime("%a, %b %d")
        time_display = f" at `{format_12hr_time(event.time)}`" if event.time else ""
        
        reply_text = f"✨ *Saved!* {icon} *{event.title}*\n📅 {friendly_date}{time_display}"
        await update.message.reply_text(reply_text, parse_mode="Markdown")
    except ValueError as error:
        await update.message.reply_text(f"⚠️ {error}")


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Schedule daily 5:30 PM EST reminder
    target_time = time(hour=17, minute=30, tzinfo=ZoneInfo("America/New_York"))
    application.job_queue.run_daily(daily_reminder, time=target_time)

    # Register commands
    commands = [
        ("start", start_command),
        ("help", help_command),
        ("today", today_command),
        ("upcoming", upcoming_command),
        ("stats", stats_command),
        ("my_id", get_id_command),
    ]
    for cmd_name, handler_func in commands:
        application.add_handler(CommandHandler(cmd_name, handler_func))

    # Register natural language input handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running! Background schedules are active.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()