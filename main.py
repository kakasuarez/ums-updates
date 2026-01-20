from telegram import Update
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    CallbackContext,
)
from dotenv import load_dotenv
import os
from scrape import Scraper
from chat_options import (
    get_chat_options,
    job_name,
    get_new_chat_options,
)


def ensure_notice_job(chat_id: int, context: CallbackContext):
    options = get_chat_options(context.chat_data)
    name = job_name(chat_id)
    existing = context.job_queue.get_jobs_by_name(name)
    if existing:
        return

    context.job_queue.run_repeating(
        callback_notices,
        options.interval,
        chat_id=chat_id,
        first=options.first,
        name=name,
    )


async def callback_notices(context: CallbackContext):
    chat_id = context.job.chat_id
    chat_data = context.chat_data
    scraper = chat_data["scraper"]
    new_notices = scraper.get_new_notices()
    if new_notices:
        for notice in new_notices:
            message_to_be_sent = (
                f"New notice on IMS: [{notice.escaped_title()}]({notice.url})"
                if notice.url
                else "New notice on IMS: " + notice.title
            )
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=message_to_be_sent,
                parse_mode="MarkdownV2" if notice.url else None,
            )


async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    new_scraper = Scraper()
    context.chat_data.setdefault("options", get_new_chat_options())
    context.chat_data.setdefault("scraper", new_scraper)
    ensure_notice_job(chat_id, context)
    await update.effective_message.reply_text("You have subscribed to notifications.")


def main() -> None:
    load_dotenv()
    TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("The bot is running!")
    app.run_polling()


if __name__ == "__main__":
    main()
