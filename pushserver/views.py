from django import http
from django.core import exceptions
from django.views.decorators import csrf
from django.conf import settings

from pushserver import signals

INTERNAL_IPS =('127.0.0.1')

@csrf.csrf_exempt
def passthrough(request):
    request_ip = request.META.get('REMOTE_ADDR')

    if request_ip not in settings.INTERNAL_IPS:
        #to fix in a non generic httpresponse
        return http.HttpResponse(status=403)
        
    if request.method != 'POST':
        raise exceptions.PermissionDenied

    channel_id = request.POST.get('channel_id')

    if not channel_id:
        raise exceptions.PermissionDenied

    if request.POST.get('subscribe'):
        signals.channel_subscribe.send_robust(sender=passthrough, request=request, channel_id=channel_id)
    elif request.POST.get('unsubscribe'):
        signals.channel_unsubscribe.send_robust(sender=passthrough, request=request, channel_id=channel_id)
    else:
        raise exceptions.PermissionDenied

    return http.HttpResponse()