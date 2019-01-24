from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.urls import reverse

from donor.models import *

def donor_details(request, donor_id):
    context = {}
    donor = Donor.objects.get(id=donor_id)
    context['donor'] = donor
    context['contribs2018'] = donor.contributions_2018.filter(active=True).order_by('-contribution_amount')
    context['contribs2020'] = donor.contributions_2020.filter(active=True).order_by('-contribution_amount')
    return render(request, 'donor/donor_details.html', context)