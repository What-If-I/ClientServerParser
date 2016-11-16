from utils.html_parser import UrlParser

stackoverflow = UrlParser('http://stackoverflow.com/')

print(stackoverflow.get_title())
for link in stackoverflow.get_links():
    print(link)
