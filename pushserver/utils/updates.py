import sys

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django.utils import regex_helper, simplejson

from pushserver import signals
from pushserver.utils import urllib

# Set by runpushserver command
# Using this host fails if it is bind-all address (eg. 0.0.0.0),
# in this case settings should be manually configured
current_host = None

def publisher_url(channel):
    push_server = getattr(settings, 'PUSH_SERVER', {})
    publisher_host = push_server.get('publisher_host', current_host)
    publisher_pattern = None
    for location in push_server.get('locations', ()):
        if location.get('type') == 'publisher':
            publisher_pattern = location.get('url')
            # TODO: Currently we support only the first publisher URL
            break
    if not publisher_host or not publisher_pattern:
        raise ValueError("Missing required settings")
    publisher = regex_helper.normalize(publisher_pattern)
    if len(publisher) != 1 or len(publisher[0][1]) != 1:
        raise ValueError("Non-reversible reg-exp: '%s'" % (publisher_pattern,))
    publisher, (arg,) = publisher[0]
    publisher = publisher % {
        arg: channel,
    }
    return 'http://%s%s' % (publisher_host, publisher)

def subscriber_url(channel):
    push_server = getattr(settings, 'PUSH_SERVER', {})
    subscriber_host = push_server.get('subscriber_host', current_host)
    subscriber_pattern = None
    for location in push_server.get('locations', ()):
        if location.get('type') == 'subscriber':
            subscriber_pattern = location.get('url')
            # TODO: Currently we support only the first subscriber URL
            break
    if not subscriber_host or not subscriber_pattern:
        raise ValueError("Missing required settings")
    subscriber = regex_helper.normalize(subscriber_pattern)
    if len(subscriber) != 1 or len(subscriber[0][1]) != 1:
        raise ValueError("Non-reversible reg-exp: '%s'" % (subscriber_pattern,))
    subscriber, (arg,) = subscriber[0]
    subscriber = subscriber % {
        arg: channel,
    }
    return 'http://%s%s' % (subscriber_host, subscriber)

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
