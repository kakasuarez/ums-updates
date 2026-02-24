from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    CallbackContext,
    CallbackQueryHandler,
)
from dotenv import load_dotenv
import os
import logging
from scrape import Scraper, get_all_branches
from logging_config import setup_logging
from database_handling import DatabaseHandler

logger = logging.getLogger(__name__)


def branch_keyboard(branches):
    keyboard = [
        [InlineKeyboardButton(branch, callback_data=branch)] for branch in branches
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: CallbackContext) -> None:

    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started bot")

    branches = context.application.bot_data["branches"]

    await update.effective_message.reply_text(
        "Choose the department you want to subscribe to:",
        reply_markup=branch_keyboard(branches),
    )


async def stop(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    db = context.application.bot_data["db"]

    db.remove_subscription(chat_id)
    context.application.bot_data["subscriptions"] = db.load_subscriptions()

    await update.effective_message.reply_text(
        "You have been unsubscribed from all departments."
    )
    logger.info(f"User {chat_id} unsubscribed from all departments")


async def branch_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    branch = query.data
    chat_id = query.message.chat_id

    db = context.application.bot_data["db"]
    db.save_subscription(chat_id, branch)
    context.application.bot_data["subscriptions"] = db.load_subscriptions()

    await query.edit_message_text(
        f"Subscribed to {branch}\nYou will now receive updates automatically. Use `/start` again to add more departments."
    )

    logger.info(f"User {query.from_user.id} subscribed to {branch}")


async def scrape_and_fanout(context: CallbackContext):
    bot_data = context.application.bot_data
    scrapers = bot_data["scrapers"]
    subscriptions = bot_data["subscriptions"]
    cursors = bot_data["branch_last_seen"]

    for branch, scraper in scrapers.items():
        try:
            notices = scraper.get_all_notices()
            if branch not in cursors:
                if subscriptions.get(branch):
                    if notices:
                        cursors[branch] = notices[0].id
                continue

            last_seen = cursors[branch]
            new = []
            for notice in notices:
                if notice.id == last_seen:
                    break
                new.append(notice)

            if not new:
                continue

            logger.info(f"Found {len(new)} new notice(s) for {branch}")
            cursors[branch] = new[0].id

            for chat_id in subscriptions.get(branch, set()):
                for notice in reversed(new):
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=(
                            f"New notice on IMS: "
                            f"[{notice.escaped_title()}]({notice.url})"
                            if notice.url
                            else notice.title
                        ),
                        parse_mode="MarkdownV2" if notice.url else None,
                    )
            subscriber_count = len(subscriptions.get(branch, set()))
            logger.info(f"Sent {len(new)} notices to {subscriber_count} subscribers")
        except Exception as e:
            logger.error(f"Error scraping {branch}: {e}", exc_info=True)


async def post_init(app):
    app.job_queue.run_repeating(
        scrape_and_fanout,
        interval=600,
        first=2,
        name="global_scrape",
    )


async def post_shutdown(app):
    db = app.bot_data.get("db")
    if db:
        db.close()


async def error_handler(update: Update, context: CallbackContext):
    logger.error(
        f"Update {update} caused error: {context.error}", exc_info=context.error
    )


def main() -> None:
    load_dotenv()
    setup_logging()
    db = DatabaseHandler()
    logger.info("Starting notification bot")
    TOKEN = os.environ.get("BOT_TOKEN")
    url = "https://www.imsnsit.org/imsnsit/notifications.php"
    branches = get_all_branches(url)
    SCRAPERS = {branch: Scraper(branch) for branch in branches}
    app = (
        ApplicationBuilder()
        .token(TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )
    app.add_error_handler(error_handler)
    app.bot_data["db"] = db
    app.bot_data["branches"] = branches
    app.bot_data["scrapers"] = SCRAPERS
    subs = db.load_subscriptions()
    app.bot_data["subscriptions"] = subs
    logger.info(
        "Loaded %d subscriptions across %d branches",
        sum(len(v) for v in subs.values()),
        len(subs),
    )
    app.bot_data["branch_last_seen"] = {}

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(branch_selected))
    app.add_handler(CommandHandler("stop", stop))
    logger.info("Bot is now running and polling for updates")
    app.run_polling()


if __name__ == "__main__":
    main()
