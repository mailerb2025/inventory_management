from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
        ('return', 'Return'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
    ]

    transaction_number = models.CharField(max_length=50, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference_number = models.CharField(max_length=50, blank=True, help_text="PO number, SO number, etc.")
    transaction_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-transaction_date']

    def __str__(self):
        return f"{self.transaction_number} - {self.transaction_type}"

    def save(self, *args, **kwargs):
        if not self.transaction_number:
            last_trans = Transaction.objects.order_by('-id').first()
            prefix = {
                'inbound': 'IN',
                'outbound': 'OUT',
                'return': 'RET',
                'adjustment': 'ADJ',
                'transfer': 'TRF',
            }.get(self.transaction_type, 'TRX')

            if last_trans:
                last_num = int(last_trans.transaction_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.transaction_number = f"{prefix}-{timezone.now().strftime('%Y%m%d')}-{new_num:04d}"
        super().save(*args, **kwargs)


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey('inventory.Material', on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock_before = models.IntegerField(default=0)
    stock_after = models.IntegerField(default=0)

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class StockAlert(models.Model):
    ALERT_STATUS = [
        ('pending', 'Pending'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('ignored', 'Ignored'),
    ]

    material = models.ForeignKey('inventory.Material', on_delete=models.CASCADE, related_name='alerts')
    current_stock = models.IntegerField()
    reorder_point = models.IntegerField()
    alert_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ALERT_STATUS, default='pending')
    resolved_date = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-alert_date']

    def __str__(self):
        return f"Alert: {self.material.name} - Stock: {self.current_stock}"