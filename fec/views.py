from django.shortcuts import render
from fec.models import *


def index(request):
    return render(request, 'index.html')