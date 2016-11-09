import requests
from bs4 import BeautifulSoup


class UrlParser:
    def __init__(self, url):
        self.url = url
        self.html = self._get_html()
        self.beautiful_html = self._beautify_html()

    def _get_html(self):
        page_request = requests.get(self.url)
        if page_request.status_code == 200:
            return page_request.text
        else:
            return None

    def _beautify_html(self):
        if self.html:
            return BeautifulSoup(self.html, 'html.parser')

    def get_links(self):
        links = []

        for link in self.beautiful_html.find_all('a'):
            link = str(link.get('href'))

            if link.startswith('/'):  # relative links
                link = self.url + link[1:]
            elif link.startswith('//'):  # links that leads to other websites
                link = link

            links.append(link)
        return list(filter(lambda l: l.startswith("http"), links))  # return only valid links

    def get_title(self):
        return str(self.beautiful_html.title.string)
