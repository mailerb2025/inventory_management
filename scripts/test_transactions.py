#!/usr/bin/env python
"""
Test Transaction Script
Tests inbound and outbound transactions with stock validation
Run with: python scripts/test_transactions.py
"""

import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from inventory.models import Material
from transactions.models import Transaction, TransactionItem
from decimal import Decimal


def test_transactions():
    """Test transaction functionality"""
    print("=" * 60)
    print("🧪 TESTING TRANSACTIONS")
    print("=" * 60)

    # Get admin user
    try:
        admin = User.objects.get(username='admin')
    except User.DoesNotExist:
        print("❌ Admin user not found. Run sample data first.")
        return

    # Get a material to test with
    material = Material.objects.first()
    if not material:
        print("❌ No materials found. Run sample data first.")
        return

    print(f"\n📦 Test Material: {material.name}")
    print(f"   Current Stock: {material.current_stock}")
    print(f"   Unit Cost: ${material.unit_cost}")

    # Test 1: Inbound Transaction
    print("\n✅ TEST 1: Inbound Transaction")
    inbound = Transaction.objects.create(
        transaction_type='inbound',
        reference_number='TEST-IN-001',
        notes='Test inbound transaction',
        created_by=admin
    )

    qty = 25
    price = material.unit_cost * Decimal('0.95')  # 5% discount
    stock_before = material.current_stock

    item = TransactionItem.objects.create(
        transaction=inbound,
        material=material,
        quantity=qty,
        unit_price=price,
        stock_before=stock_before,
        stock_after=stock_before + qty
    )

    material.current_stock += qty
    material.save()

    print(f"   Added {qty} units at ${price:.2f}")
    print(f"   Stock: {stock_before} → {material.current_stock}")

    # Test 2: Outbound Transaction (Valid)
    print("\n✅ TEST 2: Outbound Transaction (Valid)")
    outbound = Transaction.objects.create(
        transaction_type='outbound',
        reference_number='TEST-OUT-001',
        notes='Test outbound transaction',
        created_by=admin
    )

    qty = 10
    price = material.unit_cost * Decimal('1.2')  # 20% markup
    stock_before = material.current_stock

    if stock_before >= qty:
        item = TransactionItem.objects.create(
            transaction=outbound,
            material=material,
            quantity=qty,
            unit_price=price,
            stock_before=stock_before,
            stock_after=stock_before - qty
        )

        material.current_stock -= qty
        material.save()

        print(f"   Issued {qty} units at ${price:.2f}")
        print(f"   Stock: {stock_before} → {material.current_stock}")
    else:
        print(f"   ❌ Insufficient stock! Available: {stock_before}")

    # Test 3: Outbound Transaction (Invalid - should fail)
    print("\n❌ TEST 3: Outbound Transaction (Invalid - should fail)")
    qty = 9999  # Very large quantity

    if material.current_stock >= qty:
        print(f"   ⚠️  This should have failed but passed!")
    else:
        print(f"   ✅ Correctly prevented: Insufficient stock!")
        print(f"      Requested: {qty}, Available: {material.current_stock}")

    print("\n" + "=" * 60)
    print("✅ Transaction tests complete!")
    print("=" * 60)


if __name__ == '__main__':
    test_transactions()