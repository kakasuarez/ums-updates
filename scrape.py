import requests
from bs4 import BeautifulSoup
import re


class Notice:
    def __init__(self, row):
        self.text = row.text
        self.url = row.contents[0].get("href")
        part = self.text.partition("Published By: ")
        self.title = part[0]
        self.publisher = part[2]

    def escaped_title(self):
        markdown_chars = r"\\`*_{}[]()#+-.!|"
        escaped_text = re.sub(
            r"([{}])".format(re.escape(markdown_chars)), r"\\\1", self.title
        )
        return escaped_text


class Scraper:
    def __init__(self):
        self.url = "https://www.imsnsit.org/imsnsit/notifications.php"
        self.refresh_documents()
        self.last_seen_notice = self.get_latest_notice()

    def refresh_documents(self):
        self.document = requests.get(self.url)
        self.parse = BeautifulSoup(self.document.text, "html.parser")

    def get_all_notices(self):
        self.refresh_documents()
        return self.parse.find_all("td", class_="list-data-focus")

    def get_new_notices(self):
        self.refresh_documents()
        new_notices = []
        rows = self.get_all_notices()
        for row in rows:
            current_notice = Notice(row)
            current_notice_title = current_notice.title
            if current_notice_title == self.last_seen_notice.title:
                if new_notices:
                    self.last_seen_notice = new_notices[0]
                return new_notices
            new_notices.append(current_notice)
        return []

    def get_latest_notice(self):
        return Notice(self.get_all_notices()[0])
