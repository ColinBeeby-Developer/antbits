from django import template
from modelcluster.models import get_field_value

register = template.Library()

@register.filter
def radio_value(element):
    element.field.widget.attrs['data-score'] = '0'
    return element

@register.filter
def get_value(radio):
    if '~' in radio:
        radio_parts = radio.split('~')
        return radio_parts[0].strip()
    return radio


@register.filter
def get_data_value(radio):
    if '~' in radio:
        radio_parts = radio.split('~')
        return radio_parts[1].strip()
    return radio

@register.filter
def format_link(link):
    if '~' in link:
        link_parts = link.split('~')
        return '<a href={}>{}</a>'.format(link_parts[1], link_parts[0])
    return link

@register.filter
def hash(h, key):
    return h.get(key)