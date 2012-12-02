#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Analyse a JSON file of Oyster data
"""

import argparse
import json
import math
from collections import Counter
from collections import defaultdict
from pprint import pprint
import dateutil.parser as dtparse
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
