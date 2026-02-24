from telegram import Bot
from telegram.error import Forbidden, BadRequest
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = Bot(BOT_TOKEN)

CHAT_IDS = []


async def test():
    for cid in CHAT_IDS:
        try:
            await bot.send_message(
                chat_id=cid, text="Test message — validating subscription."
            )
            print(f"OK: {cid}")

        except Forbidden:
            print(f"BLOCKED or left chat: {cid}")

        except BadRequest as e:
            print(f"INVALID chat id {cid}: {e}")

        except Exception as e:
            print(f"OTHER error for {cid}: {e}")


import asyncio

asyncio.run(test())
