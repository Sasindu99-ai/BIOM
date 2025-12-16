from django.contrib import admin

__all__ = ['StudyAdmin']


class StudyAdmin(admin.ModelAdmin):
	list_display = ('name', 'status', 'category', 'createdBy', 'createdAt')
	search_fields = ('name', 'category')
	list_filter = ('status', 'category')
	readonly_fields = ('createdAt', 'updatedAt')
	fieldsets = (
		(None, {
			'fields': ('name', 'status', 'category', 'description', 'createdBy', 'reference'),
		}),
		('Timestamps', {
			'fields': ('createdAt', 'updatedAt'),
			'classes': ('collapse',),
		}),
	)
