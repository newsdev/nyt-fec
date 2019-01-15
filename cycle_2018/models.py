from django.db import models
from django.utils import timezone
from django.contrib.postgres.search import SearchVectorField, SearchQuery, SearchVector
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Sum

import datetime

class BaseModel(models.Model):
    active = models.BooleanField(default=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.__str__()

STATUS_CHOICES = (('ACTIVE', 'active'),
                    ('SUPERSEDED', 'superseded by amendment'),
                    ('COVERED', 'covered by periodic'),
                    ('MEMO', 'memo'),
                    ('PROCESSING','processing'),
                    ('FAILED','failed'),
                    ('WRONG_CYCLE','wrong cycle'))

class FilingStatus(models.Model):
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    filing_id = models.IntegerField(primary_key=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    #status options should be 'SUCCESS','FAILED','REFUSED'
    #where 'REFUSED' means we decided not to upload the filing
    #eg because it's old or a kind of filing we're not loading
    #or actblue
    @property
    def csv_url(self):
        return 'http://docquery.fec.gov/csv/{}/{}.csv'.format(self.filing_id % 1000,self.filing_id)
    
class Committee(BaseModel):
    fec_id = models.CharField(max_length=10, primary_key=True)
    committee_name = models.CharField(max_length=255, blank=True, null=True)
    street_1 = models.CharField(max_length=255, blank=True, null=True)
    street_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=20, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)
    treasurer_last_name = models.CharField(max_length=255, blank=True, null=True)
    treasurer_first_name = models.CharField(max_length=255, blank=True, null=True)
    treasurer_middle_name = models.CharField(max_length=255, blank=True, null=True)
    treasurer_prefix = models.CharField(max_length=255, blank=True, null=True)
    treasurer_suffix = models.CharField(max_length=255, blank=True, null=True)
    committee_type = models.CharField(max_length=1, blank=True, null=True)
    committee_designation = models.CharField(max_length=1, blank=True, null=True)
    name_search = SearchVectorField(null=True)

    def __str__(self):
        return self.committee_name if self.committee_name else self.fec_id

    class Meta:
        indexes = [
            models.Index(fields=['fec_id']),
            models.Index(fields=['committee_name']),
            GinIndex(fields=['name_search']),
        ]

    def find_committee_by_name(search_term):
        #does full text search on committee name and returns matching committees
        query = SearchQuery(search_term)
        return Committee.objects.filter(name_search=query)


class Filing(BaseModel):
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PROCESSING')
    filing_id = models.IntegerField(primary_key=True)
    form_type = models.CharField(max_length=20, null=True, blank=True, help_text='the full form type from the filing')
    form = models.CharField(max_length=20, null=True, blank=True, help_text='the base form type (excluding amendment indications)')
    filer_id = models.CharField(max_length=10, null=True, blank=True, help_text='FEC id of the filer')
    committee_name = models.CharField(max_length=255, null=True, blank=True)
    election_state = models.CharField(max_length=10, null=True, blank=True)
    election_district = models.CharField(max_length=10, null=True, blank=True)
    coverage_from_date = models.CharField(max_length=10, null=True, blank=True)
    coverage_through_date = models.CharField(max_length=10, null=True, blank=True)
    election_date = models.CharField(max_length=10, null=True, blank=True)
    date_signed = models.CharField(max_length=10, null=True, blank=True)
    amends_filing = models.IntegerField(null=True, help_text='the filing id of the filing this filing amends')
    cash_on_hand_close_of_period = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cash_on_hand_beginning_period = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    debts_by_summary = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True,help_text="Current debt owed by the committee")
    period_candidate_contributions=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_candidate_loan_repayments=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_candidate_loans=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_contributions_to_candidates=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_coordinated_expenditures_by_party_committees=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_exempt_legal_accounting_disbursement=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_federal_election_activity_all_federal=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_federal_election_activity_federal_share=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_federal_election_activity_levin_share=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_federal_election_activity_total=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_fundraising=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_fundraising_disbursements=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_independent_expenditures=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_individual_contribution_total=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_individuals_itemized=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_individuals_unitemized=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_items_on_hand_to_be_liquidated=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_legal_and_accounting=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_levin_funds=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_loans_made=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_made_or_guaranteed_by_candidate=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_net_contributions=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_net_operating_expenditures=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_offsets_to_expenditures=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_operating=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_operating_expenditures=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_other_disbursements=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_other_federal_operating_expenditures=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_other_federal_receipts=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_other_loan_repayments=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_other_loans=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_other_political_committees=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_other_political_committees_pacs=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_other_receipts=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_other_repayments=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_pac_contributions=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_political_party_committees_refunds=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_political_party_contributions=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_received_from_or_guaranteed_by_cand=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_refunds_to_individuals=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_refunds_to_other_committees=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_refunds_to_party_committees=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_shared_operating_expenditures_federal=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_shared_operating_expenditures_nonfederal=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_contributions_from_candidate=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_contributions=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_contributions_refunds=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_disbursements=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_disbursements_period=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_federal_disbursements=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_federal_operating_expenditures=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_federal_receipts=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_individual_contributions=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_loan_repayments_made=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_loan_repayments_received=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_loans=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_nonfederal_transfers=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_offset_to_operating_expenditures=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_operating_expenditures=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_receipts=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_total_refunds=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_transfers_from_aff_other_party_cmttees=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_transfers_from_authorized=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_transfers_from_nonfederal_h3=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_transfers_to_affiliated=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    period_transfers_to_other_authorized_committees=models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_candidate_contributions = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_candidate_loan_repayments = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_candidate_loans = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_contributions_to_candidates = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_coordinated_expenditures_by_party_committees = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_exempt_legal_accounting_disbursement = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_federal_election_activity_all_federal = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_federal_election_activity_federal_share = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_federal_election_activity_levin_share = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_federal_election_activity_total = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_fundraising = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_fundraising_disbursements = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_independent_expenditures = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_individual_contribution_total = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_individuals_itemized = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_individuals_unitemized = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_items_on_hand_to_be_liquidated = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_legal_and_accounting = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_levin_funds = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_loans_made = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_made_or_guaranteed_by_candidate = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_net_contributions = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_net_operating_expenditures = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_offsets_to_expenditures = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_operating = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_operating_expenditures = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_other_disbursements = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_other_federal_operating_expenditures = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_other_federal_receipts = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_other_loan_repayments = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_other_loans = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_other_political_committees = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_other_political_committees_pacs = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_other_receipts = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_other_repayments = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_pac_contributions = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_political_party_committees_refunds = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_political_party_contributions = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_received_from_or_guaranteed_by_cand = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_refunds_to_individuals = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_refunds_to_other_committees = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_refunds_to_party_committees = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_shared_operating_expenditures_federal = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_shared_operating_expenditures_nonfederal = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_contributions_from_candidate = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_contributions = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_contributions_refunds = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_disbursements = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_disbursements_period = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_federal_disbursements = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_federal_operating_expenditures = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_federal_receipts = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_individual_contributions = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_loan_repayments_made = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_loan_repayments_received = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_loans = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_nonfederal_transfers = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_offset_to_operating_expenditures = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_operating_expenditures = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_receipts = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_total_refunds = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_transfers_from_aff_other_party_cmttees = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_transfers_from_authorized = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_transfers_from_nonfederal_h3 = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_transfers_to_affiliated = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    cycle_transfers_to_other_authorized_committees = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    computed_ie_total_for_f24 = models.DecimalField(max_digits=12,decimal_places=2,null=True,blank=True,help_text="computed total IEs for F24s for alerting so we know if they're big enough to care about")

    @property
    def url(self):
        return "http://docquery.fec.gov/cgi-bin/forms/{}/{}/".format(self.filer_id, self.filing_id)

    @property
    def is_amendment(self):
        if self.amends_filing:
            return True
        return False
    
    @property
    def period_candidate_donations_plus_loans(self):
        contribs = self.period_candidate_contributions or 0
        loans = self.period_candidate_loans or 0
        return contribs+loans

    @property
    def cycle_candidate_donations_plus_loans(self):
        contribs = self.cycle_candidate_contributions or 0
        loans = self.cycle_candidate_loans or 0
        return contribs+loans


    def __str__(self):
        if self.committee_name:
            return "{} filing {}".format(self.committee_name, self.filing_id)
        else:
            return str(self.filing_id)



    class Meta:
        indexes = [
            models.Index(fields=['filer_id']),
            models.Index(fields=['filing_id']),
            models.Index(fields=['committee_name']),
        ]


