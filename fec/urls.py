from django.urls import include, path, re_path
from fec import views

urlpatterns = [
        path('', views.index, name='index'),
        re_path(r'contributions/$', views.contributions, name='contributions'),
        re_path(r'expenditures/$', views.expenditures, name='expenditures'),
        re_path(r'ies/$', views.ies, name='ies'),
        re_path(r'races', views.races, name='races'),
    ]