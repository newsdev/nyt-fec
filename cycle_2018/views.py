import datetime
import re
import csv
import time

from django.shortcuts import render
from django.db.models import Q, Sum
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.http import StreamingHttpResponse
from django.urls import reverse

from cycle_2018.models import *
from cycle_2018.forms import *
from donor.models import Donor

class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def index(request):
    return render(request, '2018/index.html')

def filings(request):
    form = FilingForm(request.GET)
    results = Filing.objects.filter(active=True)
    
    comm = request.GET.get('committee')
    form_type = request.GET.get('form_type')
    min_raised = request.GET.get('min_raised')
    exclude_amendments = request.GET.get('exclude_amendments')
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')
    sort_order = request.GET.get('sort_order', '-created')
    if comm:
        results = results.filter(committee_name__icontains=comm)
    if form_type:
        results = results.filter(form=form_type)
    if min_raised:
        results = results.filter(period_total_receipts__gte=min_raised)
    if exclude_amendments:
        results = results.filter(amends_filing=None)
    if min_date:
        results = results.filter(date_signed__gte=min_date)
    if max_date:
        results = results.filter(date_signed__lte=max_date)
    if sort_order and sort_order.strip('-') in [f.name for f in Filing._meta.get_fields()]:
        results = results.order_by(sort_order)

    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)
    return render(request, '2018/filings.html', {'form': form, 'results':results, 'opts': ScheduleA._meta})

def get_contribution_results(request):
    comm = request.GET.get('committee')
    filing_id = request.GET.get('filing_id')
    donor = request.GET.get('donor')
    employer = request.GET.get('employer')
    address = request.GET.get('address')
    include_memo = request.GET.get('include_memo')
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')
    form_type = request.GET.get('form_type')

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
    if address:
        query = SearchQuery(address)
        results = results.filter(address_search=query)
    if min_date:
        results = results.filter(contribution_date__gte=min_date)
    if max_date:
        results = results.filter(contribution_date__lte=max_date)
    if form_type:
        results = results.filter(form_type=form_type)

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
    return results

def contributions(request):
    form = ContributionForm(request.GET)
    if not request.GET:
        return render(request, '2018/contributions.html', {'form': form})

    results = get_contribution_results(request)

    results_sum = None if request.GET.get('include_memo') else results.aggregate(Sum('contribution_amount'))

    csv_url = reverse('2018:contributions_csv') + "?"+ request.GET.urlencode()

    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)

    
    return render(request, '2018/contributions.html', {'form': form, 'results':results, 'results_sum':results_sum, 'csv_url':csv_url})

def contributions_csv(request):
    results = get_contribution_results(request)
    filename = "ScheduleA_{}.csv".format(time.strftime("%Y%m%d-%H%M%S"))

    def rows():
        yield ScheduleA.export_fields()
        for result in results:
            yield result.csv_row()

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows()),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response

def get_expenditure_results(request):
    comm = request.GET.get('committee')
    filing_id = request.GET.get('filing_id')
    recipient = request.GET.get('recipient')
    address = request.GET.get('address')
    purpose = request.GET.get('purpose')
    include_memo = request.GET.get('include_memo')
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')
    form_type = request.GET.get('form_type')

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
    if address:
        query = SearchQuery(address)
        results = results.filter(address_search=query)
    if min_date:
        results = results.filter(expenditure_date__gte=min_date)
    if max_date:
        results = results.filter(expenditure_date__lte=max_date)
    if form_type:
        results = results.filter(form_type=form_type)

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

    return results


def expenditures(request):
    form = ExpenditureForm(request.GET)
    if not request.GET:
        return render(request, '2018/expenditures.html', {'form': form})

    results = get_expenditure_results(request)    

    results_sum = None if request.GET.get('include_memo') else results.aggregate(Sum('expenditure_amount'))

    csv_url = reverse('2018:expenditures_csv') + "?"+ request.GET.urlencode()

    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)

    return render(request, '2018/expenditures.html', {'form': form, 'results':results, 'results_sum':results_sum, 'csv_url':csv_url})

def expenditures_csv(request):
    results = get_expenditure_results(request)
    filename = "ScheduleB_{}.csv".format(time.strftime("%Y%m%d-%H%M%S"))

    def rows():
        yield ScheduleB.export_fields()
        for result in results:
            yield result.csv_row()

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows()),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response

def get_ie_results(request):
    comm = request.GET.get('committee')
    filing_id = request.GET.get('filing_id')
    recipient = request.GET.get('recipient')
    purpose = request.GET.get('purpose')
    candidate = request.GET.get('candidate')
    state = request.GET.get('state')
    district = request.GET.get('district')
    nyt_district = request.GET.get('nyt_district')
    min_date = request.GET.get('min_date')
    max_date = request.GET.get('max_date')

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
    if state:
        results = results.filter(candidate_state__iexact=state)
    if district:
        district = district.zfill(2)
        results = results.filter(candidate_district=district)
    if nyt_district:
        results = results.filter(nyt_district=nyt_district)
    if min_date:
        results = results.filter(expenditure_date__gte=min_date)
    if max_date:
        results = results.filter(expenditure_date__lte=max_date)

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

    return results

