from django.urls import path
from . import views

app_name = 'shop'
urlpatterns = [
    path('', views.ListProducts.as_view(), name='product_list'),
    path('product/<int:id>', views.ProductDetailView.as_view(), name='product_detail'),
    path('cart/add/<int:id>', views.AddToCartView.as_view(), name='cart_add'),
    path('cart/remove/<int:id>', views.RemoveFromCartView.as_view(), name='cart_remove'),
    path('cart/empty', views.EmptyCartView.as_view(), name='cart_empty'),
    path('cart/', views.ShowCartView.as_view(), name='cart_show'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('verify/', views.VerifyView.as_view(), name='verify'),
    path('cart/decrease/<int:id>', views.DecreaseFromCartView.as_view(), name='cart_decrease'),


#     path('testjson', views.Test.as_view(), name='testjson'),
#     path('ajaxtestpage', views.AjaxTestPage.as_view(),),
]