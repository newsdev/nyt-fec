import pytz
import datetime
import os
import requests
import csv
import time
import traceback
import sys
import urllib3
import lxml
from decimal import Decimal
from fec.utils import logging

from bs4 import BeautifulSoup

import process_filing #this is from fec2json

from fec.models import *
from django.conf import settings


ACCEPTABLE_FORMS = ['F3','F3X','F3P','F24']
BAD_COMMITTEES = ['C00401224','C00630012'] #actblue; it starts today


def get_filing_list(start_date, end_date, max_fails=10, waittime=10):
    #gets list of available filings from the FEC.
    #TODO: institute an API key pool or fallback?
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
                logging.log(title="FEC download failed",
                    text='Failed to download valid JSON from FEC site {} times'.format(max_fails),
                    tags=["nyt-fec", "result:fail"])
                return None
            time.sleep(waittime)
        try:
            results = files['results']
        except KeyError:
            fails += 1
            if fails >= max_fails:
                logging.log(title="FEC download failed",
                    text='Failed to download valid JSON from FEC site {} times'.format(max_fails),
                    tags=["nyt-fec", "result:fail"])
                return None
            time.sleep(waittime)

        if len(results) == 0:
            break
        for f in results:
            if evaluate_filing(f):
                filings.append(f['file_number'])

    return filings

def filing_list_from_rss():
    #backup scraper if api craps out. Will get whatever is
    #currently in the rss feed, so no dates. We should probably
    #run this occasionally on filing nights.
    http = urllib3.PoolManager()
    response = http.request('GET', 'http://efilingapps.fec.gov/rss/generate?preDefinedFilingType=ALL')
    soup = BeautifulSoup(response.data, "lxml")
    items = soup.findAll('item')
    filings = []
    for item in items:
        #make a dictionary that will match what we would have gotten from the api
        filing = {}
        filing_info = item.find('description').text
        filing_info_list = filing_info.split("CommitteeId")[1].split('|')
        filing['committee_id'] = filing_info_list[0].replace(":","").strip()
        filing['file_number'] = filing_info_list[1].replace("FilingId:","").strip()
        filing['form_type'] = filing_info_list[2].replace("FormType:","").strip()
        coverage_through = filing_info_list[4].replace('CoverageThrough:','').strip()
        filing['coverage_end_date'] = coverage_through[6:]+coverage_through[0:2]+coverage_through[3:5]

        if evaluate_filing(filing):
            filings.append(filing['file_number'])
    return filings

def evaluate_filing(filing):
    #determines whether filings in the API should be downloaded
    filing_id = filing['file_number']

    #check whether we've already marked this filing as bad
    existing_filings = FilingStatus.objects.filter(filing_id=filing_id)
    if len(existing_filings) > 0:
        #remove filings that were successful
        if existing_filings[0].status in ['SUCCESS','REFUSED']:
            return False
        else:
            #include filings that failed or are missing a status marker
            return True

    #remove bad committees:
    if filing['committee_id'] in BAD_COMMITTEES:
        status = FilingStatus.objects.create(filing_id=filing_id, status='REFUSED')
        status.save()
        return False

    #remove filing types we're not loading
    if filing['form_type'].replace('A','').replace('N','') not in ACCEPTABLE_FORMS:
        status = FilingStatus.objects.create(filing_id=filing_id, status='REFUSED')
        status.save()
        return False

    #remove filings whose coverage period ended outside the current cycle
    cycle = settings.CYCLE
    coverage_end = filing['coverage_end_date']
    if coverage_end:
        coverage_end_year = coverage_end[0:4]
        if filing['form_type'] == 'F3P' and cycle % 4 == 0:
            #if it's a presidential filing, we want it if it's in the 4-year period.
            acceptable_years = [cycle, cycle-1, cycle-3, cycle-4]
        else:
            acceptable_years = [cycle, cycle-1]
        if int(coverage_end_year) not in acceptable_years:
            create_or_update_filing_status(filing_id, 'REFUSED')
            return False


    #by the time we get here, it's filings we haven't seen but don't meet our refused conditions    
    return True


