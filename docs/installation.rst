Installation
============

Using pip_ simply by doing::

    pip install django-pushserver

.. _pip: http://pypi.python.org/pypi/pip

You should then add ``pushserver`` to ``INSTALLED_APPS`` and configure URLs
used for HTTP push. For example::

    PUSH_SERVER = {
        'port': 8001,
        'address': '127.0.0.1',
        'publisher_host': {
            'location': '127.0.0.1:8001',
            'secure': True,
        },
        'subscriber_host': {
            'location': '127.0.0.1:8001',
            'secure': False,
        },
        'store': {
            'type': 'memory',
            'min_messages': 0,
            'max_messages': 100,
            'message_timeout': 10,
        },
        'locations': (
            {
                'type': 'subscriber',
                'url': r'/updates/([^/]+)',
                'polling': 'long',
                'create_on_get': True,
                'allow_origin': 'http://127.0.0.1:8000',
                'allow_credentials': True,
                'passthrough': 'http://127.0.0.1:8000/passthrough',
            },
            {
                'type': 'publisher',
                'url': r'/send-update/([^/]+)',
            },
        ),
    }

Settings translate directly to settings of the `py-hbpush`_ package. Production
settings should match those configured in Nginx.

.. _py-hbpush: https://github.com/mitar/py-hbpush/tree/mitar

.. warning::

    Passthrough is `not yet supported in Nginx`_. The implementation in django-pushserver
    passes original headers to a special passthrough URL so that server behind can for
    example from cookies determine which user has subscribed to or unsubscribed from
    the channel. This is useful to keep track of active users connected to the site.

.. _not yet supported in Nginx: https://github.com/slact/nginx_http_push_module/issues/80

You should add passthrough URLs to ``urls.py``, matching URL configured in
settings::

    urlpatterns = patterns('',
        # ...

        url(r'^passthrough', include('pushserver.urls')),

        # ...
    )

Passthrough URLs are not publicly accessible, so you should use
``INTERNAL_IPS`` to configure from which IPs they should be accessible. As you
will probably run both Django development server and push server daemon on the
same machine, this is probably simply::

    INTERNAL_IPS = (
        '127.0.0.1',
    )

When used in production where Nginx is making passthrough requests, it should
match IP(s) on which you have Nginx running.

If you do not need or want passthrough just do not define it in ``PUSH_SERVER``
setting. Passthrough URLs and ``INTERNAL_IPS`` setting are also not needed in
this case.
