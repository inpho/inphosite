#!/bin/sh
paster request ../production.ini /page/index > ../static/index.html
paster request ../production.ini /page/docs > ../static/docs/index.html
paster request ../production.ini /page/owl > ../static/owl/index.html
paster request ../production.ini /page/json > ../static/json/index.html
paster request ../production.ini /page/papers > ../static/papers/index.html
paster request ../production.ini /page/faq > ../static/faq/index.html
paster request ../production.ini /page/graph > ../static/graph/index.html
