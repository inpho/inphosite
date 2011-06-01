""" 
AccountController

Responsible for delegating requests regarding user signin, signout and register.
Delegated to by ``config.routing``'s mapper. Also contains validation for
Usernamesand the Registration form.
"""

import logging

from pylons import request, response, session, url, tmpl_context as c
from pylons.controllers.util import abort, redirect

# import decorators
from pylons.decorators import validate
from pylons.decorators.rest import restrict

from inphosite.model import Idea, IdeaEvaluation, User
from inphosite.lib.base import BaseController, render
import inphosite.lib.helpers as h
from inphosite.model.meta import Session

from sqlalchemy import and_, or_
from sqlalchemy.orm import aliased

log = logging.getLogger(__name__)

import formencode
from formencode import htmlfill, validators as v, FancyValidator
from math import sqrt
from turbomail import Message

class UsernameValidator(FancyValidator):
    """Validates that a username does not exist or contain spaces."""
    def _to_python(self, value, state):
        if ' ' in value:
            raise formencode.Invalid(
                'Usernames cannot contain space characters',
                value, state)
        if h.auth.user_exists(value):
            raise formencode.Invalid(
                'User %s already exists'%value,
                value, state)
        return value
    
class LoginExistsValidator(FancyValidator):
    """Validates that a username does not exist or contain spaces."""
    def _to_python(self, value, state):
        user = h.get_user(value) 
        if not user:
            raise formencode.Invalid(
                'No user is registered under the username or email %s.'%value,
                value, state)
        return value

class RegisterForm(formencode.Schema):
    """
    Validator for the registration form rendered by 
    ``AccountController.register()``and accepted by 
    ``AccountController.submit()``
    """
    allow_extra_fields = True
    filter_extra_fields = True
    fullname =v.UnicodeString()
    username = formencode.All(v.UnicodeString(not_empty=True), 
                              UsernameValidator())
    password =v.UnicodeString(not_empty=True)
    confirm_password =v.UnicodeString(not_empty=True)
    email =v.Email(not_empty=True)
    confirm_email =v.Email(not_empty=True)
    first_area = v.Int(not_empty=True)
    first_area_level = v.Int(not_empty=True)
    second_area = v.Int()
    second_area_level = v.Int()
    chained_validators = [v.FieldsMatch('email', 'confirm_email'),
                          v.FieldsMatch('password', 'confirm_password')]

class EditForm(formencode.Schema):
    """
    Validator for the registration form rendered by 
    ``AccountController.register()``and accepted by 
    ``AccountController.submit()``
    """
    allow_extra_fields = True
    filter_extra_fields = True
    fullname =v.UnicodeString()
    password =v.UnicodeString()
    confirm_password =v.UnicodeString()
    email =v.Email()
    confirm_email =v.Email()
    '''
    first_area = v.Int()
    first_area_level = v.Int()
    second_area = v.Int()
    second_area_level = v.Int()
    '''
    chained_validators = [v.FieldsMatch('email', 'confirm_email'),
                          v.FieldsMatch('password', 'confirm_password')]

class ResetForm(formencode.Schema):
    """
    Validator for the reset form rendered by 
    ``AccountController.reset()``and accepted by 
    ``AccountController.reset_submit()``
    """
    allow_extra_fields = True
    filter_extra_fields = True
    login = formencode.All(v.UnicodeString(not_empty=False),
                           LoginExistsValidator())


