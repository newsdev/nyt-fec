from django.contrib import admin
from fec.models import *

class ScheduleAAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(form_type__in=['SA17A','SA11AI'], contribution_amount__gte=200000, active=True)

    def formatted_amount(self, obj):
        return '${:,.2f}'.format(obj.contribution_amount)

    ordering = ['-contribution_amount']
    list_display = ['contributor_name',
                    'committee_name',
                    'contribution_date_formatted',
                    'form_type',
                    'formatted_amount',
                    'donor'
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
    fields = readonly_fields+autocomplete_fields


class DonorAdmin(admin.ModelAdmin):
    search_fields = ['nyt_name']

admin.site.register(ScheduleA, ScheduleAAdmin)
admin.site.register(Donor, DonorAdmin)