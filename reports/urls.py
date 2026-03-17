from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('transactions/', views.transaction_report, name='transaction_report'),
    path('export/<str:report_type>/', views.export_report_excel, name='export_report'),
    path('export-csv/<str:report_type>/', views.export_report_csv, name='export_report_csv'),
]