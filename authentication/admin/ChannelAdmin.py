from django.contrib import admin

__all__ = ['ChannelAdmin']


class ChannelAdmin(admin.ModelAdmin):
    list_display_links = ('name',)
    list_display = ('name', 'user', 'isActive', 'created_at')
    list_filter = ('isActive',)
    search_fields = ('name', 'description', 'publicId')
    list_per_page = 20
    readonly_fields = ('publicId', 's3FolderPath', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'user', 'isActive'),
        }),
        ('Technical Details', {
            'fields': ('publicId', 's3FolderPath'),
        }),
        ('Important Dates', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
