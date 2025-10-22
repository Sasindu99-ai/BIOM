from django.contrib import admin

__all__ = ["UserAdmin"]


class UserAdmin(admin.ModelAdmin):
	list_display = ("name", "email", "userType", "uid", "createdAt")
	search_fields = ("name", "email", "uid")
	list_filter = ("userType",)
	readonly_fields = ("createdAt", "updatedAt")
	fieldsets = (
		(None, {
			"fields": ("name", "email", "userType", "uid", "userId")
		}),
		("Timestamps", {
			"fields": ("createdAt", "updatedAt"),
			"classes": ("collapse",),
		}),
	)
