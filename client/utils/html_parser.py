# import requests
import aiohttp
from bs4 import BeautifulSoup


class UrlParser:
    def __init__(self, url):
        self.url = url
        self.html = await self._get_html()
        self.beautiful_html = self._beautify_html()

    async def _get_html(self):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.github.com/events') as resp:
                if resp.status_code in range(200, 231):
                    return resp.text
                else:
                    raise ConnectionError(f"Error. Server returned: {resp.status_code}")

    def _beautify_html(self):
        return BeautifulSoup(self.html, 'html.parser')

    def get_links(self):
        links = []

        for link in self.beautiful_html.find_all('a'):
            link = str(link.get('href'))

            if link.startswith('/'):  # relative links
                link = self.url + link[1:]

            if link.startswith('http') or link.startswith('https'):
                links.append(link)

        return links

    def get_title(self):
        return str(self.beautiful_html.title.string)
