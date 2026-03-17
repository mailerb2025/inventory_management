from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, UserRole


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')

    def get_role(self, obj):
        try:
            return obj.profile.role.get_name_display() if obj.profile.role else 'No Role'
        except:
            return 'No Profile'

    get_role.short_description = 'Role'


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_default', 'user_count')

    def user_count(self, obj):
        return obj.userprofile_set.count()

    user_count.short_description = 'Users'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'department', 'phone_number', 'login_count')
    list_filter = ('role', 'department')


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)