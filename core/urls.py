from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('orders', views.OredersView.as_view(), name='orders'),
    path('orders/<int:id>', views.OredersDetailView.as_view(), name='order_detail'),
    path("coach/register/", views.CoachRegisterView.as_view(), name="coach_register"),
    path('fastsell/', views.FastSellView.as_view(), name='fast_sell'),
    path('fastsell/success/', views.FastSellSuccess.as_view(), name='fastsell_success'),
    path("coaches/edit/", views.CoachEditView.as_view(), name="coach_edit"),

    path("coaches/", views.CoachListView.as_view(), name="coach_list"),
    path("coaches/<user>", views.CoachDetailView.as_view(), name="coach_detail"),
    path("about/", views.AboutView.as_view(), name="about"),


    path('', views.HomeView.as_view(), name='home'),



]