def download_filings(filings, filing_dir="filings/"):
    #takes a list of filing ids, downloads the files
    http = urllib3.PoolManager()
    existing_filings = os.listdir(filing_dir)
    for filing in filings:
        #download filings
        filename = '{}{}.csv'.format(filing_dir, filing)
        if filename not in existing_filings:
            file_url = 'http://docquery.fec.gov/csv/{}/{}.csv'.format(str(filing)[-3:],filing)
            if os.path.isfile(filename):
                sys.stdout.write("we already have filing {} downloaded\n".format(filing))
            else:
                response = http.request('GET', file_url)
                with open(filename,'wb') as f:
                    f.write(response.data)
                sys.stdout.write('downloaded {}\n'.format(filing))
                #os.system('curl -o {} {}'.format(filename, file_url))

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
            if line['form_type'].startswith('SB28'):
                #these are refunds and should be processed as contribs
                #we're going to create them individually to prevent trouble
                refund = convert_refund_to_skeda(line)
                ScheduleA.objects.create(**refund)
                continue

            if line['memo_code'] == 'X':
                line['status'] = 'MEMO'
            chunk.append(sked_model(**line))
            if len(chunk) >= chunk_size:
                sked_model.objects.bulk_create(chunk)
                chunk = []
        sked_model.objects.bulk_create(chunk)
    return sked_count

def convert_refund_to_skeda(line):
    common_fields = ['form_type',
                    'filer_committee_id_number',
                    'filing_id',
                    'transaction_id',
                    'back_reference_tran_id_number',
                    'back_reference_sched_name',
                    'entity_type',
                    'election_code',
                    'election_other_description',
                    'memo_code',
                    'memo_text_description'
                    ]
    skeda_dict = {}
    for field in common_fields:
        skeda_dict[field] = line[field]
    skeda_dict['contributor_organization_name'] = line['payee_organization_name']
    skeda_dict['contributor_last_name'] = line['payee_last_name']
    skeda_dict['contributor_first_name'] = line['payee_first_name']
    skeda_dict['contributor_middle_name'] = line['payee_middle_name']
    skeda_dict['contributor_prefix'] = line['payee_prefix']
    skeda_dict['contributor_suffix'] = line['payee_suffix']
    skeda_dict['contributor_street_1'] = line['payee_street_1']
    skeda_dict['contributor_street_2'] = line['payee_street_2']
    skeda_dict['contributor_city'] = line['payee_city']
    skeda_dict['contributor_state'] = line['payee_state']
    skeda_dict['contributor_zip'] = line['payee_zip']
    skeda_dict['contribution_date'] = line['expenditure_date']
    skeda_dict['contribution_amount'] = -1*Decimal(line['expenditure_amount'])
    
    return skeda_dict

def reassign_standardized_donors(filing_id, amended_id):
    #find all skeda's with donors from the amended filing
    #that we're about to deactivate
    matched_transactions = ScheduleA.objects.filter(filing_id=amended_id).exclude(donor=None)
    for transaction in matched_transactions:
        transaction_id = transaction.transaction_id
        contributor_last_name = transaction.contributor_last_name
        new_trans = ScheduleA.objects.filter(transaction_id=transaction_id, filing_id=filing_id)
        if len(new_trans) == 0:
            logging.log(title="donor reassignment issue",
                    text="filing {} was amended by filing {} and no transaction could be found for donor reassigment for transaction id {}".format(amended_id, filing_id, transaction_id),
                    tags=["nyt-fec", "result:warning"])
            continue
        if len(new_trans) > 1:
            logging.log(title="donor reassignment issue",
                    text="filing {} was amended by filing {} and multiple transaction matches were found for {}".format(amended_id, filing_id, transaction_id),
                    tags=["nyt-fec", "result:warning"])
            continue
        new_trans = new_trans[0]
        if new_trans.contributor_last_name != contributor_last_name:
            logging.log(title="donor reassignment issue",
                    text="Want to reassign transaction {} from filing {} to filing {} but last names mismatch: {}/{}".format(transaction_id, amended_id, filing_id, contributor_last_name, new_trans.contributor_last_name),    
                    tags=["nyt-fec", "result:warning"])
            continue

        new_trans.donor = transaction.donor
        new_trans.save()
        transaction.donor = None
        transaction.save()


