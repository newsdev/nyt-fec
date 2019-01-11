from django.db import models
from django.utils import timezone
from django.db.models import Sum
from cycle_2018.models import ScheduleA

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
    contribution_total = models.DecimalField(max_digits=12,decimal_places=2, null=True, blank=True)

    @property
    def schedulea_set(self):
        return ScheduleA.objects.filter(donor_id=self.id)
    

    def save(self, *args, **kwargs):
        self.contribution_total = self.schedulea_set.filter(active=True).aggregate(Sum('contribution_amount'))['contribution_amount__sum']
        if not self.contribution_total:
            self.contribution_total = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nyt_name
