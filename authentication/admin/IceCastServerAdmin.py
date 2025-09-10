from django.contrib import admin


class IceCastServerAdmin(admin.ModelAdmin):
    """
    Admin model for IceCastServer
    """
    list_display = ('channel', 'icecastMountPoint', 'host', 'port', 'isActive', 'isSecret')
    list_filter = ('isActive', 'isSecret', 'channel')
    search_fields = ('icecastMountPoint', 'host', 'channel__name')

    fieldsets = (
        ('Channel Information', {
            'fields': ('channel',),
        }),
        ('Icecast Configuration', {
            'fields': ('icecastMountPoint', 'icecastPassword', 'isActive', 'isSecret'),
        }),
        ('Server Details', {
            'fields': ('host', 'port', 'username', 'password'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        # If not superuser, make certain fields read-only
        if not request.user.is_superuser:
            return 'icecastMountPoint', 'host', 'port'
        return tuple()
