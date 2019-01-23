import pytz
import datetime
import os
import requests
import csv
import process_filing
import time
import traceback
import sys
from cycle_2020.models import *

from cycle_2020.utils import loader

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
            help='Number of minutes before rerunning the command. If not specified, just run once. This is to make it easy to daemonize this command locally if needed')
        parser.add_argument('--filing_dir',
            dest='filing_dir',
            help='where to save and read filings from')
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
        if options['filing_dir']:
            filing_dir = options['filing_dir']
        else:
            filing_dir = 'filings/'

        while True:
            print("looking for filings for period {}-{}".format(start_date, end_date))
            #keep looping if an interval is provided, this is mostly for testing
            filings = loader.get_filing_list(start_date, end_date)
            if not filings:
                print("failed to find any filings for period {}-{}".format(start_date, end_date))
            
            loader.download_filings(filings, filing_dir)
            loader.load_filings(filing_dir)

            if repeat_interval:
                time.sleep(repeat_interval)
            else:
                break

            if repeat_interval:
                time.sleep(repeat_interval)
            else:
                break


