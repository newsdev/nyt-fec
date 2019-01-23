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
        parser.add_argument('--filing_id',
            dest='filing_id',
            help='filing_id for filing to load')
        parser.add_argument('--filing_dir',
            dest='filing_dir',
            help='where to save and read filings from')

    def handle(self, *args, **options):
        fec_time=pytz.timezone('US/Eastern') #fec time is eastern

        if options['filing_id']:
            filing_id = options['filing_id']
        else:
            print("filing_id required")
            return
        if options['filing_dir']:
            filing_dir = options['filing_dir']
        else:
            filing_dir = 'filings/'


        loader.download_filings([filing_id], filing_dir)
        loader.load_filings(filing_dir)



