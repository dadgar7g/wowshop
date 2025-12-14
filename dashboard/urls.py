from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_home, name='home'),

    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/toggle-staff/', views.user_toggle_staff, name='user_toggle_staff'),

    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),

    # Offers
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/<int:pk>/', views.offer_detail, name='offer_detail'),
    path('offers/<int:pk>/update-status/', views.offer_update_status, name='offer_update_status'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Comments
    path('comments/shop/', views.shop_comment_list, name='shop_comment_list'),
    path('comments/shop/<int:pk>/toggle/', views.shop_comment_toggle, name='shop_comment_toggle'),
    path('comments/coach/', views.coach_comment_list, name='coach_comment_list'),
    path('comments/coach/<int:pk>/toggle/', views.coach_comment_toggle, name='coach_comment_toggle'),

    # Coaches
    path('coaches/', views.coach_list, name='coach_list'),
    path('coaches/<int:pk>/toggle/', views.coach_toggle, name='coach_toggle'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
]