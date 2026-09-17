from django.contrib import admin

__all__ = ['DataImportJobAdmin']


class DataImportJobAdmin(admin.ModelAdmin):
	list_display = (
		'id', 'study', 'status', 'progress_percent', 'total_rows',
		'imported_count', 'error_count', 'created_by', 'created_at',
	)
	list_filter = ('status',)
	search_fields = ('study__name', 'file_name')
	list_select_related = ('study', 'created_by')
	autocomplete_fields = ('study', 'created_by')
	readonly_fields = (
		'created_at', 'updated_at', 'deleted_at', 'started_at', 'completed_at',
		'total_rows', 'processed_rows', 'imported_count', 'updated_count',
		'skipped_count', 'error_count', 'consecutive_errors',
		'patients_created', 'variables_created', 'errors',
	)

	@admin.display(description='Progress')
	def progress_percent(self, obj):
		return f'{obj.progress_percent}%'