class Transaction(BaseModel):
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='ACTIVE')
    form_type = models.CharField(max_length=255, null=True, blank=True)
    filer_committee_id_number = models.CharField(max_length=255, null=True, blank=True)
    filing_id = models.IntegerField(null=True, blank=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    back_reference_tran_id_number = models.CharField(max_length=255, null=True, blank=True)
    back_reference_sched_name = models.CharField(max_length=255, null=True, blank=True)
    entity_type = models.CharField(max_length=255, null=True, blank=True)
    filer_id = models.CharField(max_length=9, null=True, blank=True)

    @property
    def filing(self):
        try:
            return Filing.objects.get(filing_id=self.filing_id)
        except:
            return None

    @property
    def committee(self):
        try:
            return Committee.objects.get(fec_id=self.filer_committee_id_number)
        except:
            return None

    @property
    def committee_name(self):
        try:
            return self.committee.committee_name
        except:
            return None

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['filing_id']),
            models.Index(fields=['filer_committee_id_number']),
        ]


class ScheduleA(Transaction):
    contributor_organization_name = models.CharField(max_length=255, null=True, blank=True)
    contributor_last_name = models.CharField(max_length=255, null=True, blank=True)
    contributor_first_name = models.CharField(max_length=255, null=True, blank=True)
    contributor_middle_name = models.CharField(max_length=255, null=True, blank=True)
    contributor_prefix = models.CharField(max_length=255, null=True, blank=True)
    contributor_suffix = models.CharField(max_length=255, null=True, blank=True)
    contributor_street_1 = models.CharField(max_length=255, null=True, blank=True)
    contributor_street_2 = models.CharField(max_length=255, null=True, blank=True)
    contributor_city = models.CharField(max_length=255, null=True, blank=True)
    contributor_state = models.CharField(max_length=30, null=True, blank=True)
    contributor_zip = models.CharField(max_length=10, null=True, blank=True)
    election_code = models.CharField(max_length=255, null=True, blank=True)
    election_other_description = models.CharField(max_length=255, null=True, blank=True)
    contribution_date = models.CharField(max_length=255, null=True, blank=True)
    contribution_amount = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    contribution_aggregate = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    contribution_purpose_descrip = models.CharField(max_length=255, null=True, blank=True)
    contributor_employer = models.CharField(max_length=255, null=True, blank=True)
    contributor_occupation = models.CharField(max_length=255, null=True, blank=True)
    donor_committee_fec_id = models.CharField(max_length=255, null=True, blank=True)
    donor_committee_name = models.CharField(max_length=255, null=True, blank=True)
    donor_candidate_fec_id = models.CharField(max_length=255, null=True, blank=True)
    donor_candidate_last_name = models.CharField(max_length=255, null=True, blank=True)
    donor_candidate_first_name = models.CharField(max_length=255, null=True, blank=True)
    donor_candidate_middle_name = models.CharField(max_length=255, null=True, blank=True)
    donor_candidate_prefix = models.CharField(max_length=255, null=True, blank=True)
    donor_candidate_suffix = models.CharField(max_length=255, null=True, blank=True)
    donor_candidate_office = models.CharField(max_length=255, null=True, blank=True)
    donor_candidate_state = models.CharField(max_length=255, null=True, blank=True)
    donor_candidate_district = models.CharField(max_length=255, null=True, blank=True)
    conduit_name = models.CharField(max_length=255, null=True, blank=True)
    conduit_street1 = models.CharField(max_length=255, null=True, blank=True)
    conduit_street2 = models.CharField(max_length=255, null=True, blank=True)
    conduit_city = models.CharField(max_length=255, null=True, blank=True)
    conduit_state = models.CharField(max_length=255, null=True, blank=True)
    conduit_zip = models.CharField(max_length=255, null=True, blank=True)
    memo_code = models.CharField(max_length=255, null=True, blank=True)
    memo_text_description = models.CharField(max_length=255, null=True, blank=True)
    reference_code = models.CharField(max_length=255, null=True, blank=True)
    name_search = SearchVectorField(null=True)
    occupation_search = SearchVectorField(null=True)
    address_search = SearchVectorField(null=True)
    old_donor_id = models.CharField(max_length=255, null=True, blank=True, help_text="terrible hack for editing donor totals, do not manually edit!")
    donor = models.ForeignKey('donor.Donor', null=True, blank=True, related_name='contributions_2018', on_delete=models.SET_NULL)
    
    """
    these search fields require triggers. Please see migration 0015 which I hand-edited
    to insert these triggers. this might make inserts hopelessly slow, we shall see.
    """


    @property
    def contributor_name(self):
        #oy. there are so many ways they can do this wrong.
        if self.contributor_organization_name:
            return self.contributor_organization_name
        names = [n for n in [self.contributor_first_name, self.contributor_middle_name, self.contributor_last_name] if n]
        if len(names) == 0:
            return None
        return " ".join(names)

    @property
    def contribution_date_formatted(self):
        try:
            return datetime.datetime.strptime(self.contribution_date, '%Y%m%d')
        except:
            return

    @property
    def address(self):
        try:
            address_parts = [self.contributor_street_1, self.contributor_street_2, self.contributor_city+", "+self.contributor_state, self.contributor_zip[0:5]]
            return ' '.join([a for a in address_parts if a])
        except:
            return

    def export_fields():
        return ['status',
                    'form_type',
                    'filer_committee_id_number',
                    'committee_name',
                    'filing_id',
                    'transaction_id',
                    'back_reference_tran_id_number',
                    'back_reference_sched_name',
                    'entity_type',
                    'filer_id',
                    'contributor_organization_name',
                    'contributor_last_name',
                    'contributor_first_name',
                    'contributor_middle_name',
                    'contributor_prefix',
                    'contributor_suffix',
                    'contributor_street_1',
                    'contributor_street_2',
                    'contributor_city',
                    'contributor_state',
                    'contributor_zip',
                    'election_code',
                    'election_other_description',
                    'contribution_date',
                    'contribution_amount',
                    'contribution_aggregate',
                    'contribution_purpose_descrip',
                    'contributor_employer',
                    'contributor_occupation',
                    'memo_code',
                    'memo_text_description']

    def csv_row(self):
        row = []
        for f in ScheduleA.export_fields():
            value = getattr(self, f)
            if value is None:
                row.append("")
            else:
                row.append(value)
        return(row)

    class Meta(Transaction.Meta):
        indexes = Transaction.Meta.indexes[:] #this is a deep copy to prevent the base model's fields from being overwritten
        indexes.extend(
            [GinIndex(fields=['name_search']),
            models.Index(fields=['contribution_amount']),
            GinIndex(fields=['occupation_search']),
            GinIndex(fields=['address_search'])])

    def save(self, *args, **kwargs):
        #all of this is to update totals on donors
        old_donor = None
        if self.old_donor_id and int(self.old_donor_id) != self.donor_id:
            try:
                old_donor = Donor.objects.get(id=self.old_donor_id)
            except:
                #maybe we deleted the donor? we should not fail to save because of this
                pass
        if self.donor_id:
            self.old_donor_id = str(self.donor_id)
        else:
            self.old_donor_id = None
        super().save(*args, **kwargs)
        if old_donor:
            old_donor.save()
        if self.donor:
            self.donor.save()

