from django.contrib import admin

from ..models import Country, Currency, Page, Place, Setting
from .CountryAdmin import CountryAdmin
from .CurrencyAdmin import CurrencyAdmin
from .PageAdmin import PageAdmin
from .PlaceAdmin import PlaceAdmin
from .SettingsAdmin import SettingsAdmin

admin.site.register(Setting, SettingsAdmin)
admin.site.register(Currency, CurrencyAdmin)
admin.site.register(Place, PlaceAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(Country, CountryAdmin)
