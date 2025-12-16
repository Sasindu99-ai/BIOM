from django.contrib.admin import ModelAdmin

__all__ = ['CountersAdmin']


class CountersAdmin(ModelAdmin):
	list_display = ('id', 'seq', 'version')
	search_fields = ('id',)
	list_filter = ('seq',)
