from fec.models import *
from rest_framework import routers, serializers, viewsets

from fec import models, views

class FilingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Filing
        fields = ('filing_id','form','filer_id',
            'committee_name','period_total_receipts',
            'period_total_disbursements',
            'cash_on_hand_close_of_period',
            'computed_ie_total_for_f24',
            'is_amendment','url')

class FilingViewSet(viewsets.ModelViewSet):
    serializer_class = FilingSerializer
    queryset = Filing.objects.filter(active=True)
    ordering_fields = ('-created')
