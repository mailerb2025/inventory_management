#!/usr/bin/env python
"""
Reset Database Script - Use with caution!
This will delete all data and recreate the database.
Run with: python scripts/reset_db.py
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserRole, UserProfile
from inventory.models import Category, Material
from vendors.models import Vendor, PurchaseOrder, PurchaseOrderItem
from transactions.models import Transaction, TransactionItem, StockAlert


def reset_database():
    """Delete all data from all tables"""
    print("=" * 60)
    print("⚠️  WARNING: This will delete ALL data!")
    print("=" * 60)

    confirm = input("Type 'YES' to confirm: ")
    if confirm != 'YES':
        print("❌ Operation cancelled")
        return

    print("\n🗑️  Deleting data...")

    # Delete in correct order to avoid foreign key constraints
    print("  - Deleting stock alerts...")
    StockAlert.objects.all().delete()

    print("  - Deleting transaction items...")
    TransactionItem.objects.all().delete()

    print("  - Deleting transactions...")
    Transaction.objects.all().delete()

    print("  - Deleting purchase order items...")
    PurchaseOrderItem.objects.all().delete()

    print("  - Deleting purchase orders...")
    PurchaseOrder.objects.all().delete()

    print("  - Deleting vendors...")
    Vendor.objects.all().delete()

    print("  - Deleting materials...")
    Material.objects.all().delete()

    print("  - Deleting categories...")
    Category.objects.all().delete()

    print("  - Deleting user profiles...")
    UserProfile.objects.all().delete()

    print("  - Deleting users (except superuser)...")
    User.objects.filter(is_superuser=False).delete()

    print("  - Deleting roles...")
    UserRole.objects.all().delete()

    print("\n✅ Database reset complete!")
    print("\nRun the sample data script to repopulate:")
    print("  python scripts/create_complete_sample_data.py")


if __name__ == '__main__':
    reset_database()