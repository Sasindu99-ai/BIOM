from django.contrib import admin

__all__ = ['CurrencyAdmin']


class CurrencyAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'code',
        'symbol',
        'exchange_rate',
        'is_default',
        'is_active',
        'is_featured',
    )
    list_display_links = ('id', 'name')
    list_filter = ('is_default', 'is_active', 'is_featured', 'created_at', 'updated_at')
    search_fields = ('name', 'code', 'symbol')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at', 'deleted_at')
    list_per_page = 10
