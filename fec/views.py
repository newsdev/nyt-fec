from django.shortcuts import render
from django.db.models import Q
from fec.models import *
from fec.forms import *


def index(request):
    context = {}
    context['new_filings'] = Filing.objects.filter(active=True).order_by('-created')[:100]
    return render(request, 'index.html', context)

def contributions(request):
    form = ContributionForm(request.GET)
    comm = request.GET.get('committee')


    return render(request, 'contributions.html', {'form': form})