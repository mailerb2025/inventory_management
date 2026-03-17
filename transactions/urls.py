from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    # List views
    path('', views.transaction_list, name='transaction_list'),
    path('inbound/', views.inbound_list, name='inbound_list'),
    path('outbound/', views.outbound_list, name='outbound_list'),

    # Transaction CRUD
    path('transaction/create/', views.transaction_create, name='transaction_create'),
    path('transaction/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    path('transaction/<int:pk>/edit/', views.transaction_edit, name='transaction_edit'),
    path('transaction/<int:pk>/reverse/', views.reverse_transaction, name='reverse_transaction'),

    # Transaction items
    path('transaction/<int:transaction_id>/add-item/', views.add_transaction_item, name='add_transaction_item'),
    path('item/<int:item_id>/delete/', views.delete_transaction_item, name='delete_transaction_item'),

    # AJAX endpoint for updating alert status
    path('api/update-alert-status/', views.update_alert_status, name='update_alert_status'),
]