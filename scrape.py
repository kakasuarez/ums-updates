import requests
from bs4 import BeautifulSoup
from datetime import datetime

class Notice:
	def __init__(self, row):
		self.date_uploaded = datetime.strptime(row.find_previous_sibling("td").font.contents[0].strip(), "%d-%m-%Y")
		self.title = row.contents[0].font.contents[0]
		self.url = row.contents[0].get("href")
		self.publisher = row.contents[2].b.contents[14:]


class Scraper:
	def __init__(self):
		url = "https://www.imsnsit.org/imsnsit/notifications.php"
		document = requests.get(url)
		self.parse = BeautifulSoup(document.text, "html.parser")
		self.last_seen_notice = "ALL THE COURSE INSTRUCTORS OF THE UNIVERSITY MAY KINDLY COMPLETE THE ATTENDANCE ENTRY, FOR THE PERIOD 02.01.2024 TO 09.01.2024, ON CUMS LATEST BY 17.01.2024"
		
	def get_new_notices(self):
		new_notices = []
		for row in self.parse.find_all("td", class_="list-data-focus"):
			current_notice = Notice(row)
			current_notice_title = current_notice.title
			if current_notice_title == self.last_seen_notice:
				if new_notices != []:
					self.last_seen_notice = new_notices[0].title
				return new_notices
			new_notices.append(current_notice)