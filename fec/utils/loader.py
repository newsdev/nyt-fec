import pytz
import datetime
import os
import requests
import csv
import process_filing
import time
import traceback
import sys
from decimal import Decimal
from fec.models import *
from django.conf import settings

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


def evaluate_filing(log, filename, filing):
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
    #takes a list of filing ids, downloads the files
    existing_filings = os.listdir(filing_dir)
    for filing in filings:
        #download filings
        filename = '{}{}.csv'.format(filing_dir, filing)
        if filename not in existing_filings:
            file_url = 'http://docquery.fec.gov/csv/{}/{}.csv'.format(str(filing)[-3:],filing)
            if os.path.isfile(filename):
                log.write("we already have filing {} downloaded\n".format(filing))
            else:
                os.system('curl -o {} {}'.format(filename, file_url))

def evaluate_filings(log, filings, filing_dir="filings/"):
    #filings is a list of ids, filing_dir is the directory where filings are saved.
    #here we loop through the filings to see if they're valid.
    good_filings = []
    existing_filings = {}
    for f in os.listdir(filing_dir):
        try:
            existing_filings[int(f.split(".")[0])] = "{}{}".format(filing_dir, f)
        except:
            #skip filenames that don't conform to the filename pattern
            pass
    for filing in filings:
        if filing in existing_filings:
            if evaluate_filing(log, existing_filings[filing], filing):
                good_filings.append(filing)
        else:
            log.write('Filing {} not found\n'.format(filing))
    return good_filings


def load_itemizations(sked_model, skeds, debug=False):
    #if debug is true, we'll load one at a time, otherwise bulk_create
    sked_count = 0
    if debug:
        for line in skeds:
            if line['memo_code'] == 'X':
                line['status'] = 'MEMO'
            sked_model.objects.create(**line)
            sked_count += 1
    else:
        chunk_size = 5000
        chunk = []
        for line in skeds:
            sked_count += 1
            if line['memo_code'] == 'X':
                line['status'] = 'MEMO'
            chunk.append(sked_model(**line))
            if len(chunk) >= chunk_size:
                sked_model.objects.bulk_create(chunk)
                chunk = []
        sked_model.objects.bulk_create(chunk)
    return sked_count

def clean_filing_fields(log, processed_filing, filing_fieldnames):
    #check whether the filing requires adding odd-year totals
    odd_filing = None
    addons = {}
    if processed_filing['form_type'] == 'F3' and is_even_year(processed_filing):
        odd_filing = last_odd_filing(processed_filing)

    clean_filing = {}
    for k, v in processed_filing.items():
        key = k
        if k == 'col_a_cash_on_hand_beginning_period':
            key = 'cash_on_hand_beginning_period'
        elif k == 'col_a_cash_on_hand_close_of_period':
            key = 'cash_on_hand_close_of_period'
        elif k == 'col_a_debts_by_summary':
            key = 'debts_by_summary'
        elif k.startswith("col_a_"):
            key = "period_{}".format(k.replace('col_a_',''))
            
        elif k.startswith("col_b_"):
            key = "cycle_{}".format(k.replace('col_b_',''))
            if odd_filing:
                addons[key] = getattr(odd_filing, key)

        if key in filing_fieldnames:
            if addons.get(key):
                log.write('adding last odd cycle total for {}\n'.format(key))
                v = Decimal(v) + addons.get(key, Decimal(0))
            clean_filing[key] = v

        else:
            pass
            #log.write('dropping key {}\n'.format(k))
    return clean_filing

def is_even_year(filing):
    try:
        year = int(filing['coverage_through_date'][0:4])
    except:
        log.write('Could not find coverage date for filing {}, not fixing sums\n'.format(filing['filing_id']))
        return
    if year % 2 == 0:
        return True
    return False

def last_odd_filing(filing):
    committee_id = filing['filer_id']
    committee_filings = Filing.objects.filter(filer_id=committee_id).order_by('-coverage_through_date','-date_signed')
    return committee_filings[0]


