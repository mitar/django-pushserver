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
                'allow_origin': '*',
            },
            {
                'type': 'publisher',
                'url': r'/send-update/([^/]+)',
            },
        ),
    }

Production settings should match those configured in Nginx.