def ies(request):
    form = IEForm(request.GET)
    if not request.GET:
        return render(request, '2018/ies.html', {'form': form})

    results = get_ie_results(request)

    results_sum = results.aggregate(Sum('expenditure_amount'))

    csv_url = reverse('2018:ie_csv') + "?"+ request.GET.urlencode()

    paginator = Paginator(results, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)
    context = {'form': form, 'results':results, 'results_sum':results_sum, 'csv_url':csv_url}
    if request.GET.get('nyt_district'):
        context['nyt_district'] = True
        context['opts'] = ScheduleE._meta

    return render(request, '2018/ies.html', context)

def ie_csv(request):
    results = get_ie_results(request)
    filename = "ScheduleE_{}.csv".format(time.strftime("%Y%m%d-%H%M%S"))

    def rows():
        yield ScheduleE.export_fields()
        for result in results:
            yield result.csv_row()

    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows()),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response


def races(request):
    races = ScheduleE.objects.filter(active=True).values('nyt_district').annotate(Sum('expenditure_amount'))
    
    order_by = request.GET.get('order_by', 'expenditure_amount')
    if order_by == 'race':
        races = races.order_by('nyt_district')
    else:
        races = races.order_by('-expenditure_amount__sum')

    return render(request, '2018/races.html', {'races':races})

def top_donors(request):
    donors = sorted(Donor.objects.all(), key=lambda d: d.contribution_total_2018, reverse=True)
    #this sort might be too slow for words once the database hits a reasonable size, but also maybe not bc we will never have that many named donors
    paginator = Paginator(donors, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)
    opts = Donor._meta
    return render(request, '2018/top_donors.html', {'results':results, 'contact':settings.CONTACT, 'opts':opts})

def filing_status(request, status):
    context = {}
    status = status.upper()
    context['filings'] = FilingStatus.objects.filter(status=status).order_by('-created')
    return render(request, '2018/filing_status.html', context)

def committee(request, committee_id):
    context = {}
    committee = Committee.objects.get(fec_id=committee_id)
    context['committee'] = committee
    periodic = Filing.objects.filter(filer_id=committee_id,active=True,form__startswith='F3').order_by('-coverage_through_date')
    context['periodic'] = periodic
    context['non_periodic'] = Filing.objects.filter(filer_id=committee_id,active=True,form__in=['F24','F5']).order_by('-date_signed')
    if len(periodic) > 0:
        context['most_recent_periodic'] = periodic[0]
    else:
        context['most_recent_periodic'] = None
    return render(request, '2018/committee.html', context)

def candidates(request):
    deadline = request.GET.get('deadline')
    candidates = Candidate.objects.order_by('office','state','district_number','party')
    candidates_with_filings = []
    for c in candidates:
        if deadline:
            filing = c.filing_by_deadline(deadline)
        else:
            filing = c.most_recent_filing()
        candidates_with_filings.append((c,filing))

    context = {'deadline':deadline, 'candidates':candidates_with_filings}
    context['csv_url'] = reverse('2018:candidates_csv') + "?"+ request.GET.urlencode()
    return render(request, '2018/candidates.html', context)


def candidates_csv(request):
    deadline = request.GET.get('deadline')

    results = Candidate.objects.order_by('office','state','district_number','party')
    filename = "Candidates_{}.csv".format(time.strftime("%Y%m%d-%H%M%S"))

    candidate_fields = ['name','office','state','district_number','fec_candidate_id','fec_committee_id','party','incumbent']
    filing_fields = ['filing_id','committee_name','cycle_total_receipts', 'cash_on_hand_close_of_period', 'cycle_individuals_unitemized', 'coverage_through_date', 'created']


    def rows_with_totals():
        yield candidate_fields+filing_fields+['cycle_candidate_donations_plus_loans']
        for result in results:
            if deadline:
                filing = result.filing_by_deadline(deadline)
            else:
                filing = result.most_recent_filing()

            row = []
            for f in candidate_fields:
                value = getattr(result, f)
                if value is None:
                    row.append("")
                else:
                    row.append(value)
            for f in filing_fields:
                if not filing:
                    row.append("")
                    continue
                value = getattr(filing, f)
                if value is None:
                    row.append("")
                else:
                    row.append(value)
            if filing:
                cand_amount = filing.cycle_candidate_donations_plus_loans #this has to be done separately bc it's a property.
            if not filing or cand_amount is None:
                row.append("")
            else:
                row.append(cand_amount)
            yield row


    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows_with_totals()),
                                     content_type="text/csv")

    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response

def inaugural(request):
    form = InauguralForm(request.GET)
    if not request.GET:
        return render(request, '2018/inaugural.html', {'form': form})
    if request.GET.get('name'):
        contribs = InauguralContrib.objects.annotate(search=SearchVector('name')).filter(search=request.GET.get('name')).order_by('-amount')
    else:
        contribs = InauguralContrib.objects.order_by('-amount')
    paginator = Paginator(contribs, 50)
    page = request.GET.get('page')
    results = paginator.get_page(page)
    return render(request, '2018/inaugural.html', {'form':form, 'results':results})