def clean_filing_fields(processed_filing, filing_fieldnames):
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
                sys.stdout.write('adding last odd cycle total for {}\n'.format(key))
                v = Decimal(v) + addons.get(key, Decimal(0))
            clean_filing[key] = v

        else:
            pass
    return clean_filing

def is_even_year(filing):
    try:
        year = int(filing['coverage_through_date'][0:4])
    except:
        sys.stdout.write('Could not find coverage date for filing {}, not fixing sums\n'.format(filing['filing_id']))
        return
    if year % 2 == 0:
        return True
    return False

def last_odd_filing(filing):
    committee_id = filing['filer_id']
    committee_filings = Filing.objects.filter(filer_id=committee_id).order_by('-coverage_through_date','-date_signed')
    return committee_filings[0]


def evaluate_filing_file(filename, filing_id):
    with open(filename, "r") as filing_csv:
        #pop each filing open, check the filing type, and add to queue if we want this one
        reader = csv.reader(filing_csv)
        try:
            next(reader)
        except:
            return False
        form_line = next(reader)
        if form_line[0].replace('A','').replace('N','') not in ACCEPTABLE_FORMS:
            create_or_update_filing_status(filing_id, 'REFUSED')
            return False
        if form_line[1] in BAD_COMMITTEES:
            create_or_update_filing_status(filing_id, 'REFUSED')
            return False

        #next, check if this filing has previously been refused
        if len(FilingStatus.objects.filter(filing_id=filing_id, status='REFUSED')) > 0:
            return False

        #next check if we already have the filing
        filings = Filing.objects.filter(filing_id=filing_id)
        if len(filings) == 0:
            return True
        if filings[0].status == 'FAILED':
            #delete the filing. it failed, so we're going to try again
            filings.delete()
            return True
        if filings[0].status == 'PROCESSING':
            #alert, but do not delete or reload.
            return False

        #if we get here, a filing exists, it's not 'failed' or 'processing' so we should not load
        return False

