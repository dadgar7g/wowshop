from . import forms
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_str, force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from . import models
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from shop.models import Invoice
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import PasswordChangeForm




# Create your views here.

class RedirectAuthenticatedUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + str(timestamp) + "0"


activation_token_generator = TokenGenerator()


@method_decorator(login_required, name="dispatch")
class MyOffersView(View):
    def get(self, request):
        offers_list = request.user.offers.all().order_by('-created_at')
        return render(request, "account/my_offers.html", {"offers": offers_list})


class SignUpView(RedirectAuthenticatedUserMixin, View):
    def get(self, request):
        form = forms.SignUpForm()
        return render(request, 'account/signup.html', {'form':form})

    def post(self, request):
        email = request.POST.get('email')
        user = models.User.objects.filter(email=email, is_active=False).first()
        if user and timezone.now() - user.date_joined < timedelta(minutes=5):
            messages.error(
                request,
                "شما اخیرا ثبت نام کرده‌اید، لطفاً ایمیل خود را چک کرده و ثبت نام را نهایی کنید"
            )
            return redirect('account:signup')
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            # obj = form.save()
            obj = form.save(commit=False)
            obj.is_active = False
            obj.save()

            uid = urlsafe_base64_encode(force_bytes(obj.pk))
            hash = activation_token_generator.make_token(obj)
            domain = get_current_site(request)
            url = reverse('account:activate', kwargs= {'uid':uid, 'hash':hash})
            protocol = 'https' if request.is_secure() else 'http'
            link = f"{protocol}://{domain}{url}"
            subject = 'Please activate your account'
            body = render_to_string('account/signup_email.html',{
                                                 'obj':obj,
                                                 'link':link,})
            to = obj.email
            email = EmailMessage(subject, body, 'alireza.sayfaei@gmail.com', [to])
            email.content_subtype = "html"
            try:
                email.send()
            except Exception:
                obj.delete()
                form.add_error(None, 'خطا در ارسال ایمیل؛ لطفاً دوباره تلاش کنید.')
                return render(request, 'account/signup.html', {'form': form})

            return render(request, 'account/signup_done.html', {'obj':obj})
        return render(request, 'account/signup.html', {'form':form})


class ActivateView(RedirectAuthenticatedUserMixin, View):
    def get(self, request, uid, hash):
        try:
            id = force_str(urlsafe_base64_decode(uid))
        except (TypeError, ValueError, OverflowError):
            return render(request, 'account/activate_error.html',  {'message': 'کاربر پیدا نشد.'})

        # user = get_object_or_404(models.User, idk=id)
        try:
            user = models.User.objects.get(id=id)
            if user.is_active:
                return render(request, 'account/activate_error.html',  {'message': 'کاربر قبلا حساب خود را فعال کرده است.'})
        except models.User.DoesNotExist:
            return render(request, 'account/activate_error.html', {'message': 'کاربر پیدا نشد'} )

        if activation_token_generator.check_token(user, hash):
            user.is_active = True
            user.save()
            return render(request, 'account/activate_done.html')
        return render(request, 'account/activate_error.html', )



class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "account/dashboard.html")


@method_decorator(login_required, name="dispatch")
class ProfileView(View):
    def get(self, request):
        return render(request, "account/profile.html")


@method_decorator(login_required, name="dispatch")
class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request):
        form = forms.EditProfileForm(user=request.user, instance=request.user)
        return render(request, "account/profile_edit.html", {"form": form})

    def post(self, request):
        form = forms.EditProfileForm(request.POST, user=request.user, instance=request.user)

        if form.is_valid():
            user = form.save()


            discord_id = form.cleaned_data.get("discord_id")
            request.user.discord_id = discord_id
            request.user.save()


            return redirect("account:dashboard")

        return render(request, "account/profile_edit.html", {"form": form})