class ScheduleB(Transaction):
    payee_organization_name = models.CharField(max_length=255, null=True, blank=True)
    payee_last_name = models.CharField(max_length=255, null=True, blank=True)
    payee_first_name = models.CharField(max_length=255, null=True, blank=True)
    payee_middle_name = models.CharField(max_length=255, null=True, blank=True)
    payee_prefix = models.CharField(max_length=255, null=True, blank=True)
    payee_suffix = models.CharField(max_length=255, null=True, blank=True)
    payee_street_1 = models.CharField(max_length=255, null=True, blank=True)
    payee_street_2 = models.CharField(max_length=255, null=True, blank=True)
    payee_city = models.CharField(max_length=255, null=True, blank=True)
    payee_state = models.CharField(max_length=30, null=True, blank=True)
    payee_zip = models.CharField(max_length=10, null=True, blank=True)
    election_code = models.CharField(max_length=255, null=True, blank=True)
    election_other_description = models.CharField(max_length=255, null=True, blank=True)
    expenditure_date = models.CharField(max_length=255, null=True, blank=True)
    expenditure_amount = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    semi_annual_refunded_bundled_amt = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    expenditure_purpose_descrip = models.CharField(max_length=255, null=True, blank=True)
    category_code = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_committee_fec_id = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_committee_name = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_candidate_fec_id = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_candidate_last_name = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_candidate_first_name = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_candidate_middle_name = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_candidate_prefix = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_candidate_suffix = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_candidate_office = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_candidate_state = models.CharField(max_length=255, null=True, blank=True)
    beneficiary_candidate_district = models.CharField(max_length=255, null=True, blank=True)
    conduit_name = models.CharField(max_length=255, null=True, blank=True)
    conduit_street_1 = models.CharField(max_length=255, null=True, blank=True)
    conduit_street_2 = models.CharField(max_length=255, null=True, blank=True)
    conduit_city = models.CharField(max_length=255, null=True, blank=True)
    conduit_state = models.CharField(max_length=255, null=True, blank=True)
    conduit_zip = models.CharField(max_length=255, null=True, blank=True)
    memo_code = models.CharField(max_length=255, null=True, blank=True)
    memo_text_description = models.CharField(max_length=255, null=True, blank=True)
    reference_to_si_or_sl_system_code_that_identifies_the_account = models.CharField(max_length=255, null=True, blank=True)
    name_search = SearchVectorField(null=True)
    purpose_search = SearchVectorField(null=True)
    address_search = SearchVectorField(null=True)


    @property
    def payee_name(self):
        if self.payee_organization_name:
            return self.payee_organization_name
        if self.payee_middle_name:
            return ' '.join([self.payee_first_name, self.payee_middle_name, self.payee_last_name])
        return ' '.join([self.payee_first_name, self.payee_last_name])

    @property
    def expenditure_date_formatted(self):
        try:
            return datetime.datetime.strptime(self.expenditure_date, '%Y%m%d')
        except:
            return

    @property
    def address(self):
        try:
            address_parts = [self.payee_street_1, self.payee_street_2, self.payee_city+", "+self.payee_state, self.payee_zip[0:5]]
            return ' '.join([a for a in address_parts if a])
        except:
            return

    def export_fields():
        return ['status',
                    'form_type',
                    'filer_committee_id_number',
                    'committee_name',
                    'filing_id',
                    'transaction_id',
                    'back_reference_tran_id_number',
                    'back_reference_sched_name',
                    'entity_type',
                    'filer_id',
                    'payee_organization_name',
                    'payee_last_name',
                    'payee_first_name',
                    'payee_middle_name',
                    'payee_prefix',
                    'payee_suffix',
                    'payee_street_1',
                    'payee_street_2',
                    'payee_city',
                    'payee_state',
                    'payee_zip',
                    'election_code',
                    'election_other_description',
                    'expenditure_date',
                    'expenditure_amount',
                    'semi_annual_refunded_bundled_amt',
                    'expenditure_purpose_descrip',
                    'category_code',
                    'memo_code',
                    'memo_text_description'
                    ]

    def csv_row(self):
        row = []
        for f in ScheduleB.export_fields():
            value = getattr(self, f)
            if value is None:
                row.append("")
            else:
                row.append(value)
        return(row)

    class Meta(Transaction.Meta):
        indexes = Transaction.Meta.indexes[:] #this is a deep copy to prevent the base model's fields from being overwritten
        indexes.extend([GinIndex(fields=['name_search']),
            GinIndex(fields=['purpose_search']),
            GinIndex(fields=['address_search'])])


