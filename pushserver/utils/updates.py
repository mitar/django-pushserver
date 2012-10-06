import sys

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.utils import regex_helper, simplejson

from pushserver import signals
from pushserver.utils import urllib

def publisher_url(channel):
    push_server = getattr(settings, 'PUSH_SERVER', {})
    port = push_server.get('port', None)
    publisher_pattern = None
    for location in push_server.get('locations', ()):
        if location.get('type') == 'publisher':
            publisher_pattern = location.get('url')
            # TODO: Currently we support only the first publisher URL
            break
    address = push_server.get('address')
    if not address or not publisher_pattern or port is None:
        raise ValueError("Missing required settings")
    if port == 80:
        port = ''
    else:
        port = ':%s' % (port,)
    publisher = regex_helper.normalize(publisher_pattern)
    if len(publisher) != 1 or len(publisher[0][1]) != 1:
        raise ValueError("Non-reversible reg-exp: '%s'" % (publisher_pattern,))
    publisher, (arg,) = publisher[0]
    publisher = publisher % {
        arg: channel,
    }
    return 'http://%s%s%s' % (address, port, publisher)

def subscriber_url(channel):
    push_server = getattr(settings, 'PUSH_SERVER', {})
    port = push_server.get('port', None)
    subscriber_pattern = None
    for location in push_server.get('locations', ()):
        if location.get('type') == 'subscriber':
            subscriber_pattern = location.get('url')
            # TODO: Currently we support only the first subscriber URL
            break
    address = push_server.get('address')
    if not address or not subscriber_pattern or port is None:
        raise ValueError("Missing required settings")
    if port == 80:
        port = ''
    else:
        port = ':%s' % (port,)
    subscriber = regex_helper.normalize(subscriber_pattern)
    if len(subscriber) != 1 or len(subscriber[0][1]) != 1:
        raise ValueError("Non-reversible reg-exp: '%s'" % (subscriber_pattern,))
    subscriber, (arg,) = subscriber[0]
    subscriber = subscriber % {
        arg: channel,
    }
    return 'http://%s%s%s' % (address, port, subscriber)

def send_update(channel_id, data, already_serialized=False, ignore_errors=False):
    if already_serialized:
        serialized = data
        length = len(data)
    else:
        serialized = StringIO()
        simplejson.dump(data, serialized)

        serialized.seek(0, 2)
        length = serialized.tell()
        serialized.seek(0)

    request = urllib.Request(publisher_url(channel_id))
    request.add_data(serialized)
    request.add_unredirected_header('Content-type', 'application/json; charset=utf-8')
    request.add_unredirected_header('Content-length', '%d' % length)

    signals.pre_send_update.send(sender=sys.modules[__name__], channel_id=channel_id, data=data, already_serialized=already_serialized, request=request)

    try:
        response = urllib.urlopen(request)
    except Exception, e:
        signals.post_send_update.send(sender=sys.modules[__name__], channel_id=channel_id, data=data, already_serialized=already_serialized, request=request, response=e)

        if ignore_errors or getattr(settings, 'PUSH_SERVER_IGNORE_ERRORS', False):
            return

        raise

    signals.post_send_update.send(sender=sys.modules[__name__], channel_id=channel_id, data=data, already_serialized=already_serialized, request=request, response=response)
