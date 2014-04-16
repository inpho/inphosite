import codecs
from pylons import config

class PartialDelegate:
    """
    Class used to fetch mustache partial contents. Intended use is
    to pass an instance of this class to the pystache.Renderer().
    """
    def __init__(self, dirpath):
        self.dirpath = dirpath

    def get(self, title):
        """
        Takes the title of a partial and gives the corresponding
        contents of the mustache file in the public/templates directory
        """
        try:
            f = codecs.open(self.dirpath + title + ".mustache", 'r', encoding='utf-8')
            return f.read()
        except IOError:
            print "File not found: " + self.dirpath + title
            return None
