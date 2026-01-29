from django.contrib import admin

from ..enums import StudyVariableStatus
from ..models import StudyVariableAnswer

__all__ = ['StudyVariableAdmin', 'StudyVariableAnswerInline']


class StudyVariableAnswerInline(admin.TabularInline):
	model = StudyVariableAnswer
	fields = ('value', )
	extra = 0


@admin.action(description='Activate selected variables')
def activate_variables(modeladmin, request, queryset):  # noqa: ARG001
	queryset.update(status=StudyVariableStatus.ACTIVE)


@admin.action(description='Deactivate selected variables')
def deactivate_variables(modeladmin, request, queryset):  # noqa: ARG001
	queryset.update(status=StudyVariableStatus.INACTIVE)


class StudyVariableAdmin(admin.ModelAdmin):
	list_display = ('name', 'type', 'field', 'status', 'isRange', 'isSearchable', 'isUnique', 'order')
	search_fields = ('name', 'type', 'field')
	list_filter = ('status', 'type', 'field', 'isRange', 'isSearchable', 'isUnique')
	readonly_fields = ('created_at', 'updated_at', 'deleted_at')
	inlines = [StudyVariableAnswerInline]
	actions = (activate_variables, deactivate_variables)
	fieldsets = (
		(None, {
			'fields': ('name', 'status', 'type', 'field', 'isRange', 'isSearchable', 'isUnique', 'order'),
		}),
		('Notes', {
			'fields': ('notes',),
			'classes': ('collapse',),
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at', 'deleted_at'),
			'classes': ('collapse',),
		}),
	)
