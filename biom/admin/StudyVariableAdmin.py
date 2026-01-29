from django.contrib import admin

__all__ = ['StudyVariableAdmin']


class StudyVariableAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'status', 'study', 'order', 'isUnique')
    search_fields = ('name', 'type')
    list_filter = ('type', 'status', 'isUnique')
    readonly_fields = ('createdAt', 'updatedAt')
    fieldsets = (
        (None, {
            'fields': (
				'name', 'notes', 'type', 'answerOptions', 'status', 'study', 'order', 'isSearchable', 'isRange',
				'isUnique',
			),
        }),
        ('Timestamps', {
            'fields': ('createdAt', 'updatedAt'),
            'classes': ('collapse',),
        }),
    )