@method_decorator(login_required, name="dispatch")
class OffersView(View):
    def get(self, request):
        offers_list = getattr(request.user, "offers", []).all() if hasattr(request.user, "offers") else []
        return render(request, "account/offers.html", {"offers": offers_list})




class MyPasswordChangeForm(PasswordChangeForm):
    error_messages = {
        'password_mismatch': "رمز عبور جدید با تکرار آن مطابقت ندارد",
        'password_incorrect': "رمز عبور فعلی اشتباه است",
    }
# -----------------------------
@method_decorator(login_required, name="dispatch")
class PasswordChangeView(View):

    def get(self, request):
        form = MyPasswordChangeForm(request.user)
        return render(request, "registration/password_change_form.html", {"form": form})

    def post(self, request):
        form = MyPasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # prevents logout after password change
            return redirect("account:dashboard")

        return render(request, "registration/password_change_form.html", {"form": form})


@method_decorator(login_required, name="dispatch")
class BankAccountEditView(LoginRequiredMixin, View):
    def get(self, request):
        # بررسی وجود اطلاعات قبلی
        try:
            bank_account = models.BankAccount.objects.get(user=request.user)
        except models.BankAccount.DoesNotExist:
            bank_account = None

        form = forms.BankAccountForm(instance=bank_account)
        return render(request, 'account/bank_edit.html', {'form': form})

    def post(self, request):
        try:
            bank_account = models.BankAccount.objects.get(user=request.user)
        except models.BankAccount.DoesNotExist:
            bank_account = None

        form = forms.BankAccountForm(request.POST, instance=bank_account)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            return redirect('account:dashboard')


        return render(request, 'account/bank_edit.html', {'form': form})



# class SignUpView(View):
#     def get(self, request):
#         form = forms.SignUpForm()
#         return render(request, 'account/signup.html', {'form':form})
#
#     def post(self, request):
#         # print(request.POST.get('name'))
#         form = forms.SignUpForm(request.POST)
#         if form.is_valid():
#             print(form.cleaned_data['email'])
#         return render(request, 'account/signup.html', {'form':form})

@method_decorator(login_required, name='dispatch')
class MyInvoiceView(View):
    def get(self, request):
        invoices = Invoice.objects.filter(user=request.user).order_by('-date')
        return render(request, 'account/invoices.html', {'invoices': invoices})



class ReSendEmailView(View):
    def get(self, request):
        form = forms.ResendEmailForm()
        return render(request, 'account/resendemail.html', {'form': form})

    def post(self, request):
        form = forms.ResendEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                obj = models.User.objects.get(email=email)
            except models.User.DoesNotExist:
                messages.error(
                    request,
                    "این ایمیل قبلا ثبت نشده است لطفا ایمیل خود را چک کنید یا ثبت نام کنید")
                return redirect('account:resend_email')
            if obj.is_active==True:
                messages.error(
                    request,
                    "این ایمیل قبلا ثبت ثبت شده است و در حال حاضر فعال است")
                return redirect('account:resend_email')
            else:
                uid = urlsafe_base64_encode(force_bytes(obj.pk))
                hash = activation_token_generator.make_token(obj)
                domain = get_current_site(request)
                url = reverse('account:activate', kwargs={'uid': uid, 'hash': hash})
                protocol = 'https' if request.is_secure() else 'http'
                link = f"{protocol}://{domain}{url}"
                subject = 'Please activate your account'
                body = render_to_string('account/signup_email.html', {
                    'obj': obj,
                    'link': link, })
                to = obj.email
                email = EmailMessage(subject, body, 'alireza.sayfaei@gmail.com', [to])
                email.content_subtype = "html"
                try:
                    email.send()
                except Exception:
                    messages.error(
                        request,
                        "خطا در ارسال ایمیل لطفا دوباره تلاش کنید")
                    return redirect('account:resend_email')


                return render(request, 'account/signup_done.html', {'obj': obj})
            return render(request, 'account/resendemail.html', {'form': form})


