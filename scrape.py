import requests
from bs4 import BeautifulSoup
import re
import hashlib
import logging

logger = logging.getLogger(__name__)


class DownloadError(Exception):
    pass


class Notice:
    def __init__(self, row):
        self.text = row.text
        self.url = row.contents[0].get("href")
        part = self.text.partition("Published By: ")
        self.title = part[0]
        self.publisher = part[2]

        self.id = self._make_id()

    def escaped_title(self):
        markdown_chars = r"\\`*_{}[]()#+-.!|"
        escaped_text = re.sub(
            r"([{}])".format(re.escape(markdown_chars)), r"\\\1", self.title
        )
        return escaped_text

    def _make_id(self):
        base = self.title
        return hashlib.sha256(base.encode("utf-8")).hexdigest()

    def download(self):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.imsnsit.org/imsnsit/notifications.php",
        }
        if not self.url:
            raise DownloadError("This notice does not have a download URL")
        pdf_resp = requests.get(self.url, headers=headers)
        content_type = pdf_resp.headers.get("Content-type", "").lower()
        if "pdf" not in content_type:
            raise DownloadError(
                f"Expected PDF, got {content_type} (status {pdf_resp.status_code})"
            )
        return pdf_resp.content

    def safe_filename(self) -> str:
        name = re.sub(r"[^\w\-. ]", "_", self.title)
        return name.strip()[:120] + ".pdf"


class Scraper:
    def __init__(self, department_filter: str):
        self.url = "https://www.imsnsit.org/imsnsit/notifications.php"
        self.enc_branch = None
        self.department_filter = department_filter
        self.session = requests.Session()
        self.last_seen_notice = self.get_latest_notice()
        self.refresh_documents()

    def load_metadata(self):
        document = self.session.get(self.url)
        soup = BeautifulSoup(document.text, "html.parser")
        self.enc_branch = soup.find("input", {"name": "enc_branch"})["value"]

    def refresh_documents(self):
        if not self.enc_branch:
            self.load_metadata()

        payload = {
            "branch": self.department_filter,
            "enc_branch": self.enc_branch,
            "submit": "Submit",
        }

        document = self.session.post(self.url, data=payload)
        self.parse = BeautifulSoup(document.text, "html.parser")

    def get_all_notices(self):
        self.refresh_documents()
        return [
            Notice(row) for row in self.parse.find_all("td", class_="list-data-focus")
        ]

    def get_new_notices(self):
        self.refresh_documents()
        new_notices = []
        notices = self.get_all_notices()
        if self.last_seen_notice is None:
            self.last_seen_notice = notices[0]
            return new_notices
        for current_notice in notices:
            current_notice_title = current_notice.title
            if current_notice_title == self.last_seen_notice.title:
                if new_notices:
                    self.last_seen_notice = new_notices[0]
                return new_notices
            new_notices.append(current_notice)
        return []

    def get_latest_notice(self):
        notices = self.get_all_notices()
        return notices[0] if notices else None


def get_all_branches(url: str):
    document = requests.get(url)
    soup = BeautifulSoup(document.text, "html.parser")

    select = soup.find("select", {"name": "branch"})
    options = select.find_all("option")

    branches = []

    for option in options:
        value = option["value"]
        if value and value.lower() != "select":
            branches.append(value)

    return branches
