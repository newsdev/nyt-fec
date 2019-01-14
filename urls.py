from django.urls import path, include
from django.views.generic import TemplateView
from django.contrib import admin


urlpatterns = [
    path('', TemplateView.as_view(template_name="index.html")),
    path('admin/', admin.site.urls),
    path('2018/', include('cycle_2018.urls', namespace='2018')),
    path('donor/', include('donor.urls', namespace='donor')),

]

