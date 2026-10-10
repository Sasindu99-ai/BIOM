from django.contrib import admin

__all__ = ['PatientAdmin']


class PatientAdmin(admin.ModelAdmin):
	list_display = ('reference', 'fullName', 'dateOfBirth', 'gender', 'createdBy', 'created_at')
	search_fields = ('reference', 'fullName')
	list_filter = ('gender', 'dateOfBirth')
	readonly_fields = ('created_at', 'updated_at', 'deleted_at')
	autocomplete_fields = ('createdBy',)
	fieldsets = (
		(None, {
			'fields': ('reference', 'firstName', 'lastName', 'fullName', 'dateOfBirth', 'gender', 'createdBy'),
			'classes': ('wide',),
		}),
		('Additional Info', {
			'fields': ('notes',),
			'classes': ('collapse',),
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at', 'deleted_at'),
			'classes': ('collapse',),
		}),
	)
