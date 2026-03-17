from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import TransactionItem, StockAlert
from inventory.models import Material


@receiver(post_save, sender=TransactionItem)
def check_stock_level(sender, instance, created, **kwargs):
    material = instance.material

    if material.current_stock <= material.reorder_point:
        existing_alert = StockAlert.objects.filter(
            material=material,
            status='pending'
        ).first()

        if existing_alert:
            existing_alert.current_stock = material.current_stock
            existing_alert.save()
        else:
            StockAlert.objects.create(
                material=material,
                current_stock=material.current_stock,
                reorder_point=material.reorder_point,
                notes=f'Stock level dropped to {material.current_stock} after transaction'
            )
    else:
        StockAlert.objects.filter(
            material=material,
            status='pending'
        ).update(
            status='resolved',
            resolved_date=timezone.now(),
            notes='Stock level restored'
        )


@receiver(pre_save, sender=Material)
def check_material_stock_before_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_material = Material.objects.get(pk=instance.pk)
            if old_material.current_stock != instance.current_stock:
                if instance.current_stock <= instance.reorder_point:
                    alert, created = StockAlert.objects.get_or_create(
                        material=instance,
                        status='pending',
                        defaults={
                            'current_stock': instance.current_stock,
                            'reorder_point': instance.reorder_point,
                            'notes': 'Manual stock update'
                        }
                    )
                    if not created:
                        alert.current_stock = instance.current_stock
                        alert.save()
                else:
                    StockAlert.objects.filter(
                        material=instance,
                        status='pending'
                    ).update(
                        status='resolved',
                        resolved_date=timezone.now(),
                        notes='Stock level restored'
                    )
        except Material.DoesNotExist:
            pass