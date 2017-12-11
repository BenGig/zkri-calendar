#!/usr/bin/python2
# -*- coding: utf-8 -*-

#########################
# Bengt Giger 2017
# MIT licenced
#
# Convert JSON containing event information from
#
# "Zweckverband Kehrichtentsorgung Region Innerschweiz"
#
# to iCal
#

import icalendar as ical
import json, urllib2, datetime, argparse

url = "http://www.zkri.ch/kunden_sammlung_ausw_cont.php?nGem=%s&nAbar=%s&nSage=%s&sDatum=%s&delsel=%s&jahr1=%s&jahr2=%s"

# defaults to Arth
loc = "33"
abar = "null"
sage = "189"
date = ""
delsel = "no"
year = "2018"
year2 = ""

def splitLine(line, pos):
    # cut out separating garbage "Karton\u00a7@_..\u00a3KE\u00e7Kehricht"
    item = line[0:pos-1]
    rest = line[pos+9:]
    return item, rest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert JSON from www.zkri.ch to iCal")
    parser.add_argument('year', help="Year to get data for")
    parser.add_argument('--location', default=33, type=int, help="Numeric location identifier")
    parser.add_argument('--area', default=189, type=int, help="Numeric area identifier")

    args = parser.parse_args()

    loc = str(args.location)
    sage = str(args.area)
    year = str(args.year)

    # get source data
    jdata = json.load(urllib2.urlopen(url % (loc, abar, sage, date, delsel, year, year2)))
    
    events = [] # event storage list
    
    for d in jdata:
        # indicates a valid event (?)
        if not d["SA_onlySage"] == None and len(d["SA_onlySage"]) > 1:
            # remove strange garbage around event description: "_..\u00a3KE\u00e7Kehricht\u00a7"
            item = d['SA_onlyAbar'][7:-1]
            
            (y, m, d) = d['DATUM'].split("-")
            date = datetime.date(int(y),int(m),int(d))

            # more gargabe, separates events if more than one per day
            pos = item.find(u'§@_..£KEç')
            if pos > 0:
                while pos > 0:
                    item, rest = splitLine(item, pos)
                    events.append((item, date))
                    item = rest
                    pos = item.find(u'§@_..£KEç')
            else:
                events.append((item, date))

    # main iCal calendar object, will hold events. Mandatory properties follow
    cal = ical.cal.Calendar()
    cal.add('prodid', 'zkri-Generator')
    cal.add('version', '1.0')

    uid = 1000000
    # create iCal events
    for event in events:
        (item, date) = event
        ev = ical.cal.Event()
        # only date = all day event
        ev.add('dtstart', "%04d%02d%02d" % (date.year, date.month, date.day), encode=0)
        # when iCal event was created
        ev.add('dtstamp', datetime.datetime.now())
        # readable text
        ev.add('summary', item)
        # unique identifier
        ev.add('uid', "zkri-%s-%s" % (uid, datetime.datetime.now().isoformat()))
        # do not mark as busy; not in basic property catalog
        ev['TRANSP'] = u"TRANSPARENT"
        cal.add_component(ev)
        uid += 1

    # dump iCal to stdout
    print cal.to_ical()
