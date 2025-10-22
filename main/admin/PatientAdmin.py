from django.contrib import admin

__all__ = ["PatientAdmin"]


class PatientAdmin(admin.ModelAdmin):
	list_display = ("fullName", "dateOfBirth", "gender", "createdBy", "created_at")
	search_fields = ("fullName", "pid")
	list_filter = ("gender", "dateOfBirth")
	readonly_fields = ("created_at", "updated_at", "deleted_at")
	autocomplete_fields = ("createdBy",)
	fieldsets = (
		(None, {
			"fields": ("firstName", "lastName", "pid", "dateOfBirth", "gender", "createdBy"),
			"classes": ("wide",),
		}),
		("Timestamps", {
			"fields": ("created_at", "updated_at", "deleted_at"),
			"classes": ("collapse",),
		}),
	)
