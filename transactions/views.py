from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from django.core.exceptions import FieldError  # Fix: Import from core.exceptions
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from datetime import timedelta
import json
from .models import Transaction, TransactionItem, StockAlert
from inventory.models import Material
from .forms import TransactionForm, TransactionItemForm


# ========== TRANSACTION LIST VIEWS ==========

@login_required
def transaction_list(request):
    """List all transactions with stock alert information"""
    transactions = Transaction.objects.prefetch_related('items__material').all().order_by('-transaction_date')

    # Get all materials with their alert status for quick lookup
    try:
        materials = Material.objects.all().values(
            'id', 'current_stock', 'minimum_stock',
            'maximum_stock', 'reorder_point',
            'alert_status_override'
        )
    except FieldError:
        # If alert_status_override field doesn't exist, get without it
        materials = Material.objects.all().values(
            'id', 'current_stock', 'minimum_stock',
            'maximum_stock', 'reorder_point'
        )
        for material in materials:
            material['alert_status_override'] = None

    material_alerts = {}
    for material in materials:
        alert_override = material.get('alert_status_override')
        if alert_override:
            status = alert_override
        else:
            if material['current_stock'] <= material['minimum_stock']:
                status = 'low'
            elif material['current_stock'] >= material['maximum_stock']:
                status = 'excess'
            else:
                status = 'normal'

        status_map = {
            'low': {'name': 'Low Stock', 'color': 'danger'},
            'normal': {'name': 'Normal', 'color': 'success'},
            'excess': {'name': 'Excess', 'color': 'warning'}
        }

        material_alerts[material['id']] = {
            'status': status,
            'status_display': status_map[status]['name'],
            'status_color': status_map[status]['color'],
            'current_stock': material['current_stock'],
            'min_stock': material['minimum_stock'],
            'max_stock': material['maximum_stock'],
            'has_override': bool(material.get('alert_status_override'))
        }

    transaction_type = request.GET.get('type')
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)

    search_query = request.GET.get('search', '')
    if search_query:
        transactions = transactions.filter(
            Q(transaction_number__icontains=search_query) |
            Q(reference_number__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        transactions = transactions.filter(transaction_date__date__gte=date_from)
    if date_to:
        transactions = transactions.filter(transaction_date__date__lte=date_to)

    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'transaction_type': transaction_type,
        'date_from': date_from,
        'date_to': date_to,
        'material_alerts': material_alerts,
    }

    return render(request, 'transactions/transaction_list.html', context)


@login_required
def inbound_list(request):
    """List inbound transactions"""
    transactions = Transaction.objects.filter(transaction_type='inbound').order_by('-transaction_date')

    try:
        materials = Material.objects.all().values(
            'id', 'current_stock', 'minimum_stock',
            'maximum_stock', 'alert_status_override'
        )
    except FieldError:
        materials = Material.objects.all().values(
            'id', 'current_stock', 'minimum_stock',
            'maximum_stock'
        )
        for material in materials:
            material['alert_status_override'] = None

    material_alerts = {}
    for material in materials:
        if material.get('alert_status_override'):
            status = material['alert_status_override']
        else:
            if material['current_stock'] <= material['minimum_stock']:
                status = 'low'
            elif material['current_stock'] >= material['maximum_stock']:
                status = 'excess'
            else:
                status = 'normal'

        status_map = {
            'low': {'name': 'Low Stock', 'color': 'danger'},
            'normal': {'name': 'Normal', 'color': 'success'},
            'excess': {'name': 'Excess', 'color': 'warning'}
        }

        material_alerts[material['id']] = {
            'status': status,
            'status_display': status_map[status]['name'],
            'status_color': status_map[status]['color'],
            'has_override': bool(material.get('alert_status_override'))
        }

    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'transactions/inbound_list.html', {
        'page_obj': page_obj,
        'material_alerts': material_alerts
    })


