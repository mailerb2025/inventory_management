from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.material_list, name='material_list'),
    path('material/<int:pk>/', views.material_detail, name='material_detail'),
    path('material/create/', views.material_create, name='material_create'),
    path('material/<int:pk>/update/', views.material_update, name='material_update'),
    path('material/<int:pk>/delete/', views.material_delete, name='material_delete'),
    path('categories/', views.category_list, name='category_list'),
    path('category/create/', views.category_create, name='category_create'),
    path('category/<int:pk>/update/', views.category_update, name='category_update'),
    path('category/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('alerts/', views.stock_alerts, name='stock_alerts'),

    # Export/Import URLs
    path('export/csv/', views.export_materials_csv, name='export_materials_csv'),
    path('export/excel/', views.export_materials_excel, name='export_materials_excel'),
    path('export/pdf/', views.export_materials_pdf, name='export_materials_pdf'),
    path('import/', views.import_materials, name='import_materials'),
    path('download-template/', views.download_import_template, name='download_import_template'),

    # AJAX endpoint for updating alert status
    path('api/update-alert-status/', views.update_alert_status, name='update_alert_status'),
]