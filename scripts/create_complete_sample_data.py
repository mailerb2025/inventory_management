#!/usr/bin/env python
"""
Complete Sample Data Generator for Inventory Management System
This script creates comprehensive test data for all modules.
Run with: python scripts/create_complete_sample_data.py
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from accounts.models import UserRole, UserProfile
from inventory.models import Category, Material
from vendors.models import Vendor, PurchaseOrder, PurchaseOrderItem
from transactions.models import Transaction, TransactionItem, StockAlert


class SampleDataGenerator:
    def __init__(self):
        self.admin_user = None
        self.categories = []
        self.materials = []
        self.vendors = []
        self.users = []

    def run(self):
        """Run all sample data generation"""
        print("=" * 70)
        print("📊 INVENTORY MANAGEMENT SYSTEM - SAMPLE DATA GENERATOR")
        print("=" * 70)

        self.create_roles()
        self.create_users()
        self.create_categories()
        self.create_materials()
        self.create_vendors()
        self.associate_materials_with_vendors()
        self.create_purchase_orders()
        self.create_transactions()
        self.create_stock_alerts()
        self.print_summary()

    def create_roles(self):
        """Create user roles"""
        print("\n📋 Creating user roles...")

        roles_data = [
            {
                'name': 'admin',
                'description': 'Full system access',
                'is_default': False,
                'can_view_inventory': True,
                'can_edit_inventory': True,
                'can_delete_inventory': True,
                'can_create_inventory': True,
                'can_view_transactions': True,
                'can_create_transactions': True,
                'can_edit_transactions': True,
                'can_delete_transactions': True,
                'can_approve_transactions': True,
                'can_view_vendors': True,
                'can_edit_vendors': True,
                'can_delete_vendors': True,
                'can_create_vendors': True,
                'can_view_reports': True,
                'can_export_reports': True,
                'can_view_users': True,
                'can_edit_users': True,
                'can_delete_users': True,
                'can_create_users': True,
            },
            {
                'name': 'manager',
                'description': 'Department manager',
                'is_default': False,
                'can_view_inventory': True,
                'can_edit_inventory': True,
                'can_delete_inventory': False,
                'can_create_inventory': True,
                'can_view_transactions': True,
                'can_create_transactions': True,
                'can_edit_transactions': True,
                'can_delete_transactions': False,
                'can_approve_transactions': True,
                'can_view_vendors': True,
                'can_edit_vendors': True,
                'can_delete_vendors': False,
                'can_create_vendors': True,
                'can_view_reports': True,
                'can_export_reports': True,
                'can_view_users': True,
                'can_edit_users': False,
                'can_delete_users': False,
                'can_create_users': False,
            },
            {
                'name': 'staff',
                'description': 'Staff member',
                'is_default': False,
                'can_view_inventory': True,
                'can_edit_inventory': True,
                'can_delete_inventory': False,
                'can_create_inventory': True,
                'can_view_transactions': True,
                'can_create_transactions': True,
                'can_edit_transactions': False,
                'can_delete_transactions': False,
                'can_approve_transactions': False,
                'can_view_vendors': True,
                'can_edit_vendors': False,
                'can_delete_vendors': False,
                'can_create_vendors': False,
                'can_view_reports': True,
                'can_export_reports': False,
                'can_view_users': False,
                'can_edit_users': False,
                'can_delete_users': False,
                'can_create_users': False,
            },
            {
                'name': 'viewer',
                'description': 'Read-only access',
                'is_default': True,
                'can_view_inventory': True,
                'can_edit_inventory': False,
                'can_delete_inventory': False,
                'can_create_inventory': False,
                'can_view_transactions': True,
                'can_create_transactions': False,
                'can_edit_transactions': False,
                'can_delete_transactions': False,
                'can_approve_transactions': False,
                'can_view_vendors': True,
                'can_edit_vendors': False,
                'can_delete_vendors': False,
                'can_create_vendors': False,
                'can_view_reports': True,
                'can_export_reports': False,
                'can_view_users': False,
                'can_edit_users': False,
                'can_delete_users': False,
                'can_create_users': False,
            },
        ]

        for role_data in roles_data:
            role, created = UserRole.objects.update_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            if created:
                print(f"  ✅ Created role: {role.get_name_display()}")
            else:
                print(f"  📌 Updated role: {role.get_name_display()}")

    def create_users(self):
        """Create test users"""
        print("\n👥 Creating test users...")

        users_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'admin123',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': 'admin',
                'is_superuser': True,
                'is_staff': True,
                'phone': '+1-555-0100',
                'department': 'IT Administration',
                'employee_id': 'EMP001'
            },
            {
                'username': 'john.manager',
                'email': 'john.manager@example.com',
                'password': 'manager123',
                'first_name': 'John',
                'last_name': 'Smith',
                'role': 'manager',
                'is_superuser': False,
                'is_staff': True,
                'phone': '+1-555-0101',
                'department': 'Warehouse Operations',
                'employee_id': 'EMP002'
            },
            {
                'username': 'sarah.staff',
                'email': 'sarah.staff@example.com',
                'password': 'staff123',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'role': 'staff',
                'is_superuser': False,
                'is_staff': False,
                'phone': '+1-555-0102',
                'department': 'Inventory Control',
                'employee_id': 'EMP003'
            },
            {
                'username': 'mike.staff',
                'email': 'mike.staff@example.com',
                'password': 'staff123',
                'first_name': 'Mike',
                'last_name': 'Wilson',
                'role': 'staff',
                'is_superuser': False,
                'is_staff': False,
                'phone': '+1-555-0103',
                'department': 'Receiving',
                'employee_id': 'EMP004'
            },
            {
                'username': 'lisa.viewer',
                'email': 'lisa.viewer@example.com',
                'password': 'viewer123',
                'first_name': 'Lisa',
                'last_name': 'Brown',
                'role': 'viewer',
                'is_superuser': False,
                'is_staff': False,
                'phone': '+1-555-0104',
                'department': 'Audit',
                'employee_id': 'EMP005'
            },
        ]

        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_superuser': user_data['is_superuser'],
                    'is_staff': user_data['is_staff'],
                }
            )

            if created:
                user.set_password(user_data['password'])
                user.save()

                # Assign role
                role = UserRole.objects.get(name=user_data['role'])
                UserProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        'role': role,
                        'phone_number': user_data['phone'],
                        'department': user_data['department'],
                        'employee_id': user_data['employee_id'],
                        'notification_email': True,
                        'notification_sms': False,
                    }
                )
                print(f"  ✅ Created user: {user_data['username']} / {user_data['password']}")
                self.users.append(user)

                if user_data['username'] == 'admin':
                    self.admin_user = user
            else:
                print(f"  📌 User already exists: {user_data['username']}")
                self.users.append(user)
                if user_data['username'] == 'admin':
                    self.admin_user = user

    def create_categories(self):
        """Create material categories"""
        print("\n📦 Creating material categories...")

        categories_data = [
            {'name': 'Electronics', 'description': 'Electronic components, boards, and devices'},
            {'name': 'Hardware', 'description': 'Screws, nuts, bolts, and other hardware items'},
            {'name': 'Tools', 'description': 'Hand tools, power tools, and equipment'},
            {'name': 'Packaging', 'description': 'Boxes, bubble wrap, tape, and packaging materials'},
            {'name': 'Raw Materials', 'description': 'Raw materials for production'},
            {'name': 'Office Supplies', 'description': 'Stationery and office consumables'},
            {'name': 'Safety Equipment', 'description': 'PPE, safety gear, and first aid'},
            {'name': 'Electrical', 'description': 'Wires, cables, connectors, and electrical components'},
            {'name': 'Plumbing', 'description': 'Pipes, fittings, and plumbing supplies'},
            {'name': 'Chemicals', 'description': 'Cleaning supplies, lubricants, and chemicals'},
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                print(f"  ✅ Created category: {cat_data['name']}")
            self.categories.append(category)

    def create_materials(self):
        """Create sample materials"""
        print("\n📦 Creating sample materials...")

        materials_data = [
            # Electronics
            {'code': 'ELEC001', 'name': 'Arduino Uno R3', 'category': 'Electronics',
             'unit': 'pcs', 'stock': 45, 'min': 10, 'max': 100, 'reorder': 20,
             'cost': 24.99, 'location': 'A1-01'},
            {'code': 'ELEC002', 'name': 'Raspberry Pi 4 4GB', 'category': 'Electronics',
             'unit': 'pcs', 'stock': 28, 'min': 5, 'max': 50, 'reorder': 10,
             'cost': 55.00, 'location': 'A1-02'},
            {'code': 'ELEC003', 'name': 'LED Display 16x2', 'category': 'Electronics',
             'unit': 'pcs', 'stock': 120, 'min': 20, 'max': 200, 'reorder': 40,
             'cost': 8.50, 'location': 'A1-03'},
            {'code': 'ELEC004', 'name': 'Resistor Kit 500pcs', 'category': 'Electronics',
             'unit': 'kit', 'stock': 65, 'min': 15, 'max': 150, 'reorder': 30,
             'cost': 12.75, 'location': 'A1-04'},
            {'code': 'ELEC005', 'name': 'Capacitor Kit 200pcs', 'category': 'Electronics',
             'unit': 'kit', 'stock': 42, 'min': 10, 'max': 100, 'reorder': 20,
             'cost': 14.25, 'location': 'A1-05'},
            {'code': 'ELEC006', 'name': 'Breadboard 400 points', 'category': 'Electronics',
             'unit': 'pcs', 'stock': 8, 'min': 15, 'max': 80, 'reorder': 20,
             'cost': 5.99, 'location': 'A1-06'},
            {'code': 'ELEC007', 'name': 'Jumper Wires 120pcs', 'category': 'Electronics',
             'unit': 'set', 'stock': 35, 'min': 10, 'max': 100, 'reorder': 20,
             'cost': 6.50, 'location': 'A1-07'},
            {'code': 'ELEC008', 'name': '9V Battery Connector', 'category': 'Electronics',
             'unit': 'pcs', 'stock': 150, 'min': 30, 'max': 300, 'reorder': 60,
             'cost': 1.25, 'location': 'A1-08'},

            # Hardware
            {'code': 'HARD001', 'name': 'M3 Screws 100pcs', 'category': 'Hardware',
             'unit': 'box', 'stock': 25, 'min': 10, 'max': 50, 'reorder': 15,
             'cost': 4.99, 'location': 'B2-01'},
            {'code': 'HARD002', 'name': 'M4 Screws 100pcs', 'category': 'Hardware',
             'unit': 'box', 'stock': 18, 'min': 10, 'max': 50, 'reorder': 15,
             'cost': 5.49, 'location': 'B2-02'},
            {'code': 'HARD003', 'name': 'M3 Nuts 100pcs', 'category': 'Hardware',
             'unit': 'box', 'stock': 22, 'min': 10, 'max': 50, 'reorder': 15,
             'cost': 3.99, 'location': 'B2-03'},
            {'code': 'HARD004', 'name': 'Washers M3 100pcs', 'category': 'Hardware',
             'unit': 'box', 'stock': 30, 'min': 10, 'max': 60, 'reorder': 15,
             'cost': 2.99, 'location': 'B2-04'},
            {'code': 'HARD005', 'name': 'Hex Keys Set 9pcs', 'category': 'Hardware',
             'unit': 'set', 'stock': 5, 'min': 5, 'max': 30, 'reorder': 8,
             'cost': 9.99, 'location': 'B2-05'},

            # Tools
            {'code': 'TOOL001', 'name': 'Soldering Iron 60W', 'category': 'Tools',
             'unit': 'pcs', 'stock': 15, 'min': 5, 'max': 30, 'reorder': 8,
             'cost': 29.99, 'location': 'C3-01'},
            {'code': 'TOOL002', 'name': 'Digital Multimeter', 'category': 'Tools',
             'unit': 'pcs', 'stock': 12, 'min': 4, 'max': 25, 'reorder': 6,
             'cost': 34.50, 'location': 'C3-02'},
            {'code': 'TOOL003', 'name': 'Wire Stripper', 'category': 'Tools',
             'unit': 'pcs', 'stock': 8, 'min': 4, 'max': 20, 'reorder': 5,
             'cost': 12.99, 'location': 'C3-03'},
            {'code': 'TOOL004', 'name': 'Screwdriver Set 6pcs', 'category': 'Tools',
             'unit': 'set', 'stock': 3, 'min': 5, 'max': 25, 'reorder': 8,
             'cost': 15.99, 'location': 'C3-04'},
            {'code': 'TOOL005', 'name': 'Pliers Set 3pcs', 'category': 'Tools',
             'unit': 'set', 'stock': 7, 'min': 3, 'max': 20, 'reorder': 5,
             'cost': 22.50, 'location': 'C3-05'},

            # Packaging
            {'code': 'PACK001', 'name': 'Small Box 10x10x10cm', 'category': 'Packaging',
             'unit': 'pcs', 'stock': 250, 'min': 50, 'max': 500, 'reorder': 100,
             'cost': 0.75, 'location': 'D4-01'},
            {'code': 'PACK002', 'name': 'Medium Box 20x20x20cm', 'category': 'Packaging',
             'unit': 'pcs', 'stock': 180, 'min': 40, 'max': 400, 'reorder': 80,
             'cost': 1.25, 'location': 'D4-02'},
            {'code': 'PACK003', 'name': 'Bubble Wrap 10m', 'category': 'Packaging',
             'unit': 'roll', 'stock': 35, 'min': 10, 'max': 60, 'reorder': 15,
             'cost': 8.99, 'location': 'D4-03'},
            {'code': 'PACK004', 'name': 'Packing Tape 50m', 'category': 'Packaging',
             'unit': 'roll', 'stock': 42, 'min': 15, 'max': 80, 'reorder': 20,
             'cost': 3.49, 'location': 'D4-04'},
            {'code': 'PACK005', 'name': 'Anti-static Bags 100pcs', 'category': 'Packaging',
             'unit': 'pack', 'stock': 15, 'min': 10, 'max': 40, 'reorder': 12,
             'cost': 12.99, 'location': 'D4-05'},

            # Raw Materials
            {'code': 'RAW001', 'name': 'ABS Filament 1kg', 'category': 'Raw Materials',
             'unit': 'spool', 'stock': 28, 'min': 8, 'max': 40, 'reorder': 12,
             'cost': 22.99, 'location': 'E5-01'},
            {'code': 'RAW002', 'name': 'PLA Filament 1kg', 'category': 'Raw Materials',
             'unit': 'spool', 'stock': 32, 'min': 10, 'max': 50, 'reorder': 15,
             'cost': 21.99, 'location': 'E5-02'},
            {'code': 'RAW003', 'name': 'Aluminum Sheet 1mm', 'category': 'Raw Materials',
             'unit': 'sheet', 'stock': 22, 'min': 5, 'max': 30, 'reorder': 8,
             'cost': 15.50, 'location': 'E5-03'},
            {'code': 'RAW004', 'name': 'Copper Wire 100m', 'category': 'Raw Materials',
             'unit': 'roll', 'stock': 12, 'min': 4, 'max': 25, 'reorder': 6,
             'cost': 18.99, 'location': 'E5-04'},
            {'code': 'RAW005', 'name': 'Solder Wire 100g', 'category': 'Raw Materials',
             'unit': 'roll', 'stock': 18, 'min': 5, 'max': 30, 'reorder': 8,
             'cost': 8.99, 'location': 'E5-05'},
        ]

        for mat_data in materials_data:
            try:
                category = Category.objects.get(name=mat_data['category'])
                material, created = Material.objects.get_or_create(
                    material_code=mat_data['code'],
                    defaults={
                        'name': mat_data['name'],
                        'category': category,
                        'unit': mat_data['unit'],
                        'current_stock': mat_data['stock'],
                        'minimum_stock': mat_data['min'],
                        'maximum_stock': mat_data['max'],
                        'reorder_point': mat_data['reorder'],
                        'location': mat_data['location'],
                        'unit_cost': Decimal(str(mat_data['cost'])),
                        'status': 'active',
                        'created_by': self.admin_user,
                    }
                )
                if created:
                    print(f"  ✅ Created material: {mat_data['code']} - {mat_data['name']}")
                self.materials.append(material)
            except Category.DoesNotExist:
                print(f"  ❌ Category {mat_data['category']} not found, skipping {mat_data['code']}")
            except Exception as e:
                print(f"  ❌ Error creating material {mat_data['code']}: {e}")

    def create_vendors(self):
        """Create sample vendors"""
        print("\n🚚 Creating sample vendors...")

        vendors_data = [
            {
                'code': 'VEN001',
                'name': 'Tech Components Ltd',
                'type': 'distributor',
                'contact': 'David Chen',
                'email': 'david.chen@techcomponents.com',
                'phone': '+86-755-1234-5678',
                'address': '123 Tech Park, Shenzhen',
                'city': 'Shenzhen',
                'country': 'China',
                'rating': 5,
                'payment_terms': 'Net 30',
                'notes': 'Premium electronic components supplier',
            },
            {
                'code': 'VEN002',
                'name': 'Global Hardware Supply',
                'type': 'wholesaler',
                'contact': 'Maria Garcia',
                'email': 'maria@globalhardware.com',
                'phone': '+1-555-123-4567',
                'address': '456 Industrial Ave, Chicago, IL',
                'city': 'Chicago',
                'country': 'USA',
                'rating': 4,
                'payment_terms': 'Net 45',
                'notes': 'Industrial hardware and tools',
            },
            {
                'code': 'VEN003',
                'name': 'Packaging Solutions Inc',
                'type': 'manufacturer',
                'contact': 'James Wilson',
                'email': 'james@packagingsolutions.com',
                'phone': '+1-555-987-6543',
                'address': '789 Packaging Way, Atlanta, GA',
                'city': 'Atlanta',
                'country': 'USA',
                'rating': 4,
                'payment_terms': 'Net 30',
                'notes': 'Custom packaging solutions',
            },
            {
                'code': 'VEN004',
                'name': 'ElectroWorld Distributors',
                'type': 'distributor',
                'contact': 'Sarah Lee',
                'email': 'sarah@electroworld.com',
                'phone': '+852-2345-6789',
                'address': '12 Electronics Plaza, Hong Kong',
                'city': 'Hong Kong',
                'country': 'China',
                'rating': 5,
                'payment_terms': 'Net 15',
                'notes': 'Fast shipping, quality components',
            },
            {
                'code': 'VEN005',
                'name': 'ToolMaster Industries',
                'type': 'manufacturer',
                'contact': 'Robert Brown',
                'email': 'robert@toolmaster.com',
                'phone': '+1-555-555-1212',
                'address': '321 Tool Street, Cleveland, OH',
                'city': 'Cleveland',
                'country': 'USA',
                'rating': 3,
                'payment_terms': 'Net 60',
                'notes': 'Professional tools and equipment',
            },
        ]

        for ven_data in vendors_data:
            try:
                vendor, created = Vendor.objects.get_or_create(
                    vendor_code=ven_data['code'],
                    defaults={
                        'name': ven_data['name'],
                        'vendor_type': ven_data['type'],
                        'contact_person': ven_data['contact'],
                        'email': ven_data['email'],
                        'phone': ven_data['phone'],
                        'address': ven_data['address'],
                        'city': ven_data['city'],
                        'country': ven_data['country'],
                        'rating': ven_data['rating'],
                        'payment_terms': ven_data['payment_terms'],
                        'notes': ven_data['notes'],
                        'status': 'active',
                        'created_by': self.admin_user,
                    }
                )
                if created:
                    print(f"  ✅ Created vendor: {ven_data['code']} - {ven_data['name']}")
                self.vendors.append(vendor)
            except Exception as e:
                print(f"  ❌ Error creating vendor {ven_data['code']}: {e}")

    def associate_materials_with_vendors(self):
        """Associate materials with vendors"""
        print("\n🔗 Associating materials with vendors...")

        try:
            # Tech Components - Electronics
            tech_vendor = Vendor.objects.get(vendor_code='VEN001')
            electronics = Material.objects.filter(category__name='Electronics')[:8]
            if electronics:
                tech_vendor.materials.add(*electronics)
                print(f"  ✅ Tech Components: {electronics.count()} electronics materials")
        except Exception as e:
            print(f"  ⚠️ Could not associate Tech Components materials: {e}")

        try:
            # Global Hardware - Hardware
            hardware_vendor = Vendor.objects.get(vendor_code='VEN002')
            hardware = Material.objects.filter(category__name='Hardware')[:5]
            if hardware:
                hardware_vendor.materials.add(*hardware)
                print(f"  ✅ Global Hardware: {hardware.count()} hardware materials")
        except Exception as e:
            print(f"  ⚠️ Could not associate Global Hardware materials: {e}")

        try:
            # ToolMaster - Tools
            tool_vendor = Vendor.objects.get(vendor_code='VEN005')
            tools = Material.objects.filter(category__name='Tools')[:5]
            if tools:
                tool_vendor.materials.add(*tools)
                print(f"  ✅ ToolMaster: {tools.count()} tool materials")
        except Exception as e:
            print(f"  ⚠️ Could not associate ToolMaster materials: {e}")

        try:
            # Packaging Solutions - Packaging
            packaging_vendor = Vendor.objects.get(vendor_code='VEN003')
            packaging = Material.objects.filter(category__name='Packaging')[:5]
            if packaging:
                packaging_vendor.materials.add(*packaging)
                print(f"  ✅ Packaging Solutions: {packaging.count()} packaging materials")
        except Exception as e:
            print(f"  ⚠️ Could not associate Packaging Solutions materials: {e}")

        try:
            # ElectroWorld - Electronics and Raw Materials
            electro_vendor = Vendor.objects.get(vendor_code='VEN004')
            electro_mats = list(Material.objects.filter(category__name='Electronics')[8:10]) + \
                           list(Material.objects.filter(category__name='Raw Materials')[:3])
            if electro_mats:
                electro_vendor.materials.add(*electro_mats)
                print(f"  ✅ ElectroWorld: {len(electro_mats)} materials")
        except Exception as e:
            print(f"  ⚠️ Could not associate ElectroWorld materials: {e}")

    def create_purchase_orders(self):
        """Create sample purchase orders"""
        print("\n📝 Creating sample purchase orders...")

        po_statuses = ['draft', 'sent', 'confirmed', 'shipped', 'delivered']

        po_count = 0
        for i in range(15):
            if not self.vendors:
                continue

            vendor = random.choice(self.vendors)
            status = random.choice(po_statuses)

            try:
                # Create PO
                po = PurchaseOrder.objects.create(
                    vendor=vendor,
                    order_date=timezone.now().date() - timedelta(days=random.randint(1, 30)),
                    expected_delivery=timezone.now().date() + timedelta(days=random.randint(5, 20)),
                    status=status,
                    notes=f"Sample purchase order #{i + 1}",
                    created_by=random.choice(self.users[1:]) if len(self.users) > 1 else self.admin_user,
                )

                # Add 2-5 items
                num_items = random.randint(2, 5)
                vendor_materials = list(vendor.materials.all())
                if vendor_materials:
                    selected_materials = random.sample(
                        vendor_materials,
                        min(num_items, len(vendor_materials))
                    )

                    subtotal = Decimal('0')
                    for material in selected_materials:
                        qty = random.randint(5, 50)
                        # Convert float to Decimal properly
                        price_multiplier = Decimal(str(random.uniform(0.9, 1.1)))
                        price = material.unit_cost * price_multiplier

                        item = PurchaseOrderItem.objects.create(
                            purchase_order=po,
                            material=material,
                            quantity=qty,
                            unit_price=price
                        )
                        subtotal += item.line_total

                    # Update PO totals
                    po.subtotal = subtotal
                    po.tax = subtotal * Decimal('0.1')
                    po.total = subtotal + po.tax
                    po.save()
                    po_count += 1
                    print(f"  ✅ Created PO: {po.po_number} - {vendor.name} (${po.total:.2f})")
                else:
                    # Delete PO if no items
                    po.delete()
            except Exception as e:
                print(f"  ⚠️ Error creating purchase order: {e}")

        if po_count == 0:
            print("  ⚠️ No purchase orders created - vendors may not have materials")

    def create_transactions(self):
        """Create sample transactions"""
        print("\n🔄 Creating sample transactions...")

        # Get staff users for transaction creation
        staff_users = User.objects.filter(username__in=['john.manager', 'sarah.staff', 'mike.staff'])

        if not self.materials:
            print("  ⚠️ No materials found, skipping transactions")
            return

        transaction_count = 0
        # Create transactions over the last 60 days
        for i in range(50):
            try:
                trans_type = random.choice(['inbound', 'outbound'])
                days_ago = random.randint(0, 60)
                hours_ago = random.randint(0, 23)
                transaction_date = timezone.now() - timedelta(days=days_ago, hours=hours_ago)

                # Select random staff user
                created_by = random.choice(staff_users) if staff_users else self.admin_user

                # Create transaction
                transaction = Transaction.objects.create(
                    transaction_type=trans_type,
                    reference_number=f"REF-{i + 1000:04d}",
                    transaction_date=transaction_date,
                    notes=f"Sample {trans_type} transaction #{i + 1}",
                    created_by=created_by,
                )

                # Add 1-3 items
                num_items = random.randint(1, 3)
                selected_materials = random.sample(self.materials, min(num_items, len(self.materials)))

                items_added = 0
                for material in selected_materials:
                    if trans_type == 'inbound':
                        qty = random.randint(10, 100)
                        # Convert float to Decimal properly
                        price_multiplier = Decimal(str(random.uniform(0.95, 1.05)))
                        price = material.unit_cost * price_multiplier
                        stock_before = material.current_stock
                        material.current_stock += qty
                    else:  # outbound
                        max_qty = min(50, material.current_stock)
                        if max_qty <= 0:
                            continue
                        qty = random.randint(1, min(20, max_qty))
                        # Convert float to Decimal properly
                        price_multiplier = Decimal(str(random.uniform(1.1, 1.3)))
                        price = material.unit_cost * price_multiplier
                        stock_before = material.current_stock
                        material.current_stock -= qty

                    material.save()

                    TransactionItem.objects.create(
                        transaction=transaction,
                        material=material,
                        quantity=qty,
                        unit_price=price,
                        stock_before=stock_before,
                        stock_after=material.current_stock
                    )
                    items_added += 1

                if items_added > 0:
                    transaction_count += 1
                else:
                    # Delete transaction if no items
                    transaction.delete()

            except Exception as e:
                print(f"  ⚠️ Error creating transaction: {e}")
                continue

        print(f"  ✅ Created {transaction_count} transactions")

    def create_stock_alerts(self):
        """Create stock alerts for low stock items"""
        print("\n⚠️ Creating stock alerts...")

        # Find materials below reorder point
        low_stock_materials = Material.objects.filter(
            current_stock__lte=models.F('reorder_point')
        )

        alert_count = 0
        for material in low_stock_materials:
            try:
                alert, created = StockAlert.objects.get_or_create(
                    material=material,
                    status='pending',
                    defaults={
                        'current_stock': material.current_stock,
                        'reorder_point': material.reorder_point,
                        'notes': f'Low stock alert: {material.current_stock} units remaining',
                    }
                )
                if created:
                    alert_count += 1
            except Exception as e:
                print(f"  ⚠️ Error creating alert for {material.name}: {e}")

        if alert_count > 0:
            print(f"  ✅ Created {alert_count} new stock alerts")

        # Create some acknowledged alerts
        if len(self.materials) >= 15:
            for i, material in enumerate(self.materials[10:15]):
                try:
                    alert_date = timezone.now() - timedelta(days=i + 2)

                    alert, created = StockAlert.objects.get_or_create(
                        material=material,
                        status='acknowledged',
                        defaults={
                            'current_stock': material.reorder_point - 5,
                            'reorder_point': material.reorder_point,
                            'alert_date': alert_date,
                            'resolved_date': alert_date + timedelta(hours=2),
                            'resolved_by': random.choice(self.users[1:]) if len(self.users) > 1 else self.admin_user,
                            'notes': 'Acknowledged alert',
                        }
                    )
                except Exception as e:
                    print(f"  ⚠️ Error creating acknowledged alert: {e}")

        # Create resolved alerts
        if len(self.materials) >= 18:
            for i, material in enumerate(self.materials[15:18]):
                try:
                    alert_date = timezone.now() - timedelta(days=i + 10)

                    alert, created = StockAlert.objects.get_or_create(
                        material=material,
                        status='resolved',
                        defaults={
                            'current_stock': material.reorder_point - 3,
                            'reorder_point': material.reorder_point,
                            'alert_date': alert_date,
                            'resolved_date': alert_date + timedelta(days=1),
                            'resolved_by': self.admin_user,
                            'notes': 'Stock replenished',
                        }
                    )
                except Exception as e:
                    print(f"  ⚠️ Error creating resolved alert: {e}")

    def print_summary(self):
        """Print summary of created data"""
        print("\n" + "=" * 70)
        print("📊 SAMPLE DATA CREATION SUMMARY")
        print("=" * 70)

        print(f"\n👥 USERS:")
        print(f"  Total users: {User.objects.count()}")
        for user in User.objects.all():
            try:
                role = user.profile.role.get_name_display() if hasattr(user,
                                                                       'profile') and user.profile.role else 'No role'
                print(f"    - {user.username} ({user.email}) - {role}")
            except:
                print(f"    - {user.username} ({user.email}) - No profile")

        print(f"\n📦 INVENTORY:")
        print(f"  Categories: {Category.objects.count()}")
        print(f"  Materials: {Material.objects.count()}")
        print(f"  Low stock items: {Material.objects.filter(current_stock__lte=models.F('reorder_point')).count()}")

        print(f"\n🚚 VENDORS:")
        print(f"  Vendors: {Vendor.objects.count()}")
        print(f"  Purchase Orders: {PurchaseOrder.objects.count()}")

        print(f"\n🔄 TRANSACTIONS:")
        print(f"  Total: {Transaction.objects.count()}")
        print(f"  Inbound: {Transaction.objects.filter(transaction_type='inbound').count()}")
        print(f"  Outbound: {Transaction.objects.filter(transaction_type='outbound').count()}")

        print(f"\n⚠️ STOCK ALERTS:")
        print(f"  Total: {StockAlert.objects.count()}")
        print(f"  Pending: {StockAlert.objects.filter(status='pending').count()}")
        print(f"  Acknowledged: {StockAlert.objects.filter(status='acknowledged').count()}")
        print(f"  Resolved: {StockAlert.objects.filter(status='resolved').count()}")

        print("\n" + "=" * 70)
        print("✅ SAMPLE DATA GENERATION COMPLETE!")
        print("=" * 70)
        print("\n📝 TEST CREDENTIALS:")
        print("  admin / admin123")
        print("  john.manager / manager123")
        print("  sarah.staff / staff123")
        print("  mike.staff / staff123")
        print("  lisa.viewer / viewer123")
        print("\n🌐 Access the system at: http://localhost:8000")


if __name__ == '__main__':
    generator = SampleDataGenerator()
    generator.run()