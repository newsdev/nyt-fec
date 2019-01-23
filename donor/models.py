from django.db import models
from django.utils import timezone
from django.db.models import Sum
#from cycle_2018.models import ScheduleA

import datetime

class BaseModel(models.Model):
    active = models.BooleanField(default=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.__str__()

class Donor(BaseModel):
    nyt_name = models.CharField(max_length=255, null=True, blank=True)
    nyt_employer = models.CharField(max_length=255, null=True, blank=True)
    nyt_occupation = models.CharField(max_length=255, null=True, blank=True)
    nyt_note = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    contribution_total_2018 = models.DecimalField(max_digits=12,decimal_places=2, default=0)
    contribution_total_2020 = models.DecimalField(max_digits=12,decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.contribution_total_2018 = self.contributions_2018.filter(active=True).aggregate(Sum('contribution_amount'))['contribution_amount__sum']
        if not self.contribution_total_2018:
            self.contribution_total_2018 = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nyt_name
