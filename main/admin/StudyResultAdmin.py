from django.contrib import admin

__all__ = ['StudyResultAdmin']


class StudyResultAdmin(admin.ModelAdmin):
	list_display = ('userStudy', 'studyVariable', 'value')
	search_fields = ('value', 'userStudy__reference', 'studyVariable__name')
	list_select_related = ('userStudy', 'studyVariable')
	readonly_fields = ('created_at', 'updated_at', 'deleted_at')
	autocomplete_fields = ('userStudy', 'studyVariable')
