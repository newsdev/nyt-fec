from django.urls import include, path, re_path
from rest_framework import routers, serializers, viewsets
from cycle_2018 import views
from cycle_2018.api import *

router = routers.DefaultRouter()
router.register(r'filings', FilingViewSet, base_name=Filing)


API = [path('2018/api/v1/', include(router.urls))]


urlpatterns = API + [
        path('2018/', views.index, name='index'),
        re_path(r'2018/filings/$', views.filings, name='filings'), #we might someday want a real index but good enough for now 
        re_path(r'2018/contributions/$', views.contributions, name='contributions'),
        re_path(r'2018/contributions_csv/$', views.contributions_csv, name='contributions_csv'),
        re_path(r'2018/expenditures/$', views.expenditures, name='expenditures'),
        re_path(r'2018/expenditures_csv/$', views.expenditures_csv, name='expenditures_csv'),
        re_path(r'2018/ies/$', views.ies, name='ies'),
        re_path(r'2018/ie_csv/$', views.ie_csv, name='ie_csv'),
        path('2018/races', views.races, name='races'),
        path('2018/top_donors', views.top_donors, name='top_donors'),
        path('2018/donor_details/<int:donor_id>', views.donor_details, name='donor_details'),
        path('2018/filing_status/<str:status>', views.filing_status, name='filing_status'),
        path('2018/committee/<str:committee_id>', views.committee, name='committee'),
        re_path(r'2018/candidates/$', views.candidates, name='candidates'),
        re_path(r'2018/candidates_csv/$', views.candidates_csv, name='candidates_csv'),
        re_path(r'2018/inaugural/$', views.inaugural, name='inaugural'),

    ]