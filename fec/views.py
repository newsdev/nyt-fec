from django.shortcuts import render
from fec.models import *


def index(request):
    context = {}
    context['new_filings'] = Filing.objects.filter(active=True).order_by('-created')[:100]
    return render(request, 'index.html', context)