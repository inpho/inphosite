#!/usr/bin/python
from environment import load

if __name__ == "__main__":
    # must load in inpho environment - SQL Session, model, etc.
    import sys
    load(sys.argv[-1])

    from model import *

    # What do we call the idea?
    label = raw_input("Name: ")

    # create the thinker using the ORM
    new = Thinker(label)

    # ask for additional data or use defaults
    new.sep_dir =  raw_input("SEP Dir: ")
    new.searchpattern =\
        raw_input("Search Pattern (default: '%s'): " % new.searchpattern)\
            or new.searchpattern
    new.searchstring =\
        raw_input("Search String (default: '%s'): " % new.searchstring)\
            or new.searchstring

    # add to the session
    Session.add(new)

    # write to the database
    Session.commit()
    Session.flush()

    if new.ID:
        print "Succesfully added Idea %d: %s" % (new.ID, new.label)
    else:
        print "Commit failed!"

