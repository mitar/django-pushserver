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

Production settings should match those configured in Nginx.

You should add passthrough URLs to ``urls.py``, matching URL configured in
settings::

    urlpatterns = patterns('',
        # ...

        url(r'^passthrough', include('pushserver.urls')),

        # ...
    )

If you do not need or want passthrough just do not define it in ``PUSH_SERVER``
setting. Passthrough URLs are also not needed in this case.
