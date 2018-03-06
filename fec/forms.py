from django import forms

class ContributionForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    donor = forms.CharField(label='Donor name', max_length=500, required=False)
    employer = forms.CharField(label='Donor\'s employer or occupation', max_length=500, required=False)
    include_memo = forms.BooleanField(label='Include memo entries', required=False)
