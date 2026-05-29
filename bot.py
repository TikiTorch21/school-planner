import os
import logging
from datetime import date, timedelta, time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Import your existing planner logic
from planner import add_event, load_events, purge_expired_events

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Safely get the tokens
BOT_TOKEN = os.getenv("BOT_TOKEN")
MY_CHAT_ID = os.getenv("MY_CHAT_ID")

if not BOT_TOKEN:
    raise ValueError("No BOT_TOKEN found! Make sure you have a .env file with your token.")

# --- THE AUTOMATED DAILY REMINDER ---
async def daily_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check tomorrow's schedule and send a proactive message."""
    if not MY_CHAT_ID:
        logging.warning("Daily reminder skipped: MY_CHAT_ID is not set in the .env file.")
        return

    events = load_events()
    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()
    
    # Filter for only tomorrow's events
    tomorrow_events = [e for e in events if e.date == tomorrow_str]

    # If nothing is due, we stay silent so we don't spam you!
    if not tomorrow_events:
        return

    text = f"🔔 *Heads Up! Here is your schedule for tomorrow ({tomorrow.strftime('%a, %b %d')}):*\n\n"
    for e in tomorrow_events:
        time_str = f" at {e.time}" if e.time else " (All day)"
        text += f"• *{e.title}*{time_str} [{e.category}]\n"

    # Send the proactive message
    await context.bot.send_message(chat_id=MY_CHAT_ID, text=text, parse_mode="Markdown")
# ------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message with instructions."""
    welcome_text = (
        "👋 *Welcome to your School Planner Bot!*\n\n"
        "You can text me an event like 'History essay due next Friday at 3pm' "
        "and I'll add it to your calendar.\n\n"
        "Try these commands:\n"
        "📅 /today - See what is due today\n"
        "🔮 /upcoming - View your schedule\n"
        "📊 /stats - Get a quick overview\n"
        "🔑 /my_id - Get your Chat ID for daily reminders\n"
        "🆘 /help - Show this menu again"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def get_id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Give the user their Chat ID so they can put it in the .env file."""
    user_id = update.effective_chat.id
    msg = (
        "Here is your unique Chat ID:\n"
        f"`{user_id}`\n\n"
        "Copy this number, open your `.env` file, and paste it so it looks like this:\n"
        "`MY_CHAT_ID=123456789`\n\n"
        "Once you restart the app, daily 5:30 PM reminders will be activated!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the command cheat sheet."""
    help_text = (
        "🛠️ *Planner Commands*\n\n"
        "• Just type naturally to add an event.\n"
        "• /today - Events due exactly today\n"
        "• /upcoming - Next 10 scheduled events\n"
        "• /stats - Quick dashboard numbers\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display events due today."""
    events = load_events()
    today_str = date.today().isoformat()
    today_events = [e for e in events if e.date == today_str]

    if not today_events:
        await update.message.reply_text("🎉 *All caught up!* You have nothing scheduled for today.", parse_mode="Markdown")
        return

    text = "📅 *Due Today:*\n\n"
    for e in today_events:
        time_str = f" at {e.time}" if e.time else " (All day)"
        text += f"• *{e.title}*{time_str} [{e.category}]\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def upcoming_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display the next several upcoming events."""
    purge_expired_events()
    events = load_events()
    
    if not events:
        await update.message.reply_text("📭 Your planner is completely empty!", parse_mode="Markdown")
        return

    text = "🔮 *Upcoming Schedule:*\n\n"
    for e in events[:10]:
        e_date = date.fromisoformat(e.date).strftime("%a, %b %d")
        time_str = f" at {e.time}" if e.time else ""
        text += f"• *{e.title}* - {e_date}{time_str} [{e.category}]\n"

    if len(events) > 10:
        text += f"\n_...and {len(events) - 10} more. Open your app to see the full calendar!_"
    await update.message.reply_text(text, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show quick metrics mirroring the Streamlit app."""
    events = load_events()
    today = date.today()
    end_of_week = today + timedelta(days=6 - today.weekday())
    
    upcoming_count = len([e for e in events if date.fromisoformat(e.date) >= today])
    due_this_week = len([e for e in events if today <= date.fromisoformat(e.date) <= end_of_week])
    overdue_count = len([e for e in events if date.fromisoformat(e.date) < today])
    
    text = "📊 *Quick Stats:*\n\n"
    text += f"🗓️ Upcoming Events: *{upcoming_count}*\n"
    text += f"🎯 Due This Week: *{due_this_week}*\n"
    
    if overdue_count > 0:
        text += f"⚠️ Overdue Events: *{overdue_count}*"
    else:
        text += "✨ Overdue Events: *0* (Great job!)"
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process natural language to add events."""
    user_text = update.message.text
    try:
        event = add_event(user_text)
        time_display = f" at {event.time}" if event.time else ""
        reply_text = f"✨ Saved: *{event.title}* for {event.date}{time_display} \\[{event.category}\\]."
        await update.message.reply_text(reply_text, parse_mode="Markdown")
    except ValueError as error:
        await update.message.reply_text(f"⚠️ {str(error)}")

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # --- SCHEDULE THE DAILY JOB ---
    # Set the timezone to US Eastern Time
    est_tz = ZoneInfo("America/New_York")
    # Set the target time to 17:30 (5:30 PM)
    target_time = time(hour=17, minute=30, tzinfo=est_tz)
    
    # Add the daily job to the queue
    application.job_queue.run_daily(daily_reminder, time=target_time)
    # ------------------------------

    # Register commands
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("upcoming", upcoming_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("my_id", get_id_command))

    # Register natural language input handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running! Background schedules are active.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()