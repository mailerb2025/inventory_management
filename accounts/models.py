from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserRole(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('viewer', 'Viewer'),
    ]

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)

    # Permissions
    can_view_inventory = models.BooleanField(default=True)
    can_edit_inventory = models.BooleanField(default=False)
    can_delete_inventory = models.BooleanField(default=False)
    can_create_inventory = models.BooleanField(default=False)

    can_view_transactions = models.BooleanField(default=True)
    can_create_transactions = models.BooleanField(default=False)
    can_edit_transactions = models.BooleanField(default=False)
    can_delete_transactions = models.BooleanField(default=False)
    can_approve_transactions = models.BooleanField(default=False)

    can_view_vendors = models.BooleanField(default=True)
    can_edit_vendors = models.BooleanField(default=False)
    can_delete_vendors = models.BooleanField(default=False)
    can_create_vendors = models.BooleanField(default=False)

    can_view_reports = models.BooleanField(default=True)
    can_export_reports = models.BooleanField(default=False)

    can_view_users = models.BooleanField(default=False)
    can_edit_users = models.BooleanField(default=False)
    can_delete_users = models.BooleanField(default=False)
    can_create_users = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.get_name_display()

    def get_permissions_list(self):
        """Return list of all permission field names"""
        return [
            'can_view_inventory', 'can_edit_inventory', 'can_delete_inventory', 'can_create_inventory',
            'can_view_transactions', 'can_create_transactions', 'can_edit_transactions',
            'can_delete_transactions', 'can_approve_transactions',
            'can_view_vendors', 'can_edit_vendors', 'can_delete_vendors', 'can_create_vendors',
            'can_view_reports', 'can_export_reports',
            'can_view_users', 'can_edit_users', 'can_delete_users', 'can_create_users'
        ]


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    notification_email = models.BooleanField(default=True)
    notification_sms = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)
    login_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def has_permission(self, permission_name):
        if not self.role:
            return False
        return getattr(self.role, permission_name, False)

    def get_full_name(self):
        return self.user.get_full_name() or self.user.username


# Add permission methods to User model
def user_has_permission(self, permission_name):
    if self.is_superuser:
        return True
    if hasattr(self, 'profile') and self.profile:
        return self.profile.has_permission(permission_name)
    return False


# Attach method to User model
User.add_to_class('has_permission', user_has_permission)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Try to get default role, create if doesn't exist
        role, created = UserRole.objects.get_or_create(
            name='viewer',
            defaults={
                'description': 'Default viewer role',
                'is_default': True,
                'can_view_inventory': True,
                'can_view_transactions': True,
                'can_view_vendors': True,
                'can_view_reports': True,
            }
        )
        UserProfile.objects.create(user=instance, role=role)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()