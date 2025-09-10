from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError

__all__ = ['UserManager']


class UserManager(BaseUserManager):
    def create_user(
        self,
        username,
        firstName,
        lastName,
        password=None,
    ):
        if not username:
            raise ValidationError('Username is required')
        if not firstName:
            raise ValidationError('First Name is required')
        if not lastName:
            raise ValidationError('Last Name is required')
        user = self.model(
            username=username,
            firstName=firstName,
            lastName=lastName,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        username,
        firstName,
        lastName,
        password=None,
    ):
        user = self.create_user(
            username=username,
            firstName=firstName,
            lastName=lastName,
        )
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user
