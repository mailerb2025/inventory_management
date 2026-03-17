from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import csv
import pandas as pd
from io import BytesIO, TextIOWrapper
from django.http import HttpResponse
from django.template.loader import get_template
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from .models import Material, Category
from .forms import MaterialForm, CategoryForm
from transactions.models import StockAlert


# ========== MATERIAL VIEWS ==========

@login_required
def material_list(request):
    materials = Material.objects.select_related('category').all()

    search_query = request.GET.get('search', '')
    if search_query:
        materials = materials.filter(
            Q(material_code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    category_id = request.GET.get('category')
    if category_id:
        materials = materials.filter(category_id=category_id)

    stock_status = request.GET.get('stock_status')
    if stock_status:
        if stock_status == 'low':
            materials = materials.filter(current_stock__lte=F('reorder_point'))
        elif stock_status == 'normal':
            materials = materials.filter(
                current_stock__gt=F('reorder_point'),
                current_stock__lt=F('maximum_stock')
            )
        elif stock_status == 'excess':
            materials = materials.filter(current_stock__gte=F('maximum_stock'))

    paginator = Paginator(materials, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_status': stock_status,
    }
    return render(request, 'inventory/material_list.html', context)


@login_required
def material_detail(request, pk):
    material = get_object_or_404(Material.objects.select_related('category'), pk=pk)
    transactions = material.transactionitem_set.select_related('transaction').all()[:20]
    alerts = material.alerts.all()[:5]

    if material.maximum_stock > 0:
        stock_percentage = (material.current_stock / material.maximum_stock) * 100
    else:
        stock_percentage = 0

    context = {
        'material': material,
        'transactions': transactions,
        'alerts': alerts,
        'stock_percentage': stock_percentage,
    }
    return render(request, 'inventory/material_detail.html', context)


@login_required
def material_create(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.created_by = request.user
            material.save()
            messages.success(request, f'Material {material.name} created!')
            return redirect('inventory:material_detail', pk=material.pk)
    else:
        form = MaterialForm()
    return render(request, 'inventory/material_form.html', {'form': form, 'title': 'Create Material'})


@login_required
def material_update(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, f'Material {material.name} updated!')
            return redirect('inventory:material_detail', pk=material.pk)
    else:
        form = MaterialForm(instance=material)
    return render(request, 'inventory/material_form.html',
                  {'form': form, 'title': 'Update Material', 'material': material})


@login_required
def material_delete(request, pk):
    material = get_object_or_404(Material, pk=pk)
    if request.method == 'POST':
        material.delete()
        messages.success(request, f'Material {material.name} deleted!')
        return redirect('inventory:material_list')
    return render(request, 'inventory/material_confirm_delete.html', {'material': material})


# ========== CATEGORY VIEWS ==========

@login_required
def category_list(request):
    categories = Category.objects.annotate(material_count=Count('materials')).all()
    return render(request, 'inventory/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created!')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm()
    return render(request, 'inventory/category_form.html', {'form': form, 'title': 'Create Category'})


@login_required
def category_update(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated!')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'inventory/category_form.html',
                  {'form': form, 'title': 'Update Category', 'category': category})


@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted!')
        return redirect('inventory:category_list')
    return render(request, 'inventory/category_confirm_delete.html', {'category': category})


# ========== STOCK ALERT VIEWS ==========

@login_required
def stock_alerts(request):
    """View and manage stock alerts"""
    pending_alerts = StockAlert.objects.select_related('material__category').filter(
        status='pending'
    ).order_by('-alert_date')

    resolved_alerts = StockAlert.objects.select_related('material', 'resolved_by').filter(
        status='resolved'
    ).order_by('-resolved_date')[:50]

    acknowledged_alerts = StockAlert.objects.select_related('material', 'resolved_by').filter(
        status='acknowledged'
    ).order_by('-resolved_date')[:50]

    total_alerts = StockAlert.objects.count()
    pending_count = pending_alerts.count()
    resolved_count = StockAlert.objects.filter(status='resolved').count()
    acknowledged_count = StockAlert.objects.filter(status='acknowledged').count()

    if request.method == 'POST':
        action = request.POST.get('action')
        alert_ids = request.POST.getlist('alerts')
        single_alert = request.POST.get('single_alert')

        if single_alert:
            alert_ids = [single_alert]

        if not alert_ids:
            messages.warning(request, 'No alerts selected.')
            return redirect('inventory:stock_alerts')

        if action == 'acknowledge':
            count = StockAlert.objects.filter(id__in=alert_ids, status='pending').update(
                status='acknowledged',
                resolved_by=request.user,
                resolved_date=timezone.now(),
                notes='Acknowledged by user'
            )
            messages.success(request, f'{count} alert(s) acknowledged.')

        elif action == 'resolve':
            count = StockAlert.objects.filter(id__in=alert_ids, status='pending').update(
                status='resolved',
                resolved_by=request.user,
                resolved_date=timezone.now(),
                notes='Manually resolved'
            )
            messages.success(request, f'{count} alert(s) resolved.')

        elif action == 'resolve_all':
            count = pending_alerts.update(
                status='resolved',
                resolved_by=request.user,
                resolved_date=timezone.now(),
                notes='Bulk resolve'
            )
            messages.success(request, f'{count} alert(s) resolved.')

        return redirect('inventory:stock_alerts')

    context = {
        'pending_alerts': pending_alerts,
        'resolved_alerts': resolved_alerts,
        'acknowledged_alerts': acknowledged_alerts,
        'total_alerts': total_alerts,
        'pending_count': pending_count,
        'resolved_count': resolved_count,
        'acknowledged_count': acknowledged_count,
        'now': timezone.now(),
    }

    return render(request, 'inventory/stock_alerts.html', context)


# ========== EXPORT/IMPORT VIEWS ==========

@login_required
def export_materials_csv(request):
    """Export materials to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="materials_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Material Code', 'Name', 'Category', 'Description', 'Unit',
                     'Specification', 'Current Stock', 'Min Stock', 'Max Stock',
                     'Reorder Point', 'Location', 'Unit Cost', 'Status'])

    materials = Material.objects.select_related('category').all()
    for material in materials:
        writer.writerow([
            material.material_code,
            material.name,
            material.category.name,
            material.description or '',
            material.unit,
            material.specification or '',
            material.current_stock,
            material.minimum_stock,
            material.maximum_stock,
            material.reorder_point,
            material.location or '',
            float(material.unit_cost),
            material.status
        ])

    return response


@login_required
def export_materials_excel(request):
    """Export materials to Excel"""
    materials = Material.objects.select_related('category').all().values(
        'material_code', 'name', 'category__name', 'description', 'unit',
        'specification', 'current_stock', 'minimum_stock', 'maximum_stock',
        'reorder_point', 'location', 'unit_cost', 'status'
    )

    df = pd.DataFrame(list(materials))
    df.columns = ['Material Code', 'Name', 'Category', 'Description', 'Unit',
                  'Specification', 'Current Stock', 'Min Stock', 'Max Stock',
                  'Reorder Point', 'Location', 'Unit Cost', 'Status']

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Materials', index=False)

        worksheet = writer.sheets['Materials']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response[
        'Content-Disposition'] = f'attachment; filename="materials_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'

    return response


@login_required
def export_materials_pdf(request):
    """Export materials to PDF"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="materials_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))
    elements = []

    styles = getSampleStyleSheet()
    title = Paragraph(f"Materials Inventory Report - {timezone.now().strftime('%Y-%m-%d %H:%M')}",
                      styles['Title'])
    elements.append(title)
    elements.append(Paragraph("<br/>", styles['Normal']))

    data = [['Code', 'Name', 'Category', 'Unit', 'Stock', 'Min', 'Max', 'Reorder', 'Location', 'Cost']]

    materials = Material.objects.select_related('category').all()[:50]
    for material in materials:
        data.append([
            material.material_code,
            material.name[:20] + '...' if len(material.name) > 20 else material.name,
            material.category.name[:15] if material.category.name else '',
            material.unit,
            str(material.current_stock),
            str(material.minimum_stock),
            str(material.maximum_stock),
            str(material.reorder_point),
            material.location or '',
            f"${material.unit_cost:.2f}"
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    return response


@login_required
def download_import_template(request):
    """Download template CSV for importing materials"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="material_import_template.csv"'

    writer = csv.writer(response)
    writer.writerow(['material_code', 'name', 'category_name', 'description', 'unit',
                     'specification', 'current_stock', 'minimum_stock', 'maximum_stock',
                     'reorder_point', 'location', 'unit_cost', 'status'])

    writer.writerow(['M001', 'Sample Material', 'Electronics', 'Sample description', 'pcs',
                     '5x5cm', '100', '10', '500', '20', 'A-01-01', '25.50', 'active'])

    return response


@login_required
def import_materials(request):
    """Import materials from CSV file"""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']

        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'Please upload a CSV file.')
            return redirect('inventory:material_list')

        try:
            data = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(data)

            success_count = 0
            error_count = 0
            errors = []

            for row_num, row in enumerate(reader, start=2):
                try:
                    category_name = row.get('category_name', '').strip()
                    if not category_name:
                        errors.append(f"Row {row_num}: Category name is required")
                        error_count += 1
                        continue

                    category, _ = Category.objects.get_or_create(name=category_name)

                    material_data = {
                        'material_code': row.get('material_code', '').strip(),
                        'name': row.get('name', '').strip(),
                        'category': category,
                        'description': row.get('description', '').strip(),
                        'unit': row.get('unit', '').strip(),
                        'specification': row.get('specification', '').strip(),
                        'current_stock': int(row.get('current_stock', 0)),
                        'minimum_stock': int(row.get('minimum_stock', 10)),
                        'maximum_stock': int(row.get('maximum_stock', 1000)),
                        'reorder_point': int(row.get('reorder_point', 20)),
                        'location': row.get('location', '').strip(),
                        'unit_cost': float(row.get('unit_cost', 0)),
                        'status': row.get('status', 'active').strip(),
                        'created_by': request.user
                    }

                    material_code = material_data['material_code']
                    if not material_code:
                        errors.append(f"Row {row_num}: Material code is required")
                        error_count += 1
                        continue

                    material, created = Material.objects.update_or_create(
                        material_code=material_code,
                        defaults=material_data
                    )

                    if created:
                        success_count += 1
                    else:
                        success_count += 1

                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1

            if success_count > 0:
                messages.success(request, f'Successfully imported {success_count} materials.')
            if error_count > 0:
                messages.warning(request, f'Failed to import {error_count} materials. Check errors below.')
                request.session['import_errors'] = errors

            return redirect('inventory:material_list')

        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('inventory:material_list')

    return render(request, 'inventory/material_import.html')


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

        material.alert_status_override = status if status else None
        material.save()

        if material.alert_status_override:
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
            'has_override': material.has_override() if hasattr(material, 'has_override') else bool(
                material.alert_status_override)
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