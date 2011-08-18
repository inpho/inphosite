import re
import HTMLParser
from collections import defaultdict

from inphosite.model import *
from inphosite.model import Session
from sqlalchemy import or_
import os.path
import inphosite.lib.helpers as h

def getentries(db_dir):
    #to do feb 10: do something more elegant than just delete existing and rewrite...perhaps only write new?
    
    #first, clear out the current table
    #Session.query(SEPEntry).delete()
    #Session.flush()
    #Session.commit()
    
    entries = defaultdict(lambda: {'title' : '', 'published' : False, 'status' : ''})
    
    pars = HTMLParser.HTMLParser()
    
    #get published entries
    published = open('/Users/inpho/SitesOld/dev/entries-published.txt')
    status = open(os.path.join(db_dir , 'entrystatus.txt'))
        
    entrylist = open(os.path.join(db_dir, 'entries.txt'))

    #set up entries dict
    for line in entrylist:
        line = line.split('::')
        sep_dir = pars.unescape(re.sub('<(/)?[a-zA-Z]*>', '', line[0]))
        title = re.sub("\\\\\'", "'", pars.unescape(re.sub('<(/)?[a-zA-Z]*>', '', line[1])))
        entries[sep_dir]['title'] = title
        
    for line in published:
        line = re.sub('\\n', '', line)
        if entries[line]['title']:
            entries[line]['published'] = True
        else:
            print "uh-oh, " + line + "doesn't appear to be in dict object"
    
    for line in status:
        line = line.split('::')
        if entries[line[0]]['title']:
            entries[line[0]]['status'] = line[1]
            #print "status = " + line[1] + ' for ' + line[0]
        else:
            print "uh-oh, " + line[0] + "doesn't appear to be in dict object"
        
    
    for key in entries.keys():
        #so, what I should really do here is figure out whether the entry already has a place in the table; if so, update its existing stats; if not, 
        #insert a new one; 
        #also need to check if old entries in sepentries table are no longer in file...
        
        entry_q = Session.query(SEPEntry)
        o = SEPEntry.title.like(entries[key]['title'])
        entry_q = entry_q.filter(o)
        # if only 1 result, go ahead and view that idea
        if entry_q.count() == 0:
            entry_add = SEPEntry(entries[key]['title'], key, entries[key]['published'], entries[key]['status'])
            Session.add(entry_add)
        elif entry_q.count() == 1:
            #replace data from most recent from SEPMirror
            entry = entry_q.first()
            entry.title = entries[key]['title']
            entry.published = entries[key]['published']
            entry.status = entries[key]['status']
    #need to really add something here to delete entries no longer in the DB...
    
    entry_q2 = Session.query(SEPEntry)
    for entry in entry_q2:
        if not entries[entry.sep_dir]['title']:
            print str(entry.title) + " appears to have been deleted from SEPMirror; deleting from InPhO database."
            Session.delete(entry)    
    
    Session.flush()
    Session.commit()

def addlist():
    #simply returns the list of published or about to be published sepentries that do not yet have sep_dir fields in the entity table
    entities_q = Session.query(Entity)
    entities_q = entities_q.filter(Entity.sep_dir != None)
    entities_q = entities_q.subquery()
    missing = Session.query(SEPEntry)
    missing = missing.outerjoin((entities_q, SEPEntry.sep_dir == entities_q.c.sep_dir))
    missing = missing.filter(entities_q.c.sep_dir == None)
    #suppress snark, sample
    missing = missing.filter(SEPEntry.title != "Snark")
    missing = missing.filter(SEPEntry.title != "Sample")
    missing = missing.filter(or_(SEPEntry.published == 1, SEPEntry.status == 'au_submit_proofread'))
    return missing.all()
