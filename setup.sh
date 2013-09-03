#!/bin/sh
virtualenv --no-site-packages ../sandbox
../sandbox/bin/easy_install PyYAML
../sandbox/bin/easy_install nltk
../sandbox/bin/python setup.py develop