def load_filing(log, filing, filename, filing_fieldnames):
    #returns boolean depending on whether filing was loaded
    
    
    #this means the filing already exists
    #TODO add checking to see if import was successful
    filing_matches = Filing.objects.filter(filing_id=filing)
    if len(filing_matches) == 1:
        if filing_matches[0].status != "FAILED":
            log.write('filing {} already exists\n'.format(filing))
            return False
        else:
            log.write("Reloading {}, it failed perviously\n".format(filing))
    
    #filing does not exist or it failed previously
    try:
        filing_dict = process_filing.process_electronic_filing(filename)
    except Exception as e:
        log.write("fec2json failed {} {}\n".format(filing, e))
        return False

    #do not load filings outside of this cycle (these will likely be amendments of old filings)
    cycle = settings.CYCLE
    coverage_end = filing_dict.get('coverage_through_date')
    if coverage_end:
        coverage_end_year = coverage_end[0:4]
        if filing_dict['form_type'] == 'F3P' and cycle % 4 == 0:
            #if it's a presidential filing, we want it if it's in the 4-year period.
            acceptable_years = [cycle, cycle-1, cycle-3, cycle-4]
        else:
            acceptable_years = [cycle, cycle-1]
        if int(coverage_end_year) not in acceptable_years:
            log.write('Filing {} covered through {}, not importing\n'.format(coverage_end))
            return False

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

    clean_filing_dict = clean_filing_fields(log,filing_dict, filing_fieldnames)
    clean_filing_dict['filing_id'] = filing
    clean_filing_dict['filer_id'] = filing_dict['filer_committee_id_number']
    
    if len(filing_matches) == 1:
        filing_matches.update(**clean_filing_dict)
        filing_obj = filing_matches[0]
    else:
        filing_obj = Filing.objects.create(**clean_filing_dict)
    filing_obj.save()

    #create or update committee
    try:
        comm = Committee.objects.create(fec_id=filing_dict['filer_committee_id_number'])
        comm.save()
    except:
        #committee already exists
        pass

    try:
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
    except:
        log.write('failed to update committee\n')

    #add itemizations - eventually we're going to need to bulk insert here
    #skedA's
    try:
        scha_count = 0
        schb_count = 0
        sche_count = 0
        if 'itemizations' in filing_dict:
            if 'SchA' in filing_dict['itemizations']:
                scha_count = load_itemizations(ScheduleA, filing_dict['itemizations']['SchA'])
            if 'SchB' in filing_dict['itemizations']:
                schb_count = load_itemizations(ScheduleB, filing_dict['itemizations']['SchB'])
            if 'SchE' in filing_dict['itemizations']:
                sche_count = load_itemizations(ScheduleE, filing_dict['itemizations']['SchE'])
        log.write("inserted {} schedule A's\n".format(scha_count))
        log.write("inserted {} schedule B's\n".format(schb_count))
        log.write("inserted {} schedule E's\n".format(sche_count))
    except:
        #something failed in the transaction loading, keep the filing as failed
        #but remove the itemizations
        filing_obj.status='FAILED'
        filing_obj.save()
        ScheduleA.objects.filter(filing_id=filing).delete()
        ScheduleB.objects.filter(filing_id=filing).delete()
        ScheduleE.objects.filter(filing_id=filing).delete()
        log.write('Something failed in itemizations, marking {} as FAILED\n'.format(filing_id))
        return False

    log.write('Marking {} as ACTIVE\n'.format(filing))
    filing_obj.status='ACTIVE'
    filing_obj.save()
    return True


def load_filings(log, good_filings, filing_dir):
    filing_fieldnames = [f.name for f in Filing._meta.get_fields()]

    for filing in good_filings:
                
        log.write("-------------------\n{}: Started filing {}\n".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filing))
        
        filename = "{}{}.csv".format(filing_dir, filing)


        if load_filing(log, filing, filename, filing_fieldnames):

            log.write("{}: Finished filing {}, SUCCESS!\n".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filing))
