from django.contrib import admin
from . import models


# Register your models here.

class UserAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'is_active', 'email', 'phone', 'discord_id']
    search_fields = ['username']
    list_editable = ['is_active']
    # readonly_fields = ['ref', 'total', 'invoice', 'authority', 'description', 'user_ip']

admin.site.register(models.User, UserAdmin)


class BankEditAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'full_name', 'card_number', 'shaba_number',]
    search_fields = ['user__username', 'full_name']

admin.site.register(models.BankAccount, BankEditAdmin)
# class ProfileAdmin(admin.ModelAdmin):
#     ...
#
# admin.site.register(models.Profile, ProfileAdmin)