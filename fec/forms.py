from django import forms

class ContributionForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    filing_id = forms.CharField(label='filing id', max_length=20, required=False)
    donor = forms.CharField(label='Donor name', max_length=500, required=False)
    employer = forms.CharField(label='Donor\'s employer or occupation', max_length=500, required=False)
    include_memo = forms.BooleanField(label='Include memo entries', required=False)


class ExpenditureForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    filing_id = forms.CharField(label='filing id', max_length=20, required=False)
    recipient = forms.CharField(label='recipient name', max_length=500, required=False)
    purpose = forms.CharField(label='expenditure purpose', max_length=500, required=False)
    include_memo = forms.BooleanField(label='Include memo entries', required=False)


class IEForm(forms.Form):
    committee = forms.CharField(label='Committee name or ID', max_length=500, required=False)
    filing_id = forms.CharField(label='filing id', max_length=20, required=False)
    recipient = forms.CharField(label='recipient name', max_length=500, required=False)
    purpose = forms.CharField(label='expenditure purpose', max_length=500, required=False)
    candidate = forms.CharField(label='candidate', max_length=500, required=False)

