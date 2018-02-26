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
            


            filing_fieldnames = [f.name for f in Filing._meta.get_fields()]

            filing_dir = 'filings/'
            good_filings = loader.download_filings(log, filings, filing_dir)

            for filing in good_filings:
                #this is the load loop
                log.write("-------------------\n{}: Started filing {}\n".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filing))
                
                filename = "{}{}.csv".format(filing_dir, filing)

                try:
                    filing_dict = process_filing.process_electronic_filing(filename)
                except Exception as e:
                    log.write("fec2json failed {} {}\n".format(filing, e))
                    continue
                try:
                    #this means the filing already exists
                    #TODO add checking to see if import was successful
                    f = Filing.objects.get(filing_id=filing)
                except:
                    #deal with amended filings
                    if filing_dict['amendment']:
                        amends_filing = int(filing_dict['amends_filing'])
                        try:
                            amended_filing = Filing.objects.filter(filing_id=amends_filing)[0]
                        except IndexError:
                            log.write("could not find filing {}, which was amended by {}, so not deactivating any transactions\n".format(amends_filing, filing))
                        else:
                            amended_filing.active = False
                            amended_filing.status = 'SUPERSEDED'
                            amended_filing.save()
                            ScheduleA.objects.filter(filing_id=amends_filing).update(active=False, status='SUPERSEDED')
                            ScheduleB.objects.filter(filing_id=amends_filing).update(active=False, status='SUPERSEDED')
                            ScheduleE.objects.filter(filing_id=amends_filing).update(active=False, status='SUPERSEDED')

                    if filing_dict['form_type'] in ['F3','F3X','F3P']:
                        #could be a periodic, so see if there are covered forms that need to be deactivated
                        coverage_start_date = filing_dict['coverage_start_date']
                        coverage_end_date = filing_dict['coverage_end_date']
                        covered_filings = Filing.objects.filter(date_signed__gte=coverage_start_date,
                                                                date_signed__lte=coverage_end_date,
                                                                form='F24')
                        covered_filings.update(active=False, status='COVERED')
                        covered_transactions = ScheduleE.objects.filter(filing_id__in=[f.filing_id for f in covered_filings])
                        covered_transactions.update(active=False, status='COVERED')

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
                                ScheduleA.objects.create(**line)
                                scha_count += 1
                        if 'SchB' in filing_dict['itemizations']:
                            for line in filing_dict['itemizations']['SchB']:
                                ScheduleB.objects.create(**line)
                                schb_count += 1
                        if 'SchE' in filing_dict['itemizations']:
                            for line in filing_dict['itemizations']['SchE']:
                                ScheduleE.objects.create(**line)
                                schb_count += 1
                    log.write("inserted {} schedule A's\n".format(scha_count))
                    log.write("inserted {} schedule B's\n".format(schb_count))
                    log.write("inserted {} schedule E's\n".format(sche_count))


                else:
                    log.write('filing {} already exists\n'.format(filing))
                    continue
                log.write("{}: Finished filing {}, SUCCESS!\n".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filing))

            #except:
            #    log.write(traceback.format_exc())
            #    log.write("{}: Run failed.\n".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))


            if logfile:
                log.close()
            if repeat_interval:
                time.sleep(repeat_interval)
            else:
                break


