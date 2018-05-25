from django import forms

import datetime

from django.conf import settings

class ContributionForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    filing_id = forms.CharField(label='filing id', max_length=20, required=False)
    donor = forms.CharField(label='Donor name', max_length=500, required=False)
    employer = forms.CharField(label='Donor\'s employer or occupation', max_length=500, required=False)
    include_memo = forms.BooleanField(label='Include memo entries', required=False)
    min_date = forms.CharField(label="Min receipt date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max receipt date (YYYYMMDD)", required=False)

class ExpenditureForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    filing_id = forms.CharField(label='filing id', max_length=20, required=False)
    recipient = forms.CharField(label='recipient name', max_length=500, required=False)
    purpose = forms.CharField(label='expenditure purpose', max_length=500, required=False)
    include_memo = forms.BooleanField(label='Include memo entries', required=False)
    min_date = forms.CharField(label="Min expend date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max expend date (YYYYMMDD)", required=False)

class IEForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    filing_id = forms.CharField(label='filing id', max_length=20, required=False)
    recipient = forms.CharField(label='recipient name', max_length=500, required=False)
    purpose = forms.CharField(label='expenditure purpose', max_length=500, required=False)
    candidate = forms.CharField(label='candidate', max_length=500, required=False)
    min_date = forms.CharField(label="Min ie date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max ie date (YYYYMMDD)", required=False)

class FilingForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    form_type = forms.CharField(label='Form type', max_length=500, required=False)
    min_raised = forms.DecimalField(label='Minimum raised', required=False)
    exclude_amendments = forms.BooleanField(label='Exclude amendments', required=False)
    min_date = forms.CharField(label="Min filing date (YYYYMMDD)", required=False)
    max_date = forms.DateField(label="Max filing date (YYYYMMDD)", required=False)    