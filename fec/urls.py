from django.urls import include, path
from fec import views

urlpatterns = [
        path('', views.index, name='index'),
    ]