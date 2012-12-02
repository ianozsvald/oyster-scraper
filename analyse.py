#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Analyse a JSON file of Oyster data
"""

import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--filename", help="JSON file of Oyster data e.g. 123456.json", required=True)
args = parser.parse_args()
print "Running with args:", args

oyster = json.load(open(args.filename))

print "Read %d lines of JSON data" % (len(oyster))
