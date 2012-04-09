from django import dispatch

SUBSCRIBE_ACTION = 'subscribe'
UNSUBSCRIBE_ACTION = 'unsubscribe'

passthrough = dispatch.Signal(providing_args=['request', 'channel_id', 'action'])
