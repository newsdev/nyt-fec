from django.urls import include, path, re_path
from fec import views

urlpatterns = [
        path('', views.index, name='index'),
        re_path(r'contributions/$', views.contributions, name='contributions'),
    ]