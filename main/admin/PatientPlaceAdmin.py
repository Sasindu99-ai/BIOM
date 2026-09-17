from django.contrib import admin

__all__ = ['PatientPlaceAdmin']


class PatientPlaceAdmin(admin.ModelAdmin):
	list_display = ('patient', 'place', 'isCurrent', 'visitedAt')
	list_filter = ('isCurrent',)
	search_fields = ('patient__fullName', 'place__name')
	autocomplete_fields = ('patient', 'place')
	readonly_fields = ('created_at', 'updated_at', 'deleted_at')
