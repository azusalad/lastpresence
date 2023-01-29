from pypresence import Presence
import time
import requests
from bs4 import BeautifulSoup

from config import *

class LastPresence:
    def __init__(self):
        self.client = Presence(client_id)

    def start(self):
        self.client.connect()
        self.loop()

    def scrape(self):
        """Fetches the song data from last.fm"""

        # fetch profile page
        print('fetching song information')
        self.r = requests.get(profile_url)
        self.soup = BeautifulSoup(self.r.text, 'lxml')

        # find song information
        self.current = self.soup.find_all("tr")[1]
        self.name = self.current.find('td', class_='chartlist-name').find('a')
        self.title = self.name.attrs['title']
        self.href = "https://www.last.fm" + self.name.attrs['href']
        self.artist = self.current.find('td', class_='chartlist-artist').find('a').attrs['title']
        if "Scrobbling now" in self.current.find('span', class_= "chartlist-now-scrobbling").find('a').text:
            self.scrobbling = True
        else:
            self.scrobbling = False
        time.sleep(1)

        # now try to find the song length
        self.r = requests.get(self.href)
        self.soup = BeautifulSoup(self.r.text, 'lxml')
        try:
            self.soup.find('dd', class_='catalogue-metadata-description').string.strip()
        except AttributeError:
            self.length = None
        else:
            self.length = self.soup.find('dd', class_='catalogue-metadata-description').string.strip()
            self.length = self.length.split(":")
            self.length = int(self.length[0]) * 60 + int(self.length[1])
        print('Current artist: ' + str(self.artist))
        print('Current title: ' + str(self.title))

    def cooldown(self):
        # wait before fetching last.fm again
        if self.length:
            print('waiting ' + str(self.length))
            time.sleep(self.length)
        else:
            print('waiting ' + str(default_wait))
            time.sleep(default_wait)

    def loop(self):
        self.scrape()
        if self.scrobbling:
            self.client.update(large_image="large_img",
                large_text=LARGE_TXT,
                details="Playing a song",
                state=f'{self.artist}: {self.title}',
                start=time.time())
        else:
            self.client.update(large_image="large_img",
            large_text=LARGE_TXT,
            details="Idle")
        self.cooldown()
        self.loop()

if __name__ == "__main__":
    updater = LastPresence()
    updater.start()

