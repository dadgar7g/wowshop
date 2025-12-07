from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
#---------------------------------------------------------------------------
class User(AbstractUser):
    email = models.EmailField('Email Address', unique=True)
    phone = models.CharField('Phone Number', max_length=15)
    discord_id = models.CharField('Discord ID', max_length=255)
    last_activation_email_sent = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.username}"

#---------------------------------------------------------------------------
class BankAccount(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100, blank=True, null=True, verbose_name="نام روی کارت")
    card_number = models.CharField(max_length=16, blank=True, null=True, verbose_name="شماره کارت")
    shaba_number = models.CharField(max_length=26, blank=True, null=True, verbose_name="شماره شبا")

    def __str__(self):
        return f"{self.user.username} Bank Account"
