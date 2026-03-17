from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from .models import Vendor, PurchaseOrder, PurchaseOrderItem
from inventory.models import Material
from .forms import VendorForm, PurchaseOrderForm, PurchaseOrderItemForm
from decimal import Decimal


@login_required
def vendor_list(request):
    """List all vendors"""
    vendors = Vendor.objects.annotate(po_count=Count('purchase_orders')).all()

    search_query = request.GET.get('search', '')
    if search_query:
        vendors = vendors.filter(
            Q(name__icontains=search_query) |
            Q(vendor_code__icontains=search_query) |
            Q(contact_person__icontains=search_query)
        )

    status = request.GET.get('status')
    if status:
        vendors = vendors.filter(status=status)

    paginator = Paginator(vendors, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_status': status,
    }

    return render(request, 'vendors/vendor_list.html', context)


@login_required
def vendor_detail(request, pk):
    """View vendor details"""
    vendor = get_object_or_404(Vendor.objects.prefetch_related('materials__category'), pk=pk)
    purchase_orders = vendor.purchase_orders.all().order_by('-order_date')[:10]
    materials = vendor.materials.all().select_related('category')

    context = {
        'vendor': vendor,
        'purchase_orders': purchase_orders,
        'materials': materials,
    }

    return render(request, 'vendors/vendor_detail.html', context)


@login_required
def vendor_create(request):
    """Create a new vendor"""
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.created_by = request.user
            vendor.save()
            form.save_m2m()
            messages.success(request, f'Vendor {vendor.name} created successfully!')
            return redirect('vendors:vendor_detail', pk=vendor.pk)
    else:
        form = VendorForm()

    return render(request, 'vendors/vendor_form.html', {'form': form, 'title': 'Create Vendor'})


@login_required
def vendor_update(request, pk):
    """Update a vendor"""
    vendor = get_object_or_404(Vendor, pk=pk)

    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            vendor = form.save()
            messages.success(request, f'Vendor {vendor.name} updated successfully!')
            return redirect('vendors:vendor_detail', pk=vendor.pk)
    else:
        form = VendorForm(instance=vendor)

    return render(request, 'vendors/vendor_form.html', {'form': form, 'title': 'Update Vendor', 'vendor': vendor})


@login_required
def vendor_delete(request, pk):
    """Delete a vendor"""
    vendor = get_object_or_404(Vendor, pk=pk)

    if request.method == 'POST':
        vendor.delete()
        messages.success(request, f'Vendor {vendor.name} deleted successfully!')
        return redirect('vendors:vendor_list')

    return render(request, 'vendors/vendor_confirm_delete.html', {'vendor': vendor})


@login_required
def purchase_order_list(request):
    """List all purchase orders"""
    orders = PurchaseOrder.objects.select_related('vendor').all().order_by('-order_date')

    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        orders = orders.filter(order_date__gte=date_from)
    if date_to:
        orders = orders.filter(order_date__lte=date_to)

    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'selected_status': status,
        'date_from': date_from,
        'date_to': date_to,
    }

    return render(request, 'vendors/purchase_order_list.html', context)


@login_required
def purchase_order_detail(request, pk):
    """View purchase order details"""
    order = get_object_or_404(PurchaseOrder.objects.select_related('vendor'), pk=pk)
    items = order.items.select_related('material').all()

    context = {
        'order': order,
        'items': items,
    }

    return render(request, 'vendors/purchase_order_detail.html', context)


@login_required
def purchase_order_create(request):
    """Create a new purchase order"""
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()

            item_count = int(request.POST.get('item_count', 0))
            items_created = 0
            subtotal = Decimal('0.00')

            for i in range(item_count):
                material_id = request.POST.get(f'material_{i}')
                quantity = request.POST.get(f'quantity_{i}')
                unit_price = request.POST.get(f'unit_price_{i}')

                if material_id and quantity and unit_price:
                    try:
                        material_id = int(material_id)
                        quantity = int(quantity)
                        unit_price = Decimal(str(unit_price))

                        # Calculate line total
                        line_total = quantity * unit_price
                        subtotal += line_total

                        PurchaseOrderItem.objects.create(
                            purchase_order=order,
                            material_id=material_id,
                            quantity=quantity,
                            unit_price=unit_price
                        )
                        items_created += 1
                    except (ValueError, TypeError) as e:
                        messages.warning(request, f'Error adding item: {e}')
                        continue

            # Update order totals
            order.subtotal = subtotal
            order.tax = subtotal * Decimal('0.1')
            order.total = subtotal + order.tax
            order.save()

            messages.success(request, f'Purchase Order {order.po_number} created with {items_created} items.')
            return redirect('vendors:purchase_order_detail', pk=order.pk)
    else:
        form = PurchaseOrderForm()

    materials = Material.objects.filter(status='active')

    context = {
        'form': form,
        'materials': materials,
        'title': 'Create Purchase Order',
    }

    return render(request, 'vendors/purchase_order_form.html', context)


