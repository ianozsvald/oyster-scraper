#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Script to automate download and processing of journey history
from the Oystercard website.

Forked from https://github.com/markk/oyster.py

Usage:
$ python oyster.py -n oystercardnumber -u oysterweblogin -p oysterwebpassword

Output:
Generates a JSON output file with a list of entries like:
[
    {u'balance': 29.46,
    u'date': u'30/11/12',
    u'datetime': u'2012-11-30T08:39:00',
    u'fare': 2.7,
    u'location': u'Archway to Old Street',
    u'time': u'08:39-09:01'},
...]

TODO
* fix datetime to save in UTC
"""

import argparse
import urllib
import urllib2
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
from BeautifulSoup import BeautifulSoup
__version__ = '0.1'



def download_data(card):
    """Download data from Oyster (original method from markk)"""
    o = urllib2.build_opener(urllib2.HTTPCookieProcessor())
    urllib2.install_opener(o)
    # log in
    pw = urllib.urlencode({'j_username': card['username'],
                           'j_password': card['password']})
    headers = {'User-Agent': config['web']['useragent']}
    req = urllib2.Request(config['web']['oysterwww'] + '/oyster/security_check', pw, headers)
    f = urllib2.urlopen(req)
    welcomepage = BeautifulSoup(f)
    # find journey history link
    jhtag = welcomepage.find(lambda tag: tag.string == 'Journey history')
    if jhtag is None:
        # get card form
        cardform = welcomepage.find('form', id='selectCardForm')
        cardurl = config['web']['oysterwww'] + cardform['action']
        q = urllib.urlencode({'cardId': card['id'], 'method': 'input'})
        # form (sometimes?) has stupid text input hidden by css
        cardhidden = cardform.find('input', type='hidden')
        if cardhidden:
            q += urllib.urlencode({cardhidden['name']: cardhidden['value']})
        creq = urllib2.Request(cardurl, q, headers)
        g = urllib2.urlopen(creq)
        cardpage = BeautifulSoup(g)
        jhtag = cardpage.find(lambda tag: tag.string == 'Journey history')
        if jhtag is None:
            raise Exception('Failed to find journey history')
    # now ready to get journey history
    todate = datetime.now()
    fromdate = todate - relativedelta(weeks=8)
    jhdict = {'dateRange': 'custom date range',
              'customDateRangeSel': 'false', 'isJSEnabledForPagenation': 'false',
              'offset': '0', 'rows': '0',
              'csDateTo': todate.strftime("%d/%m/%Y"),
              'csDateFrom': fromdate.strftime("%d/%m/%Y")}
    jhurl = config['web']['oysterwww'] + jhtag['href']
    jhreq = urllib2.Request(jhurl, urllib.urlencode(jhdict))
    jh = urllib2.urlopen(jhreq)
    jhpage = jh.read()
    return jhpage


def parse_page(page):
    """Parse the Oyster data (original method from markk)"""
    soup = BeautifulSoup(page)
    journeysdata = soup.find('table', attrs={'class': 'journeyhistory'})
    if journeysdata is None:
        return []
    journeys = []
    for j in journeysdata.findAll('tr', recursive=False):
        try:
            if j.td['class'] == u'data-set':
                # ignore first row which is form
                continue
        except:
            pass
        try:
            if j.td['colspan'] == u'4':
                # ignore second row which is show/hide details link
                # and hidden details rows
                continue
        except:
            pass
        if j.th is not None:
            # ignore header row
            continue
        if j.text == u'No pay as you go journey history to display for the selected period.':
            continue
        # date
        try:
            if u'day-date' in j.td['class']:
                # this is a date row
                if j.td.a is not None:
                    # date has anchor if day is incomplete
                    date = j.td.a.text
                else:
                    date = j.td.text
                try:
                    parseddate = datetime.strptime(date, '%A, %d %B %Y').strftime('%d/%m/%y')
                except ValueError:
                    print "Unable to parse date format:\n\t{0}\n".format(date)
                continue
        except:
            pass
        # otherwise, parse journey row
        journey = {'date': parseddate}
        cells = j.findAll('td')
        # time
        times = cells[0].string.strip().replace('????', '00:00')
        if '-' in times:
            starttime, endtime = times.split('-')
            starttime = starttime.strip()
            endtime = endtime.strip()
            journey['time'] = starttime + '-' + endtime
        else:
            starttime = times
            journey['time'] = starttime
        # datetime - for sorting
        journey['datetime'] = datetime.strptime(date + starttime, '%A, %d %B %Y%H:%M')
        # check if this journey is within requested daterange
        #if options.startdate:
        #    if journey['datetime'] < options.startdate:
        #        continue
        #if options.enddate:
        #    if journey['datetime'] > options.enddate:
        #        continue
        # adjust early morning times to next day
        if datetime.strptime(starttime, '%H:%M').hour < 4:
            # add one day to journey['datetime'] and journey['date']
            journey['datetime'] = datetime.strptime(date + starttime, '%A, %d %B %Y%H:%M') + relativedelta(days=1)
            journey['date'] = journey['datetime'].strftime('%d/%m/%y')
        # location
        if cells[1].a is not None:
            # cell sometimes has more info link
            location = cells[1].a.string
        else:
            location = cells[1].string
        #TODO deal with html characters properly
        journey['location'] = location.strip().replace('&amp;', '&').replace('&#39;', "'")
        # fare
        fare = cells[2].string.strip().replace('&pound;', '').replace(u'\xa3', '').replace('&#163;', '')
        try:
            journey['fare'] = float(fare)
        except ValueError:
            print 'Fare is not a number!'
            journey['fare'] = fare
        # balance
        if cells[3].a is not None:
            balance = cells[3].a.string
        else:
            balance = cells[3].string
        try:
            journey['balance'] = float(balance.strip().replace('&pound;', '').replace(u'\xa3', '').replace('&#163;', ''))
        except ValueError:
            print 'Balance is not a number!', j
            journey['balance'] = balance
        journeys.append(journey)
    return journeys


def json_handler(obj):
    """Write datetime objects in ISO format"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    #elif isinstance(obj, ...):
    #    return ...
    else:
        raise TypeError('Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj)))


def get_oyster_journeys(card):
    """Download, parse and save Oyster data to a JSON file"""
    page = download_data(card)
    all_journeys = parse_page(page)
    filename = "%s.json" % (card['id'])
    print "Writing %d lines of Oyster data to %s" % (len(all_journeys), filename)
    json.dump(all_journeys, open(filename, 'w'), default=json_handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--cardnum", help="Oyster card number (e.g. 012345678901)", required=True)
    parser.add_argument("-u", "--username", help="Oyster website username (e.g. bob)", required=True)
    parser.add_argument("-p", "--password", help="Oyster website password (e.g. abcdefg)", required=True)
    args = parser.parse_args()
    print "Running with args:", args

    # details of Oyster card
    card = {}
    card['username'] = args.username
    card['password'] = args.password
    card['id'] = args.cardnum

    config = {}
    config['web'] = {'useragent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.1.8) Gecko/20100216 Fedora/3.5.8-1.fc12 Firefox/3.5.8',
                     'oysterwww': 'https://oyster.tfl.gov.uk'}

    print "Configuration:", card

    get_oyster_journeys(card)
