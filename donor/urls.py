from django.urls import include, path, re_path
from donor import views

app_name = 'donor'

urlpatterns = [
        path('donor_details/<int:donor_id>', views.donor_details, name='donor_details')
    ]