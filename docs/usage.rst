Usage
=====

Once installed, run the push server daemon (alongside Django development
server)::

    ./manage.py runpushserver

Then you can push data to all clients subscribed to the given channel with
simple HTTP request. If you for example want to push some JSON data (called
update) you can use provided functions::

    from pushserver.utils import updates

    channel_id = 'some_channel_id'
    data = {
        'type': 'answer',
        'value': 42,
    }

    updates.send_update(channel_id, data)

To get subscription URL in Django template, you can use template tag::

    {% load pushserver %}

    <script type="text/javascript">
        var updates_url = '{% filter escapejs %}{% updates_url "some_channel_id" %}{% endfilter %}';
    </script>

You can also use provided JavaScript code for processing pushed JSON data as it
comes (it requires jQuery_). The code uses ``updates_url`` global JavaScript
variable for subscription URL to read updates from. It assumes that JSON data
is a dictionary and has a top-level value named ``type`` by which you can
register different update processors. ::

    <script type="text/javascript" src="{{ STATIC_URL }}pushserver/updates.js"></script>

.. _jQuery: http://jquery.com/

You should then register update processors for wanted data types in your
JavaScript code. To continue the example::

    function updateAnswer(data) {
        // data.value == 42
    }

    registerUpdatesProcessor('answer', updateAnswer);

If you want to process passthrough requests clients are making when subscribing
or unsubscribing, you can connect to provided signals::

    from django import dispatch

    from pushserver import signals

    @dispatch.receiver(signals.passthrough)
    def process_passthrough(sender, request, channel_id, action):
        print request.user, channel_id, action

``action`` is ``pushserver.signals.SUBSCRIBE_ACTION`` or
``pushserver.signals.UNSUBSCRIBE_ACTION`` constant, depending whether user has
just subscribed to or unsubscribed from channel. Because user credentials were
being passed through in this example, Django session and authentication
middlewares should work as expected, populating ``request.user``.

Be aware that for each sent update, clients unsubscribe and soon afterwards
subscribe again so many signals could be triggered in a rapid succession.
Because of this signal receivers should be very light-weight.
