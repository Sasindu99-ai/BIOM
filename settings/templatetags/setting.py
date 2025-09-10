from django import template

from ..models import Setting

register = template.Library()


@register.filter
def setting(key):
    return Setting.objects.filter(key=key).first().getValue()
