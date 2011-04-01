#!/bin/sh
virtualenv --no-site-packages sandbox
source sandbox/bin/activate
which easy_install
easy_install PyYAML
easy_install nltk
python setup.py develop
