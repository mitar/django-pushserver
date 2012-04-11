from django import dispatch

channel_subscribe = dispatch.Signal(providing_args=['request', 'channel_id'])
channel_unsubscribe = dispatch.Signal(providing_args=['request', 'channel_id'])
