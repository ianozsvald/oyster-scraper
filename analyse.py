#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Analyse a JSON file of Oyster data

Usage:
$ python analyse.py -f 0514xxxxxxxx.json

Input:
A JSON file with contents like:
[
    {u'balance': 29.46,
    u'date': u'30/11/12',
    u'datetime': u'2012-11-30T08:39:00',
    u'fare': 2.7,
    u'location': u'Archway to Old Street',
    u'time': u'08:39-09:01'},
...]

TODO:
* Switch to Pandas and slice more interestingly

Install note:
On Ubuntu 12.04 with a virtualbox to get matplotlib working I had to install:
* libfreetype6-dev
* libpng12-dev
* libjpeg8-dev (I added this opportunistically, might not be needed)
* tk8.5-dev (for matplotlib to have a TkAgg backend during compile time else it
* is Agg only which can't open a window)

Try:
import matplotlib
matplotlib.get_backend() -> 'Agg' if it didn't find TkAgg during compile time
and it finds 'TkAgg' if it is installed correctly

BE WARNED
THE FOLLOWING CODE IS HACKY FROM 1 EVENING'S HACK!
"""

import argparse
import json
import dateutil.parser
import datetime
import math
from collections import Counter
from collections import defaultdict
from pprint import pprint
import dateutil.parser as dtparse
import pylab
# Journey types ('location' field):
# "Old Street to Finsbury Park" - tube journey
# "Bus journey, route 17" - bus journey
# "Automated Refund, Archway" - admin
# "Topped up, Archway" - admin

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", help="JSON file of Oyster data e.g. 123456.json", required=True)
args = parser.parse_args()
print "Running with args:", args

oyster = json.load(open(args.filename))

print "Read %d lines of JSON data" % (len(oyster))


def tube_journey(location):
    """True if this looks like a tube (London Underground) journey

    An example would be "Old Street to Finsbury Park"
    """
    return " to " in location


def average(s):
    return sum(s) * 1.0 / len(s)


def std_dev(s):
    avg = average(s)
    variance = map(lambda x: (x - avg) ** 2, s)
    standard_deviation = math.sqrt(average(variance))
    return standard_deviation


journey_frequency = Counter()
journey_lengths = defaultdict(list)

for entry in oyster:
    location = entry['location']
    if tube_journey(location):
        timespan = entry['time'].split('-')
        dt1 = dtparse.parse(timespan[0])
        dt2 = dtparse.parse(timespan[1])
        minutes = (dt2 - dt1).seconds / 60.0
        journey_frequency.update([location])
        journey_lengths[location].append(minutes)

print "Most frequent journeys:"
pprint(journey_frequency.most_common())

most_frequent_journey_location = journey_frequency.most_common()[0][0]
print "Most frequent journey:", most_frequent_journey_location
a_to_os = journey_lengths[most_frequent_journey_location]
print "Average commute time:", average(a_to_os)
print "Standard deviation on commute time:", std_dev(a_to_os)

time_length = []
for entry in oyster:
    location = entry['location']
    if tube_journey(location):
        timespan = entry['time'].split('-')
        dt1 = dtparse.parse(timespan[0])
        dt2 = dtparse.parse(timespan[1])
        minutes = (dt2 - dt1).seconds / 60.0
        dt_str = entry['datetime']
        dt = dateutil.parser.parse(dt_str)
        if location == most_frequent_journey_location:
            time_only = datetime.time(dt.hour, dt.minute)
            time_length.append((time_only, minutes))

# sort from earliest commute time to latest
time_length.sort()
time_length2 = []
for time, length in time_length:
    mins = (60 * time.hour + time.minute)
    time_length2.append((mins, length))
time, length = zip(*time_length2) # unzip time and length
#pylab.plot(time, length, 'rx')
