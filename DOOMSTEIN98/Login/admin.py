from django.contrib import admin
from .models import User
from django.contrib.auth.admin import UserAdmin

# Register your models here.
admin.site.register(User)

class UserAdminConfig(UserAdmin):
    """Configuration for user table

    Args:
        UserAdmin (Class): Admin config
    """
    search_fields = ('email', 'user_name')
    list_filter = ('email', 'user_name', 
                   'is_active', 'is_staff')
    ordering = ('-creation_date', 'email')
    list_display = ('email', 'user_name', 
                    'is_active', 'is_staff')

    fieldsets = (
        (None, {'fields': ('email', 'user_name')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')})
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'user_name', 'password1', 'password2', 'is_active', 'is_staff')
        }),
    )

admin.site.unregister(User)
admin.site.register(User, UserAdminConfig)