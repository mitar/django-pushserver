from django import dispatch

channel_subscribe = dispatch.Signal(providing_args=['request', 'channel_id'])
channel_unsubscribe = dispatch.Signal(providing_args=['request', 'channel_id'])

pre_send_update = dispatch.Signal(providing_args=['channel_id', 'data', 'already_serialized', 'request'])
post_send_update = dispatch.Signal(providing_args=['channel_id', 'data', 'already_serialized', 'request', 'response'])
