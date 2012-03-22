Usage
=====

Once installed, run the push server daemon (alongside Django development
server)::

    ./manage.py runpushserver

Then you can push data to all clients subscribed to the given channel with
simple HTTP request::

    from pushserver.utils import updates, urllib

    channeld_id = ...
    serialized = ...
    
    req = urllib.Request(updates.publisher_url(channel_id))
    req.add_data(serialized)
    req.add_unredirected_header('Content-type', 'application/json; charset=utf-8')
    urllib.urlopen(req)

To get subscription URL in Django template, you can use template tag::

    {% load pushserver %}

    <script type="text/javascript">
        var updates_url = '{% filter escapejs %}{% updates_url "some_channel_id" %}{% endfilter %}';
    </script>
