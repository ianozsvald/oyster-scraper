oyster-scraper
==============

Scrape the London Oyster website for Tube travel data with Python (forked from markk), forked:
https://github.com/markk/oyster.py

Goal
====

Login to Oyster website, extract travel history, write as a JSON file.

Usage:

To load Oyster data:

    $ python oyster.py -n oystercardnumber -u oysterweblogin -p oysterwebpassword

and you probably want to move the JSON file into a data/ directory.

To analyse Oyster data for plotting:

    $ python analyse.py -f data/01234xxxxxx.json

will load the data and show average and standard deviation, preparing it (with some hacky list manipulations) for plotting.