@login_required
def purchase_order_edit(request, pk):
    """Edit a purchase order"""
    order = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)

            item_count = int(request.POST.get('item_count', 0))

            # Get existing items
            existing_items = {item.id: item for item in order.items.all()}
            processed_item_ids = set()
            subtotal = Decimal('0.00')

            for i in range(item_count):
                item_id = request.POST.get(f'item_id_{i}')
                material_id = request.POST.get(f'material_{i}')
                quantity = request.POST.get(f'quantity_{i}')
                unit_price = request.POST.get(f'unit_price_{i}')

                if material_id and quantity and unit_price:
                    try:
                        material_id = int(material_id)
                        quantity = int(quantity)
                        unit_price = Decimal(str(unit_price))

                        # Calculate line total
                        line_total = quantity * unit_price
                        subtotal += line_total

                        if item_id and item_id.strip():
                            # Update existing item
                            item_id = int(item_id)
                            if item_id in existing_items:
                                item = existing_items[item_id]
                                item.material_id = material_id
                                item.quantity = quantity
                                item.unit_price = unit_price
                                item.save()
                                processed_item_ids.add(item_id)
                            else:
                                # Create new item if ID doesn't exist
                                item = PurchaseOrderItem.objects.create(
                                    purchase_order=order,
                                    material_id=material_id,
                                    quantity=quantity,
                                    unit_price=unit_price
                                )
                                processed_item_ids.add(item.id)
                        else:
                            # Create new item
                            item = PurchaseOrderItem.objects.create(
                                purchase_order=order,
                                material_id=material_id,
                                quantity=quantity,
                                unit_price=unit_price
                            )
                            processed_item_ids.add(item.id)
                    except (ValueError, TypeError) as e:
                        messages.warning(request, f'Error processing item: {e}')
                        continue

            # Delete items that were removed
            items_to_delete = set(existing_items.keys()) - processed_item_ids
            if items_to_delete:
                PurchaseOrderItem.objects.filter(id__in=items_to_delete).delete()

            # Update order totals
            order.subtotal = subtotal
            order.tax = subtotal * Decimal('0.1')
            order.total = subtotal + order.tax
            order.save()

            messages.success(request, f'Purchase Order {order.po_number} updated with {order.items.count()} items.')
            return redirect('vendors:purchase_order_detail', pk=order.pk)
    else:
        form = PurchaseOrderForm(instance=order)

    items = order.items.select_related('material').all()
    materials = Material.objects.filter(status='active')

    context = {
        'form': form,
        'order': order,
        'items': items,
        'materials': materials,
        'title': 'Edit Purchase Order',
    }

    return render(request, 'vendors/purchase_order_form.html', context)


@login_required
def add_po_item(request, po_id):
    """Add an item to a purchase order"""
    order = get_object_or_404(PurchaseOrder, pk=po_id)

    if request.method == 'POST':
        form = PurchaseOrderItemForm(request.POST)
        if form.is_valid():
            material = form.cleaned_data['material']
            quantity = int(form.cleaned_data['quantity'])
            unit_price = Decimal(str(form.cleaned_data['unit_price']))

            item = PurchaseOrderItem.objects.create(
                purchase_order=order,
                material=material,
                quantity=quantity,
                unit_price=unit_price
            )

            # Recalculate order totals
            all_items = order.items.all()
            subtotal = Decimal('0.00')
            for item in all_items:
                subtotal += item.quantity * item.unit_price

            order.subtotal = subtotal
            order.tax = subtotal * Decimal('0.1')
            order.total = subtotal + order.tax
            order.save()

            messages.success(request, 'Item added successfully!')
            return redirect('vendors:purchase_order_edit', pk=order.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseOrderItemForm()

    context = {
        'form': form,
        'order': order,
    }

    return render(request, 'vendors/po_item_form.html', context)


@login_required
def receive_purchase_order(request, pk):
    """Receive a purchase order and create inbound transaction"""
    order = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == 'POST':
        from transactions.models import Transaction, TransactionItem

        # Create inbound transaction
        transaction = Transaction.objects.create(
            transaction_type='inbound',
            reference_number=order.po_number,
            notes=f'Receiving PO: {order.po_number}',
            created_by=request.user,
            transaction_date=timezone.now()
        )

        # Process each item
        for item in order.items.all():
            material = item.material
            stock_before = material.current_stock
            material.current_stock += item.quantity
            material.save()

            TransactionItem.objects.create(
                transaction=transaction,
                material=material,
                quantity=item.quantity,
                unit_price=item.unit_price,
                stock_before=stock_before,
                stock_after=material.current_stock
            )

        # Update PO status
        order.status = 'delivered'
        order.save()

        messages.success(request,
                         f'PO {order.po_number} received! Transaction #{transaction.transaction_number} created.')
        return redirect('vendors:purchase_order_detail', pk=order.pk)

    items = order.items.select_related('material').all()

    context = {
        'order': order,
        'items': items,
    }

    return render(request, 'vendors/receive_po.html', context)