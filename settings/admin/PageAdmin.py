from typing import ClassVar

from django.contrib import admin
from django.utils.html import format_html

__all__ = ['PageAdmin']


class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug_link', 'aside', 'nav', 'footer', 'isDeleted')
    list_filter = ('aside', 'nav', 'footer')
    search_fields = ('title', 'slug')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    list_display_links = ('title',)
    date_hierarchy = 'created_at'
    fieldsets: ClassVar = [
        (None, {'fields': ('slug', 'title', 'content')}),
        ('Status Information', {'fields': ('aside', 'nav', 'footer')}),
        ('Date Information', {'fields': ('created_at', 'updated_at', 'deleted_at')}),
    ]

    @staticmethod
    def isDeleted(obj):
        if obj.deleted_at is not None:
            return format_html('<img src="/static/admin/img/icon-yes.svg" alt="True">')
        return format_html('<img src="/static/admin/img/icon-no.svg" alt="False">')

    def slug_link(self, obj):
        return format_html(
            '<a class="button nowrap" href="{}" target="_blank" '
            'style="text-decoration: none;">View {}</a>',
            obj.get_url(),
            obj.slug,
        )
