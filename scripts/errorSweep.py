import urllib.request, urllib.error, urllib.parse, json
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

l = open('error500Links.txt', 'w')
entities = json.load(urlopen('https://www.inphoproject.org/entity.json'))
for entity in entities['responseData']['results']:

    if entity['sep_dir'] != '' and urlError(entity['url']):
        print(entity['sep_dir'])
        l.write('https://inphoproject.org' + entity['url'] + '\n')

l.close()
