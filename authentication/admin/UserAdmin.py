from django.contrib import admin
from django.utils.html import format_html

__all__ = ['UserAdmin']


class UserAdmin(admin.ModelAdmin):
	list_display = ('name', 'phone', 'email', 'countryFlag', 'is_active', 'is_superuser', 'is_staff')
	list_filter = ('is_active', 'is_superuser', 'is_staff', 'country')
	search_fields = ('name', 'phone', 'email', 'country__name')
	list_per_page = 20
	list_display_links = ('name',)
	readonly_fields = ('date_joined', 'last_login')
	list_editable = ('is_active', 'is_superuser', 'is_staff')
	autocomplete_fields = ('country',)
	fieldsets = (
		(None, {
			'fields': ('username', 'email', 'password'),
		}),
		('Personal Info', {
			'fields': ('firstName', 'lastName', 'nic', 'countryCode', 'mobileNumber', 'dateOfBirth'),
		}),
		('Permissions', {
			'fields': ('is_active', 'is_superuser', 'is_staff'),
		}),
		('Important Dates', {
			'fields': ('date_joined', 'last_login'),
		}),
	)

	@staticmethod
	def name(obj):
		return f'{obj.firstName} {obj.lastName}'

	@staticmethod
	def phone(obj):
		return f'+{obj.countryCode}-{obj.mobileNumber}'

	@staticmethod
	def countryFlag(obj):
		return format_html(
			f'<span style="font-size: 20px;">{obj.country.flag} {obj.country.name}</span>',
		) if obj.country else '-'
