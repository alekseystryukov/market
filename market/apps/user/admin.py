from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from apps.user.models import User
from apps.user.models import Group as CustomGroup
from django.utils.translation import gettext_lazy as _

admin.site.unregister(Group)


@admin.register(CustomGroup)
class CustomGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_fieldsets = (
        (None, {
            "fields": ("username", "email", "password1", "password2", "store"),
            "classes": ("wide",),
        }),
    )
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (_("Store"), {"fields": ("store",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
