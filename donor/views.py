from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.urls import reverse

from donor.models import *

def donor_details(request, donor_id):
    context = {}
    donor = Donor.objects.get(id=donor_id)
    context['donor'] = donor
    context['contribs'] = donor.schedulea_set.filter(active=True).order_by('-contribution_amount')
    return render(request, 'donor/donor_details.html', context)