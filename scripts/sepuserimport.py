#!/usr/bin/python
if __name__ == "__main__":
    from inpho.model import *
    from inpho import config
    import sys
    import os.path

    # initialize a list for people
    people = []
    
    # open people database and add each person to the people list
    people_db = os.path.join(config.get("corpus", "db_path"), "people.txt")
    with open(people_db) as f:
        for line in f:
            line = line.split("::")
            people.append(line)
    
    usernames = Session.query(User.username).all()
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

        if username not in usernames:
            user = User(username, password, email=email)
            Session.add(user)
            print "created new user", username
        else:
            #update password
            user = Session.query(User).filter(User.username==username).first()
            user.set_password(username, password)
    
    Session.flush()
    Session.commit()

    print "Done!"

else:
    raise Exception("Must be called from command line")