class AccountController(BaseController):


    ''' Controller for handling user account activities. 
    
    Dispatches the registration page, signin/signout and should eventually
    have more functionality for administrative tasks, like listing and deleting
    users. Also will handle updating of user information, such as SEP subject
    areas.
    '''
    def signin(self):
        identity = request.environ.get('repoze.who.identity')
        if identity is not None:
            came_from = request.params.get('came_from', '')
            if request.environ.get('HTTP_REFERER', '').startswith(came_from)\
                or not came_from:
                redirect('/account/profile')
            if came_from:
                redirect(str(came_from))

        c.failed = request.url == request.environ.get('HTTP_REFERER','')

        return render('/account/signin.html')

    def test(self):
        identity = request.environ.get('repoze.who.identity')
        if identity is None:
            # Force skip the StatusCodeRedirect middleware; it was stripping
            #   the WWW-Authenticate header from the 401 response
            request.environ['pylons.status_code_redirect'] = True
            # Return a 401 (Unauthorized) response and signal the repoze.who
            #   basicauth plugin to set the WWW-Authenticate header.
            abort(401, 'You are not authenticated')
        
        return """
<body>
Hello %(name)s, you are logged in as %(username)s.
<a href="/account/signout">logout</a>
</body>
</html>
""" %identity['user']

    def signout(self):
        ''' 
        Action to sign the user out. The actual signout happens when the
        middleware captures the request, so this function just displays a
        confirmation pageFor ``cookie`` authentication this
        function's routing must be added to the ``authkit.cookie.signoutpath``
        directive.
        '''
        return render('account/signedout.html')
    
    @validate(schema=ResetForm(), form='reset')
    def reset_submit(self):
        ''' Action to process the Reset Form. '''
        self._reset(self.form_result['login']) 
    
    def reset(self):
        '''Renders the registration form.'''
        return render('account/reset.html')
        

    def _reset(self, username=None):
        username = username or request.environ.get('REMOTE_USER', False)
        if not username:
            abort(401)

        try:
            user = h.get_user(username)
        except:
            abort(400)
            
        new_password = user.reset_password()


        msg = Message("inpho@indiana.edu", user.email,
                      "InPhO password reset")
        msg.plain = """
%(name)s, your password at the Indiana Philosophy Ontology (InPhO) has been changed to:
Username: %(uname)s
Password: %(passwd)s

The Indiana Philosophy Ontology (InPhO) Team
inpho@indiana.edu
                       """ % {'passwd' : new_password,
                              'uname' : user.username,
                              'name' : user.fullname or user.username or ''}
        msg.send()

        Session.commit()

        h.redirect(h.url(controller='account', action='reset_result'))

    def reset_result(self):
        return render('account/reset_success.html')
        


    def profile(self):
        if not request.environ.get('REMOTE_USER', False):
            abort(401)
        
        c.user = h.get_user(request.environ['REMOTE_USER'])        

        ieq = Session.query(IdeaEvaluation).order_by(IdeaEvaluation.time.desc())
        c.recent = ieq.filter(and_(IdeaEvaluation.uid==c.user.ID,
                                   or_(IdeaEvaluation.generality>-1,
                                       IdeaEvaluation.relatedness>-1)))
        c.recent = c.recent.limit(5)
        c.message = request.params.get('message', None)



        # GENERALITY
        gen_u = ieq.filter(and_(IdeaEvaluation.uid==c.user.ID,
                                IdeaEvaluation.generality>-1))
        gen_nu = ieq.filter(and_(IdeaEvaluation.uid!=c.user.ID,
                                 IdeaEvaluation.generality>-1))
        gen_nu = gen_nu.subquery()
        c.gen_agree = gen_u.join((gen_nu,and_(IdeaEvaluation.ante_id==gen_nu.c.ante_id,
                                              IdeaEvaluation.cons_id==gen_nu.c.cons_id,
                                              IdeaEvaluation.generality==gen_nu.c.generality))).count()

        #for std dev calcs
        ie1 = aliased(IdeaEvaluation)
        ie2 = aliased(IdeaEvaluation)
        gen_overlaps = Session.query(ie1.generality - ie2.generality)
        c.gen_overlaps = gen_overlaps.filter(and_(ie1.ante_id==ie2.ante_id,
                                        ie1.cons_id==ie2.cons_id,
                                        ie1.uid==c.user.ID,
                                        ie1.uid!=ie2.uid,
                                        ie1.generality>-1,
                                        ie2.generality>-1))
        gen_overlaps = c.gen_overlaps[:]
        c.gen_overlap = float(len(gen_overlaps[:])) 

        if c.gen_overlap == 0:
            c.gen_agree_str = 'No evaluations'

            c.gen_avg = 0
            c.gen_stddev = 0
        else:
            c.gen_agree_str = '%.1f%%' % ((c.gen_agree / c.gen_overlap) * 100)

            c.gen_avg = sum([abs(x[0]) for x in gen_overlaps]) / c.gen_overlap
            c.gen_stddev = sqrt(sum(map(lambda x: (abs(x[0]) - c.gen_avg)\
                                                    * (abs(x[0]) - c.gen_avg), 
                                    gen_overlaps))\
                                / c.gen_overlap)


        # RELATEDNESS
        rel_u = ieq.filter(and_(IdeaEvaluation.uid==c.user.ID,
                                IdeaEvaluation.relatedness>-1))
        rel_nu = ieq.filter(and_(IdeaEvaluation.uid!=c.user.ID,
                                 IdeaEvaluation.relatedness>-1)).subquery()

        c.rel_agree = rel_u.join((rel_nu,and_(IdeaEvaluation.ante_id==rel_nu.c.ante_id,
                                              IdeaEvaluation.cons_id==rel_nu.c.cons_id,
                                              IdeaEvaluation.relatedness==rel_nu.c.relatedness))) 
        c.rel_agree = c.rel_agree.count()


        #for std dev calcs
        ie1 = aliased(IdeaEvaluation)
        ie2 = aliased(IdeaEvaluation)
        rel_overlaps = Session.query(ie1.relatedness - ie2.relatedness)
        c.rel_overlaps = rel_overlaps.filter(and_(ie1.ante_id==ie2.ante_id,
                                        ie1.cons_id==ie2.cons_id,
                                        ie1.uid==c.user.ID,
                                        ie1.uid!=ie2.uid,
                                        ie1.relatedness>-1,
                                        ie2.relatedness>-1))
        rel_overlaps = c.rel_overlaps[:]
        c.rel_overlap = float(len(rel_overlaps[:]))
        if c.rel_overlap == 0:
            c.rel_agree_str = 'No evaluations'
            c.rel_avg = 0
            c.rel_stddev = 0
        else:
            c.rel_agree_str = '%.1f%%' % ((c.rel_agree / c.rel_overlap) * 100)
            c.rel_avg = sum(map(lambda x: abs(x[0]), rel_overlaps)) / c.rel_overlap
            c.rel_stddev = sqrt(sum(map(lambda x: (abs(x[0]) - c.rel_avg)\
                                                    * (abs(x[0]) - c.rel_avg), 
                                        rel_overlaps))\
                                    / c.rel_overlap)

        return render('account/profile.html')
    
    def edit(self):
        '''Renders the registration form.'''
        if not h.auth.is_logged_in():
            abort(401)

        c.user = h.get_user(request.environ['REMOTE_USER'])

        return render('account/edit.html')

    def register(self):
        '''Renders the registration form.'''
        return render('account/register.html')

    @validate(schema=RegisterForm(), form='register')
    def submit(self):
        ''' 
        This function validates the submitted registration form and creates a
        new user. Restricted to ``POST`` requests. If successful, redirects to 
        the result action to prevent resubmission.
        ''' 
        
        user = User(
            self.form_result['username'],
            self.form_result['password'],
            fullname=self.form_result['fullname'],
            email=self.form_result['email'],
            first_area_id=self.form_result['first_area'],
            first_area_level=self.form_result['first_area_level'],
            second_area_id=self.form_result['second_area'],
            second_area_level=self.form_result['second_area_level']
        )


        Session.add(user) 
        Session.commit()

        msg = Message("inpho@indiana.edu", self.form_result['email'], 
                      "InPhO registration")
        msg.plain = """Dear %(name)s, 
Thank you for registering with the Indiana Philosophy Ontology Project (InPhO).

You can sign in at https://inpho.cogs.indiana.edu/signin with the following
information:

Username: %(uname)s
Password: %(passwd)s

The Indiana Philosophy Ontology Project (InPhO) Team
inpho@indiana.edu
                       """ % {'passwd' : self.form_result['password'],
                              'uname' : user.username,
                              'name' : user.fullname or user.username or ''}
        msg.send()

        h.redirect(h.url(controller='account', action='result'))
    
    @validate(schema=EditForm(), form='edit')
    def submit_changes(self):
        ''' 
        This function validates the submitted profile edit form and commits the 
        changes. Restricted to ``POST`` requests. If successful, redirects to 
        the result action to prevent resubmission.
        ''' 
        if not h.auth.is_logged_in():
            abort(401)

        c.user = h.get_user(request.environ['REMOTE_USER'])
       
        if self.form_result['password'] != '':
            c.user.set_password(self.form_result['password'])

        # TODO: Enable area editing
        #c.user.first_area_id=self.form_result['first_area'],
        #user.first_area_level=self.form_result['first_area_level'],
        #if self.form_result['second_area']:
        #    c.user.second_area_id=self.form_result['second_area'],
        #    c.user.second_area_level=self.form_result['second_area_level']
        c.user.fullname = self.form_result['fullname']

        Session.flush()

        Session.commit()

        h.redirect(h.url(controller='account', action='profile', message='edited'))


    def result(self):
        ''' Target of redirect from submit. Simply returns a "Registration
        Successful!" page '''
        return render('account/success.html')


