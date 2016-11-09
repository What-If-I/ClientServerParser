from utils.html_parser import UrlParser

stackoverflow = UrlParser('http://stackoverflow.com/')
print(stackoverflow.get_title())

print(stackoverflow.url)
print(type(stackoverflow.get_links()))
for link in stackoverflow.get_links():
    print(link)
