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

from fec.utils import loader

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--end',
            dest='end',
            help='Latest date to include for the filings parser.')
        parser.add_argument('--start',
            dest='start',
            help='Earliest date to include for the filings parser.')
        parser.add_argument('--repeat-interval',
            dest='repeat-interval',
            help='Number of minutes before rerunning the command. If not specified, just run once')
        parser.add_argument('--logfile',
            dest='logfile',
            help='File to log to, otherwise just log to console')
    #default is to do just today and just committees we have in the DB

    def handle(self, *args, **options):
        fec_time=pytz.timezone('US/Eastern') #fec time is eastern

        unparsed_start = datetime.datetime.now(fec_time) - datetime.timedelta(days=2)
        start_date = unparsed_start.strftime('%Y%m%d')
        unparsed_end = datetime.datetime.now(fec_time) + datetime.timedelta(days=1)
        end_date = unparsed_end.strftime('%Y%m%d')

        if options['start']:
            start_date = options['start']
        if options['end']:
            end_date = options['end']
        if options['repeat-interval']:
            repeat_interval = int(options['repeat-interval'])
        else:
            repeat_interval = None
        if options['logfile']:
            logfile = options['logfile']
            log = open(logfile, 'a')
        else:
            logfile = None
            log = sys.stdout

        while True:
            #keep looping if an interval is provided, this is mostly for testing
            filings = loader.get_filing_list(log, start_date, end_date)
            assert filings, "Failed to find any filings in FEC API"

            filing_dir = 'filings/'
            loader.download_filings(log, filings, filing_dir)
            good_filings = loader.evaluate_filings(log, filings, filing_dir)


            loader.load_filings(log, good_filings, filing_dir)

            if logfile:
                log.close()
            if repeat_interval:
                time.sleep(repeat_interval)
            else:
                break


