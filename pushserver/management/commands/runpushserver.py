import functools
import optparse
import re
import socket
import sys

from django.core.management import base as management_base
from django.core.management.commands import runserver
from django.core import wsgi as django_wsgi

import hbpush
from hbpush import registry
from hbpush.pubsub import publisher, subscriber
from hbpush.store import memory, redis
import tornado
from tornado import httpserver, ioloop, options as tornado_options, web, wsgi as tornado_wsgi

DEFAULT_PORT = '8001'
ALL_REQUESTS_DEFAULT_PORT = '8000'
DEFAULT_IPV4_ADDRESS = '127.0.0.1'
DEFAULT_IPV6_ADDRESS = '::1'

default_store = {
    'redis': {
        'port': 6379,
        'host': '127.0.0.1',
        'key_prefix': '',
        'database': 0,
    },
    'memory': {
        'min_messages': 0,
        'max_messages': 0,
        'message_timeout': 0,
    }
}

default_location = {
    'subscriber': {
        'polling': 'long',
        'create_on_get': False,
        'store': 'default',
    },
    'publisher': {
        'create_on_post': True,
        'store': 'default',
    }
}

defaults = {
    'port': None, # DEFAULT_PORT or ALL_REQUESTS_DEFAULT_PORT
    'address': None, # DEFAULT_IPV4_ADDRESS or DEFAULT_IPV6_ADDRESS
    'servername': None,
    'store': {
        'type': 'memory',
    },
    'locations': (
        {
            'type': 'publisher',
            'prefix': '/publisher/',
        },
        {
            'type': 'subscriber',
            'prefix': '/subscriber/',
        }
    )
}

def make_store(store_dict):
    store_conf = default_store.get(store_dict['type'], {}).copy()
    store_conf.update(store_dict)

    store_type = store_conf.pop('type')
    if store_type == 'memory':
        cls = memory.MemoryStore
    elif store_type == 'redis':
        cls = redis.RedisStore
    else:
        raise management_base.CommandError('Invalid store type "%s".' % (store_type,))

    store = cls(**store_conf)
    return {
        'store': store,
        'registry': registry.Registry(store),
    }

def make_stores(stores_dict):
    if 'type' in stores_dict:
        stores_dict = {'default': stores_dict}
    return dict([(k, make_store(stores_dict[k])) for k in stores_dict])

def make_location(loc_dict, stores=None, servername=None):
    if stores is None:
        stores = {}
    
    loc_conf = default_location.get(loc_dict['type'], {}).copy()
    loc_conf.update(loc_dict)

    loc_type = loc_conf.pop('type')
    if loc_type == 'publisher':
        cls = publisher.Publisher
    elif loc_type == 'subscriber':
        sub_type = loc_conf.pop('polling')
        if sub_type == 'long':
            cls = subscriber.LongPollingSubscriber
        elif sub_type == 'interval':
            cls = subscriber.Subscriber
        else:
            raise management_base.CommandError('Invalid polling "%s".' % (sub_type,))
    else:
        raise management_base.CommandError('Invalid location type "%s".' % (loc_type,))

    url = loc_conf.pop('url', loc_conf.pop('prefix', '')+'(.+)')
    store_id = loc_conf.pop('store')
    kwargs = {
        'registry': stores[store_id]['registry'],
        'servername': servername,
    }
    kwargs.update(loc_conf)
    return (url, cls, kwargs)

class Command(management_base.BaseCommand):
    option_list = management_base.BaseCommand.option_list + (
        optparse.make_option('--ipv6', '-6', action='store_true', dest='use_ipv6', default=False,
            help='Tells Django to use an IPv6 address.'),
        optparse.make_option('--allrequests', action='store_true', dest='allrequests', default=False,
            help='Process also non-push requests.'),
    )
    help = "Starts a push server."
    args = '[optional port number, or ipaddr:port]'

    can_import_settings = True
    requires_model_validation = False

    def handle(self, addrport='', *args, **options):
        self.use_ipv6 = options.get('use_ipv6')
        self.allrequests = options.get('allrequests')
        self._raw_ipv6 = False
        if args:
            raise management_base.CommandError('Usage is runpushserver %s' % self.args)
        if not addrport:
            self.address = None
            self.port = None
        else:
            m = re.match(runserver.naiveip_re, addrport)
            if m is None:
                raise management_base.CommandError('"%s" is not a valid port number or address:port pair.' % addrport)
            self.address, _ipv4, _ipv6, _fqdn, self.port = m.groups()
            if not self.port.isdigit():
                raise management_base.CommandError("%r is not a valid port number." % self.port)
            if self.address:
                if _ipv6:
                    self.address = self.address[1:-1]
                    self.use_ipv6 = True
                    self._raw_ipv6 = True
                elif self.use_ipv6 and not _fqdn:
                    raise management_base.CommandError('"%s" is not a valid IPv6 address.' % self.address)
        if self.use_ipv6 and not socket.has_ipv6:
            raise management_base.CommandError('Your Python does not support IPv6.')
        self.run(*args, **options)

    def run(self, *args, **options):
        from django.conf import settings
        
        quit_command = (sys.platform == 'win32') and 'CTRL-BREAK' or 'CONTROL-C'

        conf = defaults.copy()
        conf.update(getattr(settings, 'PUSH_SERVER', {}))

        if self.port:
            conf['port'] = self.port
        if self.address:
            conf['address'] = self.address

        if not conf['port']:
            conf['port'] = ALL_REQUESTS_DEFAULT_PORT if self.allrequests else DEFAULT_PORT
        if not conf['address']:
            conf['address'] = DEFAULT_IPV6_ADDRESS if self.use_ipv6 else DEFAULT_IPV4_ADDRESS

        if self._raw_ipv6 or (re.search(r'^[a-fA-F0-9:]+$', conf['address']) is not None and ':' in conf['address']):
            # Raw IPv6 address
            address = '[%s]' % conf['address']
        else:
            address = conf['address']

        self.stdout.write((
            "Django version %(version)s, using settings %(settings)r\n"
            "Push server version %(push_version)s on Tornado version %(tornado_version)s\n"
            "Development push server is running at http://%(address)s:%(port)s/\n"
            "Quit the server with %(quit_command)s.\n"
        ) % {
            "version": self.get_version(),
            "push_version": hbpush.__version__,
            "tornado_version": tornado.version,
            "settings": settings.SETTINGS_MODULE,
            "address": address,
            "port": conf['port'],
            "quit_command": quit_command,
        })

        conf['store'] = make_stores(conf['store'])
        conf['locations'] = map(functools.partial(make_location, stores=conf['store'], servername=conf['servername']), conf['locations'])

        if self.allrequests:
            class FallbackHandlerWithServerName(web.FallbackHandler):
                def set_default_headers(self):
                    if conf.get('servername', None):
                        # TODO: Does not really work, https://github.com/sunblaze-ucb/threader/issues/4
                        self.set_header('Server', conf.get('servername', None))

            wsgi_app = tornado_wsgi.WSGIContainer(django_wsgi.get_wsgi_application())
            conf['locations'] += (
                ('.*', FallbackHandlerWithServerName, {'fallback': wsgi_app}),
            )

        import logging
        logging.getLogger().setLevel('INFO')
        tornado_options.enable_pretty_logging()

        httpserver.HTTPServer(web.Application(conf['locations'])).listen(conf['port'], conf['address'])

        try:
            ioloop.IOLoop.instance().start()
        except KeyboardInterrupt:
            pass
