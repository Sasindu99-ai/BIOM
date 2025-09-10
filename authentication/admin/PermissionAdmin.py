from django.contrib import admin

__all__ = ['PermissionAdmin']


class PermissionAdmin(admin.ModelAdmin):
	list_display_links = ('codename', )
	list_display = ('codename', 'name', 'content_type')
	list_filter = ('content_type',)
	search_fields = ('codename', 'name')
	list_per_page = 20
	readonly_fields = ('codename', 'name', 'content_type')
	fieldsets = (
		(None, {
			'fields': ('codename', 'name', 'content_type'),
		}),
	)
