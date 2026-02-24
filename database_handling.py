import sqlite3

# subscriptions: chat id with branch subscribed to


class DatabaseHandler:
    def __init__(self, db_path="ums-updates.db"):
        self.conn = sqlite3.connect(db_path, timeout=10)
        self._create_subscriptions_table()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def _connection(self):
        if self.conn is None:
            raise RuntimeError("Database connection is closed")
        return self.conn

    def _create_subscriptions_table(self):
        conn = self._connection()
        with conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS subscriptions (chat_id INTEGER NOT NULL, branch TEXT NOT NULL, PRIMARY KEY (chat_id, branch));"
            )

    def save_subscription(self, chat_id, branch):
        conn = self._connection()
        with conn:
            conn.execute(
                "INSERT OR IGNORE INTO subscriptions (chat_id, branch) VALUES (?, ?);",
                (chat_id, branch),
            )

    def remove_subscription(self, chat_id):
        conn = self._connection()
        with conn:
            conn.execute("DELETE FROM subscriptions WHERE chat_id=?;", (chat_id,))

    def load_subscriptions(self):
        conn = self._connection()
        rows = conn.execute("SELECT chat_id, branch FROM subscriptions;").fetchall()
        subscriptions_dict = {}
        for chat_id, branch in rows:
            subscriptions_dict.setdefault(branch, set()).add(chat_id)
        return subscriptions_dict