class ScheduleE(Transaction):
    payee_organization_name = models.CharField(max_length=255, null=True, blank=True)
    payee_last_name = models.CharField(max_length=255, null=True, blank=True)
    payee_first_name = models.CharField(max_length=255, null=True, blank=True)
    payee_middle_name = models.CharField(max_length=255, null=True, blank=True)
    payee_prefix = models.CharField(max_length=255, null=True, blank=True)
    payee_suffix = models.CharField(max_length=255, null=True, blank=True)
    payee_street_1 = models.CharField(max_length=255, null=True, blank=True)
    payee_street_2 = models.CharField(max_length=255, null=True, blank=True)
    payee_city = models.CharField(max_length=255, null=True, blank=True)
    payee_state = models.CharField(max_length=30, null=True, blank=True)
    payee_zip = models.CharField(max_length=10, null=True, blank=True)
    election_code = models.CharField(max_length=255, null=True, blank=True)
    election_other_description = models.CharField(max_length=255, null=True, blank=True)
    dissemination_date = models.CharField(max_length=255, null=True, blank=True)
    expenditure_amount = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    expenditure_date = models.CharField(max_length=255, null=True, blank=True)
    calendar_y_t_d_per_election_office = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)
    expenditure_purpose_descrip = models.CharField(max_length=255, null=True, blank=True)
    category_code = models.CharField(max_length=255, null=True, blank=True)
    payee_cmtte_fec_id_number = models.CharField(max_length=255, null=True, blank=True)
    support_oppose_code = models.CharField(max_length=255, null=True, blank=True)
    candidate_id_number = models.CharField(max_length=255, null=True, blank=True)
    candidate_last_name = models.CharField(max_length=255, null=True, blank=True)
    candidate_first_name = models.CharField(max_length=255, null=True, blank=True)
    candidate_middle_name = models.CharField(max_length=255, null=True, blank=True)
    candidate_prefix = models.CharField(max_length=255, null=True, blank=True)
    candidate_suffix = models.CharField(max_length=255, null=True, blank=True)
    candidate_office = models.CharField(max_length=255, null=True, blank=True)
    candidate_district = models.CharField(max_length=255, null=True, blank=True)
    candidate_state = models.CharField(max_length=255, null=True, blank=True)
    completing_last_name = models.CharField(max_length=255, null=True, blank=True)
    completing_first_name = models.CharField(max_length=255, null=True, blank=True)
    completing_middle_name = models.CharField(max_length=255, null=True, blank=True)
    completing_prefix = models.CharField(max_length=255, null=True, blank=True)
    completing_suffix = models.CharField(max_length=255, null=True, blank=True)
    date_signed = models.CharField(max_length=255, null=True, blank=True)
    memo_code = models.CharField(max_length=255, null=True, blank=True)
    memo_text_description = models.CharField(max_length=255, null=True, blank=True)
    nyt_district = models.CharField(max_length=255, null=True, blank=True)
    name_search = SearchVectorField(null=True)
    purpose_search = SearchVectorField(null=True)
    candidate_search = SearchVectorField(null=True)

    @property
    def payee_name(self):
        if self.payee_organization_name:
            return self.payee_organization_name
        if self.payee_middle_name:
            return ' '.join([self.payee_first_name, self.payee_middle_name, self.payee_last_name])
        return ' '.join([self.payee_first_name, self.payee_last_name])

    @property
    def expenditure_date_formatted(self):
        try:
            return datetime.datetime.strptime(self.expenditure_date, '%Y%m%d')
        except:
            try:
                return datetime.datetime.strptime(self.dissemination_date, '%Y%m%d')
            except:
                return

    @property
    def address(self):
        try:
            address_parts = [self.payee_street_1, self.payee_street_2, self.payee_city+", "+self.payee_state, self.payee_zip[0:5]]
            return ' '.join([a for a in address_parts if a])
        except:
            return

    @property
    def candidate_name(self):
        if self.candidate_middle_name:
            return ' '.join([self.candidate_first_name, self.candidate_middle_name, self.candidate_last_name])
        if self.candidate_first_name and self.candidate_last_name:
            return ' '.join([self.candidate_first_name, self.candidate_last_name])
        return None

    @property
    def district(self):
        if self.candidate_district and self.candidate_district != '00':
            return "{}-{}".format(self.candidate_state, self.candidate_district)
        else:
            return self.candidate_state

    @property
    def support(self):
        if self.support_oppose_code == 'S':
            return "Support"
        if self.support_oppose_code == 'O':
            return "Oppose"
        return

    @property
    def filing_type(self):
        try:
            filing = Filing.objects.get(filing_id=self.filing_id)
        except:
            return None
        return filing.form
    

    def export_fields():
        return ['status',
                'form_type',
                'filer_committee_id_number',
                'committee_name',
                'filing_id',
                'transaction_id',
                'back_reference_tran_id_number',
                'back_reference_sched_name',
                'entity_type',
                'filer_id',
                'payee_organization_name',
                'payee_last_name',
                'payee_first_name',
                'payee_middle_name',
                'payee_prefix',
                'payee_suffix',
                'payee_street_1',
                'payee_street_2',
                'payee_city',
                'payee_state',
                'payee_zip',
                'election_code',
                'election_other_description',
                'dissemination_date',
                'expenditure_amount',
                'expenditure_date',
                'calendar_y_t_d_per_election_office',
                'expenditure_purpose_descrip',
                'category_code',
                'payee_cmtte_fec_id_number',
                'support_oppose_code',
                'candidate_id_number',
                'candidate_last_name',
                'candidate_first_name',
                'candidate_middle_name',
                'candidate_prefix',
                'candidate_suffix',
                'candidate_office',
                'candidate_district',
                'candidate_state',
                'completing_last_name',
                'completing_first_name',
                'completing_middle_name',
                'completing_prefix',
                'completing_suffix',
                'date_signed',
                'memo_code',
                'memo_text_description',
                ]

    def csv_row(self):
        row = []
        for f in ScheduleE.export_fields():
            value = getattr(self, f)
            if value is None:
                row.append("")
            else:
                row.append(value)
        return(row)

    class Meta(Transaction.Meta):
        indexes = Transaction.Meta.indexes[:] #this is a deep copy to prevent the base model's fields from being overwritten
        indexes.extend([GinIndex(fields=['name_search']), GinIndex(fields=['purpose_search']), GinIndex(fields=['candidate_search'])])

class Candidate(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)
    district_number = models.CharField(max_length=20, null=True, blank=True)
    district = models.CharField(max_length=23, null=True, blank=True)
    fec_candidate_id = models.CharField(max_length=9, null=True, blank=True)
    fec_committee_id = models.CharField(max_length=9, null=True, blank=True)
    party = models.CharField(max_length=1, null=True, blank=True)
    office = models.CharField(max_length=1, null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)
    incumbent = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return "{} ({}, {})".format(self.name, self.party, self.district)

    def most_recent_filing(self):
        try:
            f = Filing.objects.filter(filer_id=self.fec_committee_id, active=True).order_by('-coverage_through_date')[0]
        except:
            return None
        return f

    def filing_by_deadline(self, deadline):
        try:
            f = Filing.objects.filter(filer_id=self.fec_committee_id, active=True, coverage_through_date=deadline)[0]
        except:
            return None
        return f

class InauguralContrib(BaseModel):
    name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    zipcode = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=255, null=True, blank=True)
    amount = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)

