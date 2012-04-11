from django import http
from django.core import exceptions
from django.views.decorators import csrf

from pushserver import signals

# TODO: Should not be publicly accessible, prevent this?
@csrf.csrf_exempt
def passthrough(request):
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
