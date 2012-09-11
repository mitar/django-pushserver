Usage
=====

Once installed, run the push server daemon (alongside Django development
server)::

    ./manage.py runpushserver

Or if you want that all requests are processed through push server (and
non-push requests passed to Django), you can do::

    ./manage.py runpushserver --allrequests

(In this way you are not served static files auto-magically, like you might
be used on Django development server, so you have to take care of that
yourself. Auto-reloading on code change also doesn't happen. Furthermore,
by default it runs on port 8000 instead of 8001.)

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

For JavaScript side you can use provided JavaScript code for processing pushed JSON data as it
comes (it requires jQuery_)::

    <script type="text/javascript" src="{{ STATIC_URL }}pushserver/updates.js"></script>

.. _jQuery: http://jquery.com/

The code should be initialized with channels (and their URLs) to subscribe to.
For that a Django template tag ``channel_url`` is provided::

    {% load pushserver %}

    <script type="text/javascript">
        $.updates.subscribe({
            'main_channel': '{% filter escapejs %}{% channel_url "some_channel_id" %}{% endfilter %}'
        });
    </script>

Provided code assumes that updates are JSON data, are a dictionary, and have a
top-level value named ``type`` by which you can register different update
processors in your JavaScript code. To continue the example::

    function updateAnswer(data) {
        // data.value == 42
    }

    $.updates.registerProcessor('main_channel', 'answer', updateAnswer);

Arguments to ``$.updates.registerProcessor`` are the name of the channel as you
have given to ``$.updates.subscribe``, the ``type``, and a processor function
which will be called with given data everytime data arrives.

If you want to process passthrough requests clients are making when subscribing
or unsubscribing, you can connect to provided signals::

    from django import dispatch

    from pushserver import signals

    @dispatch.receiver(signals.channel_subscribe)
    def process_channel_subscribe(sender, request, channel_id, **kwargs):
        print "Subscribed", request.user, channel_id

    @dispatch.receiver(signals.channel_unsubscribe)
    def process_channel_unsubscribe(sender, request, channel_id, **kwargs):
        print "Unsubscribed", request.user, channel_id

Because user credentials were being passed through in this example, Django
session and authentication middlewares should work as expected, populating
``request.user``.

Be aware that for each sent update, clients unsubscribe and soon afterwards
subscribe again so many signals could be triggered in a rapid succession.
Because of this signal receivers should be very light-weight.
