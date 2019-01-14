import csv

from cycle_2018.models import InauguralContrib

from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--infile',
            dest='infile',
            help='Name of the file of inaugural donors.')
        parser.add_argument('--force',
            dest='infile',
            action='store_true',
            help='load even if table is not empty')

    def handle(self, *args, **options):
        #expects a csv with the following headers:
        #full name,street1,street2,city,state,zip,contrib date,contrib amount
        infile = options.get('infile')
        assert infile, "please provide CSV of inaugural donors"
        if not options.get('force'):
            assert len(InauguralContrib.objects.all()) == 0, "InauguralContrib table is not empty, you probably don't actually want to load"
        with open(infile, 'r') as f:
            reader = csv.DictReader(f)
            for line in reader:
                ic = InauguralContrib.objects.create(name=line['full name'],
                                            address="{} {}".format(line['street1'],line['street2']).strip(),
                                            city=line['city'],
                                            state=line['state'],
                                            zipcode=line['zip'],
                                            date=line['contrib date'],
                                            amount=line['contrib amount'])
                ic.save()





