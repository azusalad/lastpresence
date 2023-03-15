from pypresence import Presence
import time
import requests
from bs4 import BeautifulSoup

from config import *

class LastPresence:
    def __init__(self):
        self.client = Presence(client_id)

    def start(self):
        # get song duration information
        with open("lengths.txt","r") as f:
            self.original = f.read()
            self.lines = [y for y in [x.strip() for x in self.original.split("\n\n")] if y != '']
        self.lengths = {}
        for x in self.lines:
            self.lengths[x.split("\n")[0]] = x.split("\n")[1]
        # make a backup
        self.write_duration("lengths.txt~")
        print("Fetched old song duration information")
        self.client.connect()
        print("Connected to discord\n")
        self.prev = None
        self.loop()

    def scrape(self):
        """Fetches the song data from last.fm"""

        # fetch profile page
        print('Fetching song information')
        self.r = requests.get(profile_url)
        self.soup = BeautifulSoup(self.r.text, 'lxml')

        # find song information
        try:
            self.current = self.soup.find_all("tr")[1]
        except IndexError:
            print('Finding song failed retrying in 5 seconds')
            time.sleep(5)
            self.scrape()
        self.name = self.current.find('td', class_='chartlist-name').find('a')
        self.title = self.name.attrs['title']
        self.href = "https://www.last.fm" + self.name.attrs['href']
        self.artist = self.current.find('td', class_='chartlist-artist').find('a').attrs['title']
        # check if currently scrobbling
        if bool(self.current.find('span', class_= "chartlist-now-scrobbling")):
            self.scrobbling = True
        else:
            self.scrobbling = False
        time.sleep(1)

        print('Current artist: ' + str(self.artist))
        print('Current title: ' + str(self.title))

    def find_duration(self):
        """Finds the song duration either from the file or last.fm"""
        try:
            # check if length is stored in file
            self.lengths[self.artist + self.title]
        except:
            # scrape song length
            print("No old song duration found, fetching from last.fm")
            self.r = requests.get(self.href)
            self.soup = BeautifulSoup(self.r.text, 'lxml')
            try:
                self.soup.find('dd', class_='catalogue-metadata-description').string.strip()
            except AttributeError:
                self.length = None
                self.lengths[self.artist + self.title] = "None"
            else:
                # find length
                self.length = self.soup.find('dd', class_='catalogue-metadata-description').string.strip()
                self.length = self.length.split(":")
                self.length = int(self.length[0]) * 60 + int(self.length[1])
                # store length
                self.lengths[self.artist + self.title] = self.length
            finally:
                self.write_duration("lengths.txt")
                print("Wrote new song duration")
        else:
            print("Found old song duration")
            if self.lengths[self.artist + self.title] == "None":
                self.length = None
            else:
                self.length = int(self.lengths[self.artist + self.title])

    def write_duration(self, name):
        """Writes durations to file"""
        with open(name,"w") as f:
            for x in self.lengths:
                f.write(x + "\n" + str(self.lengths[x]) + "\n\n")

    def cooldown(self):
        # wait before fetching last.fm again
        if self.length:
            print('waiting ' + str(self.length) + '\n')
            time.sleep(self.length)
        else:
            print('waiting ' + str(default_wait) + '\n')
            time.sleep(default_wait)

    def loop(self):
        self.scrape()
        self.find_duration()
        if self.scrobbling:
            if self.prev != self.title + self.artist:
                self.client.update(large_image="large_img",
                                large_text=large_txt,
                                details=playing_txt,
                                state=f'{self.artist}: {self.title}',
                                start=time.time(),
                                buttons=[{"label": "My Profile", "url": profile_url},{"label": "Currently Playing", "url": self.href}])
        else:
            self.client.update(large_image="large_img",
                large_text=large_txt,
                details=idle_txt,
                state=f'{self.artist}: {self.title}',
                buttons=[{"label": "My Profile", "url": profile_url}])
        self.prev = self.title + self.artist
        self.cooldown()
        self.loop()

if __name__ == "__main__":
    updater = LastPresence()
    updater.start()
