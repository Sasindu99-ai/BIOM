from django.contrib import admin
from django.contrib.auth.models import Permission

from ..models import User
from .PermissionAdmin import PermissionAdmin
from .UserAdmin import UserAdmin

admin.site.register(User, UserAdmin)
admin.site.register(Permission, PermissionAdmin)
