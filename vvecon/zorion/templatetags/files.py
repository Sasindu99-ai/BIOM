from django import template
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import get_template

from vvecon.zorion.utils import File, Image

register = template.Library()


@register.simple_tag
def link(file: str):
    try:
        return get_template('tags/url.html').render({'file': file})
    except TemplateDoesNotExist:
        return ''


@register.simple_tag
def css(file: File):
    try:
        return get_template('tags/link.html').render({'content_type': 'text/css', 'file': file.css})
    except TemplateDoesNotExist:
        return ''


@register.simple_tag
def js(file: File, content_type='text/javascript', *, tag=True, urlOnly=False):
    try:
        return get_template('tags/script.html').render({
            'content_type': content_type,
            'file': file.js,
            'tag': tag,
            'urlOnly': urlOnly,
        })
    except TemplateDoesNotExist:
        return ''


@register.simple_tag
def font(file: File):
    try:
        return get_template('tags/link.html').render({'rel': 'preload', 'content_type': 'text/css', 'file': file.font})
    except TemplateDoesNotExist:
        return ''


@register.simple_tag
def icon(file: File):
    try:
        return get_template('tags/link.html').render({'content_type': 'text/css', 'file': file.icon})
    except TemplateDoesNotExist:
        return ''


@register.simple_tag
def img(file: Image):
    try:
        return get_template('tags/img.html').render(file.__dict__)
    except TemplateDoesNotExist:
        return ''


@register.simple_tag
def html(content: str):
    try:
        return get_template('tags/html.html').render({'content': content})
    except TemplateDoesNotExist:
        return ''
