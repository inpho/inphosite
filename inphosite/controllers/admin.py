import logging

import unittest2
#can this be put somewhere else? I feel like there's a file for these
#import sys
#sys.path.insert(0, '~/workspace/testcases')
#import autotest

from collections import namedtuple
from time import gmtime, strftime

from pylons import request, response, session, config, tmpl_context as c
from pylons.controllers.util import abort, redirect as rd

# import decorators
from pylons.decorators import validate
from pylons.decorators.cache import beaker_cache
from inphosite.lib.rest import restrict, dispatch_on

# import inphosite information
from inphosite.lib.base import BaseController, render

from inpho.corpus.sep import get_title, get_titles, new_entries
import inpho.model as model
from inpho.model import *
from inpho.model import Session
import inphosite.lib.helpers as h
import webhelpers.paginate as paginate
from sqlalchemy import or_

log = logging.getLogger(__name__)

import formencode
from formencode import htmlfill, validators, FancyValidator
import simplejson

class AdminController(BaseController):
    def __before__(self):
        # protect entire controller for admins only
        if not h.auth.is_logged_in():
            abort(401)
        if not h.auth.is_admin():
            abort(403)

    def list(self, id = None):
        return rd('/entity/list_new')

    def tests(self):
        """
        Displays the InPhO Update checklist
        """
        
        with open(config['test_file']) as f:
            # Parse TESTCASES file, stick cases into variable c.tests
            testcases = []
            count = 0
            Test = namedtuple('Test', ['title', 'description'], verbose=False)
            state = "t"
            t, d = "", ""
            # Builds list of namedtuples for each test case
            for line in f:
                if state == "t":
                    t = line
                    state = "d"
                elif state == "d":
                    if line != '\n':
                        d += line
                    else:
                        state = "t"
                        case = Test(t.rstrip('\n'), d.replace("\n", " "))
                        testcases.append(case)
                        count += 1
                        t = ""
                        d = ""
            c.tests = testcases
            c.testcount = count
            try:
                c.checked
            except AttributeError:
                # Run autotest here and save autotest.passed
                # in c.checked instead of ""
                #suite = autotest.unittest2.TestLoader().loadTestsFromTestCase(autotest.Auto>
                #autotest.unittest2.TextTestRunner(verbosity=2).run(suite)
                c.checked = ""
            pass

        # Render the test form
        return render('admin/tests.html')

    def log_tests(self):
        checks = request.params
        count = int(request.params['count']) + 1
        if len(checks) == count:
            with open('/Users/alefrost/logfile.txt', 'a') as f:
                f.write('[' + strftime("%a, %d %b %Y %H:%M:%S", gmtime()) + '] ' + h.auth.username(request) + '\n')
                            # redirect to success.html
            return render('admin/success.html')
        else:
            c.checked = []
            for key, value in checks.iteritems():
                if key == 'test':
                    c.checked.append(str(value))
            return self.tests()
