from django.contrib import admin
from cycle_2018.models import *

class ScheduleEAdmin(admin.ModelAdmin):
    ordering = ['-expenditure_amount']
    readonly_fields = ['committee_name',
                    'expenditure_amount',
                    'candidate_first_name',
                    'candidate_last_name',
                    'candidate_office',
                    'candidate_state',
                    'candidate_district',
                    'filing_id',
                    ]
    fields = readonly_fields + ['nyt_district', 'active']

class ScheduleAAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(form_type__in=['SA17A','SA17','SA11AI'], contribution_amount__gte=100000, active=True)

    def formatted_amount(self, obj):
        return '${:,.2f}'.format(obj.contribution_amount)

    def employer_occupation(self, obj):
        if obj.contributor_occupation and obj.contributor_employer:
            return "{} | {}".format(obj.contributor_employer,obj.contributor_occupation)
        if obj.contributor_occupation:
            return obj.contributor_occupation
        if obj.contributor_employer:
            return obj.contributor_employer
        return ""

    ordering = ['-contribution_amount']
    list_display = ['contributor_name',
                    'donor',
                    'employer_occupation',
                    'committee_name',
                    'contribution_date_formatted',
                    'formatted_amount',
                    ]
    list_editable = ['donor']
    readonly_fields = ['committee_name',
                    'contributor_name',
                    'contributor_suffix',
                    'contributor_employer',
                    'contributor_occupation',
                    'address',
                    'form_type',
                    'formatted_amount',
                    'contribution_date_formatted'
                    ]
    autocomplete_fields = ['donor']
    search_fields = ['contributor_first_name',
                    'contributor_last_name',
                    'contributor_organization_name',
                    'form_type',
                    'filer_committee_id_number',
                    'filing_id']
    fields = readonly_fields+autocomplete_fields


class DonorAdmin(admin.ModelAdmin):
    search_fields = ['nyt_name']

class CandidateAdmin(admin.ModelAdmin):
    search_fields = ['name']

admin.site.register(ScheduleA, ScheduleAAdmin)
admin.site.register(ScheduleE, ScheduleEAdmin)
admin.site.register(Candidate, CandidateAdmin)