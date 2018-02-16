import pytz
import datetime
import os
import requests
import csv
import process_filing
from fec.models import *

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--end',
            dest='end',
            help='Latest date to include for the filings parser.')
        parser.add_argument('--start',
            dest='start',
            help='Earliest date to include for the filings parser.')
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

        api_key = os.environ.get('FEC_API_KEY')
        url = "https://api.open.fec.gov/v1/efile/filings/?per_page=100&sort=-receipt_date"
        url += "&api_key={}".format(api_key)
        url += "&min_receipt_date={}".format(start_date)
        url += "&max_receipt_date={}".format(end_date)

        filings = []
        page = 1
        while True:
            resp = requests.get(url+"&page={}".format(page))
            page += 1
            files = resp.json()
            results = files['results']
            if len(results) == 0:
                break
            for f in results:
                filings.append(f['file_number'])

        good_filings = []
        for filing in filings:
            filename = 'filings/{}.csv'.format(filing)
            if filename not in os.listdir('filings'):
                file_url = 'http://docquery.fec.gov/csv/{}/{}.csv'.format(str(filing)[-3:],filing)
                if os.path.isfile(filename):
                    print("we already have filing {} downloaded".format(filing))
                else:
                    os.system('curl -o {} {}'.format(filename, file_url))
            with open(filename, "r") as filing_csv:
                reader = csv.reader(filing_csv)
                next(reader)
                if next(reader)[0].replace('A','').replace('N','') in ['F3','F3X','F3P']:
                    good_filings.append(filing)

        filing_fieldnames = [f.name for f in Filing._meta.get_fields()]
        for filing in good_filings:
            filename = 'filings/{}.csv'.format(filing)
            try:
                filing_dict = process_filing.process_electronic_filing(filename)
            except Exception as e:
                print("fec2json failed", filing, e)
                continue
            try:
                f = Filing.objects.get(filing_id=filing)
            except:
                clean_filing_dict = {k: filing_dict[k] for k in set(filing_fieldnames).intersection(filing_dict.keys())}
                clean_filing_dict['filing_id'] = filing
                clean_filing_dict['filer_id'] = filing_dict['filer_committee_id_number']
                filing_obj = Filing.objects.create(**clean_filing_dict)
                filing_obj.save()

                #create or update committee
                try:
                    comm = Committee.objects.create(fec_id=filing_dict['filer_committee_id_number'])
                    comm.save()
                except:
                    pass

                committee_fieldnames = [f.name for f in Committee._meta.get_fields()]
                committee = {}
                committee['zipcode'] = filing_dict['zip']
                for fn in committee_fieldnames:
                    try:
                        field = filing_dict[fn]
                    except:
                        continue
                    committee[fn] = field

                comm = Committee.objects.filter(fec_id=filing_dict['filer_committee_id_number']).update(**committee)

                #add itemizations - eventually we're going to need to bulk insert here
                #skedA's
                scha_count = 0
                schb_count = 0
                sche_count = 0
                if 'itemizations' in filing_dict:
                    if 'SchA' in filing_dict['itemizations']:
                        for line in filing_dict['itemizations']['SchA']:
                            s = ScheduleA.objects.create(filing_id=filing, **line)
                            s.save()
                            scha_count += 1
                    if 'SchB' in filing_dict['itemizations']:
                        for line in filing_dict['itemizations']['SchB']:
                            s = ScheduleB.objects.create(filing_id=filing, **line)
                            s.save()
                            schb_count += 1
                    if 'SchE' in filing_dict['itemizations']:
                        for line in filing_dict['itemizations']['SchE']:
                            s = ScheduleE.objects.create(filing_id=filing, **line)
                            s.save()
                            schb_count += 1
                print("inserted {} schedule A's".format(scha_count))
                print("inserted {} schedule B's".format(schb_count))
                print("inserted {} schedule E's".format(sche_count))


            else:
                print('filing {} already exists'.format(filing))
                continue
            



    #probably here we want to:
    #1. check whether the filing is in the queue yet
    #2. check whether it's already loaded
    #3. pop it open and see if it's a filing type we want to load