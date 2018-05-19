#!/usr/bin/env python3
import urllib.request, urllib.error, urllib.parse, json, cgitb
from urllib.request import urlopen

#function to check url doesn't resolve to 500 error
#returns true if it does,
#returns false otherwise
def urlError (url):
    try:
        check = urlopen('https://www.inphoproject.org' + url)
    except urllib.error.HTTPError as e:
        return True;
    return False;

print("Content-Type: text/html")
print()
print("<h2>Articles with an internal server error</h2><ol>")
entities = json.load(urlopen('https://www.inphoproject.org/entity.json'))
for entity in entities['responseData']['results']:

    if entity['sep_dir'] != '' and urlError(entity['url']):
        print("<li><a href=\"https://www.inphoproject.org" + entity['url'] + "\">" + entity['label'] + "</a></li>")
        
print("</ol>")

