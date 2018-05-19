import urllib.request, json
from urllib.request import urlopen

#function used to check if the query returns more than one result
#returns true if more than one result is found
#reutrns false otherwise
#error email sent if true
def isMultiple (inpho_json):
    resDat = inpho_json.get('responseData')
    res = resDat.get('results')
    if len(res) > 0: #there was >1 result
##        f.write('same sep_dir: ')
##        for entity in res:
##            f.write(entity['url'] + ', ')
        return True;
    return False;

#function to check url doesn't throw 500 error
#returns true if it does,
#returns false otherwise
def sepDirError (url):
    inpho_json = json.load(urlopen(url))
    if 'url' not in inpho_json:
        return isMultiple(inpho_json);
    return False;

#function used to ensure duplicates aren't output
def haveNotSeen(sep_dir):
    for entry in seen:
        if sep_dir == entry:
            return False;
    return True;

l = open('errorSepDirLinks.txt', 'w')
entities = json.load(urlopen('https://www.inphoproject.org/entity.json'))
entities_all = entities['responseData']['results']
seen = [None]

for entity in entities_all:
    if entity['sep_dir'] != '' and entity['sep_dir'] is not None:
        url = 'https://inphoproject.org/entity.json?sep=' + entity['sep_dir'] + '&redirect=True'
        if sepDirError(url):
            if haveNotSeen(entity['sep_dir']):
                seen.append(entity['sep_dir'])
                print(entity['sep_dir'])
                l.write(url + '\n')

l.close()
