import csv

from cycle_2018.models import Donor, ScheduleA

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):

    def handle(self, *args, **options):
        crosswalk = {} #dict from old donor id to new donor id
        with open("data/donors_from_old_system.csv","r") as infile:
            reader = csv.DictReader(infile)
            for line in reader:
                #see if donor with all matching info exists
                matching_donors = Donor.objects.filter(nyt_name=line['nyt_name'],
                                        nyt_occupation=line['nyt_occupation'],
                                        nyt_employer=line['nyt_employer'],
                                        city=line['city'],
                                        state=line['state'])
                if len(matching_donors) == 1:
                    crosswalk[line['old_system_id']] = matching_donors[0].id
                elif len(matching_donors) > 1:
                    print("multiple matching donors for {}, this is bad".format(line['nyt_name']))
                else:
                    d = Donor.objects.create(nyt_name=line['nyt_name'],
                                        nyt_occupation=line['nyt_occupation'],
                                        nyt_employer=line['nyt_employer'],
                                        city=line['city'],
                                        state=line['state'],
                                        nyt_note=line['nyt_note'])
                    d.save()
                    print("added donor {}".format(line['nyt_name']))
                crosswalk[line['old_system_id']] = d.id

        with open("data/donor_contrib_matches_from_old_system.csv","r") as match_infile:
            match_reader = csv.DictReader(match_infile)
            for line in match_reader:
                #find transaction
                transaction = ScheduleA.objects.filter(transaction_id=line['transaction_id'], filing_id=line['filing_id'])
                if len(transaction) > 1:
                    print("multiple matching transactions for trans_id {} and filing_id {}, this is very bad".format(line['transaction_id'], line['filing_id']))
                elif len(transaction) == 0:
                    continue
                else:
                    new_donor_id = crosswalk[line['old_system_donor_id']]
                    t = transaction[0]
                    t.donor_id = new_donor_id
                    t.save()



