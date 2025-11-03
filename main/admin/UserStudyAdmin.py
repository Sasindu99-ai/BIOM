from django.contrib import admin

from ..enums import UserStudyStatus
from ..models import StudyResult

__all__ = ["UserStudyAdmin", "StudyResultInline"]


class StudyResultInline(admin.TabularInline):
	model = StudyResult
	extra = 0
	autocomplete_fields = ("studyVariable",)
	fields = ("studyVariable", "value")
	show_change_link = True


@admin.action(description="Approve selected user studies")
def approve_user_studies(modeladmin, request, queryset):
	queryset.update(status=UserStudyStatus.APPROVED)


@admin.action(description="Reject selected user studies")
def reject_user_studies(modeladmin, request, queryset):
	queryset.update(status=UserStudyStatus.REJECTED)


class UserStudyAdmin(admin.ModelAdmin):
	list_display = ("patient", "study", "status", "reference", "createdBy", "administeredBy", "created_at")
	search_fields = (
		"reference",
		"study__name",
		"patient__firstName",
		"patient__lastName",
	)
	list_filter = ("status",)
	list_select_related = ("patient", "study", "createdBy", "administeredBy")
	readonly_fields = ("created_at", "updated_at", "deleted_at")
	autocomplete_fields = ("patient", "study", "createdBy", "administeredBy")
	inlines = [StudyResultInline]
	actions = (approve_user_studies, reject_user_studies)
	fieldsets = (
		(None, {
			"fields": ("patient", "study", "reference", "status", "version")
		}),
		("Administration", {
			"fields": ("createdBy", "administeredBy"),
			"classes": ("collapse",),
		}),
		("Timestamps", {
			"fields": ("created_at", "updated_at", "deleted_at"),
			"classes": ("collapse",),
		}),
	)
