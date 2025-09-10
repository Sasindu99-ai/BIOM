import json

from django import template
from django.core.serializers import serialize
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def split(value, delimiter):
	return value.split(delimiter)


@register.filter
def jsonify(data):
	return str(json.dumps(data))


@register.filter
def toJson(value):
	# If it's a queryset, serialize normally
	if hasattr(value, '__iter__'):
		return json.loads(serialize('json', value))
	# Otherwise, serialize the single object by wrapping it in a list
	return json.loads(serialize('json', [value]))[0]


@register.filter
def add(value, arg):
	return value + arg


@register.simple_tag
def multiply(value, arg):
	return value * arg


@register.filter
def multiplies(value, arg):
	return value * arg


@register.filter
def formatStr(value, strFormat):
	try:
		return strFormat % value
	except TypeError:
		return ''


@register.filter
def get(data: dict, key: str):
	return data.get(key)


@register.filter
def at(data: list, index: int):
	return data[index]


@register.filter
def to_string(value):
	return str(value)


@register.filter
def divide(value, arg):
	return value / arg


@register.filter
def Round(value, arg):
	return round(value, arg)


@register.filter
def mod(value, arg):
	return value % arg
