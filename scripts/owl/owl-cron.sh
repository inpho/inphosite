#!/bin/bash
DATE=$(date +\%Y\%m\%d)
LOGPATH=/var/inpho/log/asp/$DATE.owl.log
OWLDIR=/var/inpho/www/owl

# run owl.py and send output to OWLDIR
python /var/inpho/inphosite/scripts/owl/owl > $OWLDIR/db-arch_$DATE.owl 2> $LOGPATH
