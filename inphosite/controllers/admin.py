import logging

import unittest2

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

import inpho.tests
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

    @restrict('POST')
    def _do_test(self):
        test = request.params.get('test', None)
        if test is None:
            abort(400)

        testname = 'inpho.tests.Autotest.' + test 
        success = False
       # current_fails=0
        suite = unittest2.defaultTestLoader.loadTestsFromName(testname)
        result = unittest2.TestResult()
        suite.run(result)
        current_fails = len(result.errors) + len(result.failures)
        if current_fails == 0:
            success = True
        else:
            message = "Test Failed"

        if success:
            response.status = 200
            return test
        else:
            response.status = 500
            return message

    def list(self, id = None):
        return rd('/entity/list_new')
    
    @dispatch_on(POST='_do_test')
    def tests(self):
        """
        Displays the InPhO Update checklist
        """
        # set up test suite for running tests
        tests = unittest2.defaultTestLoader.getTestCaseNames(inpho.tests.Autotest)
        result = unittest2.TestResult()
        past_fails = 0
        checked = []
        first_run = True

        # set up string parsing for docstring
        testcases = []
        count = len(tests)
        Test_info = namedtuple('title', ['title', 'description'], verbose=False)
        
        # Parse docstring, stick cases into variable c.tests
        for test in tests:
            testname = 'inpho.tests.Autotest.' + test
            # puts docstring in variable doc
            exec ('doc = ' + testname + '.__doc__')

            # Begin docstring parsing
            state = "t"
            t, d = "", ""
            # eliminate beginning junk in string
            doc = doc[8:]
            # Builds list of namedtuples for each test case
            for char in doc:
                if state == "t":
                    if char == '\n':
                        state = "space"
                        continue
                    else:
                        t += char
                elif state == "space":
                    if char != " ":
                        d += char
                        state = "d"
                elif state == "d":
                    if char != '\n':
                        d += char
                    else:
                        case = Test_info(test, d.replace("\n", " "))
                        testcases.append(case)
            try:
                c.checked
                first_run = False
            except AttributeError:
                # ERROR: it adds all things, even if they fail
#                suite = unittest2.defaultTestLoader.loadTestsFromName(testname)
#                suite.run(result)
#                current_fails = len(result.errors) + len(result.failures)
#                if past_fails == current_fails:
#                    checked.append(t)
#                else:
#                    past_fails = current_fails
                c.checked=[]
        if first_run:
            c.checked = checked
        c.tests = testcases
        c.testcount = count
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
