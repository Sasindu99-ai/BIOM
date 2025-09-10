from django import template
from django.utils import formats

from ..models import Currency

register = template.Library()


@register.filter
def currency_format(value, prefix: str = 'code', space: bool = True):  # noqa: FBT002, FBT001
	current_currency = Currency.objects.get(is_active=True)
	if (
		value is None
		or current_currency.exchange_rate is None
		or value == ''
		or current_currency.exchange_rate == ''
	):
		value = 0
	converted_value = float(value) / float(current_currency.exchange_rate)

	if prefix == 'code':
		prefix = current_currency.code
	elif prefix == 'symbol':
		prefix = current_currency.symbol
	elif prefix != '':
		invalidPrefixErrorMsg = 'Invalid prefix'
		raise ValueError(invalidPrefixErrorMsg)

	spacer = ' ' if space else ''
	formatted_value = formats.number_format(
		converted_value, decimal_pos=2, use_l10n=True, force_grouping=True,
	)

	return f'{prefix}{spacer}{formatted_value}'


@register.simple_tag
def format_currency(value, prefix: str = 'code', space: bool = True):  # noqa: FBT002, FBT001
	return currency_format(value, prefix, space)
