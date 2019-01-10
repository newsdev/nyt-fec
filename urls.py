from django.urls import path
from django.views.generic import TemplateView
from django.contrib import admin


from cycle_2018.urls import urlpatterns as urls_2018

common_urls = [
    path('', TemplateView.as_view(template_name="index.html")),
    path('admin/', admin.site.urls),
]

urlpatterns = urls_2018 + common_urls
