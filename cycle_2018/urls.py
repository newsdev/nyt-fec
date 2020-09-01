from django.urls import include, path, re_path
from rest_framework import routers, serializers, viewsets
from cycle_2018 import views
from cycle_2018.api import *

app_name = 'cycle_2018'

router = routers.DefaultRouter()
router.register(r'filings', FilingViewSet, basename=Filing)


API = [path('api/v1/', include(router.urls))]


urlpatterns = API + [
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
        path('filing_status/<str:status>', views.filing_status, name='filing_status'),
        path('committee/<str:committee_id>', views.committee, name='committee'),
        re_path(r'candidates/$', views.candidates, name='candidates'),
        re_path(r'candidates_csv/$', views.candidates_csv, name='candidates_csv'),
        re_path(r'inaugural/$', views.inaugural, name='inaugural'),

    ]