from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard Home
    path('', views.dashboard_home, name='home'),

    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/toggle-staff/', views.user_toggle_staff, name='user_toggle_staff'),

    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<int:pk>/edit/', views.order_edit, name='order_edit'),
    path('orders/<int:pk>/delete/', views.order_delete, name='order_delete'),

    # Offers
    path('offers/', views.offer_list, name='offer_list'),
    path('offers/<int:pk>/', views.offer_detail, name='offer_detail'),
    path('offers/<int:pk>/update-status/', views.offer_update_status, name='offer_update_status'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),

    #Fastsell
    path('fastsell/', views.fastsell_list, name='fastsell_list'),
    path('fastsell/<int:pk>/', views.fastsell_detail, name='fastsell_detail'),
    # *** مسیر جدید برای به‌روزرسانی وضعیت ***
    path('fastsell/<int:pk>/toggle-read/', views.fastsell_toggle_read, name='fastsell_toggle_read'),

    # Comments
    path('comments/shop/', views.shop_comment_list, name='shop_comment_list'),
    path('comments/shop/<int:pk>/toggle/', views.shop_comment_toggle, name='shop_comment_toggle'),
    path('comments/coach/', views.coach_comment_list, name='coach_comment_list'),
    path('comments/coach/<int:pk>/toggle/', views.coach_comment_toggle, name='coach_comment_toggle'),

    # Coaches
    path('coaches/', views.coach_list, name='coach_list'),
    path('coaches/<int:pk>/', views.coach_detail, name='coach_detail'),
    path('coaches/create/', views.coach_create, name='coach_create'),
    path('coaches/<int:pk>/edit/', views.coach_edit, name='coach_edit'),
    path('coaches/<int:pk>/delete/', views.coach_delete, name='coach_delete'),
    path('coaches/<int:pk>/toggle/', views.coach_toggle, name='coach_toggle'),

    # ============ EXPANSION, REALM, METHOD ============
    # Expansions
    path('expansions/', views.expansion_list, name='expansion_list'),
    path('expansions/create/', views.expansion_create, name='expansion_create'),
    path('expansions/<int:pk>/edit/', views.expansion_edit, name='expansion_edit'),
    path('expansions/<int:pk>/delete/', views.expansion_delete, name='expansion_delete'),

    # Realms
    path('realms/', views.realm_list, name='realm_list'),
    path('realms/create/', views.realm_create, name='realm_create'),
    path('realms/<int:pk>/edit/', views.realm_edit, name='realm_edit'),
    path('realms/<int:pk>/delete/', views.realm_delete, name='realm_delete'),

    # Methods
    path('methods/', views.method_list, name='method_list'),
    path('methods/create/', views.method_create, name='method_create'),
    path('methods/<int:pk>/edit/', views.method_edit, name='method_edit'),
    path('methods/<int:pk>/delete/', views.method_delete, name='method_delete'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]