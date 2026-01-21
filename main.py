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
    context.chat_data.setdefault("subscriptions", set())

    await update.effective_message.reply_text(
        "Choose the department you want to subscribe to:",
        reply_markup=branch_keyboard(branches),
    )


async def stop(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    subs = context.application.bot_data.get("subscriptions", {})

    removed = False
    for branch, chats in subs.items():
        if chat_id in chats:
            chats.remove(chat_id)
            removed = True

    if removed:
        await update.effective_message.reply_text(
            "You have been unsubscribed from all departments."
        )
        logger.info(f"User {chat_id} unsubscribed from all departments")
    else:
        await update.effective_message.reply_text(
            "You were not subscribed to any department."
        )


async def branch_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    branch = query.data
    chat_id = query.message.chat_id

    subs = context.application.bot_data.setdefault("subscriptions", {})
    subs.setdefault(branch, set()).add(chat_id)

    await query.edit_message_text(
        f"Subscribed to {branch}\nYou will now receive updates automatically. Use `/start` again to add more departments."
    )

    logger.info(f"User {user.id} subscribed to {branch}")


async def scrape_and_fanout(context: CallbackContext):
    bot_data = context.application.bot_data
    scrapers = bot_data["scrapers"]
    subscriptions = bot_data["subscriptions"]
    cursors = bot_data["branch_last_seen"]

    for branch, scraper in scrapers.items():
        try:
            notices = scraper.get_all_notices()
            last_seen = cursors.get(branch)
            if last_seen is None:
                if notices:
                    cursors[branch] = notices[0].id if notices else None
                continue

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


async def error_handler(update: Update, context: CallbackContext):
    logger.error(
        f"Update {update} caused error: {context.error}", exc_info=context.error
    )


def main() -> None:
    load_dotenv()
    setup_logging()
    logger.info("Starting notification bot")
    TOKEN = os.environ.get("BOT_TOKEN")
    url = "https://www.imsnsit.org/imsnsit/notifications.php"
    branches = get_all_branches(url)
    SCRAPERS = {branch: Scraper(branch) for branch in branches}
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_error_handler(error_handler)
    app.bot_data["branches"] = branches
    app.bot_data["scrapers"] = SCRAPERS
    app.bot_data["subscriptions"] = {}
    app.bot_data["branch_last_seen"] = {}

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(branch_selected))
    app.add_handler(CommandHandler("stop", stop))
    logger.info("Bot is now running and polling for updates")
    app.run_polling()


if __name__ == "__main__":
    main()
