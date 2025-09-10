from django.contrib import admin

__all__ = ['PlaceAdmin']


class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'placeId', 'latitude', 'longitude')
    search_fields = ('name', 'placeId')
    list_filter = ('created_at', 'deleted_at')
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
