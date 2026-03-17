from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Material(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]

    ALERT_STATUS_CHOICES = [
        ('normal', 'Normal'),
        ('low', 'Low'),
        ('excess', 'Excess'),
    ]

    material_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='materials')
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, help_text="e.g., pcs, kg, meters")
    specification = models.CharField(max_length=200, blank=True)
    current_stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    minimum_stock = models.IntegerField(default=10)
    maximum_stock = models.IntegerField(default=1000)
    reorder_point = models.IntegerField(default=20)
    location = models.CharField(max_length=100, blank=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    image = models.ImageField(upload_to='materials/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    # Field for manual alert status override
    alert_status_override = models.CharField(
        max_length=20,
        choices=ALERT_STATUS_CHOICES,
        blank=True,
        null=True,
        help_text="Manually override the calculated alert status"
    )

    class Meta:
        ordering = ['material_code']

    def __str__(self):
        return f"{self.material_code} - {self.name}"

    def get_absolute_url(self):
        return reverse('inventory:material_detail', args=[self.pk])

    def get_calculated_status(self):
        if self.current_stock <= self.minimum_stock:
            return 'low'
        elif self.current_stock >= self.maximum_stock:
            return 'excess'
        return 'normal'

    def get_display_status(self):
        if self.alert_status_override:
            return self.alert_status_override
        return self.get_calculated_status()

    def get_status_display_name(self):
        status = self.get_display_status()
        status_map = {
            'low': 'Low Stock',
            'normal': 'Normal',
            'excess': 'Excess'
        }
        return status_map.get(status, status)

    def get_status_color(self):
        status = self.get_display_status()
        color_map = {
            'low': 'danger',
            'normal': 'success',
            'excess': 'warning'
        }
        return color_map.get(status, 'secondary')

    def needs_reorder(self):
        return self.current_stock <= self.reorder_point

    def stock_value(self):
        return self.current_stock * self.unit_cost

    def has_override(self):
        return self.alert_status_override is not None