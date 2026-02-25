# ums-updates

Telegram bot which which sends messages for new notices on the Netaji Subhas University of Technology (NSUT) [IMS](https://www.imsnsit.org/imsnsit/notifications.php).

Needs the telegram bot token to be set as an environment variable `BOT_TOKEN`.

Subscribe to new notifications by sending the message `/start`.

Setup:

- `python3 -m venv .venv`
- `source .venv/bin/activate`
- `pip install -r requirements.txt`
- Copy `.env.example` to `.env` and add the environment variables.
- Set `ENV=development` to add debugging commands.