@login_required
def outbound_list(request):
    """List outbound transactions"""
    transactions = Transaction.objects.filter(transaction_type='outbound').order_by('-transaction_date')

    try:
        materials = Material.objects.all().values(
            'id', 'current_stock', 'minimum_stock',
            'maximum_stock', 'alert_status_override'
        )
    except FieldError:
        materials = Material.objects.all().values(
            'id', 'current_stock', 'minimum_stock',
            'maximum_stock'
        )
        for material in materials:
            material['alert_status_override'] = None

    material_alerts = {}
    for material in materials:
        if material.get('alert_status_override'):
            status = material['alert_status_override']
        else:
            if material['current_stock'] <= material['minimum_stock']:
                status = 'low'
            elif material['current_stock'] >= material['maximum_stock']:
                status = 'excess'
            else:
                status = 'normal'

        status_map = {
            'low': {'name': 'Low Stock', 'color': 'danger'},
            'normal': {'name': 'Normal', 'color': 'success'},
            'excess': {'name': 'Excess', 'color': 'warning'}
        }

        material_alerts[material['id']] = {
            'status': status,
            'status_display': status_map[status]['name'],
            'status_color': status_map[status]['color'],
            'has_override': bool(material.get('alert_status_override'))
        }

    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'transactions/outbound_list.html', {
        'page_obj': page_obj,
        'material_alerts': material_alerts
    })


# ========== TRANSACTION DETAIL AND CRUD VIEWS ==========

@login_required
def transaction_detail(request, pk):
    """View transaction details with material alert status"""
    transaction = get_object_or_404(Transaction, pk=pk)
    items = transaction.items.select_related('material').all()

    material_alerts = {}
    for item in items:
        material = item.material
        if material.id not in material_alerts:
            if hasattr(material, 'alert_status_override') and material.alert_status_override:
                status = material.alert_status_override
            else:
                if material.current_stock <= material.minimum_stock:
                    status = 'low'
                elif material.current_stock >= material.maximum_stock:
                    status = 'excess'
                else:
                    status = 'normal'

            status_map = {
                'low': {'name': 'Low Stock', 'color': 'danger'},
                'normal': {'name': 'Normal', 'color': 'success'},
                'excess': {'name': 'Excess', 'color': 'warning'}
            }

            material_alerts[material.id] = {
                'status': status,
                'status_display': status_map[status]['name'],
                'status_color': status_map[status]['color'],
                'current_stock': material.current_stock,
                'min_stock': material.minimum_stock,
                'max_stock': material.maximum_stock,
                'has_override': hasattr(material, 'alert_status_override') and bool(material.alert_status_override),
                'name': material.name,
                'code': material.material_code
            }

    context = {
        'transaction': transaction,
        'items': items,
        'material_alerts': material_alerts,
    }

    return render(request, 'transactions/transaction_detail.html', context)


@login_required
def transaction_create(request):
    """Create a new transaction"""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            messages.success(request, 'Transaction created successfully. Now you can add items.')
            return redirect('transactions:transaction_edit', pk=transaction.pk)
    else:
        form = TransactionForm()

    return render(request, 'transactions/transaction_form.html', {
        'form': form,
        'title': 'Create Transaction'
    })


@login_required
def transaction_edit(request, pk):
    """Edit a transaction"""
    transaction = get_object_or_404(Transaction, pk=pk)
    items = transaction.items.select_related('material').all()

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('transactions:transaction_detail', pk=transaction.pk)
    else:
        form = TransactionForm(instance=transaction)

    context = {
        'form': form,
        'transaction': transaction,
        'items': items,
        'title': 'Edit Transaction',
    }

    return render(request, 'transactions/transaction_form.html', context)


@login_required
def reverse_transaction(request, pk):
    """Reverse a transaction and restore stock levels"""
    transaction = get_object_or_404(Transaction, pk=pk)

    if transaction.transaction_type == 'adjustment':
        messages.error(request, 'Adjustment transactions cannot be reversed.')
        return redirect('transactions:transaction_detail', pk=transaction.pk)

    if request.method == 'POST':
        reverse_type = 'outbound' if transaction.transaction_type == 'inbound' else 'inbound'

        reverse_trans = Transaction.objects.create(
            transaction_type=reverse_type,
            reference_number=f"REV-{transaction.transaction_number}",
            transaction_date=timezone.now(),
            notes=f"Reversal of {transaction.transaction_number}",
            created_by=request.user
        )

        for item in transaction.items.all():
            material = item.material
            stock_before = material.current_stock

            if transaction.transaction_type == 'inbound':
                material.current_stock -= item.quantity
            else:
                material.current_stock += item.quantity

            material.save()

            TransactionItem.objects.create(
                transaction=reverse_trans,
                material=material,
                quantity=item.quantity,
                unit_price=item.unit_price,
                stock_before=stock_before,
                stock_after=material.current_stock
            )

        messages.success(request, f'Transaction {transaction.transaction_number} reversed successfully.')
        return redirect('transactions:transaction_detail', pk=reverse_trans.pk)

    context = {
        'transaction': transaction,
        'items': transaction.items.all(),
    }

    return render(request, 'transactions/reverse_confirm.html', context)


