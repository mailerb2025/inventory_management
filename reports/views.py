from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta, datetime
import pandas as pd
import json
from io import BytesIO
import csv
from django.http import HttpResponse
from inventory.models import Material, Category
from transactions.models import Transaction, TransactionItem


@login_required
def inventory_report(request):
    """Render inventory status report"""
    total_materials = Material.objects.count()
    total_value = Material.objects.aggregate(total=Sum(F('current_stock') * F('unit_cost')))['total'] or 0
    low_stock = Material.objects.filter(current_stock__lte=F('reorder_point')).count()
    excess_stock = Material.objects.filter(current_stock__gte=F('maximum_stock')).count()

    normal_stock = Material.objects.filter(
        current_stock__gt=F('reorder_point'),
        current_stock__lt=F('maximum_stock')
    ).count()

    categories = Category.objects.annotate(
        material_count=Count('materials'),
        total_stock=Sum('materials__current_stock'),
        total_value=Sum(F('materials__current_stock') * F('materials__unit_cost'))
    ).filter(material_count__gt=0)

    recent_alerts = Material.objects.filter(
        current_stock__lte=F('reorder_point')
    ).select_related('category')[:10]

    context = {
        'report_date': timezone.now(),
        'total_materials': total_materials,
        'total_value': total_value,
        'low_stock': low_stock,
        'excess_stock': excess_stock,
        'normal_stock': normal_stock,
        'categories': categories,
        'recent_alerts': recent_alerts,
    }

    return render(request, 'reports/inventory_report.html', context)


@login_required
def transaction_report(request):
    """Render transaction/flow report"""
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    date_from = request.GET.get('date_from', start_date.strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', end_date.strftime('%Y-%m-%d'))

    transactions = Transaction.objects.filter(
        transaction_date__date__gte=date_from,
        transaction_date__date__lte=date_to
    ).prefetch_related('items').order_by('-transaction_date')

    inbound_total = transactions.filter(transaction_type='inbound').aggregate(
        total=Sum('items__quantity')
    )['total'] or 0

    outbound_total = transactions.filter(transaction_type='outbound').aggregate(
        total=Sum('items__quantity')
    )['total'] or 0

    daily_data = []
    current_date = datetime.strptime(date_from, '%Y-%m-%d').date()
    end = datetime.strptime(date_to, '%Y-%m-%d').date()

    while current_date <= end:
        day_inbound = transactions.filter(
            transaction_date__date=current_date,
            transaction_type='inbound'
        ).aggregate(total=Sum('items__quantity'))['total'] or 0

        day_outbound = transactions.filter(
            transaction_date__date=current_date,
            transaction_type='outbound'
        ).aggregate(total=Sum('items__quantity'))['total'] or 0

        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'inbound': day_inbound,
            'outbound': day_outbound
        })
        current_date += timedelta(days=1)

    context = {
        'date_from': date_from,
        'date_to': date_to,
        'transactions': transactions,
        'inbound_total': inbound_total,
        'outbound_total': outbound_total,
        'net_change': inbound_total - outbound_total,
        'total_transactions': transactions.count(),
        'daily_data': json.dumps(daily_data),
    }

    return render(request, 'reports/transaction_report.html', context)


@login_required
def export_report_excel(request, report_type):
    """Export report as Excel file"""
    if report_type == 'inventory':
        materials = Material.objects.select_related('category').all().values(
            'material_code', 'name', 'category__name', 'unit', 'current_stock',
            'minimum_stock', 'maximum_stock', 'reorder_point', 'location',
            'unit_cost'
        )
        df = pd.DataFrame(list(materials))
        df.columns = ['Material Code', 'Material Name', 'Category', 'Unit',
                      'Current Stock', 'Min Stock', 'Max Stock', 'Reorder Point',
                      'Location', 'Unit Cost']
        filename = f'inventory_report_{timezone.now().strftime("%Y%m%d")}.xlsx'

    elif report_type == 'transactions':
        transactions = Transaction.objects.prefetch_related('items').all().values(
            'transaction_number', 'transaction_type', 'reference_number',
            'transaction_date', 'notes', 'created_by__username'
        )[:1000]

        trans_list = list(transactions)
        for item in trans_list:
            if 'transaction_date' in item and item['transaction_date']:
                item['transaction_date'] = item['transaction_date'].replace(tzinfo=None)

        df = pd.DataFrame(trans_list)
        df.columns = ['Transaction #', 'Type', 'Reference', 'Date', 'Notes', 'Created By']
        filename = f'transactions_report_{timezone.now().strftime("%Y%m%d")}.xlsx'
    else:
        return HttpResponse("Invalid report type", status=400)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Report', index=False)

    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename={filename}'

    return response


@login_required
def export_report_csv(request, report_type):
    """Export report as CSV file"""
    response = HttpResponse(content_type='text/csv')
    response[
        'Content-Disposition'] = f'attachment; filename="{report_type}_report_{timezone.now().strftime("%Y%m%d")}.csv"'

    writer = csv.writer(response)

    if report_type == 'inventory':
        writer.writerow(['Material Code', 'Material Name', 'Category', 'Unit',
                         'Current Stock', 'Min Stock', 'Max Stock', 'Reorder Point',
                         'Location', 'Unit Cost'])

        for material in Material.objects.select_related('category').all():
            writer.writerow([
                material.material_code,
                material.name,
                material.category.name,
                material.unit,
                material.current_stock,
                material.minimum_stock,
                material.maximum_stock,
                material.reorder_point,
                material.location or '',
                float(material.unit_cost)
            ])

    elif report_type == 'transactions':
        writer.writerow(['Transaction #', 'Type', 'Reference', 'Date', 'Notes', 'Created By'])

        for trans in Transaction.objects.all()[:1000]:
            writer.writerow([
                trans.transaction_number,
                trans.transaction_type,
                trans.reference_number or '',
                trans.transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                trans.notes or '',
                trans.created_by.username if trans.created_by else 'System'
            ])

    return response