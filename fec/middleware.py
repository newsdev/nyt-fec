import re

from django.http import HttpResponse

#the below should hopefully make the middleware compatible with djangos 1.x and 2.x
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object

class HealthCheckMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if "/healthcheck" in request.path:
            return HttpResponse('healthy: returned by middleware.HealthCheckMiddleware', status=200)