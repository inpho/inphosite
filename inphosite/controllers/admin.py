import logging

import unittest2
import re

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
        server = str(request.params.get('server', None))
        success = False
        if test is None:
            abort(400)
        
        suite = unittest2.TestSuite()
        suite.addTest(inpho.tests.Autotest(test, server))
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
        tests = unittest2.defaultTestLoader.getTestCaseNames(inpho.tests.Autotest)
        checked = []
        first_run = True

        # set up string parsing for docstring
        testcases = []
        count = len(tests)
        Test_info = namedtuple('title', ['title', 'description', 'fn_name', 'link'], verbose=False)
        
        # Parse docstring, stick cases into variable c.tests
        for test in tests:
            testname = 'inpho.tests.Autotest.' + test
            
            exec ('doc = ' + testname + '.__doc__')
            doc = doc[9:]
            title = re.search('^.*', doc).group()
            desc = re.search('(?<=\n).*', doc).group().strip()
            url = re.search('http.*?(?= )|http.*(?=)|/.*?(?= )|/.*(?=)', desc).group()
            case = Test_info(title, desc, test, url)
            testcases.append(case)
            
            try:
                c.checked
                first_run = False
            except AttributeError:
                c.checked=[]
        if first_run:
            c.checked = checked
        c.tests = testcases
        c.testcount = count
        return render('admin/tests.html')

    def log_tests(self):
        checks = request.params
        count = int(request.params['count']) + 1
        if len(checks) == count:
            with open('/Users/alefrost/logfile.txt', 'a') as f:
                f.write('[' + strftime("%a, %d %b %Y %H:%M:%S", gmtime()) + '] ' + h.auth.username(request) + '\n')
            return render('admin/success.html')
        else:
            c.checked = []
            for key, value in checks.iteritems():
                if key == 'test':
                    c.checked.append(str(value))
            return self.tests()
