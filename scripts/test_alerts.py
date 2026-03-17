#!/usr/bin/env python
"""
Test Stock Alerts Script
Tests stock alert creation and management
Run with: python scripts/test_alerts.py
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from inventory.models import Material
from transactions.models import StockAlert
from django.contrib.auth.models import User
from django.utils import timezone


def test_alerts():
    """Test stock alert functionality"""
    print("=" * 60)
    print("⚠️  TESTING STOCK ALERTS")
    print("=" * 60)

    # Get admin user
    try:
        admin = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("❌ Admin user not found. Run sample data first.")
        return

    # Find a material with low stock
    low_stock_materials = Material.objects.filter(
        current_stock__lte=models.F('reorder_point')
    )

    if not low_stock_materials:
        print("❌ No low stock materials found. Run sample data first.")
        return

    material = low_stock_materials.first()
    print(f"\n📦 Testing with: {material.name}")
    print(f"   Current Stock: {material.current_stock}")
    print(f"   Reorder Point: {material.reorder_point}")

    # Check existing alerts
    alerts = StockAlert.objects.filter(material=material)
    print(f"\n📊 Existing alerts: {alerts.count()}")
    for alert in alerts:
        print(f"   - {alert.get_status_display()}: Stock {alert.current_stock}")

    # Create a new alert manually
    print("\n🆕 Creating new alert...")
    alert = StockAlert.objects.create(
        material=material,
        current_stock=material.current_stock,
        reorder_point=material.reorder_point,
        notes='Test alert'
    )
    print(f"   ✅ Alert created: {alert.id}")

    # Test acknowledge
    print("\n🔵 Testing acknowledge...")
    alert.status = 'acknowledged'
    alert.resolved_by = admin
    alert.resolved_date = timezone.now()
    alert.save()
    print(f"   ✅ Alert acknowledged")

    # Test resolve
    print("\n🟢 Testing resolve...")
    alert.status = 'resolved'
    alert.save()
    print(f"   ✅ Alert resolved")

    print("\n" + "=" * 60)
    print("✅ Alert tests complete!")
    print("=" * 60)


if __name__ == '__main__':
    from django.db import models

    test_alerts()