def load_filing(filing, filename, filing_fieldnames):
    #returns boolean depending on whether filing was loaded
    
    
    #this means the filing already exists
    #TODO add checking to see if import was successful
    filing_matches = Filing.objects.filter(filing_id=filing)
    if len(filing_matches) == 1:
        if filing_matches[0].status != "FAILED":
            sys.stdout.write('filing {} already exists\n'.format(filing))
            return False
        else:
            sys.stdout.write("Reloading {}, it failed perviously\n".format(filing))
    
    #filing does not exist or it failed previously
    try:
        filing_dict = process_filing.process_electronic_filing(filename)
    except Exception as e:
        logging.log(title="fec2json failed",
                    text="fec2json failed {} {}".format(filing, e),
                    tags=["nyt-fec", "result:fail"])
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
            sys.stdout.write('Covered through {}, not importing\n'.format(coverage_end))
            create_or_update_filing_status(filing, 'REFUSED')
            return False

    #deal with amended filings
    if filing_dict['amendment']:

        #oy, one filer really likes semi-colons.
        if filing_dict.get('amends_filing'):
            filing_dict['amends_filing'] = filing_dict['amends_filing'].replace(';','')
        try:
            amends_filing_str = filing_dict['amends_filing']
            amends_filing = int(amends_filing_str)
        except ValueError:
            #should be a warning or possibly critical
            logging.log(title="Filing {} Failed".format(filing_id),
                    text='Invalid amendment number {} for filing {}, creating filing and marking as FAILED\n'.format(filing_dict['amends_filing'],filing),
                    tags=["nyt-fec", "result:fail"])
            filing_obj = Filing.objects.create(filing_id=filing, status='FAILED')
            filing_obj.save()
            return False
        else:
            try:
                amended_filing = Filing.objects.filter(filing_id=amends_filing)[0]
            except IndexError:
                sys.stdout.write("could not find filing {}, which was amended by {}, so not deactivating any transactions\n".format(amends_filing, filing))
            else:
                #if there are filings that were amended by the amended filing
                #they also have to be deactivated, so look for them.
                other_amended_filings = Filing.objects.filter(amends_filing=amended_filing.filing_id)
                amended_filings = [f for f in other_amended_filings] + [amended_filing]
                for amended_filing in amended_filings:
                    amended_filing.active = False
                    amended_filing.status = 'SUPERSEDED'
                    amended_filing.save()
                    ScheduleA.objects.filter(filing_id=amends_filing).update(active=False, status='SUPERSEDED')
                    ScheduleB.objects.filter(filing_id=amends_filing).update(active=False, status='SUPERSEDED')
                    ScheduleE.objects.filter(filing_id=amends_filing).update(active=False, status='SUPERSEDED')
                    reassign_standardized_donors(filing, amends_filing)

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

    clean_filing_dict = clean_filing_fields(filing_dict, filing_fieldnames)
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
        sys.stdout.write('failed to update committee\n')

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
        sys.stdout.write("inserted {} schedule A's\n".format(scha_count))
        sys.stdout.write("inserted {} schedule B's\n".format(schb_count))
        sys.stdout.write("inserted {} schedule E's\n".format(sche_count))
    except:
        #something failed in the transaction loading, keep the filing as failed
        #but remove the itemizations
        filing_obj.status='FAILED'
        filing_obj.save()
        create_or_update_filing_status(filing, 'FAILED')
        ScheduleA.objects.filter(filing_id=filing).delete()
        ScheduleB.objects.filter(filing_id=filing).delete()
        ScheduleE.objects.filter(filing_id=filing).delete()
        logging.log(title="Itemization load failed",
                    text='Something failed in itemizations, marking {} as FAILED'.format(filing),
                    tags=["nyt-fec", "result:fail"])
        return False

    sys.stdout.write('Marking {} as ACTIVE\n'.format(filing))
    filing_obj.status='ACTIVE'
    filing_obj.save()
    create_or_update_filing_status(filing, 'SUCCESS')
    return True

def create_or_update_filing_status(filing_id, status):
    fs = FilingStatus.objects.filter(filing_id=filing_id)
    if len(fs) > 0:
        fs = fs[0]
        fs.status = status
        fs.save()
    else:
        fs = FilingStatus.objects.create(filing_id=filing_id, status=status)
        fs.save()    


def load_filings(filing_dir):

    
    filing_fieldnames = [f.name for f in Filing._meta.get_fields()]

    filing_csvs = sorted(os.listdir(filing_dir))
    filings_loaded = 0
    for filename in filing_csvs:
        filing_id = filename.split(".")[0]
        if filename[0] == ".":
            continue
        try:
            int(filing_id)
        except:
            logging.log(title="Bad FEC filename",
                    text='did not recognize filing {}'.format(filename),
                    tags=["nyt-fec", "result:warn"])
            continue

        full_filename = "{}{}".format(filing_dir, filename)
        
        if not evaluate_filing_file(full_filename, filing_id):
            continue
                
        sys.stdout.write("-------------------\n{}: Started filing {}\n".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filing_id))
        

        if load_filing(filing_id, full_filename, filing_fieldnames):

            logging.log(title="Filing {} loaded".format(filing_id),
                    text='filing {} successfully loaded'.format(filing_id),
                    tags=["nyt-fec", "result:success"])

            filings_loaded += 1

    logging.log(title="FEC scrape completed".format(filing_id),
                    text='{} filings successfully loaded'.format(filings_loaded),
                    tags=["nyt-fec", "result:success"])