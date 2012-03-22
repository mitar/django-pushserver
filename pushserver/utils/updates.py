from django.conf import settings
from django.utils import regex_helper

def publisher_url(channel):
    push_server = getattr(settings, 'PUSH_SERVER', {})
    port = push_server.get('port', 80)
    publisher_pattern = None
    for location in push_server.get('locations', ()):
        if location.get('type') == 'publisher':
            publisher_pattern = location.get('url')
            # TODO: Currently we support only the first publisher URL
            break
    if port == 80:
        port = ''
    else:
        port = ':%s' % (port,)
    address = push_server.get('address')
    if not address or not publisher_pattern:
        raise ValueError("Missing required settings")
    publisher = regex_helper.normalize(publisher_pattern)
    if len(publisher) != 1 or len(publisher[0][1]) != 1:
        raise ValueError("Non-reversible reg-exp: '%s'" % (publisher_pattern,))
    publisher, (arg,) = publisher[0]
    publisher = publisher % {
        arg: channel,
    }
    return 'http://%s%s%s' % (address, port, publisher)

def updates_url(channel):
    push_server = getattr(settings, 'PUSH_SERVER', {})
    port = push_server.get('port', 80)
    subscriber_pattern = None
    for location in push_server.get('locations', ()):
        if location.get('type') == 'subscriber':
            subscriber_pattern = location.get('url')
            # TODO: Currently we support only the first subscriber URL
            break
    if port == 80:
        port = ''
    else:
        port = ':%s' % (port,)
    address = push_server.get('address')
    if not (address and subscriber_pattern):
        raise ValueError("Missing required settings")
    subscriber = regex_helper.normalize(subscriber_pattern)
    if len(subscriber) != 1 or len(subscriber[0][1]) != 1:
        raise ValueError("Non-reversible reg-exp: '%s'" % (subscriber_pattern,))
    subscriber, (arg,) = subscriber[0]
    subscriber = subscriber % {
        arg: channel,
    }
    return 'http://%s%s%s' % (address, port, subscriber)
