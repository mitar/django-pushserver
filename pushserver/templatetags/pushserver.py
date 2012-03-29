from __future__ import absolute_import

from django import template

from ..utils import updates

register = template.Library()

@register.simple_tag
def updates_url(channel_id):
    return updates.updates_url(channel_id)
