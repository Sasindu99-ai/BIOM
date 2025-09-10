from django.contrib import admin
from django.utils.html import format_html

__all__ = ['CountryAdmin']


class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'flagPreview', 'length', 'emoji')
    list_display_links = ('id', 'name')
    list_filter = ('length',)
    search_fields = ('name', 'code')
    list_per_page = 25
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    fieldsets = (
        (None, {'fields': ('name', 'code', 'flag', 'length', 'emoji')}),
        (
            'Meta',
            {
                'fields': ('created_at', 'updated_at', 'deleted_at'),
                'classes': ('collapse',),
            },
        ),
    )

    @staticmethod
    def flagPreview(obj):
        return format_html(
            f'<img src="{obj.flag}" style="max-width: 100px; max-height: 100px;">',
        )
