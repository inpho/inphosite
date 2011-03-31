#!/usr/bin/python

from scripts.environment import load

if __name__ == "__main__":
    import sys
    load(sys.argv[-1])

    from scripts.model import *

    # initialize a list for people
    people = []
    
    # open people database and add each person to the people list
    f = open(sys.argv[-2])
    for line in f:
        line = line.split("::")
        people.append(line)
    
    
    for p in people:
        # skip incomplete entries
        if len(p) < 5:
            print "skipping %s" % p
            continue
    
        #gather data for user creation
        firstname, lastname, username, password, email = p[:5]
      
        # prepend "sep." to the username
        username = "sep.%s" % username
    
        print "importing %s" % username
        if not users.user_exists(username):
            users.user_create(
                username,
                password,
                email=email
            )
        else:
            #update password
            users.user_set_password(username, password)
    
    meta.Session.flush()
    meta.Session.commit()


    if not users.user_exists(username):
        raise Exception("Did not add %s to db!" % username)

    print "Done!"

else:
    raise Exception("Must be called from command line")

