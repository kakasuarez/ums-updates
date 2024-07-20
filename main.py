from telegram import Update
from telegram.ext import (
    CommandHandler,
    ApplicationBuilder,
    ContextTypes,
)
import os
from scrape import Scraper

last_seen_notice = "JOINT PLAN OF END SUMMER SEM EXAMINATION TO BE HELD ON 22/07/2024 (FN) .NOTE : DETAINED STUDENTS ARE NOT ALLOWED IN THAT SEMESTER"


async def callback_notices(context: ContextTypes.DEFAULT_TYPE):
    global last_seen_notice
    scraper = Scraper(last_seen_notice=last_seen_notice)
    new_notices = scraper.get_new_notices()
    if new_notices:
        for notice in new_notices:
            message_to_be_sent = (
                f"[{notice.escaped_title()}]({notice.url})"
                if notice.url
                else notice.title
            )
            await context.bot.send_message(
                chat_id=context.job.chat_id,
                text=message_to_be_sent,
                parse_mode="MarkdownV2" if notice.url else None,
            )
        last_seen_notice = new_notices[0]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_message.chat_id
    await update.message.reply_text("You have subscribed to notifications.")
    job_queue = context.job_queue
    job_queue.run_repeating(callback_notices, 600, chat_id=chat_id, first=2)


def main() -> None:
    TOKEN = os.environ.get("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()


if __name__ == "__main__":
    main()
