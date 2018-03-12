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
        results = results.filter(occupation_search=query)
    if donor:
        query = SearchQuery(donor)
        results = results.filter(name_search=query)

    if comm:
        matching_committees = Committee.find_committee_by_name(comm)
        comm_ids = [c.fec_id for c in matching_committees]
        results = results.filter(filer_committee_id_number__in=comm_ids)

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



def expenditures(request):
    form = ExpenditureForm(request.GET)
    if not request.GET:
        return render(request, 'expenditures.html', {'form': form})

    comm = request.GET.get('committee')
    filing_id = request.GET.get('filing_id')
    recipient = request.GET.get('recipient')
    purpose = request.GET.get('purpose')
    include_memo = request.GET.get('include_memo')

    results = ScheduleB.objects.filter(active=True)
    if not include_memo:
        results = results.exclude(status='MEMO')
    if filing_id:
        results = results.filter(filing_id=filing_id)
    if purpose:
        query = SearchQuery(purpose)
        results = results.filter(purpose_search=query)
    if recipient:
        query = SearchQuery(recipient)
        results = results.filter(name_search=query)

    if comm:
        matching_committees = Committee.find_committee_by_name(comm)
        comm_ids = [c.fec_id for c in matching_committees]
        results = results.filter(filer_committee_id_number__in=comm_ids)

    order_by = request.GET.get('order_by', 'expenditure_amount')
    order_direction = request.GET.get('order_direction', 'DESC')
    if order_direction == "DESC":
        results = results.order_by('-{}'.format(order_by))
    else:
        results = results.order_by(order_by)


    results_sum = None if include_memo else results.aggregate(Sum('expenditure_amount'))

    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)

    
    return render(request, 'expenditures.html', {'form': form, 'results':results, 'results_sum':results_sum})

def ies(request):
    form = IEForm(request.GET)
    if not request.GET:
        return render(request, 'ies.html', {'form': form})

    comm = request.GET.get('committee')
    filing_id = request.GET.get('filing_id')
    recipient = request.GET.get('recipient')
    purpose = request.GET.get('purpose')
    candidate = request.GET.get('candidate')

    results = ScheduleE.objects.filter(active=True)
    if filing_id:
        results = results.filter(filing_id=filing_id)
    if purpose:
        query = SearchQuery(purpose)
        results = results.filter(purpose_search=query)
    if recipient:
        query = SearchQuery(recipient)
        results = results.filter(name_search=query)
    if candidate:
        query = SearchQuery(candidate)
        results = results.filter(candidate_search=query)

    if comm:
        matching_committees = Committee.find_committee_by_name(comm)
        comm_ids = [c.fec_id for c in matching_committees]
        results = results.filter(filer_committee_id_number__in=comm_ids)

    order_by = request.GET.get('order_by', 'expenditure_amount')
    order_direction = request.GET.get('order_direction', 'DESC')
    if order_direction == "DESC":
        results = results.order_by('-{}'.format(order_by))
    else:
        results = results.order_by(order_by)


    results_sum = results.aggregate(Sum('expenditure_amount'))

    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)

    
    return render(request, 'ies.html', {'form': form, 'results':results, 'results_sum':results_sum})
