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
        parser.add_argument('--repeat-interval',
            dest='repeat-interval',
            help='Number of minutes before rerunning the command. If not specified, just run once. This is to make it easy to daemonize this command locally if needed')
        parser.add_argument('--filing_dir',
            dest='filing_dir',
            help='where to save and read filings from')
    #default is to do just today and just committees we have in the DB

    def handle(self, *args, **options):
        fec_time=pytz.timezone('US/Eastern') #fec time is eastern

        if options['repeat-interval']:
            repeat_interval = int(options['repeat-interval'])
        else:
            repeat_interval = None
    
        if options['filing_dir']:
            filing_dir = options['filing_dir']
        else:
            filing_dir = 'filings/'

        while True:
            print("Pulling filings from RSS feed")
            #keep looping if an interval is provided, this is mostly for testing
            filings = loader.filing_list_from_rss()
            if not filings:
                print("failed to find any new filings in the RSS feed")
            else:
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


