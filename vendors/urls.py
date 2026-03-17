from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    # Vendor URLs
    path('', views.vendor_list, name='vendor_list'),
    path('vendor/<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('vendor/create/', views.vendor_create, name='vendor_create'),
    path('vendor/<int:pk>/update/', views.vendor_update, name='vendor_update'),
    path('vendor/<int:pk>/delete/', views.vendor_delete, name='vendor_delete'),

    # Purchase Order URLs
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-order/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-order/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-order/<int:pk>/edit/', views.purchase_order_edit, name='purchase_order_edit'),
    path('purchase-order/<int:po_id>/add-item/', views.add_po_item, name='add_po_item'),
    path('purchase-order/<int:pk>/receive/', views.receive_purchase_order, name='receive_po'),
]