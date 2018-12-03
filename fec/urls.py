from django.urls import include, path, re_path
from django.contrib import admin
from rest_framework import routers, serializers, viewsets
from fec import views
from fec.api import *

router = routers.DefaultRouter()
router.register(r'filings', FilingViewSet, base_name=Filing)


API = [path('api/v1/', include(router.urls))]


urlpatterns = API + [
        path('admin/', admin.site.urls),
        path('', views.index, name='index'),
        re_path(r'filings/$', views.filings, name='filings'), #we might someday want a real index but good enough for now 
        re_path(r'contributions/$', views.contributions, name='contributions'),
        re_path(r'contributions_csv/$', views.contributions_csv, name='contributions_csv'),
        re_path(r'expenditures/$', views.expenditures, name='expenditures'),
        re_path(r'expenditures_csv/$', views.expenditures_csv, name='expenditures_csv'),
        re_path(r'ies/$', views.ies, name='ies'),
        re_path(r'ie_csv/$', views.ie_csv, name='ie_csv'),
        path('races', views.races, name='races'),
        path('top_donors', views.top_donors, name='top_donors'),
        path('donor_details/<int:donor_id>', views.donor_details, name='donor_details'),
        path('filing_status/<str:status>', views.filing_status, name='filing_status'),
        path('committee/<str:committee_id>', views.committee, name='committee'),
        re_path(r'candidates/$', views.candidates, name='candidates'),
        re_path(r'candidates_csv/$', views.candidates_csv, name='candidates_csv'),
        re_path(r'inaugural/$', views.inaugural, name='inaugural'),

    ]