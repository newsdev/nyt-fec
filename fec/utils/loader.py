import pytz
import datetime
import os
import requests
import csv
import process_filing
import time
import traceback
import sys
from fec.models import *

def get_filing_list(log, start_date, end_date, max_fails=5):
    api_key = os.environ.get('FEC_API_KEY')
    url = "https://api.open.fec.gov/v1/efile/filings/?per_page=100&sort=-receipt_date"
    url += "&api_key={}".format(api_key)
    url += "&min_receipt_date={}".format(start_date)
    url += "&max_receipt_date={}".format(end_date)

    filings = []
    page = 1
    fails = 0
    while True:
        #get new filing ids from FEC API
        resp = requests.get(url+"&page={}".format(page))
        page += 1
        try:
            files = resp.json()
        except:
            #failed to convert respons to JSON
            fails += 1
            if fails >= max_fails:
                log.write('Failed to download valid JSON from FEC site {} times'.format(max_fails))
                return None
            time.sleep(5)
        try:
            results = files['results']
        except KeyError:
            fails += 1
            if fails >= max_fails:
                log.write('Failed to download valid JSON from FEC site {} times'.format(max_fails))
                return None
            time.sleep(5)

        if len(results) == 0:
            break
        for f in results:
            filings.append(f['file_number'])

    return filings
