from django.urls import include, path, re_path
from django.contrib import admin
from fec import views

urlpatterns = [
        path('admin/', admin.site.urls),
        path('', views.index, name='index'),
        re_path(r'contributions/$', views.contributions, name='contributions'),
        re_path(r'expenditures/$', views.expenditures, name='expenditures'),
        re_path(r'ies/$', views.ies, name='ies'),
        path('races', views.races, name='races'),
        path('top_donors', views.top_donors, name='top_donors'),
        path('donor_details/<int:donor_id>', views.donor_details, name='donor_details')
    ]