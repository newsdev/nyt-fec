import datetime
import re

from django.shortcuts import render
from django.db.models import Q, Sum
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from fec.models import *
from fec.forms import *

def index(request):
    context = {}
    context['new_filings'] = Filing.objects.filter(active=True).order_by('-created')[:100]
    return render(request, 'index.html', context)

def contributions(request):
    form = ContributionForm(request.GET)
    if not request.GET:
        return render(request, 'contributions.html', {'form': form})

    comm = request.GET.get('committee')
    filing_id = request.GET.get('filing_id')
    donor = request.GET.get('donor')
    employer = request.GET.get('employer')
    include_memo = request.GET.get('include_memo')

    results = ScheduleA.objects.filter(active=True)
    if not include_memo:
        results = results.exclude(status='MEMO')
    if filing_id:
        results = results.filter(filing_id=filing_id)
    if employer:
        query = SearchQuery(employer)
        vector = SearchVector('contributor_employer', 'contributor_occupation')
        results = results.annotate(search=vector).filter(search=query)
    if donor:
        query = SearchQuery(donor)
        vector = SearchVector('contributor_first_name', 'contributor_middle_name', 'contributor_last_name', 'contributor_organization_name')
        results = results.annotate(search=vector).filter(search=query)

    if comm:
        if re.match('C\d\d\d\d\d\d\d\d', comm):
            #it's a committee id, search that field:
            results = results.filter(filer_id=comm)
        #TODO: deal with committee name search


    order_by = request.GET.get('order_by', 'contribution_amount')
    order_direction = request.GET.get('order_direction', 'DESC')
    if order_direction == "DESC":
        results = results.order_by('-{}'.format(order_by))
    else:
        results = results.order_by(order_by)


    results_sum = None if include_memo else results.aggregate(Sum('contribution_amount'))

    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)

    
    return render(request, 'contributions.html', {'form': form, 'results':results, 'results_sum':results_sum})



    