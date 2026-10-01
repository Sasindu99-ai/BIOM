from django.contrib import admin

from ..models import ApiKey

__all__ = ['ApiKeyAdmin']


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
	list_display = ('key_prefix', 'user', 'name', 'is_active', 'created_at', 'last_used_at', 'revoked_at')
	list_filter = ('is_active', 'created_at', 'last_used_at')
	search_fields = ('key_prefix', 'user__username', 'user__email', 'name')
	readonly_fields = ('key_prefix', 'key_hash', 'created_at', 'last_used_at', 'revoked_at')
