from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('', views.dashboard, name='home'),

    # API endpoints
    path('api/chart-data/', views.get_chart_data, name='chart_data'),

    # User Management
    path('users/', views.user_list, name='user_list'),
    path('user/<int:pk>/', views.user_detail, name='user_detail'),
    path('user/create/', views.user_create, name='user_create'),
    path('user/<int:pk>/update/', views.user_update, name='user_update'),
    path('user/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('user/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('user/<int:pk>/reset-password/', views.admin_reset_password, name='admin_reset_password'),

    # Role Management
    path('roles/', views.role_list, name='role_list'),
    path('role/create/', views.role_create, name='role_create'),
    path('role/<int:pk>/update/', views.role_update, name='role_update'),
    path('role/<int:pk>/delete/', views.role_delete, name='role_delete'),
]