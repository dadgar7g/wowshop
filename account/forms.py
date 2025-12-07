from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from . import models
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
User = get_user_model()
import re

#---------------------------------------------------------------------------
class ResendEmailForm(forms.Form):
    email = forms.EmailField(
        label="ایمیل خود را وارد کنید",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
#---------------------------------------------------------------------------

class SignUpForm(UserCreationForm):
    error_messages = {
        "password_mismatch": "رمزهای عبور با هم مطابقت ندارند.",
    }
    class Meta:
        model = models.User
        exclude = ['is_staff', 'is_active', 'date_joined', 'is_superuser',
                   'groups', 'user_permissions', 'last_login','avatar', 'discord_id', 'password']

        error_messages = {
            'username': {
                'required': "لطفاً نام کاربری را وارد کنید.",
                'unique': "این نام کاربری قبلاً ثبت شده است.",
            },
            'email': {
                'required': "وارد کردن ایمیل الزامی است.",
                'invalid': "ایمیل وارد شده معتبر نیست.",
                'unique': "این ایمیل قبلاً ثبت شده است.",
            },
            'phone': {
                'required': "شماره تلفن را وارد کنید.",
            },
            'password1': {
                'required': "رمز عبور را وارد کنید.",
            },
            'password2': {
                'required': "تکرار رمز عبور را وارد کنید.",
            }
        }

#---------------------------------------------------------------------------
class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'discord_id']

    def clean_discord_id(self):
        discord_id = self.cleaned_data.get('discord_id')
        if discord_id:  # اگر خالی نبود
            pattern = r'^[\w]{1,32}#[0-9]{4}$'
            if not re.match(pattern, discord_id):
                raise forms.ValidationError("فرمت وارد شده صحیح نیست، فرمت صحیح (USERNAME#1234 )")
        return discord_id

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
# class EditProfileForm(forms.ModelForm):
#     # discord_id = forms.CharField(max_length=255, required=False, label="Discord ID")
#
#     class Meta:
#         discord_id = forms.CharField(
#             max_length=37,  # طول حداکثر username + 5 (#1234)
#             required=False,
#             label="Discord ID"
#         )
#         model = User
#         fields = ['first_name', 'last_name', 'phone', 'discord_id']  # ایمیل و یوزرنیم حذف شد
#
#         def clean_discord_id(self):
#             discord_id = self.cleaned_data.get('discord_id')
#             if discord_id:
#                 pattern = r'^[\w]{1,32}#[0-9]{4}$'  # max 32 کاراکتر برای username
#                 if not re.match(pattern, discord_id):
#                     raise forms.ValidationError("Discord ID باید شبیه Dadgar7g#3039 باشد")
#             return discord_id

# ---------------------------------------------------------------------------
class BankAccountForm(forms.ModelForm):
    class Meta:
        model = models.BankAccount
        fields = ['full_name', 'card_number', 'shaba_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # مقدار اولیه Discord ID از Profile
        # self.fields['discord_id'].initial = user.profile.discord_id

# class SignUpForm(forms.ModelForm):
#     class Meta:
#         model = models.User
#         # fields = ['first_name', 'last_name', 'email', 'phone']
#         # field_classes = '__all__'
#         exclude = ['is_staff', 'is_superuser', 'is_active', 'groups', 'user_permissions']


# class SignUpForm(forms.Form):
#     name = forms.CharField(max_length=255)
#     family = forms.CharField(max_length=255)
#     email = forms.EmailField()
#     password1 = forms.CharField(max_length=255 ,widget=forms.PasswordInput())
#     password2 = forms.CharField(max_length=255 ,widget=forms.PasswordInput())
#     # phone = forms.CharField(max_length=255, validators=[])
#     phone = PhoneNumberField()
#
#
#     def clean_name(self):
#         if self.data['name'] == self.data['password1']:
#             raise ValidationError('Password and Name cannot be the same')
#
#         return self.cleaned_data['name']