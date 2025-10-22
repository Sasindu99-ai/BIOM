from django.contrib import admin

from ..models import StudyVariableAnswer

__all__ = ["StudyVariableAnswerAdmin"]


class StudyVariableAnswerAdmin(admin.ModelAdmin):
	list_display = ("variable", "value")
	search_fields = ("value", "variable__name")
	list_select_related = ("variable",)
	readonly_fields = ("created_at", "updated_at", "deleted_at")
	autocomplete_fields = ("variable",)
