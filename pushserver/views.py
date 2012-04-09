from django import http
from django.core import exceptions
from django.views.decorators import csrf

from pushserver import signals

# TODO: Should not be publicly accessible
@csrf.csrf_exempt
def passthrough(request):
    if request.method != 'POST':
        raise exceptions.PermissionDenied

    channel_id = request.POST.get('channel_id')
    if request.POST.get(signals.SUBSCRIBE_ACTION):
        action = signals.SUBSCRIBE_ACTION
    elif request.POST.get(signals.UNSUBSCRIBE_ACTION):
        action = signals.UNSUBSCRIBE_ACTION
    
    if not channel_id and not action:
        raise exceptions.PermissionDenied

    signals.passthrough.send_robust(sender=passthrough, request=request, channel_id=channel_id, action=action)

    return http.HttpResponse()
