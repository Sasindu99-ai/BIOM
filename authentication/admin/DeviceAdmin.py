from django.contrib import admin

__all__ = ['DeviceAdmin']


class DeviceAdmin(admin.ModelAdmin):
	list_display_links = ('name',)
	list_display = ('name', 'nickname', 'macAddress', 'deviceType', 'ipAddress')
	list_filter = ('deviceType', 'isActive')
	search_fields = ('name', 'nickname', 'macAddress', 'publicId', 'ipAddress')
	list_per_page = 20
	readonly_fields = ('publicId', 'created_at', 'updated_at')
	fieldsets = (
		(None, {
			'fields': ('name', 'nickname', 'macAddress', 'deviceType', 'ipAddress'),
		}),
		('Important Dates', {
			'fields': ('created_at', 'updated_at', 'deleted_at'),
		}),
	)
