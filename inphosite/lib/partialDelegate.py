from pylons import config

class PartialDelegate:
    def __init__(self, dirpath):
        self.dirpath = dirpath

    def get(self, title):
        try:
            f = open(self.dirpath + title)
            return f.read()
        except IOError:
            return None
