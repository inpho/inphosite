from inphosite.lib.auth import encrypt
from sqlalchemy.ext.associationproxy import association_proxy
import random
import string

class User(object):
    """
    User object for ORM, is initializable
    """
    def __init__(
        self,
        username,
        password=None,
        fullname=None,
        group_uid=None,
        email=None,
        first_area_id=None,
        first_area_level=None,
        second_area_id=None,
        second_area_level=None
    ):
        self.username   = username
        self.fullname   = fullname
        self.group_uid  = group_uid
        self.email = email
        self.first_area_id=first_area_id
        self.first_area_level=first_area_level
        self.second_area_id=second_area_id
        self.second_area_level=second_area_level
    def __repr__(self):
        return "User(%(username)s)" % self.__dict__
    
    roles = association_proxy('_roles', 'name')

    def set_password(self, new_password):
        self.password = encrypt(new_password)

    def reset_password(self):
        new_password = ''.join(random.choice(string.letters + string.digits)
                                   for i in xrange(8))

        self.set_password(new_password)
        return new_password
 

class SEPArea(object):
    pass

class Group(object):
    """
    User Group object for ORM, is initializable. Users may only belong to one Group.
    """
    def __init__(self, name=None):
        self.name = name
    def __repr__(self):
        return "Group(%(name)s)" % self.__dict__

class Role(object):
    """
    User Role object for ORM, is initializable. Users may belong to any number of Roles
    """
    def __init__(self, name=None):
        self.name = name
    def __repr__(self):
        return "Role(%(name)s)" % self.__dict__
