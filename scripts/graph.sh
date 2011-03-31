#!/bin/sh
CONFIG=$1
LOGPATH=/home/jaimie/inpho/api/static/graph/log
ARCHDIR=/home/jaimie/inpho/api/static/graph
ARCHFILE=$(date +\%Y\%m\%d)ii.txt
graph/graph.py $CONFIG ii 1> $ARCHDIR/$ARCHFILE 2>> $LOGPATH

ARCHFILE=$(date +\%Y\%m\%d)it.txt
graph/graph.py $CONFIG it 1> $ARCHDIR/$ARCHFILE 2>> $LOGPATH

ARCHFILE=$(date +\%Y\%m\%d)tt.txt
graph/graph.py $CONFIG tt 1> $ARCHDIR/$ARCHFILE 2>> $LOGPATH

