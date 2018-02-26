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


def evaluate_filing(log, filename):
    with open(filename, "r") as filing_csv:
        #pop each filing open, check the filing type, and add to queue if we want this one
        reader = csv.reader(filing_csv)
        try:
            next(reader)
        except:
            log.write("filing {} has no lines.\n".format(filing))
            return False
        form_line = next(reader)
        if form_line[0].replace('A','').replace('N','') in ['F3','F3X','F3P','F24']:
            if form_line[1] not in ['C00401224']: #bad filings we don't want to load (actblue!)
                return True
        return False

def download_filings(log, filings, filing_dir="filings/"):
    #takes a list of filing ids, downloads the files, filters them to decide
    #if we want to load the filing, and returns the list of filings we want to load
    good_filings = []
    existing_filings = os.listdir('filings')
    for filing in filings:
        #download filings
        filename = '{}{}.csv'.format(filing_dir, filing)
        if filename not in existing_filings:
            file_url = 'http://docquery.fec.gov/csv/{}/{}.csv'.format(str(filing)[-3:],filing)
            if os.path.isfile(filename):
                log.write("we already have filing {} downloaded\n".format(filing))
            else:
                os.system('curl -o {} {}'.format(filename, file_url))

        if evaluate_filing(log, filename):
            good_filings.append(filing)
    return good_filings
