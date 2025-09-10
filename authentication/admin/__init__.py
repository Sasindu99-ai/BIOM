from django.contrib import admin
from django.contrib.auth.models import Permission

from ..models import Channel, Device, IceCastServer, User
from .ChannelAdmin import ChannelAdmin
from .DeviceAdmin import DeviceAdmin
from .IceCastServerAdmin import IceCastServerAdmin
from .PermissionAdmin import PermissionAdmin
from .UserAdmin import UserAdmin

admin.site.register(User, UserAdmin)
admin.site.register(Permission, PermissionAdmin)
admin.site.register(Device, DeviceAdmin)
admin.site.register(Channel, ChannelAdmin)
admin.site.register(IceCastServer, IceCastServerAdmin)
