from database_handling import DatabaseHandler
import re

db = DatabaseHandler()

sub_re = re.compile(r"User (\d+) subscribed to (.+)")
unsub_re = re.compile(r"User (\d+) unsubscribed")

with open("telegram-bot.log") as f:
    for line in f:
        if m := sub_re.search(line):
            chat_id = int(m.group(1))
            branch = m.group(2)
            db.save_subscription(chat_id, branch)
        elif m := unsub_re.search(line):
            chat_id = int(m.group(1))
            db.remove_subscription(chat_id)
