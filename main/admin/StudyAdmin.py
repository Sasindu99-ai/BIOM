from django.contrib import admin

from ..enums import StudyStatus
from ..models import Study

__all__ = ['StudyAdmin']

# Inline for members (assuming ManyToMany with User)
class StudyMemberInline(admin.TabularInline):
	model = Study.members.through
	extra = 1
	verbose_name = 'Member'
	verbose_name_plural = 'Members'

# Inline for variables (assuming ManyToMany with StudyVariable)
class StudyVariableInline(admin.TabularInline):
	model = Study.variables.through
	extra = 1
	verbose_name = 'Variable'
	verbose_name_plural = 'Variables'


@admin.action(description='Activate selected studies')
def activate_studies(modeladmin, request, queryset):
	queryset.update(status=StudyStatus.ACTIVE)


@admin.action(description='Deactivate selected studies')
def deactivate_studies(modeladmin, request, queryset):
	queryset.update(status=StudyStatus.INACTIVE)


class StudyAdmin(admin.ModelAdmin):
	list_display = ('name', 'status', 'category', 'createdBy', 'created_at', 'reference')
	search_fields = ('name', 'reference', 'description')
	list_filter = ('status', 'category')
	readonly_fields = ('created_at', 'updated_at', 'deleted_at')
	list_select_related = ('createdBy',)
	autocomplete_fields = ('createdBy',)
	actions = (activate_studies, deactivate_studies)
	fieldsets = (
		(None, {
			'fields': ('name', 'status', 'category', 'description', 'createdBy', 'reference'),
		}),
		('Timestamps', {
			'fields': ('created_at', 'updated_at', 'deleted_at'),
			'classes': ('collapse',),
		}),
	)
	inlines = [StudyMemberInline, StudyVariableInline]
