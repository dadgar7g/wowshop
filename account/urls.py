from django.urls import path
from . import views
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.urls import path
app_name = 'account'

urlpatterns = [
    path('signup', views.SignUpView.as_view(), name='signup'),
    path('activate/<uid>/<hash>/', views.ActivateView.as_view(), name='activate'),
    path('activate/resendemail/', views.ReSendEmailView.as_view(), name='resend_email'),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/edit/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("my_offers/", views.MyOffersView.as_view(), name="offers"),
    path("my_invoices/", views.MyInvoiceView.as_view(), name="my_invoices"),
    path('bank/edit/', views.BankAccountEditView.as_view(), name='bank_edit'),
]
