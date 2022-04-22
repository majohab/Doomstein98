from statistics import mode
from xmlrpc.client import TRANSPORT_ERROR
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# Create your models here.

class AccountManager(BaseUserManager):
    """Manages custom user model

    Inheritance:
        BaseUserManager (Class): _description_
    """
    def create_user(self, email, user_name, password, **other_fields):
        """Creates a new user.

        Args:
            email (str): Unique email
            user_name (str): Unique username
            password (str): password

        Raises:
            ValueError: No email provided

        Returns:
            User: created user
        """
        if not email:
            raise ValueError(_("You must provie an email adress"))

        email = self.normalize_email(email)
        user = self.model(email=email, user_name=user_name, 
                          **other_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, user_name, **other_fields):
        """Creates admin account.

        Args:
            email (str): Unique email
            user_name (str): Unique username

        Raises:
            ValueError: No email provided

        Returns:
            User: created admin user
        """
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError('Superuser must be assigned to is_superuser=True.')

        return self.create_user(email, user_name, **other_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model

    Inheritance:
        AbstractBaseUser (Class): Contains basic user model
        PermissionsMixin (Class): Manages permissions
    """
    email = models.EmailField(_('email'), max_length=100, unique=True)
    user_name = models.CharField(max_length=100, unique=True)
    creation_date = models.DateTimeField(default=timezone.now)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    objects = AccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_name']

    def __str__(self) -> str:
        """Prints user data

        Returns:
            str: Username
        """
        return self.user_name