# ========== TRANSACTION ITEM VIEWS ==========

@login_required
def add_transaction_item(request, transaction_id):
    """Add an item to a transaction with type-specific behavior"""
    transaction = get_object_or_404(Transaction, pk=transaction_id)

    materials = Material.objects.filter(status='active').values(
        'id', 'name', 'current_stock', 'unit', 'unit_cost', 'minimum_stock',
        'maximum_stock', 'reorder_point'
    )

    materials_list = []
    for material in materials:
        material_dict = dict(material)
        if 'unit_cost' in material_dict and material_dict['unit_cost'] is not None:
            material_dict['unit_cost'] = float(material_dict['unit_cost'])
        materials_list.append(material_dict)

    stock_data = json.dumps(materials_list)

    if request.method == 'POST':
        form = TransactionItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.transaction = transaction

            material = item.material
            item.stock_before = material.current_stock

            if transaction.transaction_type in ['inbound', 'return']:
                material.current_stock += item.quantity

            elif transaction.transaction_type in ['outbound', 'transfer']:
                if material.current_stock < item.quantity:
                    messages.error(
                        request,
                        f'Insufficient stock for {material.name}. '
                        f'Available: {material.current_stock} {material.unit}'
                    )
                    return redirect('transactions:add_transaction_item',
                                    transaction_id=transaction.pk)

                if float(item.unit_price) != float(material.unit_cost):
                    item.unit_price = material.unit_cost

                material.current_stock -= item.quantity

            material.save()
            item.stock_after = material.current_stock
            item.save()

            if material.current_stock <= material.reorder_point:
                StockAlert.objects.create(
                    material=material,
                    current_stock=material.current_stock,
                    reorder_point=material.reorder_point,
                    notes=f'Stock level after {transaction.transaction_type} transaction'
                )

            messages.success(
                request,
                f'Item {material.name} added successfully! '
                f'New stock: {material.current_stock} {material.unit}'
            )
            return redirect('transactions:transaction_edit', pk=transaction.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TransactionItemForm()

    context = {
        'form': form,
        'transaction': transaction,
        'stock_data': stock_data,
    }

    return render(request, 'transactions/transaction_item_form.html', context)


@login_required
def delete_transaction_item(request, item_id):
    """Delete a transaction item and reverse stock changes"""
    item = get_object_or_404(TransactionItem, pk=item_id)
    transaction = item.transaction

    if request.method == 'POST':
        material = item.material
        if transaction.transaction_type in ['inbound', 'return']:
            material.current_stock -= item.quantity
        elif transaction.transaction_type in ['outbound', 'transfer']:
            material.current_stock += item.quantity

        material.save()
        material_name = material.name
        item.delete()

        messages.success(request, f'Item {material_name} deleted successfully. Stock has been adjusted.')
        return redirect('transactions:transaction_edit', pk=transaction.pk)

    return redirect('transactions:transaction_edit', pk=transaction.pk)


# ========== AJAX ENDPOINT FOR UPDATING ALERT STATUS ==========

@login_required
@require_POST
def update_alert_status(request):
    """AJAX endpoint to update material alert status"""
    try:
        data = json.loads(request.body)
        material_id = data.get('material_id')
        status = data.get('status')

        material = get_object_or_404(Material, id=material_id)

        valid_statuses = ['normal', 'low', 'excess', '']
        if status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'error': 'Invalid status value'
            }, status=400)

        # Check if the field exists
        if hasattr(material, 'alert_status_override'):
            material.alert_status_override = status if status else None
            material.save()

        if hasattr(material, 'alert_status_override') and material.alert_status_override:
            display_status = material.alert_status_override
        else:
            if material.current_stock <= material.minimum_stock:
                display_status = 'low'
            elif material.current_stock >= material.maximum_stock:
                display_status = 'excess'
            else:
                display_status = 'normal'

        status_map = {
            'low': {'name': 'Low Stock', 'color': 'danger'},
            'normal': {'name': 'Normal', 'color': 'success'},
            'excess': {'name': 'Excess', 'color': 'warning'}
        }

        return JsonResponse({
            'success': True,
            'material_id': material.id,
            'new_status': display_status,
            'status_display': status_map[display_status]['name'],
            'status_color': status_map[display_status]['color'],
            'has_override': hasattr(material, 'alert_status_override') and bool(material.alert_status_override)
        })

    except Material.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Material not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)