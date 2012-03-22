from django import template

from pushserver.utils import updates

register = template.Library()

@register.simple_tag
def updates_url(channel_id):
    return updates.updates_url(channel_id)
